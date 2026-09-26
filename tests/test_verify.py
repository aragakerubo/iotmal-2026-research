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


def test_hashes_per_class_counts_distinct_binaries_not_rows(contiguous_file):
    report = verify.scan_file(contiguous_file, "strace.parquet")
    # a: 4 rows Mirai, b: 3 rows Benign, c: 5 rows Unknown -> one binary each
    assert report.hashes_per_class == {"Unknown": 1, "Mirai": 1, "Benign": 1}


def test_a_class_spread_over_several_binaries_is_counted_once_per_binary(tmp_path):
    hashes = ["a"] * 2 + ["b"] * 2 + ["c"] * 2
    labels = ["Mirai"] * 6
    parquet = _write(tmp_path / "m.parquet", hashes, labels, row_group_size=4)
    report = verify.scan_file(parquet, "m.parquet")
    assert report.hashes_per_class == {"Mirai": 3}


def test_a_mean_filled_count_column_is_detected_by_its_single_repeated_fraction(tmp_path):
    n = 10
    hashes = ["a"] * n
    labels = ["Mirai"] * n
    extra = {
        # mean-filled: integers except the fill value 0.37 on three rows
        "Call_filled": pa.array([1.0, 0.37, 2.0, 0.37, 0.0, 3.0, 0.37, 1.0, 0.0, 2.0]),
        # a double column that is integer everywhere: a count, not a fill
        "Call_clean": pa.array([float(i % 3) for i in range(n)]),
        # a non-count double column with fractions is ignored by the check
        "Std": pa.array([0.5] * n),
    }
    parquet = _write(tmp_path / "f.parquet", hashes, labels, extra=extra, row_group_size=5)
    report = verify.scan_file(parquet, "f.parquet")
    assert report.sampled_row_groups == [0, 1]
    assert set(report.filled_columns) == {"Call_filled"}
    f = report.filled_columns["Call_filled"]
    assert (f.rows_sampled, f.non_integer_rows, f.distinct_non_integer) == (10, 3, 1)
    assert f.top_value == pytest.approx(0.37)
    assert f.top_value_rows == 3


def test_the_fill_check_samples_first_last_and_evenly_between():
    assert verify._spread(21, 3) == [0, 10, 20]
    assert verify._spread(2, 3) == [0, 1]
    assert verify._spread(29, 4) == [0, 9, 19, 28]
    assert verify._spread(5, 1) == [0]


def test_render_markdown_shows_binaries_per_class_and_the_fill_table(tmp_path):
    hashes = ["a"] * 4
    labels = ["Mirai"] * 4
    extra = {"Call_filled": pa.array([1.0, 0.25, 0.25, 2.0])}
    parquet = _write(tmp_path / "f.parquet", hashes, labels, extra=extra)
    md = verify.render_markdown([verify.scan_file(parquet, "f.parquet")])
    assert "| Class | Rows | Binaries |" in md
    assert "| Mirai | 4 | 1 |" in md
    assert "| Call_filled | 4 | 2 | 1 | 0.25 | 2 |" in md
