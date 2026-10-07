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

import hashlib
from pathlib import Path

import polars as pl
import pyarrow.parquet as pq
from pyarrow import fs as pafs

from iotmal import canonical
from iotmal.canonical import SHARED
from iotmal.manifest import ARCHITECTURES
from iotmal.paths import DATA_DIR

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


def load_feature_store(source: str | Path | None = None, stem: str = "strace") -> pl.DataFrame:
    """Concatenate the per-architecture feature-store files from a directory or S3 prefix.

    ``None`` reads ``data/binaries/``; a local path or an ``s3://`` prefix
    reads every ``<arch>_<stem>.parquet`` under it, in path order, for
    the four architectures. The name must match exactly: the whole-trace
    store (``strace``) and the first-window store (``first_strace``) sit
    in one directory, and a suffix glob would read both as one.
    """
    names = {f"{arch}_{stem}.parquet" for arch in ARCHITECTURES}
    if source is None or not str(source).startswith("s3://"):
        where = Path(source or DATA_DIR / "binaries")
        files = sorted(f for f in where.glob("*.parquet") if f.name in names)
        if not files:
            raise FileNotFoundError(f"no <arch>_{stem}.parquet under {where}")
        return pl.concat([pl.read_parquet(f) for f in files])
    filesystem, root = pafs.FileSystem.from_uri(str(source))
    infos = filesystem.get_file_info(pafs.FileSelector(root))
    frames = []
    for info in sorted(infos, key=lambda i: i.path):
        if info.base_name in names:
            with filesystem.open_input_file(info.path) as handle:
                frames.append(pl.read_parquet(handle))
    if not frames:
        raise FileNotFoundError(f"no <arch>_{stem}.parquet under {source}")
    return pl.concat(frames)


def stable_hash(text: pl.Expr) -> pl.Expr:
    """Return a 64-bit BLAKE2b checksum of each string, the same under every library version.

    Polars documents that its own ``hash()`` may change between versions,
    and the behaviour-group ids of the split are built from these values,
    so a polars upgrade would re-deal the split (it did, at polars 2.0).
    """
    return text.map_elements(
        lambda s: int.from_bytes(hashlib.blake2b(s.encode(), digest_size=8).digest(), "big"),
        return_dtype=pl.UInt64,
    )


def add_signatures(binaries: pl.DataFrame, vocabulary: list[str]) -> pl.DataFrame:
    """Append ``exact``, ``profile`` and ``presence`` signature columns.

    Each signature is a 64-bit checksum (``stable_hash``) of a string built
    from the vector, so equal vectors give equal signatures and the
    columns stay small. Every string is built from integers: the profile
    is each count's share of the total in hundredths, rounded half up by
    explicit arithmetic, because float formatting and the default
    rounding mode are not fixed across library versions.
    """
    counts = [pl.col(v).cast(pl.Int64) for v in vocabulary]
    total = pl.sum_horizontal(counts)
    exact = pl.concat_str([c.cast(pl.String) for c in counts], separator=",")
    scale = 10**PROFILE_DECIMALS
    profile = pl.concat_str(
        [
            # floor((count * scale * 2 + total) / (total * 2)) is count / total * scale,
            # rounded half up, in integers
            ((c * scale * 2 + total) // pl.when(total > 0).then(total * 2).otherwise(1)).cast(
                pl.String
            )
            for c in counts
        ],
        separator=",",
    )
    presence = pl.concat_str([(c > 0).cast(pl.Int8).cast(pl.String) for c in counts], separator="")
    return binaries.with_columns(
        stable_hash(exact).alias("exact"),
        stable_hash(profile).alias("profile"),
        stable_hash(presence).alias("presence"),
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


def cross_class_report(signed: pl.DataFrame, by: str = LABEL) -> pl.DataFrame:
    """Per architecture and signature: how many signatures occur in more than one class.

    A signature shared by a benign and a malicious binary is a labelling
    conflict no split can fix, and a count of them is part of the
    dataset's limitations. ``by`` names the class column: the family
    label by default, so two malware families sharing a trace count; a
    benign-or-malware column counts only the sharing that matters to
    detection.
    """
    rows = []
    for arch, frame in signed.group_by(ARCH, maintain_order=True):
        arch = arch[0]
        for s in SIGNATURES:
            classes_per_sig = frame.group_by(s).agg(pl.col(by).n_unique().alias("n"))
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
