"""Aggregate every binary's syscall counts and count near-duplicates.

Usage::

    python scripts/dedup_scan.py s3://<bucket>/raw/Yokohama [--arch mips]

Reads each strace.parquet in batches, canonicalizes (D6), sums per
binary, and writes:

* ``data/binaries/<arch>_strace.parquet``: one row per binary with the
  132 canonical sums (the per-binary feature store; gitignored).
* ``data/DEDUP.md``: distinct signatures per class and architecture,
  and signatures shared across classes.

About ten to twenty minutes for all four files on the notebook; every
feature column of every row is read once.
"""

import argparse
from datetime import date

import polars as pl
import pyarrow.parquet as pq
from pyarrow import fs as pafs

from iotmal import canonical, dedup, manifest
from iotmal.paths import DATA_DIR, ensure_dir


def main(url: str, arch: str | None) -> None:
    """Scan the strace files under ``url``; write the feature store and the report."""
    filesystem, root = pafs.FileSystem.from_uri(url)
    mapping = canonical.Mapping.load()
    out_dir = ensure_dir(DATA_DIR / "binaries")

    signed_frames = []
    for entry in manifest.scan(filesystem, root):
        if entry.modality != "strace" or (arch and entry.arch != arch):
            continue
        with filesystem.open_input_file(entry.path) as handle:
            parquet = pq.ParquetFile(handle)
            raw = [n for n in parquet.schema_arrow.names if n.startswith(canonical.PREFIX)]
            # The vocabulary is derived from the union of all four files so every
            # architecture's table has the same columns; the committed inventory holds it.
            union = pl.read_csv(DATA_DIR / "strace_columns.csv")["column"].to_list()
            vocabulary = canonical.canonical_names(mapping, union)
            binaries = dedup.aggregate_binaries(parquet, mapping, vocabulary)
        binaries.write_parquet(out_dir / f"{entry.arch}_strace.parquet")
        signed = dedup.add_signatures(binaries, vocabulary)
        signed_frames.append(signed)
        print(
            f"{entry.arch}: {binaries.height} binaries, {len(raw)} raw -> "
            f"{len(vocabulary)} canonical columns, "
            f"{signed['exact'].n_unique()} distinct exact vectors"
        )

    signed = pl.concat(signed_frames)
    duplicates = dedup.duplicate_report(signed)
    cross = dedup.cross_class_report(signed)
    (DATA_DIR / "DEDUP.md").write_text(
        f"# Near-duplicate binaries\n\nScanned `{url}` on {date.today().isoformat()}"
        + (f", architecture `{arch}` only" if arch else "")
        + ".\n\nSignatures: exact = summed canonical count vector; profile = the vector "
        "divided by its total, rounded to two decimals; presence = which calls occur at all.\n\n"
        + dedup.render_markdown(duplicates, cross)
    )
    print(dedup.render_markdown(duplicates, cross))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", help="s3://bucket/prefix or a local directory")
    parser.add_argument("--arch", choices=manifest.ARCHITECTURES)
    args = parser.parse_args()
    main(args.url, args.arch)
