"""Every raw STRACE column resolves; aliases sum; fragments fold or drop; archs match."""

import csv

import polars as pl
import pytest

from iotmal import canonical
from iotmal.paths import DATA_DIR


@pytest.fixture(scope="module")
def mapping():
    return canonical.Mapping.load()


@pytest.fixture(scope="module")
def inventory():
    """The committed union of raw columns with per-architecture presence."""
    with open(DATA_DIR / "strace_columns.csv", newline="") as f:
        rows = list(csv.DictReader(f))
    archs = [k for k in rows[0] if k != "column"]
    by_arch = {a: [r["column"] for r in rows if r[a] == "1"] for a in archs}
    return [r["column"] for r in rows], by_arch


def test_every_alias_and_fragment_in_the_yaml_is_a_real_raw_column(mapping, inventory):
    union = {canonical.strip(c) for c in inventory[0]}
    for alias in mapping.alias_to_canonical:
        assert alias in union, alias
    for fragment in mapping.fragments:
        assert fragment in union, fragment


def test_no_raw_name_is_both_an_alias_and_a_fragment_or_a_canonical_name(mapping):
    aliases = set(mapping.alias_to_canonical)
    assert not aliases & mapping.fragments
    assert not set(mapping.aliases) & aliases
    assert not set(mapping.aliases) & mapping.fragments


def test_aliases_fold_onto_their_canonical_name(mapping, inventory):
    vocabulary = canonical.canonical_names(mapping, inventory[0])
    assert canonical.resolve(mapping, "Call_mmap2", vocabulary) == "mmap"
    assert canonical.resolve(mapping, "Call__llseek", vocabulary) == "lseek"
    assert canonical.resolve(mapping, "Call_getuid32", vocabulary) == "getuid"
    assert canonical.resolve(mapping, "Call_syscall_0x193", vocabulary) == "clock_gettime"
    assert canonical.resolve(mapping, "Call_set_tls", vocabulary) == "set_thread_area"
    assert canonical.resolve(mapping, "Call_statx", vocabulary) == "stat"
    assert canonical.resolve(mapping, "Call_openat", vocabulary) == "open"
    assert "mmap2" not in vocabulary and "mmap" in vocabulary


def test_fragments_fold_only_onto_a_unique_prefix_match(mapping, inventory):
    vocabulary = canonical.canonical_names(mapping, inventory[0])
    # one vocabulary name starts with these
    assert canonical.resolve(mapping, "Call_readlin", vocabulary) == "readlink"
    assert canonical.resolve(mapping, "Call_socke", vocabulary) == "socket"
    assert canonical.resolve(mapping, "Call_setso", vocabulary) == "setsockopt"
    assert canonical.resolve(mapping, "Call_getd", vocabulary) == "getdents"
    assert canonical.resolve(mapping, "Call_rt_sigact", vocabulary) == "rt_sigaction"
    # several do (write/writev, time/times, clock_gettime/clock_nanosleep): dropped
    assert canonical.resolve(mapping, "Call_wri", vocabulary) is None
    assert canonical.resolve(mapping, "Call_tim", vocabulary) is None
    assert canonical.resolve(mapping, "Call_cloc", vocabulary) is None
    assert canonical.resolve(mapping, "Call_g", vocabulary) is None


def test_the_resolution_table_covers_every_raw_column_with_one_rule(mapping, inventory):
    table = canonical.resolution_table(mapping, inventory[0])
    assert table.height == len(inventory[0]) == 181
    rules = dict(table.group_by("rule").len().iter_rows())
    assert rules == {
        "identity": 123,
        "alias": 35,
        "fragment-folded": 8,
        "fragment-dropped": 15,
    }
    assert table.filter(pl.col("rule") == "fragment-dropped")["canonical"].null_count() == 15


def test_every_architecture_yields_the_same_vocabulary(mapping, inventory):
    union, by_arch = inventory
    vocabulary = canonical.canonical_names(mapping, union)
    assert len(vocabulary) == 132
    for arch, columns in by_arch.items():
        frame = pl.DataFrame({c: [1] for c in columns} | {"Hash": ["h"], "Arch": [arch]})
        out = canonical.canonicalize(frame, mapping, vocabulary)
        assert out.columns == ["Hash", "Arch"] + vocabulary, arch
        assert all(dt == canonical.DTYPE for dt in out.dtypes[2:]), arch


def test_canonicalize_sums_aliases_zero_fills_and_drops_fragments(mapping):
    vocabulary = ["clock_gettime", "mmap", "readlink", "write", "writev"]
    frame = pl.DataFrame(
        {
            "Hash": ["a", "b"],
            "MalwareFamily": ["Mirai", "Benign"],
            "Arch": ["arm", "arm"],
            "Call_mmap2": [2, 0],
            "Call_mmap": [1, 3],
            "Call_readlin": [5, 0],  # folds into readlink
            "Call_wri": [9, 9],  # write or writev: ambiguous, dropped
            "Call_syscall_0x193": [4, 0],
            # no source for "write": must come out as zero
        }
    )
    out = canonical.canonicalize(frame, mapping, vocabulary)
    assert out.columns == ["Hash", "MalwareFamily", "Arch", *vocabulary]
    assert out["mmap"].to_list() == [3, 3]
    assert out["readlink"].to_list() == [5, 0]
    assert out["clock_gettime"].to_list() == [4, 0]
    assert out["write"].to_list() == [0, 0]
    assert out["writev"].to_list() == [0, 0]
    assert out["mmap"].dtype == canonical.DTYPE


def test_a_column_outside_the_vocabulary_is_ignored_rather_than_failing(mapping):
    frame = pl.DataFrame({"Call_exotic": [1], "Call_read": [2]})
    out = canonical.canonicalize(frame, mapping, ["read"])
    assert out.columns == ["read"]
    assert out["read"].to_list() == [2]
