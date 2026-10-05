"""Number every STRACE row by its position within its binary, across batches.

There is one row per system call, so a row's position is the number of
calls the binary had made when the row was written; positions start at
1 (``docs/dataset_notes.md``). Reading a file in batches splits some
binaries across two batches, so the count each binary reached is
carried forward. It relies on the verified layout: every binary's rows
are one unbroken block in file order.
"""

from __future__ import annotations

from collections.abc import Iterator

import polars as pl
import pyarrow.parquet as pq

from iotmal.canonical import SHARED

HASH = SHARED[0]
POSITION = "position"


def positioned(parquet: pq.ParquetFile, batch_size: int = 200_000) -> Iterator[pl.DataFrame]:
    """Yield each batch as a frame with a ``position`` column, 1 for a binary's first row."""
    seen = pl.DataFrame(schema={HASH: pl.String, "offset": pl.Int64})
    for batch in parquet.iter_batches(batch_size=batch_size):
        frame = (
            pl.from_arrow(batch)
            .join(seen, on=HASH, how="left", maintain_order="left")
            .with_columns(
                (pl.int_range(1, pl.len() + 1).over(HASH) + pl.col("offset").fill_null(0)).alias(
                    POSITION
                )
            )
            .drop("offset")
        )
        counts = frame.group_by(HASH).agg(pl.col(POSITION).max().alias("offset"))
        seen = pl.concat([seen.join(counts, on=HASH, how="anti"), counts])
        yield frame
