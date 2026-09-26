"""Scan every raw parquet file and write data/VERIFICATION.md and .json.

Usage::

    python scripts/verify_dataset.py s3://<bucket>/raw/Yokohama [--modality strace]

Runs from the JupyterLab space: each file is read one row group at a
time and only the label and hash columns are loaded, so memory stays
under a few hundred megabytes whatever the file size. The full run over
twelve files takes minutes; ``--modality`` limits it to one kind of
file while iterating.
"""

import argparse
import json
from datetime import date

import pyarrow.parquet as pq
from pyarrow import fs as pafs

from iotmal import manifest, verify
from iotmal.paths import DATA_DIR, ensure_dir


def main(url: str, modality: str | None, sample_groups: int) -> None:
    """Scan the files under ``url`` and write both reports."""
    filesystem, root = pafs.FileSystem.from_uri(url)
    entries = manifest.scan(filesystem, root)
    reports = []
    for entry in entries:
        if entry.modality is None or (modality and entry.modality != modality):
            continue
        with filesystem.open_input_file(entry.path) as handle:
            report = verify.scan_file(pq.ParquetFile(handle), entry.path, sample_groups)
        reports.append(report)
        print(
            f"{entry.arch}/{entry.modality}: {report.rows} rows, "
            f"{report.distinct_hashes} hashes, contiguous={report.contiguous}, "
            f"unknown={report.unknown_rows}, filled_columns={len(report.filled_columns)}"
        )

    out_dir = ensure_dir(DATA_DIR)
    (out_dir / "VERIFICATION.md").write_text(
        f"# Dataset verification\n\nScanned `{url}` on {date.today().isoformat()}"
        + (f", modality `{modality}` only" if modality else "")
        + ".\n\n"
        + verify.render_markdown(reports)
    )
    (out_dir / "verification.json").write_text(
        json.dumps([r.to_dict() for r in reports], indent=2) + "\n"
    )
    print(f"wrote {out_dir / 'VERIFICATION.md'} and verification.json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", help="s3://bucket/prefix or a local directory")
    parser.add_argument("--modality", choices=manifest.MODALITIES)
    parser.add_argument(
        "--sample-groups", type=int, default=3, help="row groups for the fill check"
    )
    args = parser.parse_args()
    main(args.url, args.modality, args.sample_groups)
