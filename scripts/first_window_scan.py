"""Keep each binary's first N system calls; write the first-window feature stores.

Usage::

    python scripts/first_window_scan.py s3://<bucket>/raw/Yokohama [--arch mips]
        [--features-uri s3://<bucket>/features/binaries]

Reads each strace.parquet once, in batches, and for every prefix N in
``configs/first_window.yaml`` keeps each binary's row N (its first N
calls) or its last row when it made fewer, canonicalised (D6). Writes:

* ``data/binaries/<arch>_first<N>_strace.parquet``: one row per binary
  with the 132 canonical counts of its first N calls and, in
  ``windows``, how many calls those are (gitignored).
* the same files under ``--features-uri``, which defaults to
  ``features/binaries`` in the raw data's bucket when the input is S3.
* ``data/FIRST_WINDOW.md``: per prefix and architecture, the distinct
  first windows of benign and malware binaries and how many are shared
  by both, over the live binaries (D8); then, for the longest prefix,
  the distinct windows per family.

About three minutes for all four files on the notebook; every row is
read once, though only a few rows of each binary are kept.
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


def shared_table(stores: dict[int, pl.DataFrame], vocabulary: list[str]) -> str:
    """Per prefix and architecture: distinct benign and malware first windows, and shared ones."""
    assignment = baseline.load_assignment()
    lines = [
        "| Calls | Arch | Distinct benign | Distinct malware | Shared by benign and malware |",
        "| --- | --- | --- | --- | --- |",
    ]
    for n, store in stores.items():
        signed = dedup.add_signatures(baseline.live_binaries(store, assignment), vocabulary)
        distinct = signed.group_by(dedup.ARCH, baseline.TARGET).agg(pl.col("exact").n_unique())
        shared = dedup.cross_class_report(signed, by=baseline.TARGET).filter(
            pl.col("signature") == "exact"
        )
        for (arch,), part in distinct.sort(dedup.ARCH).group_by(dedup.ARCH, maintain_order=True):
            count = dict(zip(part[baseline.TARGET].to_list(), part["exact"].to_list()))
            both = shared.filter(pl.col(dedup.ARCH) == arch)["shared_across_classes"][0]
            lines.append(
                f"| {n} | {arch} | {count.get(False, 0)} | {count.get(True, 0)} | {both} |"
            )
    return "\n".join(lines) + "\n"


def main(url: str, arch: str | None, features_uri: str | None) -> None:
    """Scan the strace files under ``url``; write the first-window stores and their report."""
    cfg = first_window.FirstWindowConfig.load()
    filesystem, root = pafs.FileSystem.from_uri(url)
    mapping = canonical.Mapping.load()
    union = pl.read_csv(DATA_DIR / "strace_columns.csv")["column"].to_list()
    vocabulary = canonical.canonical_names(mapping, union)
    out_dir = ensure_dir(DATA_DIR / "binaries")
    remote = pafs.FileSystem.from_uri(features_uri) if features_uri else None

    frames: dict[int, list[pl.DataFrame]] = {n: [] for n in cfg.prefixes}
    for entry in manifest.scan(filesystem, root):
        if entry.modality != "strace" or (arch and entry.arch != arch):
            continue
        with filesystem.open_input_file(entry.path) as handle:
            stores = first_window.first_rows(
                pq.ParquetFile(handle), mapping, vocabulary, cfg.prefixes
            )
        for n, store in stores.items():
            name = f"{entry.arch}_{first_window.stem(n)}.parquet"
            store.write_parquet(out_dir / name)
            if remote:
                remote_fs, remote_root = remote
                with remote_fs.open_output_stream(f"{remote_root.rstrip('/')}/{name}") as sink:
                    store.write_parquet(sink)
            frames[n].append(store)
        copied = f" and {features_uri}" if remote else ""
        print(f"{entry.arch}: {len(stores)} stores written to {out_dir}{copied}")

    stores = {n: pl.concat(parts) for n, parts in frames.items()}
    longest = max(cfg.prefixes)
    live = baseline.live_binaries(stores[longest], baseline.load_assignment())
    signed = dedup.add_signatures(live, vocabulary)
    report = (
        f"# First windows\n\nScanned `{url}` on {date.today().isoformat()}"
        + (f", architecture `{arch}` only" if arch else "")
        + ". For each prefix N, one row per binary: the canonical counts of its first N system "
        "calls, or of its whole trace when it made fewer. Counted over the live binaries of the "
        "split (inert and conflict set aside, D8), so the binary counts match `data/SPLIT.md`. "
        "A first window is the exact count vector.\n\n"
        + shared_table(stores, vocabulary)
        + f"\n## Per family, first {longest} calls\n\n"
        "Signatures: exact = the first window's count vector; profile = the vector divided by "
        "its total, rounded to two decimals; presence = which calls occur at all. The second "
        "table counts windows shared by two family labels, malware families included.\n\n"
        + dedup.render_markdown(dedup.duplicate_report(signed), dedup.cross_class_report(signed))
    )
    (DATA_DIR / "FIRST_WINDOW.md").write_text(report)
    print(report)


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
