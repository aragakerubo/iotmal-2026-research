"""One syscall vocabulary across architectures (D6).

The STRACE tables name their columns ``Call_<syscall>`` with the name
strace printed on that architecture, so the same call shows up as
``Call_mmap2`` on one file and ``Call_mmap`` on another, and some names
are prefixes cut off at a log boundary (``Call_readlin``). This module
loads ``configs/syscall_canonical.yaml``, resolves every raw column name
to one canonical name or to "dropped", derives the fixed vocabulary from
the union of raw names, and rewrites a frame so every architecture has
the same integer columns in the same order, with zero where a call
never appears (D5).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import polars as pl
import yaml

from iotmal.paths import CONFIG_DIR

PREFIX = "Call_"
SHARED = ("Hash", "MalwareFamily", "Arch")
"""Columns every table carries that are not features."""

DTYPE = pl.Int16
"""Wide enough for a sum of aliases over a 20-call window; four bytes narrower than Int64."""


@dataclass(frozen=True)
class Mapping:
    """The alias table and the fragment list from the YAML file."""

    aliases: dict[str, tuple[str, ...]]
    fragments: frozenset[str]

    @classmethod
    def load(cls, path: Path | None = None) -> Mapping:
        """Read the YAML; default path is ``configs/syscall_canonical.yaml``."""
        raw = yaml.safe_load((path or CONFIG_DIR / "syscall_canonical.yaml").read_text())
        aliases = {k: tuple(v) for k, v in (raw.get("aliases") or {}).items()}
        return cls(aliases=aliases, fragments=frozenset(raw.get("fragments") or ()))

    @property
    def alias_to_canonical(self) -> dict[str, str]:
        """Inverse of ``aliases``: raw alias name to canonical name."""
        return {a: c for c, names in self.aliases.items() for a in names}


def strip(column: str) -> str:
    """``Call_mmap2`` -> ``mmap2``; a name without the prefix is returned as is."""
    return column[len(PREFIX) :] if column.startswith(PREFIX) else column


def canonical_names(mapping: Mapping, raw_columns: list[str]) -> list[str]:
    """Derive the sorted vocabulary from the raw column names.

    It holds every raw name that is neither an alias nor a fragment, plus
    every canonical name that has an alias present. A canonical name
    enters the vocabulary only if some raw column maps to it, so the
    vocabulary is exactly what the data can fill.
    """
    inverse = mapping.alias_to_canonical
    names = set()
    for column in raw_columns:
        name = strip(column)
        if name in mapping.fragments:
            continue
        names.add(inverse.get(name, name))
    return sorted(names)


def resolve(mapping: Mapping, column: str, vocabulary: list[str]) -> str | None:
    """Map one raw column to its canonical name, or ``None`` if it is dropped.

    Order of rules: an alias goes to its canonical name; a fragment goes
    to the single vocabulary name that starts with it, or is dropped when
    zero or several do; anything else is its own canonical name.
    """
    name = strip(column)
    inverse = mapping.alias_to_canonical
    if name in inverse:
        return inverse[name]
    if name in mapping.fragments:
        matches = [v for v in vocabulary if v.startswith(name)]
        return matches[0] if len(matches) == 1 else None
    return name


def resolution_table(mapping: Mapping, raw_columns: list[str]) -> pl.DataFrame:
    """One row per raw column: its canonical target (or null) and the rule used."""
    vocabulary = canonical_names(mapping, raw_columns)
    inverse = mapping.alias_to_canonical
    rows = []
    for column in raw_columns:
        name = strip(column)
        target = resolve(mapping, column, vocabulary)
        if name in inverse:
            rule = "alias"
        elif name in mapping.fragments:
            rule = "fragment-folded" if target else "fragment-dropped"
        else:
            rule = "identity"
        rows.append({"column": column, "canonical": target, "rule": rule})
    return pl.DataFrame(rows)


def canonicalize(df: pl.DataFrame, mapping: Mapping, vocabulary: list[str]) -> pl.DataFrame:
    """Rewrite ``df`` onto the vocabulary.

    Every raw ``Call_*`` column is resolved; columns resolving to the
    same canonical name are summed; vocabulary names with no source
    column become zero (D5). Shared columns that exist are kept first.
    Output feature columns are ``Int16`` in vocabulary order, so two
    architectures produce frames with identical schemas.
    """
    sources: dict[str, list[str]] = {v: [] for v in vocabulary}
    for column in df.columns:
        if not column.startswith(PREFIX):
            continue
        target = resolve(mapping, column, vocabulary)
        if target is not None and target in sources:
            sources[target].append(column)

    features = []
    for name in vocabulary:
        cols = sources[name]
        if not cols:
            expr = pl.lit(0, dtype=DTYPE)
        else:
            expr = pl.sum_horizontal([pl.col(c).cast(DTYPE) for c in cols])
        features.append(expr.alias(name))

    shared = [pl.col(c) for c in SHARED if c in df.columns]
    return df.select(shared + features)
