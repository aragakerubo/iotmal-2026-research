"""Every binary keeps its twentieth row, or its last when shorter, across batch boundaries."""

import polars as pl
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from iotmal import canonical, dedup, first_window
from iotmal.paths import DATA_DIR

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
            "Hash": pa.array([r[0] for r in rows], pa.string()),
            "MalwareFamily": pa.array([r[1] for r in rows], pa.string()),
            "Arch": pa.array([r[2] for r in rows], pa.string()),
        }
    )
    pq.write_table(table, tmp_path / "s.parquet", row_group_size=batch_size)
    return pq.ParquetFile(tmp_path / "s.parquet")


def _binary(hash_, label, rows):
    """``rows`` rows for one binary; ``read`` holds the row's position so a test can see it."""
    return [(hash_, label, "mips", 1, 0, p, 0) for p in range(1, rows + 1)]


# a: 25 rows; b: 3 rows (exits within twenty calls); c: 22 rows
ROWS = _binary("a", "Benign", 25) + _binary("b", "Mirai", 3) + _binary("c", "Mirai", 22)


def _first(tmp_path, mapping, rows=ROWS, batch_size=1000, prefixes=(20,)):
    parquet = _file(tmp_path, rows, batch_size)
    out = first_window.first_rows(parquet, mapping, VOCAB, prefixes, batch_size=batch_size)
    return out if len(prefixes) > 1 else out[prefixes[0]]


def test_keeps_the_twentieth_row_in_file_order(tmp_path, mapping):
    out = _first(tmp_path, mapping)
    assert out["Hash"].to_list() == ["a", "b", "c"]
    assert out.filter(pl.col("Hash") != "b")["read"].to_list() == [20, 20]


def test_a_binary_shorter_than_twenty_calls_keeps_its_last_row(tmp_path, mapping):
    out = _first(tmp_path, mapping)
    b = out.filter(pl.col("Hash") == "b")
    assert b["read"].to_list() == [3]
    assert out["windows"].to_list() == [20, 3, 20]


@pytest.mark.parametrize("batch_size", [7, 13, 26, 35])
def test_positions_are_counted_across_batch_boundaries(tmp_path, mapping, batch_size):
    # 7 and 13 split a before its twentieth row; 26 splits b, the short binary,
    # after its first row; 35 splits c after its seventh row
    out = _first(tmp_path, mapping, batch_size=batch_size)
    assert out["Hash"].to_list() == ["a", "b", "c"]
    assert out["read"].to_list() == [20, 3, 20]


def test_aliases_are_folded(tmp_path, mapping):
    out = _first(tmp_path, mapping)
    assert out["mmap"].to_list() == [1, 1, 1]  # mmap2 counted under mmap


def test_schema_matches_the_whole_trace_store(tmp_path, mapping):
    parquet = _file(tmp_path, ROWS, 1000)
    first = first_window.first_rows(parquet, mapping, VOCAB)[20]
    whole = dedup.aggregate_binaries(parquet, mapping, VOCAB)
    assert first.schema == whole.schema


def test_an_empty_file_gives_an_empty_store_with_the_schema(tmp_path, mapping):
    out = first_window.first_rows(_file(tmp_path, [], 3), mapping, VOCAB, (5, 20))
    assert set(out) == {5, 20}
    out = out[20]
    assert out.is_empty()
    assert out.columns == ["Hash", "MalwareFamily", "Arch", "windows", *VOCAB]


@pytest.mark.parametrize("batch_size", [4, 7, 26, 1000])
def test_every_prefix_comes_from_one_pass(tmp_path, mapping, batch_size):
    rows = ROWS + _binary("d", "Mirai", 7)
    out = _first(tmp_path, mapping, rows, batch_size, prefixes=(5, 10, 20))
    assert out[5]["read"].to_list() == [5, 3, 5, 5]
    assert out[10]["read"].to_list() == [10, 3, 10, 7]
    assert out[20]["read"].to_list() == [20, 3, 20, 7]
    assert out[10]["windows"].to_list() == [10, 3, 10, 7]


def test_config_loads_and_checks_its_prefixes(tmp_path):
    cfg = first_window.FirstWindowConfig.load()
    assert cfg.prefixes == tuple(sorted(cfg.prefixes)) and max(cfg.prefixes) <= 20
    assert cfg.ablation_prefix in cfg.prefixes
    for body in (
        "prefixes: [5, 21]\nablation_prefix: 5\n",
        "prefixes: [0, 5]\nablation_prefix: 5\n",
        "prefixes: [5, 10]\nablation_prefix: 20\n",
    ):
        bad = tmp_path / "f.yaml"
        bad.write_text(body)
        with pytest.raises(ValueError):
            first_window.FirstWindowConfig.load(bad)


def test_the_network_calls_are_socket_calls_of_the_vocabulary():
    cfg = first_window.FirstWindowConfig.load()
    vocabulary = set(pl.read_csv(DATA_DIR / "syscall_vocabulary.csv")["canonical"])
    assert set(cfg.network_calls) <= vocabulary
    assert {"socket", "connect", "getsockname"} <= set(cfg.network_calls)
    assert "sendfile" not in cfg.network_calls
