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
"""

from __future__ import annotations

import statistics
from collections import Counter
from dataclasses import asdict, dataclass, field

import pyarrow.parquet as pq

LABEL = "MalwareFamily"
HASH = "Hash"
UNKNOWN = "unknown"
"""Label value, compared case-insensitively, that the paper's counts exclude."""


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


def scan_file(parquet: pq.ParquetFile, path: str) -> FileReport:
    """Scan one open parquet file row group by row group."""
    meta = parquet.metadata
    names = parquet.schema_arrow.names
    report = FileReport(path=path, rows=meta.num_rows, row_groups=meta.num_row_groups)
    report.null_columns = _null_columns(meta, names)
    report.has_hash = HASH in names

    columns = [c for c in (LABEL, HASH) if c in names]
    if not columns:
        return report

    classes: Counter[str] = Counter()
    per_hash: Counter[str] = Counter()
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
    return report


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
        lines += ["", f"### {r.path}", "", "| Class | Rows |", "| --- | --- |"]
        lines += [f"| {c} | {n} |" for c, n in r.class_counts.items()]
        if r.null_columns:
            lines += ["", "Columns with nulls: " + ", ".join(r.null_columns)]
    return "\n".join(lines) + "\n"
