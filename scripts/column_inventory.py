"""Write the STRACE column inventory and the canonical vocabulary.

Usage::

    python scripts/column_inventory.py s3://<bucket>/raw/Yokohama

Reads only the parquet schemas (footers), so it runs in seconds. Writes:

* ``data/strace_columns.csv``: one row per raw ``Call_*`` column with a
  0/1 presence flag per architecture.
* ``data/syscall_resolution.csv``: every raw column, the canonical name
  it resolves to (blank when dropped), and the rule that decided it.
* ``data/syscall_vocabulary.csv``: the canonical names with a 0/1 flag
  per architecture saying whether any raw column of that architecture
  feeds it.
"""

import sys

import polars as pl
import pyarrow.parquet as pq
from pyarrow import fs as pafs

from iotmal import canonical, manifest
from iotmal.paths import DATA_DIR, ensure_dir


def main(url: str) -> None:
    """Read the four strace schemas and write the three CSVs."""
    filesystem, root = pafs.FileSystem.from_uri(url)
    columns_by_arch: dict[str, list[str]] = {}
    for entry in manifest.scan(filesystem, root):
        if entry.modality != "strace" or entry.arch is None:
            continue
        with filesystem.open_input_file(entry.path) as handle:
            names = pq.ParquetFile(handle).schema_arrow.names
        columns_by_arch[entry.arch] = [n for n in names if n.startswith(canonical.PREFIX)]

    archs = sorted(columns_by_arch)
    union = sorted(set().union(*columns_by_arch.values()))
    out = ensure_dir(DATA_DIR)

    inventory = pl.DataFrame(
        {"column": union, **{a: [int(c in columns_by_arch[a]) for c in union] for a in archs}}
    )
    inventory.write_csv(out / "strace_columns.csv")

    mapping = canonical.Mapping.load()
    resolution = canonical.resolution_table(mapping, union)
    resolution.write_csv(out / "syscall_resolution.csv")

    vocabulary = canonical.canonical_names(mapping, union)
    fed = {
        a: {canonical.resolve(mapping, c, vocabulary) for c in columns_by_arch[a]} for a in archs
    }
    pl.DataFrame(
        {"canonical": vocabulary, **{a: [int(v in fed[a]) for v in vocabulary] for a in archs}}
    ).write_csv(out / "syscall_vocabulary.csv")

    dropped = resolution.filter(pl.col("canonical").is_null())["column"].to_list()
    print(f"{len(union)} raw columns -> {len(vocabulary)} canonical; dropped {len(dropped)}:")
    print("  " + " ".join(dropped))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: python scripts/column_inventory.py <s3://bucket/prefix | /local/dir>")
    main(sys.argv[1])
