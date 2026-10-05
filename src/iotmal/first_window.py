"""The first N system calls of every binary, as feature stores.

There is one STRACE row per call, and row ``i`` counts the calls so far
until the twentieth (``docs/dataset_notes.md``). Row 1 is ``execve``
alone in every binary; row 20 counts the first twenty calls, which for
a dynamically linked program is the dynamic loader (``open`` of the
libraries, ``mmap``, ``mprotect``, ``close``) and for a statically
linked one is the program's own start. D8 raised the possibility that
this prologue alone names the class, because the generated benign
programs link OpenWrt's shared libc and honeypot malware is mostly
static. The tables built here are what the first-window baselines train
on, one per prefix length N in ``configs/first_window.yaml``.

For each N, a binary keeps its row N, or its last row when it made
fewer than N calls, which is then its whole trace. Every table has the
schema of the whole-trace store from ``iotmal.dedup.aggregate_binaries``.
Its ``windows`` column holds the number of calls the kept row counts,
N or fewer; the baseline's feature map reads that column as the trace
length, so the model knows whether the program exited within its first
N calls and nothing about its length beyond them.

It relies on the verified file layout: every binary's rows are one
unbroken block in file order.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import polars as pl
import pyarrow.parquet as pq
import yaml

from iotmal import canonical
from iotmal.dedup import ARCH, HASH, LABEL, WINDOWS
from iotmal.paths import CONFIG_DIR
from iotmal.split import WINDOW

POSITION = "position"


def stem(calls: int) -> str:
    """File stem of the N-call store: ``<arch>_first<N>_strace.parquet``."""
    return f"first{calls}_strace"


@dataclass(frozen=True)
class FirstWindowConfig:
    """The YAML, typed."""

    prefixes: tuple[int, ...]
    ablation_prefix: int
    network_calls: tuple[str, ...]

    @classmethod
    def load(cls, path: Path | None = None) -> FirstWindowConfig:
        """Read ``configs/first_window.yaml`` (or ``path``) and check the prefixes."""
        raw = yaml.safe_load((path or CONFIG_DIR / "first_window.yaml").read_text())
        prefixes = tuple(sorted(int(n) for n in raw["prefixes"]))
        if not prefixes or any(n < 1 or n > WINDOW for n in prefixes):
            raise ValueError(f"prefixes must lie between 1 and {WINDOW}, got {prefixes}")
        ablation = int(raw["ablation_prefix"])
        if ablation not in prefixes:
            raise ValueError(f"ablation_prefix {ablation} is not one of {prefixes}")
        return cls(prefixes, ablation, tuple(raw.get("network_calls") or ()))


def first_rows(
    parquet: pq.ParquetFile,
    mapping: canonical.Mapping,
    vocabulary: list[str],
    prefixes: tuple[int, ...] = (WINDOW,),
    batch_size: int = 200_000,
) -> dict[int, pl.DataFrame]:
    """One table per prefix N: shared columns, ``windows`` = calls counted, canonical counts.

    Each row's position within its binary is counted across batches, by
    carrying every hash's row count forward. A batch keeps the rows at
    the prefix positions and, per hash, its last row before the longest
    prefix, since a short binary's last row can only be known once its
    rows stop. For each N, of the kept rows at or before position N, the
    one with the largest position wins: row N when the binary reached it,
    the last row otherwise. All tables come from one pass over the file.
    Counts are ``Int64`` to match the whole-trace store.
    """
    longest = max(prefixes)
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
        kept = frame.filter(
            pl.col(POSITION).is_in(prefixes) | (last & (pl.col(POSITION) < longest))
        )
        parts.append(canonical.canonicalize(kept, mapping, vocabulary).with_columns(kept[POSITION]))
        counts = frame.group_by(HASH).agg(pl.col(POSITION).max().alias("offset"))
        seen = pl.concat([seen.join(counts, on=HASH, how="anti"), counts])
    schema = {HASH: pl.String, LABEL: pl.String, ARCH: pl.String, WINDOWS: pl.UInt32}
    if not parts:
        empty = pl.DataFrame(schema={**schema, **{v: pl.Int64 for v in vocabulary}})
        return {n: empty for n in prefixes}
    rows = pl.concat(parts)
    # positions are unique within a hash, so each filter keeps one row per
    # binary, in file order
    return {
        n: rows.filter(pl.col(POSITION) <= n)
        .filter(pl.col(POSITION) == pl.col(POSITION).max().over(HASH))
        .select(
            pl.col(HASH, LABEL, ARCH),
            pl.col(POSITION).cast(pl.UInt32).alias(WINDOWS),
            *[pl.col(v).cast(pl.Int64) for v in vocabulary],
        )
        for n in prefixes
    }
