"""Keep each binary's first twenty system calls; write the first-window feature store.

Usage::

    python scripts/first_window_scan.py s3://<bucket>/raw/Yokohama [--arch mips]
        [--features-uri s3://<bucket>/features/binaries]

Reads each strace.parquet in batches, keeps each binary's twentieth row
(its first twenty calls) or its last row when it made fewer, canonicalises
it (D6), and writes:

* ``data/binaries/<arch>_first_strace.parquet``: one row per binary with
  the 132 canonical counts of its first twenty calls and, in ``windows``,
  how many calls those are (gitignored).
* the same file under ``--features-uri``, which defaults to
  ``features/binaries`` in the raw data's bucket when the input is S3.
* ``data/FIRST_WINDOW.md``: distinct first windows per class and
  architecture over the live binaries (D8), how many first windows
  occur in more than one family, and how many are shared by a benign
  and a malware binary.

About ten to twenty minutes for all four files on the notebook; every
row is read once, though only one row of each binary is kept.
"""

import argparse
from datetime import date

import polars as pl
import pyarrow.parquet as pq
from pyarrow import fs as pafs

from iotmal import baseline, canonical, dedup, first_window, manifest
from iotmal.paths import DATA_DIR, ensure_dir


def default_features_uri(url: str) -> str | None:
    """``s3://bucket/...`` -> ``s3://bucket/features/binaries``; a local input has no default."""
    if not url.startswith("s3://"):
        return None
    return f"s3://{url[len('s3://') :].split('/')[0]}/features/binaries"


def main(url: str, arch: str | None, features_uri: str | None) -> None:
    """Scan the strace files under ``url``; write the first-window store and its report."""
    filesystem, root = pafs.FileSystem.from_uri(url)
    mapping = canonical.Mapping.load()
    union = pl.read_csv(DATA_DIR / "strace_columns.csv")["column"].to_list()
    vocabulary = canonical.canonical_names(mapping, union)
    out_dir = ensure_dir(DATA_DIR / "binaries")
    remote = pafs.FileSystem.from_uri(features_uri) if features_uri else None

    frames = []
    for entry in manifest.scan(filesystem, root):
        if entry.modality != "strace" or (arch and entry.arch != arch):
            continue
        with filesystem.open_input_file(entry.path) as handle:
            first = first_window.first_rows(pq.ParquetFile(handle), mapping, vocabulary)
        name = f"{entry.arch}_{first_window.STEM}.parquet"
        first.write_parquet(out_dir / name)
        if remote:
            remote_fs, remote_root = remote
            with remote_fs.open_output_stream(f"{remote_root.rstrip('/')}/{name}") as sink:
                first.write_parquet(sink)
        frames.append(first)
        copied = f" and {features_uri}/{name}" if remote else ""
        print(f"{entry.arch}: {first.height} binaries written to {out_dir / name}{copied}")

    live = baseline.live_binaries(pl.concat(frames), baseline.load_assignment())
    signed = dedup.add_signatures(live, vocabulary)
    duplicates = dedup.duplicate_report(signed)
    cross = dedup.cross_class_report(signed)
    detection = dedup.cross_class_report(signed, by=baseline.TARGET).filter(
        pl.col("signature") == "exact"
    )
    shared = "\n".join(
        f"| {r['Arch']} | {r['shared_across_classes']} |" for r in detection.iter_rows(named=True)
    )
    (DATA_DIR / "FIRST_WINDOW.md").write_text(
        f"# First windows\n\nScanned `{url}` on {date.today().isoformat()}"
        + (f", architecture `{arch}` only" if arch else "")
        + ". One row per binary: the canonical counts of its first twenty system calls, "
        "or of its whole trace when it made fewer. "
        "Counted over the live binaries of the split (inert and conflict set aside, D8), "
        "so the binary counts match `data/SPLIT.md`.\n\n"
        "Signatures: exact = the first window's count vector; profile = the vector divided by "
        "its total, rounded to two decimals; presence = which calls occur at all.\n\n"
        + dedup.render_markdown(duplicates, cross)
        + "\nThe table above counts first windows shared by two family labels, malware "
        "families included. Shared by a benign and a malware binary:\n\n"
        "| Arch | Exact first windows shared by benign and malware |\n| --- | --- |\n"
        + shared
        + "\n"
    )
    print(dedup.render_markdown(duplicates, cross))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", help="s3://bucket/prefix or a local directory")
    parser.add_argument("--arch", choices=manifest.ARCHITECTURES)
    parser.add_argument(
        "--features-uri",
        help="where to copy the store; default s3://<bucket>/features/binaries for an S3 input",
    )
    args = parser.parse_args()
    main(args.url, args.arch, args.features_uri or default_features_uri(args.url))
