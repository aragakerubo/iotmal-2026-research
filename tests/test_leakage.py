"""Draws are exact and nested, splits leak only where they should, and leakage is measured."""

import numpy as np
import polars as pl
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from iotmal import baseline, canonical, leakage, rows, split

VOCAB = ["mmap", "read", "write"]
SIX = ["a", "b", "c", "d", "e", "f"]


@pytest.fixture
def cfg():
    return leakage.LeakageConfig.load()


@pytest.fixture
def model_cfg():
    return baseline.BaselineConfig.load()


def _cfg(tmp_path, body):
    path = tmp_path / "l.yaml"
    path.write_text(body)
    return leakage.LeakageConfig.load(path)


SMALL = (
    "units:\n  mid: {first_row: 21}\n  all: {first_row: 1}\n"
    "cap: 8\nsensitivity_cap: 3\nseeds: [0, 1]\n"
)


def test_config_loads_and_rejects_bad_caps_units_and_seeds(cfg, tmp_path):
    assert cfg.units["mid"] == 21 and cfg.units["all"] == 1
    assert cfg.sensitivity_cap <= cfg.cap and len(cfg.seeds) == 5
    for body in (
        SMALL.replace("sensitivity_cap: 3", "sensitivity_cap: 9"),
        SMALL.replace("first_row: 1}", "first_row: 0}"),
        SMALL.replace("seeds: [0, 1]", "seeds: []"),
    ):
        with pytest.raises(ValueError):
            _cfg(tmp_path, body)


def _binaries(windows):
    return pl.DataFrame(
        {
            "Hash": [f"h{i}" for i in range(len(windows))],
            "Arch": ["x86"] * len(windows),
            "windows": windows,
        }
    )


def test_plan_draws_cap_rows_from_the_eligible_ones_only(tmp_path):
    lcfg = _cfg(tmp_path, SMALL)
    plan = leakage.plan_sample(_binaries([5, 25, 150]), lcfg)
    per = plan.group_by("Hash", "unit", "seed").agg(
        pl.len(),
        pl.col("position").min().alias("lo"),
        pl.col("position").max().alias("hi"),
        pl.col("position").n_unique().alias("distinct"),
        pl.col("rank").max().alias("ranks"),
    )
    counts = {(r["Hash"], r["unit"]): r["len"] for r in per.iter_rows(named=True)}
    # h0 has 5 rows: none from 21 on, all 5 in "all"; h1 has 25: 5 mid rows; h2: the cap
    assert ("h0", "mid") not in counts and counts[("h0", "all")] == 5
    assert counts[("h1", "mid")] == 5 and counts[("h2", "mid")] == 8 and counts[("h2", "all")] == 8
    mid = per.filter(pl.col("unit") == "mid")
    assert mid["lo"].min() >= 21
    windows = {"h0": 5, "h1": 25, "h2": 150}
    assert all(r["hi"] <= windows[r["Hash"]] for r in per.iter_rows(named=True))
    assert (per["distinct"] == per["len"]).all() and (per["ranks"] == per["len"]).all()


def test_plan_is_reproducible_and_differs_by_seed(tmp_path):
    lcfg = _cfg(tmp_path, SMALL)
    first = leakage.plan_sample(_binaries([150, 300]), lcfg)
    assert first.equals(leakage.plan_sample(_binaries([150, 300]), lcfg))
    pick = (pl.col("Hash") == "h1") & (pl.col("unit") == "all")
    s0 = first.filter(pick & (pl.col("seed") == 0))["position"].to_list()
    s1 = first.filter(pick & (pl.col("seed") == 1))["position"].to_list()
    assert s0 != s1


def _file(tmp_path, binaries_rows, batch_size):
    """One binary per (hash, rows): read holds the position, mmap2 is 1 on every row."""
    hashes, reads = [], []
    for hash_, n in binaries_rows:
        hashes += [hash_] * n
        reads += list(range(1, n + 1))
    table = pa.table(
        {
            "Call_mmap2": pa.array([1] * len(hashes), pa.int8()),
            "Call_read": pa.array(reads, pa.int16()),
            "Call_write": pa.array([0] * len(hashes), pa.int8()),
            "Hash": pa.array(hashes, pa.string()),
            "MalwareFamily": pa.array(["Mirai"] * len(hashes), pa.string()),
            "Arch": pa.array(["x86"] * len(hashes), pa.string()),
        }
    )
    pq.write_table(table, tmp_path / "s.parquet", row_group_size=batch_size)
    return pq.ParquetFile(tmp_path / "s.parquet")


@pytest.mark.parametrize("batch_size", [7, 40, 1000])
def test_positions_are_counted_across_batches(tmp_path, batch_size):
    parquet = _file(tmp_path, [("p", 30), ("q", 12), ("r", 25)], batch_size)
    out = pl.concat(list(rows.positioned(parquet, batch_size)))
    assert out["position"].to_list() == out["Call_read"].cast(pl.Int64).to_list()


@pytest.mark.parametrize("batch_size", [7, 40, 1000])
def test_sample_rows_keeps_exactly_the_wanted_rows(tmp_path, batch_size):
    parquet = _file(tmp_path, [("p", 30), ("q", 12), ("r", 25)], batch_size)
    wanted = pl.DataFrame({"Hash": ["p", "p", "q", "r", "r"], "position": [1, 29, 12, 2, 25]})
    out = leakage.sample_rows(
        parquet, canonical.Mapping.load(), VOCAB, wanted, batch_size=batch_size
    )
    got = sorted(zip(out["Hash"].to_list(), out["position"].to_list()))
    assert got == sorted(zip(wanted["Hash"].to_list(), wanted["position"].to_list()))
    assert (out["read"].cast(pl.Int64) == out["position"]).all()  # the row at that position
    assert (out["mmap"] == 1).all()  # mmap2 folded into mmap


def test_draw_takes_the_first_ranks_and_refuses_a_short_sample(tmp_path):
    lcfg = _cfg(tmp_path, SMALL)
    plan = leakage.plan_sample(_binaries([150]), lcfg)
    sample = (
        plan.select("Hash", "Arch", "position")
        .unique()
        .with_columns(pl.lit("Mirai").alias("MalwareFamily"), *[pl.lit(1).alias(v) for v in VOCAB])
    )
    big = leakage.draw(sample, plan, "all", 0, 8)
    small = leakage.draw(sample, plan, "all", 0, 3)
    assert big.height == 8 and small.height == 3
    assert set(small["position"]) <= set(big["position"])
    with pytest.raises(ValueError):
        needed = plan.filter((pl.col("unit") == "all") & (pl.col("seed") == 0))["position"][0]
        leakage.draw(sample.filter(pl.col("position") != needed), plan, "all", 0, 8)


def _world(n_binaries=200, rows_per=30, seed=0, separable=False):
    """One architecture of binaries, each its own behaviour group and its own fingerprint.

    Labels are random per binary; with ``separable`` the fingerprint also
    carries the label, otherwise only a binary's identity links rows to labels.
    """
    rng = np.random.default_rng(seed)
    labels = rng.integers(0, 2, size=n_binaries)
    data = {"Hash": [], "MalwareFamily": [], "Arch": [], "position": []}
    data.update({v: [] for v in SIX})
    for i in range(n_binaries):
        base = rng.integers(1, 21, size=len(SIX))
        if separable:
            base[0] = 40 if labels[i] else 0
        for p in range(1, rows_per + 1):
            noisy = base + rng.integers(0, 2, size=len(SIX))
            data["Hash"].append(f"b{i}")
            data["MalwareFamily"].append("Mirai" if labels[i] else "Benign")
            data["Arch"].append("x86")
            data["position"].append(p)
            for v, x in zip(SIX, noisy):
                data[v].append(int(x))
    drawn = pl.DataFrame(data)
    sides = np.array(split.SPLITS)[np.searchsorted([0.7, 0.8], rng.random(n_binaries))]
    behaviour = pl.DataFrame(
        {
            "Hash": [f"b{i}" for i in range(n_binaries)],
            "Arch": ["x86"] * n_binaries,
            "group": [f"x86:g{i}" for i in range(n_binaries)],
            "split": sides,
        }
    )
    by_hash = behaviour.select("Hash", "Arch", pl.col("split").alias(leakage.HASH_GROUPED))
    return drawn, behaviour, by_hash


FRACTIONS = {"train": 0.7, "val": 0.1, "test": 0.2}


def test_row_random_spreads_binaries_and_the_grouped_splits_never_do():
    drawn, behaviour, by_hash = _world(n_binaries=40)
    out = leakage.assign_splits(drawn, behaviour, by_hash, 0, FRACTIONS)
    sides = out.group_by("Hash").agg(*[pl.col(k).n_unique().alias(k) for k in leakage.SPLIT_KINDS])
    assert sides[leakage.ROW_RANDOM].max() > 1
    assert sides[leakage.HASH_GROUPED].max() == 1 and sides[leakage.BEHAVIOUR_GROUPED].max() == 1
    shares = out[leakage.ROW_RANDOM].value_counts(normalize=True)
    train = shares.filter(pl.col(leakage.ROW_RANDOM) == "train")["proportion"][0]
    assert abs(train - 0.7) < 0.05


def test_assign_splits_is_seeded_and_keeps_only_live_binaries():
    drawn, behaviour, by_hash = _world(n_binaries=40)
    dead = behaviour.with_columns(
        pl.when(pl.col("Hash") == "b0")
        .then(pl.lit("inert"))
        .otherwise(pl.col("split"))
        .alias("split")
    )
    a = leakage.assign_splits(drawn, dead, by_hash, 0, FRACTIONS)
    assert "b0" not in set(a["Hash"]) and a.height == 39 * 30
    assert a.equals(leakage.assign_splits(drawn.reverse(), dead, by_hash, 0, FRACTIONS))
    b = leakage.assign_splits(drawn, dead, by_hash, 1, FRACTIONS)
    assert not a[leakage.ROW_RANDOM].equals(b[leakage.ROW_RANDOM])
    with pytest.raises(ValueError):
        leakage.assign_splits(
            drawn, behaviour, by_hash.filter(pl.col("Hash") != "b3"), 0, FRACTIONS
        )


def test_hash_split_keeps_each_binary_whole_but_can_split_identical_binaries():
    # sixty binaries with one identical trace: dealt by hash, they spread over the sides
    n = 60
    store = pl.DataFrame(
        {
            "Hash": [f"m{i}" for i in range(n)],
            "MalwareFamily": ["Mirai"] * n,
            "Arch": ["x86"] * n,
            "windows": [500] * n,
            **{v: [3] * n for v in ["connect", "read", "socket"]},
        }
    )
    out = leakage.hash_split(store, split.SplitConfig.load())
    assert out.height == n and out["Hash"].n_unique() == n
    assert out[leakage.HASH_GROUPED].n_unique() == 3


def test_window_features_are_proportions():
    frame = pl.DataFrame({"mmap": [2, 0], "read": [2, 0], "write": [16, 0]})
    x = leakage.window_features(frame, VOCAB)
    assert np.allclose(x[0], [0.1, 0.1, 0.8]) and np.allclose(x[1], 0)


def test_a_row_random_split_rewards_memorising_binaries(model_cfg):
    # labels are noise: only a binary's identity links its rows to its label, so a
    # split that keeps binaries whole sits near chance and a row split does not
    drawn, behaviour, by_hash = _world()
    labelled = leakage.assign_splits(drawn, behaviour, by_hash, 0, FRACTIONS)
    out = pl.DataFrame(leakage.run_draw(labelled, SIX, model_cfg))
    window = out.filter(pl.col("view") == "window")
    mcc = dict(zip(window["split"], window["mcc"]))
    assert mcc[leakage.ROW_RANDOM] > 0.8
    assert abs(mcc[leakage.BEHAVIOUR_GROUPED]) < 0.3 and abs(mcc[leakage.HASH_GROUPED]) < 0.3
    assert set(out["view"]) == set(leakage.VIEWS)


def test_real_signal_survives_every_split(model_cfg):
    drawn, behaviour, by_hash = _world(separable=True)
    labelled = leakage.assign_splits(drawn, behaviour, by_hash, 0, FRACTIONS)
    out = pl.DataFrame(leakage.run_draw(labelled, SIX, model_cfg))
    assert out["mcc"].min() > 0.9


def test_binary_and_group_views_count_binaries_and_groups(model_cfg):
    drawn, behaviour, by_hash = _world(separable=True)
    # pair up binaries into groups of two
    behaviour = behaviour.with_columns(
        (pl.lit("x86:g") + (pl.col("Hash").str.slice(1).cast(pl.Int64) // 2).cast(pl.String)).alias(
            "group"
        )
    )
    labelled = leakage.assign_splits(drawn, behaviour, by_hash, 0, FRACTIONS)
    out = pl.DataFrame(leakage.run_draw(labelled, SIX, model_cfg))
    grouped = out.filter(pl.col("split") == leakage.BEHAVIOUR_GROUPED)
    n = dict(zip(grouped["view"], grouped["test_n"]))
    test = labelled.filter(pl.col(leakage.BEHAVIOUR_GROUPED) == "test")
    assert n["window"] == test.height
    assert n["binary"] == test["Hash"].n_unique()
    assert n["group"] == test["group"].n_unique()


def test_summarize_reports_both_gaps():
    results = pl.DataFrame(
        [
            {
                "unit": "mid",
                "cap": 100,
                "seed": s,
                "arch": "x86",
                "split": k,
                "view": "window",
                "mcc": m + 0.01 * s,
                "auroc": 0.99,
            }
            for s in (0, 1)
            for k, m in (
                (leakage.ROW_RANDOM, 0.9),
                (leakage.HASH_GROUPED, 0.8),
                (leakage.BEHAVIOUR_GROUPED, 0.75),
            )
        ]
    )
    table = leakage.summarize(results)
    r = table.row(0, named=True)
    assert r["row_gap"] == pytest.approx(0.1) and r["identity_gap"] == pytest.approx(0.05)
    assert r["seeds"] == 2 and r[f"mcc_min_{leakage.ROW_RANDOM}"] == pytest.approx(0.9)
    md = leakage.render_markdown(table)
    assert "## mid rows, cap 100, window view" in md and "+0.100" in md and "+0.050" in md


def test_empty_inputs_give_empty_frames_with_the_columns(tmp_path):
    lcfg = _cfg(tmp_path, SMALL)
    plan = leakage.plan_sample(_binaries([]).cast({"windows": pl.UInt32}), lcfg)
    assert plan.is_empty() and plan.columns == ["Hash", "Arch", "unit", "seed", "position", "rank"]
    parquet = _file(tmp_path, [("p", 5)], 100)
    none = pl.DataFrame({"Hash": ["zz"], "position": [1]})
    out = leakage.sample_rows(parquet, canonical.Mapping.load(), VOCAB, none)
    assert out.is_empty() and "position" in out.columns and set(VOCAB) <= set(out.columns)
