"""The scan counts classes, finds Unknown, tests hash contiguity, and names null columns."""

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from iotmal import verify


def _write(path, hashes, labels, extra=None, row_group_size=None):
    """Write a parquet file shaped like the dataset: Call_* columns plus the shared three."""
    n = len(hashes)
    columns = {
        "Call_read": pa.array([1] * n, pa.int8()),
        "Call_mmap": pa.array([None if i % 2 else 2.0 for i in range(n)], pa.float64()),
        # null only in the very last row, so only the last row group sees it
        "Call_late": pa.array([3.0] * (n - 1) + [None], pa.float64()),
        "Hash": pa.array(hashes),
        "MalwareFamily": pa.array(labels),
        "Arch": pa.array(["mips"] * n),
    }
    if extra:
        columns.update(extra)
    table = pa.table(columns)
    pq.write_table(table, path, row_group_size=row_group_size or n)
    return pq.ParquetFile(path)


@pytest.fixture
def contiguous_file(tmp_path):
    """Three binaries, each a single block, one of them spanning two row groups."""
    hashes = ["a"] * 4 + ["b"] * 3 + ["c"] * 5
    labels = ["Mirai"] * 4 + ["Benign"] * 3 + ["Unknown"] * 5
    # row groups of 5: [a a a a b] [b b c c c] [c c]  -> b and c each span a boundary
    return _write(tmp_path / "strace.parquet", hashes, labels, row_group_size=5)


@pytest.fixture
def scattered_file(tmp_path):
    """Two binaries whose rows are interleaved: not contiguous."""
    hashes = ["a", "b", "a", "b"]
    labels = ["Mirai", "Benign", "Mirai", "Benign"]
    return _write(tmp_path / "scattered.parquet", hashes, labels)


def test_class_counts_and_unknown_rows(contiguous_file):
    report = verify.scan_file(contiguous_file, "strace.parquet")
    assert report.rows == 12
    assert report.class_counts == {"Unknown": 5, "Mirai": 4, "Benign": 3}
    assert report.unknown_rows == 5


def test_contiguous_hashes_are_recognised_across_row_group_boundaries(contiguous_file):
    report = verify.scan_file(contiguous_file, "strace.parquet")
    assert report.has_hash
    assert report.row_groups == 3
    assert report.distinct_hashes == 3
    assert report.hash_runs == 3
    assert report.contiguous
    assert report.hashes_spanning_row_groups == 2
    assert (report.rows_per_hash_min, report.rows_per_hash_median, report.rows_per_hash_max) == (
        3,
        4.0,
        5,
    )


def test_interleaved_hashes_are_not_contiguous(scattered_file):
    report = verify.scan_file(scattered_file, "strace.parquet")
    assert report.distinct_hashes == 2
    assert report.hash_runs == 4
    assert not report.contiguous


def test_null_columns_come_from_footer_statistics(contiguous_file):
    report = verify.scan_file(contiguous_file, "strace.parquet")
    # Call_mmap has nulls on odd rows, Call_late only in the last row group;
    # Call_read and the string columns have none.
    assert report.null_columns == ["Call_mmap", "Call_late"]


def test_a_file_without_a_hash_column_reports_it_and_still_counts_classes(tmp_path):
    table = pa.table({"Call_read": [1, 2], "MalwareFamily": ["Mirai", "Mirai"]})
    pq.write_table(table, tmp_path / "x.parquet")
    report = verify.scan_file(pq.ParquetFile(tmp_path / "x.parquet"), "x.parquet")
    assert not report.has_hash
    assert not report.contiguous
    assert report.class_counts == {"Mirai": 2}


def test_render_markdown_has_one_summary_row_and_one_class_table_per_file(
    contiguous_file, scattered_file
):
    reports = [
        verify.scan_file(contiguous_file, "a/strace.parquet"),
        verify.scan_file(scattered_file, "b/strace.parquet"),
    ]
    md = verify.render_markdown(reports)
    assert md.count("| a/strace.parquet |") == 1
    assert "| yes | 3 | 3 | yes | 2 |" in md
    assert "| yes | 2 | 4 | no | 0 |" in md
    assert md.count("### ") == 2
    assert "| Unknown | 5 |" in md
    assert "Columns with nulls: Call_mmap, Call_late" in md


def test_to_dict_includes_the_derived_contiguous_flag(contiguous_file):
    d = verify.scan_file(contiguous_file, "strace.parquet").to_dict()
    assert d["contiguous"] is True
    assert d["class_counts"]["Mirai"] == 4
