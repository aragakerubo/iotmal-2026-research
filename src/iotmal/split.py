"""Assign every binary to train, validation or test without leaking behaviour.

The unit of assignment is a group of binaries that share one behaviour
signature (``configs/split.yaml``, ``group_by``), so two binaries with
identical traces can never sit on opposite sides. Within each
architecture and family the groups are shuffled with a seed of their
own, derived from the configured seed and the family's name, and dealt
out greedily: each group goes to whichever split is furthest
below its target share of binaries, which keeps the split stratified
by family even when one group holds hundreds of binaries. Because each
family has its own seed, a change to one family's binaries never
re-deals another family.

Before assignment, inert binaries are set aside. A trace of fewer than
``max_calls`` system calls with no network call is a program that never
reached its own logic, and on ARM that describes most of the benign
class (D8). They are reported, never trained on or scored.

Window arithmetic: there is one STRACE row per system call. Row ``i``
of a binary counts its first ``i`` calls while ``i`` is at most twenty,
and the twenty calls ending at call ``i`` after that, so a binary with
``w`` rows (the store's ``windows`` column) has a trace of ``w`` calls.
"""

from __future__ import annotations

import zlib
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import polars as pl
import yaml

from iotmal.canonical import SHARED
from iotmal.paths import CONFIG_DIR

HASH, LABEL, ARCH = SHARED
WINDOW = 20
"""Calls per full window; rows before the twentieth count a shorter prefix."""
SPLITS = ("train", "val", "test")
INERT = "inert"
CONFLICT = "conflict"
"""Split value for binaries whose behaviour signature is both benign and malicious."""
BENIGN = "Benign"


@dataclass(frozen=True)
class SplitConfig:
    """The YAML, typed."""

    seed: int
    fractions: dict[str, float]
    group_by: str
    inert_max_calls: int
    inert_network_calls: tuple[str, ...]
    drop_labels: frozenset[str] = field(default_factory=frozenset)

    @classmethod
    def load(cls, path: Path | None = None) -> SplitConfig:
        """Read ``configs/split.yaml`` (or ``path``) and validate the shares."""
        raw = yaml.safe_load((path or CONFIG_DIR / "split.yaml").read_text())
        fractions = {k: float(v) for k, v in raw["fractions"].items()}
        if set(fractions) != set(SPLITS) or abs(sum(fractions.values()) - 1.0) > 1e-9:
            raise ValueError(f"fractions must name {SPLITS} and sum to 1, got {fractions}")
        if raw["group_by"] not in ("exact", "profile", "hash"):
            raise ValueError(f"group_by must be exact, profile or hash, got {raw['group_by']}")
        return cls(
            seed=int(raw["seed"]),
            fractions=fractions,
            group_by=raw["group_by"],
            inert_max_calls=int(raw["inert"]["max_calls"]),
            inert_network_calls=tuple(raw["inert"]["network_calls"]),
            drop_labels=frozenset(raw.get("drop_labels") or ()),
        )


def family_rng(seed: int, arch: str, family: str) -> np.random.Generator:
    """Return the random generator that deals one architecture's family.

    The configured seed is combined with a CRC-32 of ``arch/family``,
    which is the same in every run and on every machine; Python's own
    ``hash`` of a string changes between runs and cannot be used.
    """
    return np.random.default_rng([seed, zlib.crc32(f"{arch}/{family}".encode())])


def trace_length(windows: pl.Expr) -> pl.Expr:
    """Return the number of system calls in a trace with ``windows`` rows.

    One row per call, so the two are equal. The function stays so that
    every caller states which of the two quantities it means.
    """
    return windows


def mark_inert(signed: pl.DataFrame, cfg: SplitConfig) -> pl.DataFrame:
    """Add a boolean ``inert`` column: short trace and no network call at all."""
    present = [c for c in cfg.inert_network_calls if c in signed.columns]
    network = pl.sum_horizontal([pl.col(c) for c in present]) if present else pl.lit(0)
    return signed.with_columns(
        ((trace_length(pl.col("windows")) < cfg.inert_max_calls) & (network == 0)).alias(INERT)
    )


def assign(signed: pl.DataFrame, cfg: SplitConfig) -> pl.DataFrame:
    """One row per binary: shared columns, ``group``, ``inert``, ``split``.

    ``signed`` is the per-binary feature store with signature columns
    (``dedup.add_signatures``). Rows whose label is in ``drop_labels`` are
    removed; inert rows get split ``inert``; rows whose group holds both
    benign and malicious binaries within an architecture get split
    ``conflict``, since identical behaviour with opposite labels can be
    neither trained on nor scored; the rest are dealt out per architecture and
    family in whole groups. A group whose binaries carry more than one
    malware family is dealt once, under the family that holds most of
    them, so it cannot be dealt twice and land on two sides. Groups are
    scoped to an architecture, so the
    same signature on two architectures is two groups, which is what
    leave-one-architecture-out needs.
    """
    frame = signed.filter(~pl.col(LABEL).is_in(list(cfg.drop_labels)))
    frame = mark_inert(frame, cfg)
    key = HASH if cfg.group_by == "hash" else cfg.group_by
    frame = frame.with_columns(
        pl.concat_str([pl.col(ARCH), pl.col(key).cast(pl.String)], separator=":").alias("group")
    )
    # A group conflicts only when it mixes benign and malicious binaries. Two
    # malware labels on one trace (190 x86 Mirai binaries share a trace with one
    # labelled Generic) agree on the detection target, and the family
    # experiment selects its own classes (D7), so they are not a conflict here.
    sides_per_group = (
        frame.filter(~pl.col(INERT))
        .with_columns((pl.col(LABEL) == BENIGN).alias("is_benign"))
        .group_by("group")
        .agg(pl.col("is_benign").n_unique().alias("n_sides"))
    )
    conflicted = set(sides_per_group.filter(pl.col("n_sides") > 1)["group"].to_list())
    frame = frame.with_columns(pl.col("group").is_in(list(conflicted)).alias(CONFLICT))

    # One family per group for dealing: the most common label in the group,
    # ties to the alphabetically first. On x86 one trace is shared by 190 Mirai
    # binaries and one Generic; dealt per label, the two copies drew separately.
    dealer = (
        frame.group_by("group", LABEL)
        .len()
        .sort(["group", "len", LABEL], descending=[False, True, False])
        .group_by("group", maintain_order=True)
        .agg(pl.col(LABEL).first().alias("deal_as"))
    )
    frame = frame.join(dealer, on="group", how="left", maintain_order="left")

    pieces = []
    for (arch, label), part in frame.group_by(ARCH, "deal_as", maintain_order=True):
        live = part.filter(~pl.col(INERT) & ~pl.col(CONFLICT))
        dead = part.filter(pl.col(INERT)).with_columns(pl.lit(INERT).alias("split"))
        clash = part.filter(~pl.col(INERT) & pl.col(CONFLICT)).with_columns(
            pl.lit(CONFLICT).alias("split")
        )
        pieces.append(dead.select(HASH, LABEL, ARCH, "group", INERT, "split"))
        pieces.append(clash.select(HASH, LABEL, ARCH, "group", INERT, "split"))
        if live.is_empty():
            continue
        sizes = live.group_by("group").len().sort("group")
        order = family_rng(cfg.seed, arch, label).permutation(sizes.height)
        groups = sizes["group"].to_list()
        counts = sizes["len"].to_list()
        total = sum(counts)
        got = dict.fromkeys(SPLITS, 0)
        where: dict[str, str] = {}
        for i in order:
            # The split furthest below its target share, measured as a fraction
            # of the target, takes the next group. Ties go in SPLITS order, so
            # a family with one group lands in train.
            target = {s: cfg.fractions[s] * total for s in SPLITS}
            deficit = {s: (got[s] / target[s]) if target[s] > 0 else float("inf") for s in SPLITS}
            chosen = min(SPLITS, key=lambda s: deficit[s])
            where[groups[i]] = chosen
            got[chosen] += counts[i]
        assigned = live.with_columns(
            pl.col("group").replace_strict(where, default=None).alias("split")
        )
        pieces.append(assigned.select(HASH, LABEL, ARCH, "group", INERT, "split"))
    return pl.concat(pieces).sort(ARCH, LABEL, "split", HASH)


def summary(assignment: pl.DataFrame) -> pl.DataFrame:
    """Per architecture and family: binaries, inert, conflict, groups, binaries per split."""
    live = assignment.filter(pl.col("split").is_in(list(SPLITS)))
    base = assignment.group_by(ARCH, LABEL).agg(
        pl.len().alias("binaries"),
        pl.col(INERT).sum().alias("inert"),
        (pl.col("split") == CONFLICT).sum().alias("conflict"),
    )
    groups = live.group_by(ARCH, LABEL).agg(pl.col("group").n_unique().alias("groups"))
    per_split = (
        live.group_by(ARCH, LABEL, "split")
        .len()
        .pivot(on="split", index=[ARCH, LABEL], values="len")
        .fill_null(0)
    )
    for s in SPLITS:
        if s not in per_split.columns:
            per_split = per_split.with_columns(pl.lit(0).alias(s))
    out = base.join(groups, on=[ARCH, LABEL], how="left").join(
        per_split.select(ARCH, LABEL, *SPLITS), on=[ARCH, LABEL], how="left"
    )
    # The class name breaks ties, so two classes of one size print in one order.
    return out.fill_null(0).sort(ARCH, "binaries", LABEL, descending=[False, True, False])


def check(assignment: pl.DataFrame) -> None:
    """Raise if any group or hash appears in more than one of train, val, test.

    Groups already carry the architecture; hashes are checked within an
    architecture too, since one binary never appears in two architectures.
    """
    live = assignment.filter(pl.col("split").is_in(list(SPLITS)))
    for col in ("group", HASH):
        spread = live.group_by(ARCH, col).agg(pl.col("split").n_unique().alias("n"))
        leaked = spread.filter(pl.col("n") > 1)
        if not leaked.is_empty():
            raise AssertionError(f"{leaked.height} {col} values appear in more than one split")


def render_markdown(table: pl.DataFrame) -> str:
    """Render the summary as a markdown table."""
    lines = [
        "| Arch | Class | Binaries | Inert | Conflict | Groups | Train | Val | Test |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in table.iter_rows(named=True):
        cells = [
            r[ARCH],
            r[LABEL],
            r["binaries"],
            r["inert"],
            r["conflict"],
            r["groups"],
            r["train"],
            r["val"],
            r["test"],
        ]
        lines.append("| " + " | ".join(str(c) for c in cells) + " |")
    return "\n".join(lines) + "\n"
