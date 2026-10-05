"""Binaries aggregate across batches; signatures find the duplicates they should."""

import polars as pl
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from iotmal import canonical, dedup

VOCAB = ["mmap", "read", "write"]


@pytest.fixture
def mapping():
    return canonical.Mapping.load()


def _file(tmp_path, rows, batch_size):
    """rows: list of (hash, label, arch, mmap2, mmap, read, write) written as Call_* columns."""
    table = pa.table(
        {
            "Call_mmap2": pa.array([r[3] for r in rows], pa.int8()),
            "Call_mmap": pa.array([r[4] for r in rows], pa.int8()),
            "Call_read": pa.array([r[5] for r in rows], pa.int8()),
            "Call_write": pa.array([r[6] for r in rows], pa.int8()),
            "Hash": [r[0] for r in rows],
            "MalwareFamily": [r[1] for r in rows],
            "Arch": [r[2] for r in rows],
        }
    )
    pq.write_table(table, tmp_path / "s.parquet", row_group_size=batch_size)
    return pq.ParquetFile(tmp_path / "s.parquet")


def test_aggregate_sums_windows_per_binary_across_batches(tmp_path, mapping):
    rows = [
        ("a", "Mirai", "mips", 1, 1, 2, 0),
        ("a", "Mirai", "mips", 0, 1, 2, 0),
        ("a", "Mirai", "mips", 1, 0, 2, 0),  # third window lands in the second batch
        ("b", "Benign", "mips", 0, 0, 1, 1),
    ]
    out = dedup.aggregate_binaries(_file(tmp_path, rows, 2), mapping, VOCAB, batch_size=2)
    out = out.sort("Hash")
    assert out.columns == ["Hash", "MalwareFamily", "Arch", "windows", *VOCAB]
    assert out["windows"].to_list() == [3, 1]
    assert out["mmap"].to_list() == [4, 0]  # mmap2 + mmap summed over three windows
    assert out["read"].to_list() == [6, 1]
    assert out["mmap"].dtype == pl.Int64


def test_signatures_distinguish_exact_profile_and_presence():
    binaries = pl.DataFrame(
        {
            "Hash": ["a", "b", "c", "d"],
            "MalwareFamily": ["Benign"] * 4,
            "Arch": ["mips"] * 4,
            "windows": [1, 1, 2, 1],
            "mmap": [2, 2, 4, 3],
            "read": [2, 2, 4, 0],
            "write": [0, 0, 0, 1],
        }
    )
    s = dedup.add_signatures(binaries, VOCAB)
    # a and b: identical vectors -> same on all three
    assert s["exact"][0] == s["exact"][1]
    # c is a doubled a: same profile and presence, different exact
    assert s["exact"][2] != s["exact"][0]
    assert s["profile"][2] == s["profile"][0]
    assert s["presence"][2] == s["presence"][0]
    # d uses a different set of calls: different on all three
    assert s["presence"][3] != s["presence"][0]


def test_duplicate_report_counts_distinct_signatures_and_the_largest_group():
    binaries = pl.DataFrame(
        {
            "Hash": list("abcdef"),
            "MalwareFamily": ["Benign"] * 4 + ["Mirai"] * 2,
            "Arch": ["mips"] * 6,
            "windows": [1] * 6,
            "mmap": [2, 2, 2, 4, 1, 5],
            "read": [2, 2, 2, 4, 0, 5],
            "write": [0, 0, 0, 0, 1, 0],
        }
    )
    report = dedup.duplicate_report(dedup.add_signatures(binaries, VOCAB))
    benign = report.filter(pl.col("MalwareFamily") == "Benign").row(0, named=True)
    assert benign["binaries"] == 4
    assert benign["distinct_exact"] == 2  # (2,2,0) x3 and (4,4,0)
    assert benign["distinct_profile"] == 1  # (4,4,0) is (2,2,0) doubled
    assert benign["distinct_presence"] == 1
    assert benign["largest_exact"] == 3
    mirai = report.filter(pl.col("MalwareFamily") == "Mirai").row(0, named=True)
    assert (mirai["binaries"], mirai["distinct_exact"], mirai["largest_exact"]) == (2, 2, 1)


def test_cross_class_report_counts_signatures_seen_in_more_than_one_class():
    binaries = pl.DataFrame(
        {
            "Hash": list("abcd"),
            "MalwareFamily": ["Benign", "Mirai", "Benign", "Mirai"],
            "Arch": ["mips"] * 4,
            "windows": [1] * 4,
            "mmap": [2, 2, 1, 9],  # a and b identical across classes
            "read": [2, 2, 1, 0],
            "write": [0, 0, 0, 1],
        }
    )
    cross = dedup.cross_class_report(dedup.add_signatures(binaries, VOCAB))
    by = {r["signature"]: r["shared_across_classes"] for r in cross.iter_rows(named=True)}
    # a=b exactly; c is a's profile (1,1,0 == 2,2,0 normalised) so profile and presence
    # also collide, but still between the same two classes: one shared signature each
    assert by == {"exact": 1, "profile": 1, "presence": 1}


def test_render_markdown_has_one_row_per_class_and_per_signature():
    binaries = pl.DataFrame(
        {
            "Hash": ["a", "b"],
            "MalwareFamily": ["Benign", "Mirai"],
            "Arch": ["arm", "arm"],
            "windows": [1, 1],
            "mmap": [1, 2],
            "read": [1, 0],
            "write": [0, 1],
        }
    )
    signed = dedup.add_signatures(binaries, VOCAB)
    md = dedup.render_markdown(dedup.duplicate_report(signed), dedup.cross_class_report(signed))
    assert "| arm | Benign | 1 | 1 | 1 | 1 | 1 |" in md
    assert "| arm | Mirai | 1 | 1 | 1 | 1 | 1 |" in md
    assert md.count("| arm | exact |") == 1 and "| arm | presence | 0 |" in md


def test_cross_class_report_can_count_by_benign_or_malware():
    binaries = pl.DataFrame(
        {
            "Hash": list("abcd"),
            "MalwareFamily": ["Mirai", "Generic", "Benign", "Mirai"],
            "Arch": ["x86"] * 4,
            "windows": [1] * 4,
            "is_malware": [True, True, False, True],
            "mmap": [1, 1, 2, 2],
            "read": [0, 0, 0, 0],
            "write": [0, 0, 0, 0],
        }
    )
    signed = dedup.add_signatures(binaries, VOCAB)
    exact = pl.col("signature") == "exact"
    by_family = dedup.cross_class_report(signed).filter(exact)
    by_target = dedup.cross_class_report(signed, by="is_malware").filter(exact)
    assert by_family["shared_across_classes"].to_list() == [2]  # Mirai/Generic and Benign/Mirai
    assert by_target["shared_across_classes"].to_list() == [1]  # only Benign/Mirai
