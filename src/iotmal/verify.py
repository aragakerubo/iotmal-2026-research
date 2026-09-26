"""Full-scan facts about one raw parquet file, one row group at a time.

The manifest reads footers only. This module answers the questions that
need the rows: how many of each class, how many Unknown, whether every
row carries a hash, whether the rows of one binary sit together (the
precondition for any sequence model, D2), how rows are spread across
binaries, and which columns carry nulls (the columns D5's zero-fill will
touch).

It never loads a whole file. Row groups in the STRACE tables hold about a
million rows each, and only the two string columns are read per group;
null counts come from the footer statistics without reading data at all.
That keeps the scan inside the memory of the smallest notebook instance
while running straight from S3.

Two further questions need feature columns and are answered on a sample
of row groups: how many distinct binaries each class has (the number
that governs a hash-grouped split, D2), and whether any ``double``
count column carries a repeated non-integer value, which is the
fingerprint of a mean-fill applied before release (D5).
"""

from __future__ import annotations

import statistics
from collections import Counter
from dataclasses import asdict, dataclass, field

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq

LABEL = "MalwareFamily"
HASH = "Hash"
UNKNOWN = "unknown"
"""Label value, compared case-insensitively, that the paper's counts exclude."""

COUNT_PREFIX = "Call_"
"""Feature columns that are counts by construction, so any non-integer value is a fill."""


@dataclass
class FileReport:
    """Everything the scan learned about one file."""

    path: str
    rows: int
    row_groups: int
    class_counts: dict[str, int] = field(default_factory=dict)
    unknown_rows: int = 0
    has_hash: bool = False
    distinct_hashes: int = 0
    hash_runs: int = 0
    hashes_spanning_row_groups: int = 0
    rows_per_hash_min: int = 0
    rows_per_hash_median: float = 0.0
    rows_per_hash_max: int = 0
    null_columns: list[str] = field(default_factory=list)
    hashes_per_class: dict[str, int] = field(default_factory=dict)
    sampled_row_groups: list[int] = field(default_factory=list)
    filled_columns: dict[str, "FillReport"] = field(default_factory=dict)

    @property
    def contiguous(self) -> bool:
        """True when every binary's rows form one unbroken block.

        A run is a maximal stretch of consecutive rows with the same
        hash. If the number of runs equals the number of distinct hashes,
        no hash is split across two places in the file.
        """
        return self.has_hash and self.hash_runs == self.distinct_hashes

    def to_dict(self) -> dict:
        """Plain dict for JSON, with the derived ``contiguous`` included."""
        return {**asdict(self), "contiguous": self.contiguous}


@dataclass
class FillReport:
    """What the sampled rows of one ``double`` count column look like.

    A count column that was mean-filled before release holds integers
    everywhere except the rows that were NaN, which all carry the same
    non-integer value (the column mean). So ``distinct_non_integer == 1``
    with a large ``non_integer_rows`` is the signature; a genuinely
    integer column has ``non_integer_rows == 0``.
    """

    rows_sampled: int
    non_integer_rows: int
    distinct_non_integer: int
    top_value: float | None
    top_value_rows: int


def scan_file(parquet: pq.ParquetFile, path: str, sample_groups: int = 3) -> FileReport:
    """Scan one open parquet file row group by row group.

    The label and hash pass reads every row group. The fill check reads
    the ``double`` count columns of ``sample_groups`` row groups spread
    across the file (first, last and evenly between), because a fill
    applied to the whole file shows in any sample and reading every
    feature column of a hundred million rows from S3 is not worth it.
    """
    meta = parquet.metadata
    schema = parquet.schema_arrow
    names = schema.names
    report = FileReport(path=path, rows=meta.num_rows, row_groups=meta.num_row_groups)
    report.null_columns = _null_columns(meta, names)
    report.has_hash = HASH in names
    report.sampled_row_groups = _spread(meta.num_row_groups, sample_groups)
    report.filled_columns = _fill_check(parquet, schema, report.sampled_row_groups)

    columns = [c for c in (LABEL, HASH) if c in names]
    if not columns:
        return report

    classes: Counter[str] = Counter()
    per_hash: Counter[str] = Counter()
    class_hashes: dict[str, set] = {}
    runs = 0
    spans = 0
    previous = None  # last hash of the previous row group
    for i in range(meta.num_row_groups):
        table = parquet.read_row_group(i, columns=columns)
        if LABEL in columns:
            classes.update(table.column(LABEL).to_pylist())
        if HASH in columns:
            hashes = table.column(HASH).to_pylist()
            per_hash.update(hashes)
            if LABEL in columns:
                # Distinct binaries per class: the set stays small (thousands).
                for label, h in zip(table.column(LABEL).to_pylist(), hashes):
                    class_hashes.setdefault(label, set()).add(h)
            group_runs, first, last = _runs(hashes)
            runs += group_runs
            # A run that continues from the previous group is not a new run,
            # and the hash it belongs to spans a row-group boundary.
            if previous is not None and first == previous:
                runs -= 1
                spans += 1
            previous = last

    report.class_counts = dict(classes.most_common())
    report.unknown_rows = sum(n for c, n in classes.items() if (c or "").lower() == UNKNOWN)
    if per_hash:
        counts = sorted(per_hash.values())
        report.distinct_hashes = len(per_hash)
        report.hash_runs = runs
        report.hashes_spanning_row_groups = spans
        report.rows_per_hash_min = counts[0]
        report.rows_per_hash_median = float(statistics.median(counts))
        report.rows_per_hash_max = counts[-1]
        report.hashes_per_class = {c: len(class_hashes.get(c, ())) for c in report.class_counts}
    return report


def _spread(total: int, k: int) -> list[int]:
    """``k`` row-group indices spread over ``range(total)``, first and last included."""
    if total <= k:
        return list(range(total))
    if k == 1:
        return [0]
    return sorted({round(i * (total - 1) / (k - 1)) for i in range(k)})


def _fill_check(
    parquet: pq.ParquetFile, schema: pa.Schema, groups: list[int]
) -> dict[str, FillReport]:
    """Inspect every ``double`` column named ``Call_*`` over the sampled row groups.

    Columns are read in small batches so memory stays bounded whatever
    the row-group size. Only columns with at least one non-integer value
    are reported; an all-integer ``double`` column is simply a count.
    """
    targets = [
        f.name for f in schema if f.name.startswith(COUNT_PREFIX) and pa.types.is_floating(f.type)
    ]
    if not targets or not groups:
        return {}
    rows = 0
    non_integer: dict[str, int] = dict.fromkeys(targets, 0)
    values: dict[str, Counter] = {t: Counter() for t in targets}
    step = 16  # columns per read; 16 doubles x 1M rows is 128 MB
    for g in groups:
        rows += parquet.metadata.row_group(g).num_rows
        for start in range(0, len(targets), step):
            chunk = targets[start : start + step]
            table = parquet.read_row_group(g, columns=chunk)
            for name in chunk:
                col = table.column(name)
                fractional = pc.not_equal(col, pc.floor(col))
                odd = pc.filter(col, pc.fill_null(fractional, False))
                if len(odd) == 0:
                    continue
                non_integer[name] += len(odd)
                counted = pc.value_counts(odd)
                for item in counted.to_pylist():
                    values[name][item["values"]] += item["counts"]
    reports = {}
    for name in targets:
        if non_integer[name] == 0:
            continue
        top_value, top_rows = values[name].most_common(1)[0]
        reports[name] = FillReport(
            rows_sampled=rows,
            non_integer_rows=non_integer[name],
            distinct_non_integer=len(values[name]),
            top_value=float(top_value),
            top_value_rows=int(top_rows),
        )
    return reports


def _runs(values: list) -> tuple[int, object, object]:
    """Count maximal runs of equal consecutive values; return (runs, first, last)."""
    if not values:
        return 0, None, None
    runs = 1
    for a, b in zip(values, values[1:]):
        if a != b:
            runs += 1
    return runs, values[0], values[-1]


def _null_columns(meta: pq.FileMetaData, names: list[str]) -> list[str]:
    """Columns with at least one null, from footer statistics; no data read.

    A column chunk without statistics is treated as possibly null so the
    list errs on the side of naming it.
    """
    nullable = set()
    for i in range(meta.num_row_groups):
        group = meta.row_group(i)
        for j in range(group.num_columns):
            stats = group.column(j).statistics
            if stats is None or stats.null_count is None or stats.null_count > 0:
                nullable.add(names[j])
    return [n for n in names if n in nullable]


def render_markdown(reports: list[FileReport]) -> str:
    """One summary table, then a class table per file."""
    lines = [
        "| Path | Rows | Row groups | Unknown | Hash | Distinct hashes | Runs | Contiguous "
        "| Spanning groups | Rows/hash min | median | max | Null columns |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in reports:
        has_hash = "yes" if r.has_hash else "no"
        contiguous = "yes" if r.contiguous else "no"
        cells = [
            r.path,
            r.rows,
            r.row_groups,
            r.unknown_rows,
            has_hash,
            r.distinct_hashes,
            r.hash_runs,
            contiguous,
            r.hashes_spanning_row_groups,
            r.rows_per_hash_min,
            f"{r.rows_per_hash_median:g}",
            r.rows_per_hash_max,
            len(r.null_columns),
        ]
        lines.append("| " + " | ".join(str(c) for c in cells) + " |")
    for r in reports:
        lines += ["", f"### {r.path}", "", "| Class | Rows | Binaries |", "| --- | --- | --- |"]
        lines += [
            f"| {c} | {n} | {r.hashes_per_class.get(c, '')} |" for c, n in r.class_counts.items()
        ]
        if r.null_columns:
            lines += ["", "Columns with nulls: " + ", ".join(r.null_columns)]
        if r.sampled_row_groups:
            groups = ", ".join(str(g) for g in r.sampled_row_groups)
            if r.filled_columns:
                lines += [
                    "",
                    f"Non-integer values in `double` count columns, row groups {groups}:",
                    "",
                    "| Column | Rows sampled | Non-integer rows | Distinct values | Top value "
                    "| Rows at top value |",
                    "| --- | --- | --- | --- | --- | --- |",
                ]
                for name, f in r.filled_columns.items():
                    cells = [
                        name,
                        f.rows_sampled,
                        f.non_integer_rows,
                        f.distinct_non_integer,
                        f"{f.top_value:.6g}",
                        f.top_value_rows,
                    ]
                    lines.append("| " + " | ".join(str(c) for c in cells) + " |")
            else:
                lines += [
                    "",
                    f"No non-integer values in any `double` count column (row groups {groups}).",
                ]
    return "\n".join(lines) + "\n"
