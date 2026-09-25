"""The manifest reads footers, names files by arch and modality, and finds Unknown rows."""

import fsspec
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from iotmal import manifest
from iotmal.paths import DATA_DIR


def _write_parquet(path, rows: int, columns: int, row_groups: int = 1) -> None:
    """Write a small parquet file with the given shape; values are irrelevant."""
    path.parent.mkdir(parents=True, exist_ok=True)
    table = pa.table({f"c{i}": list(range(rows)) for i in range(columns)})
    pq.write_table(table, path, row_group_size=max(1, rows // row_groups))


@pytest.fixture
def raw_tree(tmp_path):
    """A miniature copy of the download's layout with three architectures."""
    _write_parquet(tmp_path / "mips" / "mips" / "Parquet Format" / "strace.parquet", 120, 5, 3)
    _write_parquet(tmp_path / "mips" / "mips" / "Parquet Format" / "pcap.parquet", 100, 4)
    _write_parquet(tmp_path / "mipsel" / "mipsel" / "Parquet Format" / "pcap.parquet", 90, 4)
    _write_parquet(tmp_path / "arms" / "Parquet Format" / "sar.parquet", 50, 6)
    (tmp_path / "mips" / "mips" / "README.pdf").write_bytes(b"%PDF")
    (tmp_path / "Supplementary" / "notes.parquet").parent.mkdir()
    _write_parquet(tmp_path / "Supplementary" / "notes.parquet", 3, 2)
    return tmp_path


@pytest.fixture
def paper():
    """Paper counts in the shape of data/paper_counts.csv for the fixture tree."""
    return pd.DataFrame(
        [
            ("Mirai", 80, "MIPS", "strace"),
            ("Benign", 40, "MIPS", "strace"),
            ("Mirai", 70, "MIPS", "pcap"),
            ("Mirai", 60, "MIPSEL", "pcap"),
            ("Mirai", 200, "x86", "pcap"),
        ],
        columns=["MalwareFamily", "count", "Architecture", "DataType"],
    )


def test_classify_names_arch_and_modality_from_the_download_layout():
    assert manifest.classify("raw/Yokohama/mips/mips/Parquet Format/strace.parquet") == (
        "mips",
        "strace",
    )
    assert manifest.classify("raw/Yokohama/mipsel/mipsel/Parquet Format/pcap.parquet") == (
        "mipsel",
        "pcap",
    )
    assert manifest.classify("raw/Yokohama/x86/x86/Parquet Format/sar.parquet") == ("x86", "sar")


def test_classify_maps_the_arms_folder_to_arm_and_leaves_unknown_files_unnamed():
    assert manifest.classify("raw/Yokohama/arms/Parquet Format/strace.parquet") == (
        "arm",
        "strace",
    )
    assert manifest.classify("raw/Yokohama/Supplementary/notes.parquet") == (None, None)


def test_scan_reads_footers_for_every_parquet_and_skips_other_files(raw_tree):
    fs = fsspec.filesystem("file")
    entries = manifest.scan(fs, str(raw_tree))
    assert [e.path.split("/")[-1] for e in entries] == [
        "notes.parquet",
        "sar.parquet",
        "pcap.parquet",
        "strace.parquet",
        "pcap.parquet",
    ]
    strace = next(e for e in entries if e.modality == "strace")
    assert (strace.rows, strace.columns, strace.row_groups) == (120, 5, 3)
    on_disk = (raw_tree / "mips/mips/Parquet Format/strace.parquet").stat().st_size
    assert strace.size_bytes == on_disk


def test_compare_reports_unknown_rows_and_missing_files(raw_tree, paper):
    entries = manifest.scan(fsspec.filesystem("file"), str(raw_tree))
    got = manifest.compare(entries, paper).set_index(["arch", "modality"])
    # 120 rows in the file, 80 + 40 in the paper: nothing Unknown
    assert got.loc[("mips", "strace"), "unknown_rows"] == 0
    # 100 in the file, 70 in the paper: 30 Unknown
    assert got.loc[("mips", "pcap"), "unknown_rows"] == 30
    # x86 pcap is in the paper but not in the tree
    assert pd.isna(got.loc[("x86", "pcap"), "rows_in_file"])
    # arm sar is in the tree but not in the paper
    assert pd.isna(got.loc[("arm", "sar"), "rows_in_paper"])


def test_render_markdown_and_comparison_are_tables_with_one_row_per_entry(raw_tree, paper):
    entries = manifest.scan(fsspec.filesystem("file"), str(raw_tree))
    files_md = manifest.render_markdown(entries)
    assert files_md.count("\n") == 2 + len(entries)
    assert "| mips | strace | " in files_md
    cmp_md = manifest.render_comparison(manifest.compare(entries, paper))
    assert "| mips | pcap | 100 | 70 | 30 | 30.0 |" in cmp_md
    assert "| x86 | pcap |  | 200 |  |  |" in cmp_md


def test_the_committed_paper_counts_sum_to_table_5():
    """The CSV the authors shipped reproduces the paper's per-architecture totals."""
    totals = manifest.paper_totals(pd.read_csv(DATA_DIR / "paper_counts.csv"))
    totals = totals.set_index(["arch", "modality"])["rows_in_paper"]
    assert totals[("mips", "strace")] == 29_993_871
    assert totals[("mips", "pcap")] == 720_884
    assert totals[("mipsel", "pcap")] == 678_690
    assert totals[("x86", "pcap")] == 424_110
    assert set(totals.index.get_level_values("arch")) == set(manifest.ARCHITECTURES)
