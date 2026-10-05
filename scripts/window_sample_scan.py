"""Keep the planned sample of STRACE rows for the H3 leakage experiment.

Usage::

    python scripts/window_sample_scan.py s3://<bucket>/raw/Yokohama [--arch mips]
        [--features-uri s3://<bucket>/features/windows]

Plans every draw of ``configs/leakage.yaml`` from the binaries' row
counts in the whole-trace store (``data/binaries/``), reads each
strace.parquet once in batches, keeps the planned rows canonicalised
(D6), and writes:

* ``data/windows/<arch>_sample_strace.parquet``: every row any draw
  needs, once, with its ``position`` (gitignored).
* the same file under ``--features-uri``, which defaults to
  ``features/windows`` in the raw data's bucket when the input is S3.

A few minutes for all four files on the notebook; every row is read
once.
"""

import argparse

import polars as pl
import pyarrow.parquet as pq
from pyarrow import fs as pafs

from iotmal import canonical, dedup, leakage, manifest
from iotmal.paths import DATA_DIR, ensure_dir

STEM = "sample_strace"


def default_features_uri(url: str) -> str | None:
    """``s3://bucket/...`` -> ``s3://bucket/features/windows``; a local input has no default."""
    if not url.startswith("s3://"):
        return None
    return f"s3://{url[len('s3://') :].split('/')[0]}/features/windows"


def main(url: str, arch: str | None, features_uri: str | None) -> None:
    """Plan the draws, scan the strace files under ``url``, write the sample."""
    cfg = leakage.LeakageConfig.load()
    filesystem, root = pafs.FileSystem.from_uri(url)
    mapping = canonical.Mapping.load()
    union = pl.read_csv(DATA_DIR / "strace_columns.csv")["column"].to_list()
    vocabulary = canonical.canonical_names(mapping, union)
    plan = leakage.plan_sample(dedup.load_feature_store(), cfg)
    out_dir = ensure_dir(DATA_DIR / "windows")
    remote = pafs.FileSystem.from_uri(features_uri) if features_uri else None

    for entry in manifest.scan(filesystem, root):
        if entry.modality != "strace" or (arch and entry.arch != arch):
            continue
        wanted = (
            plan.filter(pl.col(leakage.ARCH) == entry.arch)
            .select(leakage.HASH, leakage.POSITION)
            .unique()
        )
        with filesystem.open_input_file(entry.path) as handle:
            sample = leakage.sample_rows(pq.ParquetFile(handle), mapping, vocabulary, wanted)
        if sample.height != wanted.height:
            raise ValueError(f"{entry.arch}: kept {sample.height} of {wanted.height} planned rows")
        name = f"{entry.arch}_{STEM}.parquet"
        sample.write_parquet(out_dir / name)
        if remote:
            remote_fs, remote_root = remote
            with remote_fs.open_output_stream(f"{remote_root.rstrip('/')}/{name}") as sink:
                sample.write_parquet(sink)
        copied = f" and {features_uri}/{name}" if remote else ""
        print(f"{entry.arch}: {sample.height} rows written to {out_dir / name}{copied}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", help="s3://bucket/prefix or a local directory")
    parser.add_argument("--arch", choices=manifest.ARCHITECTURES)
    parser.add_argument(
        "--features-uri",
        help="where to copy the sample; default s3://<bucket>/features/windows for an S3 input",
    )
    args = parser.parse_args()
    main(args.url, args.arch, args.features_uri or default_features_uri(args.url))
