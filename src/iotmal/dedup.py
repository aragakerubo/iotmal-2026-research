"""Per-binary syscall profiles and how many of them are duplicates.

A hash-grouped split (D2) keeps every window of one binary on one side.
It does nothing about two binaries that behave identically: the benign
programs were generated from one prompt template and may compile to the
same syscall behaviour under different hashes, and Mirai variants are
builds of one source tree. Such pairs sit on both sides of a split and
leak the same way a row split does.

This module aggregates every binary's canonical syscall counts into one
vector, derives three signatures of decreasing strictness, and reports
per class and architecture how many distinct signatures the binaries
have. The aggregate table it builds is also the per-binary feature
store that the binary-level baselines train on.

Signatures:

* ``exact``: the summed count vector itself. Two binaries match only if
  their whole traces add up identically.
* ``profile``: the count vector divided by its total, rounded to two
  decimals. Matches binaries that do the same things in the same
  proportions for different lengths of time.
* ``presence``: which canonical calls occur at all. The loosest: matches
  binaries that use the same set of calls, whatever the counts.
"""

from __future__ import annotations

import polars as pl
import pyarrow.parquet as pq

from iotmal import canonical
from iotmal.canonical import SHARED

HASH, LABEL, ARCH = SHARED
WINDOWS = "windows"
SIGNATURES = ("exact", "profile", "presence")
PROFILE_DECIMALS = 2


def aggregate_binaries(
    parquet: pq.ParquetFile,
    mapping: canonical.Mapping,
    vocabulary: list[str],
    batch_size: int = 200_000,
) -> pl.DataFrame:
    """One row per binary: shared columns, window count, summed canonical counts.

    Reads the file in batches so memory stays bounded; a binary that
    spans batches is summed across them at the end. Column sums are
    ``Int64`` because a long-running binary can exceed ``Int16``.
    """
    parts = []
    for batch in parquet.iter_batches(batch_size=batch_size):
        frame = canonical.canonicalize(pl.from_arrow(batch), mapping, vocabulary)
        parts.append(
            frame.group_by(HASH, LABEL, ARCH, maintain_order=True).agg(
                pl.len().alias(WINDOWS),
                *[pl.col(v).cast(pl.Int64).sum() for v in vocabulary],
            )
        )
    if not parts:
        return pl.DataFrame(
            schema={
                HASH: pl.String,
                LABEL: pl.String,
                ARCH: pl.String,
                WINDOWS: pl.UInt32,
                **{v: pl.Int64 for v in vocabulary},
            }
        )
    return (
        pl.concat(parts)
        .group_by(HASH, LABEL, ARCH, maintain_order=True)
        .agg(pl.col(WINDOWS).sum(), *[pl.col(v).sum() for v in vocabulary])
    )


def add_signatures(binaries: pl.DataFrame, vocabulary: list[str]) -> pl.DataFrame:
    """Append ``exact``, ``profile`` and ``presence`` signature columns.

    Each signature is a 64-bit hash of a string built from the vector, so
    equal vectors give equal signatures and the columns stay small.
    """
    counts = [pl.col(v) for v in vocabulary]
    total = pl.sum_horizontal(counts).cast(pl.Float64)
    exact = pl.concat_str([c.cast(pl.String) for c in counts], separator=",")
    profile = pl.concat_str(
        [
            (c.cast(pl.Float64) / pl.when(total > 0).then(total).otherwise(1.0))
            .round(PROFILE_DECIMALS)
            .cast(pl.String)
            for c in counts
        ],
        separator=",",
    )
    presence = pl.concat_str([(c > 0).cast(pl.Int8).cast(pl.String) for c in counts], separator="")
    return binaries.with_columns(
        exact.hash().alias("exact"),
        profile.hash().alias("profile"),
        presence.hash().alias("presence"),
    )


def duplicate_report(signed: pl.DataFrame) -> pl.DataFrame:
    """Per (architecture, class): binaries, distinct signatures, largest exact group.

    ``distinct_<sig>`` well below ``binaries`` means many binaries behave
    identically under that signature. ``largest_exact`` is the size of
    the biggest set of binaries with the same exact vector.
    """
    return (
        signed.group_by(ARCH, LABEL)
        .agg(
            pl.len().alias("binaries"),
            *[pl.col(s).n_unique().alias(f"distinct_{s}") for s in SIGNATURES],
            pl.col("exact").value_counts().struct.field("count").max().alias("largest_exact"),
        )
        .sort(ARCH, "binaries", descending=[False, True])
    )


def cross_class_report(signed: pl.DataFrame) -> pl.DataFrame:
    """Per architecture and signature: how many signatures occur in more than one class.

    A signature shared by a benign and a malicious binary is a labelling
    conflict no split can fix, and a count of them is part of the
    dataset's limitations.
    """
    rows = []
    for arch, frame in signed.group_by(ARCH, maintain_order=True):
        arch = arch[0]
        for s in SIGNATURES:
            classes_per_sig = frame.group_by(s).agg(pl.col(LABEL).n_unique().alias("n"))
            shared = classes_per_sig.filter(pl.col("n") > 1).height
            rows.append({ARCH: arch, "signature": s, "shared_across_classes": shared})
    return pl.DataFrame(rows).sort(ARCH, "signature")


def render_markdown(duplicates: pl.DataFrame, cross: pl.DataFrame) -> str:
    """Both reports as markdown tables."""
    lines = [
        "| Arch | Class | Binaries | Distinct exact | Distinct profile | Distinct presence "
        "| Largest exact group |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in duplicates.iter_rows(named=True):
        cells = [
            r[ARCH],
            r[LABEL],
            r["binaries"],
            r["distinct_exact"],
            r["distinct_profile"],
            r["distinct_presence"],
            r["largest_exact"],
        ]
        lines.append("| " + " | ".join(str(c) for c in cells) + " |")
    lines += [
        "",
        "| Arch | Signature | Signatures shared across classes |",
        "| --- | --- | --- |",
    ]
    for r in cross.iter_rows(named=True):
        lines.append(f"| {r[ARCH]} | {r['signature']} | {r['shared_across_classes']} |")
    return "\n".join(lines) + "\n"
