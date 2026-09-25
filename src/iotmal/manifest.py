"""Inventory of the raw parquet files and a comparison with the paper's counts.

The dataset ships one parquet file per architecture and modality under a
layout like ``<root>/mips/mips/Parquet Format/strace.parquet``. This
module reads only the parquet footers (row count, column count, row
groups), so it is cheap enough to run from a small notebook against S3,
and compares the row counts with the per-family counts the authors
published (``data/paper_counts.csv``), which exclude rows labelled
Unknown. The difference is the number of Unknown rows in each file.

Any fsspec filesystem works: a local directory in tests, S3 in
production. Nothing here needs boto3 or s3fs at import time.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath

import pandas as pd
import pyarrow.parquet as pq
from fsspec import AbstractFileSystem

ARCHITECTURES = ("arm", "mips", "mipsel", "x86")
"""Canonical lower-case names. The paper writes them ARM, MIPS, MIPSEL, x86."""

MODALITIES = ("pcap", "sar", "strace")

_ARCH_ALIASES = {"arms": "arm"}
"""Folder names in the download that differ from the canonical name."""


@dataclass(frozen=True)
class ParquetEntry:
    """One parquet file's footer facts.

    ``arch`` and ``modality`` are ``None`` when the path does not name
    them, so a stray file still appears in the manifest instead of
    being silently dropped.
    """

    path: str
    size_bytes: int
    rows: int
    columns: int
    row_groups: int
    arch: str | None
    modality: str | None


def classify(path: str) -> tuple[str | None, str | None]:
    """Infer (architecture, modality) from a parquet path.

    The architecture is the first path segment that is a known name or
    alias, matched exactly so ``mips`` is never confused with ``mipsel``.
    The modality is the file stem (``strace.parquet`` -> ``strace``).
    """
    parts = PurePosixPath(path).parts
    arch = next(
        (
            _ARCH_ALIASES.get(p.lower(), p.lower())
            for p in parts
            if _ARCH_ALIASES.get(p.lower(), p.lower()) in ARCHITECTURES
        ),
        None,
    )
    stem = PurePosixPath(path).stem.lower()
    modality = stem if stem in MODALITIES else None
    return arch, modality


def scan(fs: AbstractFileSystem, root: str) -> list[ParquetEntry]:
    """List every ``*.parquet`` under ``root`` and read its footer.

    ``root`` is a path on ``fs`` (``bucket/raw/Yokohama`` for S3, a
    directory for the local filesystem). Entries come back sorted by
    path so the rendered manifest is stable across runs.
    """
    entries = []
    for path in sorted(fs.find(root)):
        if not path.endswith(".parquet"):
            continue
        with fs.open(path, "rb") as handle:
            meta = pq.ParquetFile(handle).metadata
        arch, modality = classify(path)
        entries.append(
            ParquetEntry(
                path=path,
                size_bytes=fs.size(path),
                rows=meta.num_rows,
                columns=meta.num_columns,
                row_groups=meta.num_row_groups,
                arch=arch,
                modality=modality,
            )
        )
    return entries


def render_markdown(entries: list[ParquetEntry]) -> str:
    """Render the entries as the table that goes into ``data/MANIFEST.md``."""
    lines = [
        "| Path | Arch | Modality | Bytes | Rows | Columns | Row groups |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for e in entries:
        lines.append(
            f"| {e.path} | {e.arch or ''} | {e.modality or ''} | {e.size_bytes} "
            f"| {e.rows} | {e.columns} | {e.row_groups} |"
        )
    return "\n".join(lines) + "\n"


def paper_totals(paper_counts: pd.DataFrame) -> pd.DataFrame:
    """Sum the paper's per-family counts to one row per (arch, modality).

    ``paper_counts`` has the columns of ``data/paper_counts.csv``:
    ``MalwareFamily, count, Architecture, DataType``. Architecture names
    are lower-cased to match :func:`classify`.
    """
    totals = (
        paper_counts.assign(arch=paper_counts["Architecture"].str.lower())
        .rename(columns={"DataType": "modality", "count": "rows_in_paper"})
        .groupby(["arch", "modality"], as_index=False)["rows_in_paper"]
        .sum()
    )
    return totals


def compare(entries: list[ParquetEntry], paper_counts: pd.DataFrame) -> pd.DataFrame:
    """Join file row counts with the paper's totals; the gap is Unknown rows.

    One row per (arch, modality) in either source. ``rows_in_file`` is
    NaN for a file that is missing from the scan (the ARM tarball not yet
    extracted, say), and ``rows_in_paper`` is NaN for a file the paper
    does not count. ``unknown_rows`` is file minus paper; a negative
    value means the file holds fewer rows than the paper reports.
    """
    files = pd.DataFrame(
        [
            {"arch": e.arch, "modality": e.modality, "rows_in_file": e.rows}
            for e in entries
            if e.arch and e.modality
        ]
    )
    if files.empty:
        files = pd.DataFrame(columns=["arch", "modality", "rows_in_file"])
    merged = files.merge(paper_totals(paper_counts), on=["arch", "modality"], how="outer")
    merged["unknown_rows"] = merged["rows_in_file"] - merged["rows_in_paper"]
    return merged.sort_values(["arch", "modality"]).reset_index(drop=True)


def render_comparison(comparison: pd.DataFrame) -> str:
    """Render :func:`compare`'s frame as a markdown table with a share column."""
    lines = [
        "| Arch | Modality | Rows in file | Rows in paper | Unknown rows | Unknown % |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in comparison.itertuples(index=False):
        share = (
            f"{100 * row.unknown_rows / row.rows_in_file:.1f}"
            if pd.notna(row.unknown_rows) and row.rows_in_file
            else ""
        )
        lines.append(
            f"| {row.arch} | {row.modality} | {_int(row.rows_in_file)} "
            f"| {_int(row.rows_in_paper)} | {_int(row.unknown_rows)} | {share} |"
        )
    return "\n".join(lines) + "\n"


def _int(value: float) -> str:
    """Format a possibly-NaN count as an integer string, blank for NaN."""
    return "" if pd.isna(value) else str(int(value))
