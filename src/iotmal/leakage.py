"""H3: how much a row-level random split overstates accuracy (D10).

The dataset paper classified single STRACE rows and split them at
random, so rows of one binary sat on both sides and a test row's
near-twin (nineteen of its twenty calls shared) was in training. This
module measures the effect on our data. It draws a capped sample of
rows per binary, splits the sampled rows three ways within each
architecture, and scores the same XGBoost on each:

* ``row-random``: every row goes to train, val or test at random, as in
  the dataset paper; rows of one binary land on several sides.
* ``hash-grouped``: every binary's rows stay on one side (the original
  D2), dealt by hash with the split rules of ``iotmal.split``.
* ``behaviour-grouped``: the committed split in ``data/splits/``, which
  also keeps binaries with identical traces on one side (D2 revised).

The step from row-random to hash-grouped is the leak through a binary's
own neighbouring rows; the step from hash-grouped to behaviour-grouped
is the leak through identical binaries under different hashes.

Rows are drawn per binary, per unit and per seed (``configs/leakage.yaml``):
the ``mid`` unit draws from rows 21 on, which hold no program start-up,
and the ``all`` unit from every row. Which rows a draw holds is decided
from each binary's row count alone, before any file is read, so a draw
is exact and reproducible and the scan only has to keep the planned
rows. A smaller cap takes the first rows of the larger cap's draw.

Each fold is scored per window, per binary (the mean of the binary's
test-window scores) and per behaviour group, at thresholds chosen on
the fold's validation windows or binaries (D9).
"""

from __future__ import annotations

import zlib
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np
import polars as pl
import pyarrow.parquet as pq
import yaml

from iotmal import baseline, canonical, rows, split
from iotmal.canonical import SHARED
from iotmal.paths import CONFIG_DIR

HASH, LABEL, ARCH = SHARED
POSITION = rows.POSITION
GROUP = "group"
ROW_RANDOM = "row-random"
HASH_GROUPED = "hash-grouped"
BEHAVIOUR_GROUPED = "behaviour-grouped"
SPLIT_KINDS = (ROW_RANDOM, HASH_GROUPED, BEHAVIOUR_GROUPED)
VIEWS = ("window", "binary", "group")
RESULT_COLUMNS = (
    "unit",
    "cap",
    "seed",
    "arch",
    "split",
    "view",
    "train_n",
    "test_n",
    "test_benign",
    "test_malware",
    "chance",
    "threshold",
    "accuracy",
    "macro_f1",
    "mcc",
    "mcc_half",
    "auroc",
    "best_round",
)


@dataclass(frozen=True)
class LeakageConfig:
    """The YAML, typed."""

    units: dict[str, int]
    cap: int
    sensitivity_cap: int
    seeds: tuple[int, ...]

    @classmethod
    def load(cls, path: Path | None = None) -> LeakageConfig:
        """Read ``configs/leakage.yaml`` (or ``path``) and check the caps and units."""
        raw = yaml.safe_load((path or CONFIG_DIR / "leakage.yaml").read_text())
        units = {name: int(spec["first_row"]) for name, spec in raw["units"].items()}
        cap, small = int(raw["cap"]), int(raw["sensitivity_cap"])
        if not units or min(units.values()) < 1:
            raise ValueError(f"every unit needs a first_row of at least 1, got {units}")
        if not 0 < small <= cap:
            raise ValueError(f"need 0 < sensitivity_cap <= cap, got {small} and {cap}")
        seeds = tuple(int(s) for s in raw["seeds"])
        if not seeds:
            raise ValueError("at least one seed is needed")
        return cls(units, cap, small, seeds)


def plan_sample(binaries: pl.DataFrame, cfg: LeakageConfig) -> pl.DataFrame:
    """Return which rows every draw holds: one row per binary, unit, seed and drawn position.

    ``binaries`` needs ``Hash``, ``Arch`` and ``windows`` (the binary's
    row count, from the whole-trace store). For each unit and seed, a
    binary contributes ``cap`` positions drawn uniformly without
    replacement from its eligible rows, or all of them when it has
    fewer; ``rank`` is the order of the draw, so the first ``k`` ranks
    are a draw of ``k``. The generator is seeded by the seed and a CRC-32
    of ``arch/hash/unit``, stable across runs and machines.
    """
    units = list(cfg.units.items())
    parts: dict[str, list[np.ndarray]] = {
        k: [] for k in ("index", "unit", "seed", POSITION, "rank")
    }
    keyed = binaries.select(HASH, ARCH, "windows").with_row_index("index")
    for index, hash_, arch, windows in keyed.iter_rows():
        for u, (unit, first_row) in enumerate(units):
            eligible = max(0, int(windows) - first_row + 1)
            if not eligible:
                continue
            key = zlib.crc32(f"{arch}/{hash_}/{unit}".encode())
            k = min(cfg.cap, eligible)
            for seed in cfg.seeds:
                drawn = np.random.default_rng([seed, key]).choice(eligible, size=k, replace=False)
                parts["index"].append(np.full(k, index, dtype=np.uint32))
                parts["unit"].append(np.full(k, u, dtype=np.int8))
                parts["seed"].append(np.full(k, seed, dtype=np.int64))
                parts[POSITION].append(drawn.astype(np.int64) + first_row)
                parts["rank"].append(np.arange(1, k + 1, dtype=np.int64))
    if not parts["index"]:
        empty = {"index": np.uint32, "unit": np.int8, "seed": np.int64, POSITION: np.int64}
        parts = {k: [np.zeros(0, dtype=empty.get(k, np.int64))] for k in parts}
    flat = pl.DataFrame({k: np.concatenate(v) for k, v in parts.items()})
    names = {i: name for i, (name, _) in enumerate(units)}
    return flat.join(
        keyed.select("index", HASH, ARCH), on="index", how="left", maintain_order="left"
    ).select(
        HASH,
        ARCH,
        pl.col("unit").replace_strict(names, return_dtype=pl.String),
        "seed",
        POSITION,
        "rank",
    )


def sample_rows(
    parquet: pq.ParquetFile,
    mapping: canonical.Mapping,
    vocabulary: list[str],
    wanted: pl.DataFrame,
    batch_size: int = 200_000,
) -> pl.DataFrame:
    """Keep the rows whose ``(Hash, position)`` is in ``wanted``, canonicalised (D6).

    Returns the shared columns, ``position`` and the vocabulary as
    ``Int16``, one row per wanted row present in the file, in file order.
    """
    keys = wanted.select(pl.col(HASH), pl.col(POSITION).cast(pl.Int64)).unique()
    parts = []
    for frame in rows.positioned(parquet, batch_size):
        kept = frame.with_columns(pl.col(POSITION).cast(pl.Int64)).join(
            keys, on=[HASH, POSITION], how="semi", maintain_order="left"
        )
        if kept.height:
            parts.append(
                canonical.canonicalize(kept, mapping, vocabulary).with_columns(kept[POSITION])
            )
    if not parts:
        schema = {HASH: pl.String, LABEL: pl.String, ARCH: pl.String}
        return pl.DataFrame(
            schema={**schema, **{v: canonical.DTYPE for v in vocabulary}, POSITION: pl.Int64}
        )
    return pl.concat(parts)


def draw(sample: pl.DataFrame, plan: pl.DataFrame, unit: str, seed: int, cap: int) -> pl.DataFrame:
    """Return the sampled rows of one draw: the first ``cap`` ranks of one unit and seed.

    Raises when the sample lacks a planned row, which happens when the
    config asks for rows the scan did not keep; the scan must be rerun.
    """
    planned = plan.filter(
        (pl.col("unit") == unit) & (pl.col("seed") == seed) & (pl.col("rank") <= cap)
    ).select(HASH, ARCH, POSITION)
    got = planned.join(sample, on=[HASH, ARCH, POSITION], how="inner")
    if got.height != planned.height:
        raise ValueError(
            f"{planned.height - got.height} planned rows are missing from the sample; "
            "rerun scripts/window_sample_scan.py"
        )
    return got.sort(ARCH, HASH, POSITION)


def hash_split(binaries: pl.DataFrame, split_cfg: split.SplitConfig) -> pl.DataFrame:
    """Deal binaries by hash with the split rules and seed of ``configs/split.yaml``.

    The original D2 split: every binary on one side, identical binaries
    free to land on different sides. Inert binaries are set aside as in
    the committed split.
    """
    return split.assign(binaries, replace(split_cfg, group_by="hash")).select(
        HASH, ARCH, pl.col("split").alias(HASH_GROUPED)
    )


def assign_splits(
    drawn: pl.DataFrame,
    behaviour: pl.DataFrame,
    by_hash: pl.DataFrame,
    seed: int,
    fractions: dict[str, float],
) -> pl.DataFrame:
    """Label every drawn row with its side under each of the three splits.

    Only binaries live in the committed split are kept, so the three
    splits share one population. ``behaviour`` is the committed
    assignment (``Hash``, ``Arch``, ``group``, ``split``); ``by_hash`` is
    ``hash_split``. The row-random side is drawn per row from the seed,
    with the committed shares.
    """
    live = behaviour.filter(pl.col("split").is_in(list(split.SPLITS))).select(
        HASH, ARCH, GROUP, pl.col("split").alias(BEHAVIOUR_GROUPED)
    )
    # sorted so the row-random draw below meets the rows in one fixed order
    out = (
        drawn.join(live, on=[HASH, ARCH], how="inner")
        .join(by_hash, on=[HASH, ARCH], how="left")
        .sort(ARCH, HASH, POSITION)
    )
    if not out[HASH_GROUPED].is_in(list(split.SPLITS)).fill_null(False).all():
        raise ValueError("a live binary has no hash-grouped side; the two splits disagree")
    u = np.random.default_rng([seed, zlib.crc32(ROW_RANDOM.encode())]).random(out.height)
    edges = np.cumsum([fractions[s] for s in split.SPLITS])
    sides = np.array(split.SPLITS)[
        np.searchsorted(edges, u, side="right").clip(max=len(split.SPLITS) - 1)
    ]
    return out.with_columns(
        pl.Series(ROW_RANDOM, sides), (pl.col(LABEL) != baseline.BENIGN).alias(baseline.TARGET)
    )


def window_features(frame: pl.DataFrame, vocabulary: list[str]) -> np.ndarray:
    """Each row's counts divided by its total: what the window did, not how many calls it held.

    A row before the twentieth holds fewer than twenty calls; dividing
    by the total keeps that count, and so the row's position, out of the
    features.
    """
    counts = frame.select(vocabulary).to_numpy().astype(np.float64)
    total = counts.sum(axis=1, keepdims=True)
    return np.divide(counts, total, out=np.zeros_like(counts), where=total > 0).astype(np.float32)


def score_split(
    frame: pl.DataFrame, features: np.ndarray, kind: str, cfg: baseline.BaselineConfig
) -> list[dict]:
    """Fit on one architecture's rows under one split; one result per view.

    Window thresholds come from validation windows. Binary and group
    thresholds come from validation binaries, scored by the mean of
    their validation windows, and the group view collapses test binaries
    into behaviour groups with the binary threshold.
    """
    y = frame[baseline.TARGET].to_numpy().astype(int)
    side = frame[kind].to_numpy()
    train, val, test = (np.flatnonzero(side == s) for s in split.SPLITS)
    model = baseline.fit(cfg, features[train], y[train], features[val], y[val])
    best = int(getattr(model, "best_iteration", model.get_num_boosting_rounds() - 1)) + 1
    hashes = frame[HASH].to_numpy()
    groups = frame[GROUP].to_numpy()
    s_val = model.predict_proba(features[val])[:, 1]
    s_test = model.predict_proba(features[test])[:, 1]

    yb_val, sb_val = baseline.collapse_groups(hashes[val], y[val], s_val)
    yb_test, sb_test = baseline.collapse_groups(hashes[test], y[test], s_test)
    # one behaviour group per test binary, in the order collapse_groups returns binaries
    keys = np.unique(hashes[test])
    group_of = dict(zip(hashes[test], groups[test]))
    yg_test, sg_test = baseline.collapse_groups(
        np.array([group_of[h] for h in keys]), yb_test, sb_test
    )

    window_cut = baseline.choose_threshold(y[val], s_val)
    binary_cut = baseline.choose_threshold(yb_val, sb_val)
    views = {
        "window": (y[test], s_test, window_cut),
        "binary": (yb_test, sb_test, binary_cut),
        "group": (yg_test, sg_test, binary_cut),
    }
    out = []
    for view, (yv, sv, cut) in views.items():
        out.append(
            {
                "split": kind,
                "view": view,
                "train_n": int(len(train)),
                "test_n": int(len(yv)),
                "test_benign": int((yv == 0).sum()),
                "test_malware": int((yv == 1).sum()),
                **baseline.metrics(yv, sv, cut),
                "best_round": best,
            }
        )
    return out


def run_draw(
    labelled: pl.DataFrame,
    vocabulary: list[str],
    cfg: baseline.BaselineConfig,
) -> list[dict]:
    """Score every architecture under every split for one draw labelled by ``assign_splits``."""
    out = []
    for arch in sorted(labelled[ARCH].unique().to_list()):
        frame = labelled.filter(pl.col(ARCH) == arch)
        features = window_features(frame, vocabulary)
        for kind in SPLIT_KINDS:
            out += [{"arch": arch, **r} for r in score_split(frame, features, kind, cfg)]
    return out


def summarize(results: pl.DataFrame) -> pl.DataFrame:
    """Mean and range of MCC and AUROC over seeds, with the leak each step of the split adds.

    One row per unit, cap, architecture and view. ``row_gap`` is
    row-random minus hash-grouped mean MCC, the leak through a binary's
    own rows; ``identity_gap`` is hash-grouped minus behaviour-grouped,
    the leak through identical binaries.
    """
    keys = ["unit", "cap", "arch", "view"]
    stats = results.group_by(*keys, "split").agg(
        pl.col("mcc").mean().alias("mcc"),
        pl.col("mcc").min().alias("mcc_min"),
        pl.col("mcc").max().alias("mcc_max"),
        pl.col("auroc").mean().alias("auroc"),
        pl.len().alias("seeds"),
    )
    wide = stats.pivot(on="split", index=keys, values=["mcc", "mcc_min", "mcc_max", "auroc"])
    seeds = stats.group_by(keys).agg(pl.col("seeds").min())
    return (
        wide.join(seeds, on=keys)
        .with_columns(
            (pl.col(f"mcc_{ROW_RANDOM}") - pl.col(f"mcc_{HASH_GROUPED}")).alias("row_gap"),
            (pl.col(f"mcc_{HASH_GROUPED}") - pl.col(f"mcc_{BEHAVIOUR_GROUPED}")).alias(
                "identity_gap"
            ),
        )
        .sort("unit", pl.col("cap"), "view", "arch", descending=[True, True, False, False])
    )


def render_markdown(summary: pl.DataFrame) -> str:
    """One table per unit, cap and view: MCC per split with its range, and the two gaps."""
    out = []
    for (unit, cap, view), part in summary.group_by("unit", "cap", "view", maintain_order=True):
        out += [
            f"## {unit} rows, cap {cap}, {view} view",
            "",
            "| Arch | Seeds | Row-random MCC | Hash-grouped MCC | Behaviour-grouped MCC "
            "| Row gap | Identity gap | Row-random AUROC | Behaviour-grouped AUROC |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
        for r in part.iter_rows(named=True):

            def cell(kind: str, r: dict = r) -> str:
                return (
                    f"{r[f'mcc_{kind}']:.3f} ({r[f'mcc_min_{kind}']:.3f} to "
                    f"{r[f'mcc_max_{kind}']:.3f})"
                )

            out.append(
                f"| {r['arch']} | {r['seeds']} | {cell(ROW_RANDOM)} | {cell(HASH_GROUPED)} "
                f"| {cell(BEHAVIOUR_GROUPED)} | {r['row_gap']:+.3f} | {r['identity_gap']:+.3f} "
                f"| {r[f'auroc_{ROW_RANDOM}']:.3f} | {r[f'auroc_{BEHAVIOUR_GROUPED}']:.3f} |"
            )
        out.append("")
    return "\n".join(out)
