"""The first twenty system calls of every binary, as a feature store.

There is one STRACE row per call, and row ``i`` counts the calls so far
until the twentieth (``docs/dataset_notes.md``). Row 1 is ``execve``
alone in every binary; row 20 counts the first twenty calls, which for
a dynamically linked program is the dynamic loader (``open`` of the
libraries, ``mmap``, ``mprotect``, ``close``) and for a statically
linked one is the program's own start. D8 raised the possibility that
this prologue alone names the class, because the generated benign
programs link OpenWrt's shared libc and honeypot malware is mostly
static. The table built here is what the first-window baseline trains
on.

Each binary keeps its twentieth row, or its last row when it made fewer
than twenty calls, which is then its whole trace. The table has the
schema of the whole-trace store from ``iotmal.dedup.aggregate_binaries``.
Its ``windows`` column holds the number of calls the kept row counts,
twenty or fewer; the baseline's feature map reads that column as the
trace length, so the model knows whether the program exited within its
first twenty calls and nothing about its length beyond them.

It relies on the verified file layout: every binary's rows are one
unbroken block in file order.
"""

from __future__ import annotations

import polars as pl
import pyarrow.parquet as pq

from iotmal import canonical
from iotmal.dedup import ARCH, HASH, LABEL, WINDOWS
from iotmal.split import WINDOW

STEM = "first_strace"
"""File stem: the store is written as ``<arch>_first_strace.parquet``."""

POSITION = "position"


def first_rows(
    parquet: pq.ParquetFile,
    mapping: canonical.Mapping,
    vocabulary: list[str],
    batch_size: int = 200_000,
) -> pl.DataFrame:
    """One row per binary: shared columns, ``windows`` = calls counted, canonical counts.

    Each row's position within its binary is counted across batches, by
    carrying every hash's row count forward. A batch keeps the row at
    position twenty and, per hash, its last row before twenty, since a
    short binary's last row can only be known once its rows stop. Of the
    rows kept for one hash, the one with the largest position wins: row
    twenty when the binary reached it, the last row otherwise. Counts are
    ``Int64`` to match the whole-trace store.
    """
    seen = pl.DataFrame(schema={HASH: pl.String, "offset": pl.Int64})
    parts = []
    for batch in parquet.iter_batches(batch_size=batch_size):
        frame = (
            pl.from_arrow(batch)
            .join(seen, on=HASH, how="left", maintain_order="left")
            .with_columns(
                (pl.int_range(1, pl.len() + 1).over(HASH) + pl.col("offset").fill_null(0)).alias(
                    POSITION
                )
            )
        )
        last = pl.col(POSITION) == pl.col(POSITION).max().over(HASH)
        kept = frame.filter((pl.col(POSITION) == WINDOW) | (last & (pl.col(POSITION) < WINDOW)))
        parts.append(canonical.canonicalize(kept, mapping, vocabulary).with_columns(kept[POSITION]))
        counts = frame.group_by(HASH).agg(pl.col(POSITION).max().alias("offset"))
        seen = pl.concat([seen.join(counts, on=HASH, how="anti"), counts])
    schema = {HASH: pl.String, LABEL: pl.String, ARCH: pl.String, WINDOWS: pl.UInt32}
    if not parts:
        return pl.DataFrame(schema={**schema, **{v: pl.Int64 for v in vocabulary}})
    # positions are unique within a hash, so this keeps one row per binary,
    # in file order
    return (
        pl.concat(parts)
        .filter(pl.col(POSITION) == pl.col(POSITION).max().over(HASH))
        .select(
            pl.col(HASH, LABEL, ARCH),
            pl.col(POSITION).cast(pl.UInt32).alias(WINDOWS),
            *[pl.col(v).cast(pl.Int64) for v in vocabulary],
        )
    )
