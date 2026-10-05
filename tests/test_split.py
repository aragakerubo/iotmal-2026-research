"""Groups never cross a split, inert traces are set aside, and the deal is reproducible."""

from dataclasses import replace

import polars as pl
import pytest

from iotmal import dedup, split

VOCAB = ["connect", "execve", "mmap", "read", "socket", "write"]


@pytest.fixture
def cfg():
    return split.SplitConfig.load()


def _binaries(rows):
    """rows: (hash, label, arch, windows, connect, execve, mmap, read, socket, write)."""
    return pl.DataFrame(
        {
            "Hash": [r[0] for r in rows],
            "MalwareFamily": [r[1] for r in rows],
            "Arch": [r[2] for r in rows],
            "windows": [r[3] for r in rows],
            **{v: [r[4 + i] for r in rows] for i, v in enumerate(VOCAB)},
        }
    )


def _signed(rows):
    return dedup.add_signatures(_binaries(rows), VOCAB)


def test_config_loads_and_checks_shares(cfg):
    assert set(cfg.fractions) == set(split.SPLITS)
    assert abs(sum(cfg.fractions.values()) - 1) < 1e-9
    assert cfg.group_by == "exact"
    assert "socket" in cfg.inert_network_calls
    assert "Unknown" in cfg.drop_labels


def test_trace_length_is_one_call_per_row():
    frame = pl.DataFrame({"windows": [1, 16, 4]})
    assert frame.select(split.trace_length(pl.col("windows")))["windows"].to_list() == [1, 16, 4]


def test_a_trace_of_fifty_calls_without_network_is_inert(cfg):
    # 50 rows is 50 calls, under the 64-call threshold; the old w + 19 arithmetic
    # read it as 69 calls and kept it live
    rows = [
        ("a", "Benign", "mips", 50, 0, 20, 300, 100, 0, 200),
        ("b", "Benign", "mips", 64, 0, 20, 300, 100, 0, 200),  # at the threshold: live
    ]
    out = split.mark_inert(_signed(rows), cfg)
    assert out["inert"].to_list() == [True, False]


def test_inert_is_short_and_without_network_calls(cfg):
    rows = [
        ("a", "Benign", "arm", 16, 0, 16, 15, 9, 0, 7),  # the ARM loader-and-exit trace
        ("b", "Mirai", "arm", 4, 0, 4, 0, 0, 0, 3),  # print and quit
        ("c", "Benign", "arm", 16, 1, 16, 15, 9, 1, 7),  # short but it opened a socket
        ("d", "Mirai", "arm", 5000, 0, 1, 2, 9, 0, 9),  # long, no network: ran, not inert
    ]
    out = split.mark_inert(_signed(rows), cfg)
    assert out["inert"].to_list() == [True, True, False, False]


def test_identical_behaviour_lands_on_one_side_whatever_the_hash(cfg):
    # 30 benign binaries that are 10 copies each of three traces, plus 30 distinct Mirai
    rows = []
    for i in range(30):
        rows.append((f"b{i}", "Benign", "mips", 500, 1, 1, i % 3, 2, 1, 3))
    for i in range(30):
        rows.append((f"m{i}", "Mirai", "mips", 500 + i, 1, 1, 7, i, 1, 3))
    out = split.assign(_signed(rows), cfg)
    split.check(out)  # raises on any crossing
    benign = out.filter(pl.col("MalwareFamily") == "Benign")
    assert benign["group"].n_unique() == 3
    assert benign.group_by("group").agg(pl.col("split").n_unique())["split"].max() == 1
    assert set(out["split"].unique()) <= {"train", "val", "test"}


def test_shares_are_approximately_met_per_family_in_whole_groups(cfg):
    rows = [(f"m{i}", "Mirai", "x86", 100, 1, 1, i, i, 1, i) for i in range(100)]
    out = split.assign(_signed(rows), cfg)
    counts = out.group_by("split").len().to_dict(as_series=False)
    got = dict(zip(counts["split"], counts["len"]))
    assert got["train"] == 70 and got["val"] == 10 and got["test"] == 20


def test_a_family_with_a_single_group_goes_to_train(cfg):
    rows = [(f"g{i}", "Gafgyt", "arm", 100, 1, 1, 1, 1, 1, 1) for i in range(5)]
    out = split.assign(_signed(rows), cfg)
    assert out["split"].to_list() == ["train"] * 5


def test_inert_rows_are_excluded_from_splits_and_unknown_is_dropped(cfg):
    rows = [
        ("a", "Benign", "arm", 16, 0, 16, 15, 9, 0, 7),
        ("b", "Benign", "arm", 900, 2, 1, 15, 9, 2, 7),
        ("u", "Unknown", "arm", 900, 2, 1, 15, 9, 2, 7),
    ]
    out = split.assign(_signed(rows), cfg)
    assert out.filter(pl.col("Hash") == "a")["split"].item() == "inert"
    assert out.filter(pl.col("Hash") == "b")["split"].item() == "train"
    assert "u" not in out["Hash"].to_list()


def test_the_same_seed_gives_the_same_assignment(cfg):
    rows = [(f"m{i}", "Mirai", "mipsel", 100, 1, 1, i, i, 1, i) for i in range(50)]
    first = split.assign(_signed(rows), cfg)
    second = split.assign(_signed(rows), cfg)
    assert first.equals(second)


def test_check_raises_when_a_group_crosses(cfg):
    bad = pl.DataFrame(
        {
            "Hash": ["a", "b"],
            "MalwareFamily": ["Mirai", "Mirai"],
            "Arch": ["arm", "arm"],
            "group": ["g", "g"],
            "inert": [False, False],
            "split": ["train", "test"],
        }
    )
    with pytest.raises(AssertionError):
        split.check(bad)


def test_summary_and_markdown_report_inert_groups_and_per_split_counts(cfg):
    rows = [("a", "Benign", "arm", 16, 0, 16, 15, 9, 0, 7)]
    rows += [(f"m{i}", "Mirai", "arm", 100, 1, 1, i, i, 1, i) for i in range(10)]
    out = split.assign(_signed(rows), cfg)
    table = split.summary(out)
    md = split.render_markdown(table)
    assert "| arm | Benign | 1 | 1 | 0 | 0 | 0 | 0 | 0 |" in md
    assert "| arm | Mirai | 10 | 0 | 0 | 10 | 7 | 1 | 2 |" in md


def test_a_signature_shared_by_benign_and_malware_is_set_aside_as_conflict(cfg):
    rows = [
        ("a", "Benign", "arm", 300, 1, 1, 2, 2, 1, 3),
        ("b", "Mirai", "arm", 300, 1, 1, 2, 2, 1, 3),  # identical to a, other side
        ("c", "Mirai", "arm", 300, 1, 1, 9, 2, 1, 3),
    ]
    out = split.assign(_signed(rows), cfg)
    by = dict(zip(out["Hash"].to_list(), out["split"].to_list()))
    assert by["a"] == "conflict" and by["b"] == "conflict" and by["c"] == "train"
    split.check(out)


def test_a_signature_shared_by_two_malware_labels_is_not_a_conflict(cfg):
    # the x86 case: 190 Mirai binaries and one Generic binary with one trace
    rows = [(f"m{i}", "Mirai", "x86", 300, 1, 1, 2, 2, 1, 3) for i in range(5)]
    rows.append(("g", "Generic", "x86", 300, 1, 1, 2, 2, 1, 3))
    out = split.assign(_signed(rows), cfg)
    assert "conflict" not in out["split"].to_list()
    assert out["split"].n_unique() == 1  # one group, one side
    split.check(out)


def test_the_same_signature_on_two_architectures_is_two_groups(cfg):
    rows = [
        ("a", "Mirai", "arm", 300, 1, 1, 2, 2, 1, 3),
        ("b", "Mirai", "mips", 300, 1, 1, 2, 2, 1, 3),
    ]
    out = split.assign(_signed(rows), cfg)
    assert out["group"].n_unique() == 2
    split.check(out)


def test_a_trace_shared_by_two_malware_families_lands_on_one_side(cfg):
    # ten Mirai and one Generic binary with one trace, beside distinct traces of each
    shared = [(f"s{i}", "Mirai", "x86", 300, 1, 1, 5, 5, 1, 5) for i in range(10)]
    shared.append(("sg", "Generic", "x86", 300, 1, 1, 5, 5, 1, 5))
    mirai = [(f"m{i}", "Mirai", "x86", 400 + i, 1, 1, i, 2, 1, 3) for i in range(30)]
    generic = [(f"g{i}", "Generic", "x86", 400 + i, 1, 1, 9, i, 1, 3) for i in range(10)]
    signed = _signed(shared + mirai + generic)
    for seed in range(20):
        out = split.assign(signed, replace(cfg, seed=seed))
        split.check(out)
        assert out.filter(pl.col("Hash").str.starts_with("s"))["split"].n_unique() == 1
