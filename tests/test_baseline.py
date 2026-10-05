"""Folds never leak, test binaries stay unseen, and separable data is separated."""

import numpy as np
import polars as pl
import pytest

from iotmal import baseline, dedup, split

VOCAB = ["connect", "execve", "mmap", "read", "socket", "write"]
ARCHES = ["arm", "mips", "x86"]


@pytest.fixture
def cfg():
    return baseline.BaselineConfig.load()


def _store(rng, per_class=40):
    """A separable feature store: benign reads and writes, malware opens sockets."""
    rows = []
    for arch in ARCHES:
        for i in range(per_class):
            b = rng.integers(20, 60, size=3)
            m = rng.integers(10, 40, size=3)
            rows.append((f"{arch}b{i}", "Benign", arch, 200 + i, 0, 1, b[0], b[1], 0, b[2]))
            rows.append((f"{arch}m{i}", "Mirai", arch, 200 + i, m[0], 1, m[1], 3, m[2], 2))
    # one inert benign, one benign/malware conflict pair, one Unknown
    rows.append(("armi", "Benign", "arm", 16, 0, 16, 15, 9, 0, 7))
    rows.append(("armc1", "Benign", "arm", 300, 1, 1, 2, 2, 1, 3))
    rows.append(("armc2", "Mirai", "arm", 300, 1, 1, 2, 2, 1, 3))
    rows.append(("armu", "Unknown", "arm", 300, 1, 1, 9, 2, 1, 3))
    return pl.DataFrame(
        {
            "Hash": [r[0] for r in rows],
            "MalwareFamily": [r[1] for r in rows],
            "Arch": [r[2] for r in rows],
            "windows": [r[3] for r in rows],
            **{v: [r[4 + i] for r in rows] for i, v in enumerate(VOCAB)},
        }
    )


@pytest.fixture
def store():
    return _store(np.random.default_rng(0))


@pytest.fixture
def assignment(store):
    signed = dedup.add_signatures(store, VOCAB)
    return split.assign(signed, split.SplitConfig.load())


@pytest.fixture
def live(store, assignment):
    return baseline.live_binaries(store, assignment)


def test_config_loads_and_rejects_an_unknown_feature_kind(cfg, tmp_path):
    assert cfg.features in baseline.FEATURE_KINDS
    assert cfg.xgboost["n_estimators"] > 0
    bad = tmp_path / "b.yaml"
    bad.write_text("seed: 1\nfeatures: raw\nearly_stopping_rounds: 5\n")
    with pytest.raises(ValueError):
        baseline.BaselineConfig.load(bad)


def test_live_binaries_keeps_only_split_rows_and_labels_malware(live):
    hashes = set(live["Hash"].to_list())
    assert {"armi", "armc1", "armc2", "armu"}.isdisjoint(hashes)
    assert live.height == 3 * 80
    assert live.filter(pl.col("MalwareFamily") == "Mirai")["is_malware"].all()
    assert not live.filter(pl.col("MalwareFamily") == "Benign")["is_malware"].any()
    assert set(live["split"].unique()) <= set(split.SPLITS)


def test_profile_features_are_proportions_plus_log_length(live):
    x = baseline.featurize(live, VOCAB, "profile")
    assert x.shape == (live.height, len(VOCAB) + 1)
    assert np.allclose(x[:, : len(VOCAB)].sum(axis=1), 1.0)
    assert np.allclose(x[:, -1], np.log1p(live["windows"].to_numpy() + 19))
    y = baseline.featurize(live, VOCAB, "log_counts")
    assert y.shape == (live.height, len(VOCAB))


def test_in_architecture_folds_stay_inside_one_architecture(live):
    folds = baseline.in_architecture_folds(live)
    assert [f.held_out for f in folds] == ARCHES
    arch = live["Arch"].to_numpy()
    splits = live["split"].to_numpy()
    for f in folds:
        for part in (f.train, f.val, f.test):
            assert set(arch[part]) == {f.held_out}
        assert set(splits[f.train]) == {"train"}
        assert set(splits[f.val]) == {"val"}
        assert set(splits[f.test]) == {"test"}
        assert not (set(f.train) & set(f.test)) and not (set(f.val) & set(f.test))


def test_leave_one_out_tests_on_the_whole_held_out_architecture(live):
    folds = baseline.leave_one_out_folds(live)
    arch = live["Arch"].to_numpy()
    splits = live["split"].to_numpy()
    for f in folds:
        assert set(arch[f.test]) == {f.held_out}
        assert len(f.test) == int((arch == f.held_out).sum())
        assert f.held_out not in set(arch[f.train]) | set(arch[f.val])
        assert "test" not in set(splits[f.train]) | set(splits[f.val])


def test_collapse_groups_averages_scores_within_a_group():
    groups = np.array(["g2", "g1", "g2", "g3"])
    y = np.array([1, 0, 1, 1])
    s = np.array([0.9, 0.2, 0.5, 0.4])
    yg, sg = baseline.collapse_groups(groups, y, s)
    assert yg.tolist() == [0, 1, 1]
    assert np.allclose(sg, [0.2, 0.7, 0.4])


def test_metrics_are_perfect_on_perfect_scores_and_auroc_needs_both_classes():
    y = np.array([0, 0, 1, 1])
    m = baseline.metrics(y, np.array([0.1, 0.2, 0.8, 0.9]))
    assert m["mcc"] == 1.0 and m["accuracy"] == 1.0 and m["auroc"] == 1.0 and m["chance"] == 0.5
    single = baseline.metrics(np.array([1, 1]), np.array([0.9, 0.4]))
    assert single["auroc"] is None and single["accuracy"] == 0.5


def test_run_separates_separable_data_and_reports_every_fold(store, assignment, cfg):
    results = baseline.run(store, assignment, VOCAB, cfg)
    assert list(results.columns) == list(baseline.RESULT_COLUMNS)
    assert results.height == 2 * len(ARCHES) * len(baseline.VIEWS) + 1
    detection = results.filter(pl.col("experiment") != baseline.SANITY)
    assert detection["mcc"].min() > 0.8
    loao = results.filter(pl.col("experiment") == baseline.LOAO)
    assert loao.filter(pl.col("view") == "binary")["test_n"].to_list() == [80, 80, 80]
    sanity = results.filter(pl.col("experiment") == baseline.SANITY)
    assert sanity.height == 1 and sanity["auroc"][0] is None
    md = baseline.render_markdown(results)
    assert "## leave-one-architecture-out" in md and "| arm | group |" in md
    assert "## in-architecture" not in baseline.render_markdown(loao)


def test_the_same_seed_gives_the_same_results(store, assignment, cfg):
    first = baseline.run(store, assignment, VOCAB, cfg)
    second = baseline.run(store, assignment, VOCAB, cfg)
    assert first.equals(second)


def test_load_feature_store_reads_a_directory_and_complains_when_empty(tmp_path, store):
    store.filter(pl.col("Arch") == "arm").write_parquet(tmp_path / "arm_strace.parquet")
    store.filter(pl.col("Arch") == "mips").write_parquet(tmp_path / "mips_strace.parquet")
    (tmp_path / "notes.parquet").write_bytes(b"")  # wrong suffix, ignored
    out = dedup.load_feature_store(tmp_path)
    assert set(out["Arch"].unique()) == {"arm", "mips"}
    with pytest.raises(FileNotFoundError):
        dedup.load_feature_store(tmp_path / "empty")


def test_load_assignment_concatenates_split_files(tmp_path, assignment):
    for (arch,), part in assignment.group_by("Arch", maintain_order=True):
        part.write_csv(tmp_path / f"{arch}.csv")
    out = baseline.load_assignment(tmp_path)
    assert out.height == assignment.height
    with pytest.raises(FileNotFoundError):
        baseline.load_assignment(tmp_path / "none")
