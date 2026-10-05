"""Folds never leak, test binaries stay unseen, and separable data is separated."""

import numpy as np
import polars as pl
import pytest

from iotmal import baseline, dedup, first_window, split

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
    assert np.allclose(x[:, -1], np.log1p(live["windows"].to_numpy()))
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


def test_load_feature_store_reads_only_the_named_store(tmp_path, store):
    arm = pl.col("Arch") == "arm"
    first = store.with_columns(pl.lit(20, dtype=store["windows"].dtype).alias("windows"))
    store.filter(arm).write_parquet(tmp_path / "arm_strace.parquet")
    first.filter(arm).write_parquet(tmp_path / f"arm_{first_window.stem(20)}.parquet")
    assert dedup.load_feature_store(tmp_path).equals(store.filter(arm))
    assert dedup.load_feature_store(tmp_path, stem="first20_strace").equals(first.filter(arm))
    with pytest.raises(FileNotFoundError):
        dedup.load_feature_store(tmp_path, stem="pcap")


def _first_store(store, same=False):
    """Twenty calls per binary; ``same`` gives every binary the identical first window."""
    first = store.with_columns(pl.lit(20, dtype=store["windows"].dtype).alias("windows"))
    if same:
        first = first.with_columns(*[pl.lit(3).alias(v) for v in VOCAB])
    return first


def test_first_window_rejects_a_store_describing_more_than_twenty_calls(store, assignment, cfg):
    with pytest.raises(ValueError):
        baseline.first_window(store, assignment, VOCAB, cfg)
    too_long = _first_store(store).with_columns(
        pl.lit(21).cast(store["windows"].dtype).alias("windows")
    )
    with pytest.raises(ValueError):
        baseline.first_window(too_long, assignment, VOCAB, cfg)


def test_first_window_repeats_the_three_experiments_on_the_same_binaries(store, assignment, cfg):
    whole = baseline.run(store, assignment, VOCAB, cfg)
    first = baseline.first_window(_first_store(store), assignment, VOCAB, cfg)
    assert first["experiment"].unique().sort().to_list() == sorted(
        f"first-20 {e}" for e in baseline.EXPERIMENTS
    )
    assert first["test_n"].to_list() == whole["test_n"].to_list()
    other = baseline.first_window(_first_store(store), assignment, VOCAB, cfg, label="x")
    results = pl.concat([whole, first, other])
    table = baseline.compare(results, ["first-20", "x"])
    assert table.columns == ["experiment", "held_out", "view", "test_n", "whole", "first-20", "x"]
    assert table.height == whole.height
    md = baseline.render_markdown(results)
    assert "## first-20 leave-one-architecture-out" in md and "## x architecture-sanity" in md
    rendered = baseline.render_comparison(table)
    assert "| Experiment | Held out | View | Test | whole | first-20 | x |" in rendered
    assert "| leave-one-architecture-out | arm | group |" in rendered


def test_identical_first_windows_carry_no_signal(store, assignment, cfg):
    first = baseline.first_window(_first_store(store, same=True), assignment, VOCAB, cfg)
    detection = first.filter(~pl.col("experiment").str.ends_with(baseline.SANITY))
    assert detection["mcc"].abs().max() == 0.0
    assert detection["auroc"].max() == 0.5


def test_dropping_the_only_separating_calls_removes_the_signal(store, assignment, cfg):
    # every first window identical except that malware opens a socket and connects
    first = _first_store(store, same=True).with_columns(
        *[
            pl.when(pl.col("MalwareFamily") == "Benign").then(3).otherwise(4).alias(c)
            for c in ("socket", "connect")
        ]
    )
    with_net = baseline.first_window(first, assignment, VOCAB, cfg)
    without = baseline.first_window(first, assignment, VOCAB, cfg, drop=("socket", "connect"))
    detect = ~pl.col("experiment").str.ends_with(baseline.SANITY)
    assert with_net.filter(detect)["mcc"].min() > 0.9
    assert without.filter(detect)["mcc"].abs().max() == 0.0
    with pytest.raises(ValueError):
        baseline.first_window(first, assignment, VOCAB, cfg, drop=("sokcet",))


def test_compare_raises_when_a_run_scores_different_binaries(store, assignment, cfg):
    whole = baseline.run(store, assignment, VOCAB, cfg)
    first = baseline.first_window(_first_store(store), assignment, VOCAB, cfg)
    shifted = first.with_columns(pl.col("test_n") + 1)
    with pytest.raises(ValueError):
        baseline.compare(pl.concat([whole, shifted]), ["first-20"])


def test_choose_threshold_takes_the_middle_of_a_clean_gap():
    y = np.array([0, 0, 1, 1])
    assert baseline.choose_threshold(y, np.array([0.1, 0.6, 0.9, 0.95])) == pytest.approx(0.75)
    assert baseline.choose_threshold(y, np.array([0.01, 0.02, 0.98, 0.99])) == pytest.approx(0.5)


def test_choose_threshold_maximises_mcc_and_breaks_ties_toward_half():
    # a malware at 0.4 and a benign at 0.6 sit between the classes; cutting at 0.275
    # or at 0.7 both reach MCC 0.707, and 0.7 is closer to 0.5
    y = np.array([0, 0, 1, 0, 1, 1])
    s = np.array([0.1, 0.15, 0.4, 0.6, 0.8, 0.9])
    assert baseline.choose_threshold(y, s) == pytest.approx(0.7)
    # without the tie the larger MCC wins whatever its distance from 0.5
    y = np.array([0, 0, 0, 1, 0, 1, 1])
    s = np.array([0.1, 0.2, 0.3, 0.6, 0.7, 0.8, 0.9])
    assert baseline.choose_threshold(y, s) == pytest.approx(0.45)
    assert baseline.choose_threshold(np.array([1, 1]), np.array([0.2, 0.9])) == 0.5
    assert baseline.choose_threshold(y, np.full(7, 0.4)) == 0.5


def test_choose_threshold_agrees_with_a_brute_force_search():
    from sklearn.metrics import matthews_corrcoef

    rng = np.random.default_rng(3)
    for _ in range(20):
        y = rng.integers(0, 2, size=60)
        s = np.round(np.clip(rng.normal(0.3 + 0.4 * y, 0.25), 0, 1), 2)
        t = baseline.choose_threshold(y, s)
        values = np.unique(s)
        brute = max(matthews_corrcoef(y, s >= c) for c in (values[:-1] + values[1:]) / 2)
        assert matthews_corrcoef(y, s >= t) == pytest.approx(brute)


def test_metrics_report_mcc_at_the_threshold_and_at_half():
    y = np.array([0, 0, 1, 1])
    m = baseline.metrics(y, np.array([0.55, 0.6, 0.8, 0.9]), threshold=0.7)
    assert m["mcc"] == 1.0 and m["threshold"] == 0.7
    assert m["mcc_half"] == 0.0


def test_the_held_out_architecture_never_moves_its_own_threshold(store, assignment, cfg):
    # arm's benign binaries take a malware-like profile, which moves arm's test scores
    arm_benign = (pl.col("Arch") == "arm") & (pl.col("MalwareFamily") == "Benign")
    malware_like = dict(zip(VOCAB, [20, 1, 25, 3, 20, 2]))
    shifted = store.with_columns(
        *[pl.when(arm_benign).then(malware_like[v]).otherwise(pl.col(v)).alias(v) for v in VOCAB]
    )
    loao = (pl.col("experiment") == baseline.LOAO) & (pl.col("held_out") == "arm")
    before = baseline.run(store, assignment, VOCAB, cfg).filter(loao)["threshold"]
    after = baseline.run(shifted, assignment, VOCAB, cfg).filter(loao)["threshold"]
    assert before.to_list() == after.to_list()
    assert 0 < before[0] < 1
