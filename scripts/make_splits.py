"""Assign every binary to train, validation, test or inert; write the split files.

Usage::

    python scripts/make_splits.py                      # reads data/binaries/*.parquet
    python scripts/make_splits.py s3://<bucket>/features/binaries

Reads the per-binary feature store written by scripts/dedup_scan.py,
adds the behaviour signatures, applies configs/split.yaml, checks that
no group or hash crosses a split, and writes:

* ``data/splits/<arch>.csv``: Hash, MalwareFamily, Arch, group, inert,
  split; committed, since the reproducibility package needs them.
* ``data/SPLIT.md``: binaries, inert, groups and per-split counts for
  every architecture and family.

Seconds on the notebook.
"""

import sys
from datetime import date

import polars as pl

from iotmal import dedup, split
from iotmal.paths import DATA_DIR, ensure_dir


def main(source: str | None) -> None:
    """Build, check and write the splits."""
    cfg = split.SplitConfig.load()
    vocabulary = pl.read_csv(DATA_DIR / "syscall_vocabulary.csv")["canonical"].to_list()
    binaries = dedup.load_feature_store(source)
    signed = dedup.add_signatures(binaries, vocabulary)
    assignment = split.assign(signed, cfg)
    split.check(assignment)

    out = ensure_dir(DATA_DIR / "splits")
    for (arch,), part in assignment.group_by(split.ARCH, maintain_order=True):
        part.write_csv(out / f"{arch}.csv")
    table = split.summary(assignment)
    (DATA_DIR / "SPLIT.md").write_text(
        f"# Splits\n\nBuilt on {date.today().isoformat()} with seed {cfg.seed}, grouped by "
        f"`{cfg.group_by}`, shares {cfg.fractions}, inert = fewer than {cfg.inert_max_calls} "
        "calls and no network call. Inert binaries are excluded from every split.\n\n"
        + split.render_markdown(table)
    )
    print(split.render_markdown(table))
    print(f"wrote {len(list(out.glob('*.csv')))} split files and data/SPLIT.md")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
