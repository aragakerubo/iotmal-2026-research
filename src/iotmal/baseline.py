"""Gradient-boosted-tree baselines on the per-binary feature store.

Three experiments share one model, one feature map and one scoring
routine, so their numbers differ only in which binaries sit on which
side:

* **in-architecture**: for each architecture, train on its ``train``
  binaries, stop early on its ``val`` binaries, score its ``test``
  binaries. This is the reference every published number on this
  dataset implicitly claims, done with a behaviour-grouped split (D2).
* **leave-one-architecture-out**: for each architecture, train on the
  ``train`` binaries of the other three, stop early on their ``val``
  binaries, and score every live binary of the held-out architecture,
  test column or not. This is the paper's question. The held-out
  architecture is never seen, so its whole live population is a fair
  test set, and using all of it is what makes the ARM fold usable at
  all: ARM has 150 live benign binaries in total (D8).
* **architecture-sanity**: train on every architecture's ``train``
  binaries to predict the architecture itself, score on ``test``. If
  this is far above chance, the canonical vocabulary (D6) still lets a
  model tell architectures apart, and a cross-architecture detector may
  be learning "which sandbox" rather than "which behaviour".
* **first-window**: the three experiments above, run again on each
  first-N store (``iotmal.first_window``), where each binary is
  represented by its first N system calls only, or its whole trace when
  it made fewer, and once more on one prefix with the network calls
  removed from the features. The split, the folds and the model are
  unchanged, so the gap to the whole-trace numbers is how much the class
  depends on behaviour past the prologue (D8), and the prefix at which
  the gap closes is how early the class is named.

Every binary labelled ``test`` by the split is unseen in every
experiment, so the in-architecture and leave-one-out numbers for one
architecture are scored on overlapping populations and can be compared.

Each detection fold is scored twice: once per binary, and once per
behaviour group, where the binaries that share one exact syscall vector
count as a single example with the mean of their scores. The group
view answers "how many distinct behaviours does the model get right",
which the duplicate-heavy classes (190 identical x86 Mirai builds)
would otherwise swamp.

The model is XGBoost with the parameters in ``configs/baseline.yaml``.
It is a baseline: fast, strong on tabular counts, and nothing a
microcontroller runs. The neural models in later steps are compared
against it.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import polars as pl
import yaml
from sklearn.metrics import accuracy_score, f1_score, matthews_corrcoef, roc_auc_score
from xgboost import XGBClassifier

from iotmal.canonical import SHARED
from iotmal.paths import CONFIG_DIR, DATA_DIR
from iotmal.split import BENIGN, SPLITS, WINDOW, trace_length

HASH, LABEL, ARCH = SHARED
TARGET = "is_malware"
GROUP = "group"
SPLIT = "split"
IN_ARCH = "in-architecture"
LOAO = "leave-one-architecture-out"
SANITY = "architecture-sanity"
FIRST_WINDOW = "first"
"""Label stem of the first-window runs: ``first-20``, ``first-20-no-network``."""
EXPERIMENTS = (IN_ARCH, LOAO, SANITY)
"""The three evaluations; each first-window run repeats them under a prefixed name."""
VIEWS = ("binary", "group")
FEATURE_KINDS = ("profile", "log_counts")
RESULT_COLUMNS = (
    "experiment",
    "held_out",
    "view",
    "train_n",
    "test_n",
    "test_benign",
    "test_malware",
    "chance",
    "accuracy",
    "macro_f1",
    "mcc",
    "auroc",
    "best_round",
)


@dataclass(frozen=True)
class BaselineConfig:
    """The YAML, typed."""

    seed: int
    features: str
    early_stopping_rounds: int
    xgboost: dict

    @classmethod
    def load(cls, path: Path | None = None) -> BaselineConfig:
        """Read ``configs/baseline.yaml`` (or ``path``) and validate the feature kind."""
        raw = yaml.safe_load((path or CONFIG_DIR / "baseline.yaml").read_text())
        if raw["features"] not in FEATURE_KINDS:
            raise ValueError(f"features must be one of {FEATURE_KINDS}, got {raw['features']}")
        return cls(
            seed=int(raw["seed"]),
            features=raw["features"],
            early_stopping_rounds=int(raw["early_stopping_rounds"]),
            xgboost=dict(raw.get("xgboost") or {}),
        )


@dataclass(frozen=True)
class Fold:
    """Row positions into one frame for one train, validation and test set."""

    experiment: str
    held_out: str
    train: np.ndarray
    val: np.ndarray
    test: np.ndarray


def load_assignment(splits_dir: Path | None = None) -> pl.DataFrame:
    """Concatenate ``data/splits/<arch>.csv`` into one frame."""
    files = sorted((splits_dir or DATA_DIR / "splits").glob("*.csv"))
    if not files:
        raise FileNotFoundError("no split files; run scripts/make_splits.py first")
    return pl.concat([pl.read_csv(f, schema_overrides={HASH: pl.String}) for f in files])


def live_binaries(binaries: pl.DataFrame, assignment: pl.DataFrame) -> pl.DataFrame:
    """Join the feature store to its split assignment and keep the live rows.

    Rows whose split is ``inert`` or ``conflict`` are dropped, as are
    binaries the assignment does not know (labels in ``drop_labels``).
    Adds ``is_malware`` and sorts so every run sees rows in one order.
    """
    keyed = assignment.select(HASH, ARCH, GROUP, SPLIT)
    return (
        binaries.join(keyed, on=[HASH, ARCH], how="inner")
        .filter(pl.col(SPLIT).is_in(list(SPLITS)))
        .with_columns((pl.col(LABEL) != BENIGN).alias(TARGET))
        .sort(ARCH, HASH)
    )


def featurize(frame: pl.DataFrame, vocabulary: list[str], kind: str) -> np.ndarray:
    """Turn summed counts into a float32 matrix, one row per binary.

    ``profile`` divides each count by the trace's total and appends the
    log of the trace length, so two traces that do the same things in
    the same proportions look alike whatever their length. ``log_counts``
    keeps the raw magnitudes under ``log1p``.
    """
    counts = frame.select(vocabulary).to_numpy().astype(np.float64)
    if kind == "log_counts":
        return np.log1p(counts).astype(np.float32)
    total = counts.sum(axis=1, keepdims=True)
    profile = np.divide(counts, total, out=np.zeros_like(counts), where=total > 0)
    length = frame.select(trace_length(pl.col("windows"))).to_numpy().astype(np.float64)
    return np.hstack([profile, np.log1p(length)]).astype(np.float32)


def _where(frame: pl.DataFrame, condition: pl.Expr) -> np.ndarray:
    """Row positions where ``condition`` holds."""
    return np.flatnonzero(frame.select(condition).to_series().to_numpy())


def in_architecture_folds(frame: pl.DataFrame) -> list[Fold]:
    """One fold per architecture, each confined to that architecture's split columns."""
    folds = []
    for arch in sorted(frame[ARCH].unique().to_list()):
        own = pl.col(ARCH) == arch
        folds.append(
            Fold(
                IN_ARCH,
                arch,
                _where(frame, own & (pl.col(SPLIT) == "train")),
                _where(frame, own & (pl.col(SPLIT) == "val")),
                _where(frame, own & (pl.col(SPLIT) == "test")),
            )
        )
    return folds


def leave_one_out_folds(frame: pl.DataFrame) -> list[Fold]:
    """One fold per architecture: train on the others, test on all of it."""
    folds = []
    for arch in sorted(frame[ARCH].unique().to_list()):
        own = pl.col(ARCH) == arch
        folds.append(
            Fold(
                LOAO,
                arch,
                _where(frame, ~own & (pl.col(SPLIT) == "train")),
                _where(frame, ~own & (pl.col(SPLIT) == "val")),
                _where(frame, own),
            )
        )
    return folds


def fit(
    cfg: BaselineConfig,
    x_train: np.ndarray,
    y_train: np.ndarray,
    x_val: np.ndarray | None = None,
    y_val: np.ndarray | None = None,
    *,
    num_class: int | None = None,
) -> XGBClassifier:
    """Fit a booster, stopping early on the validation set when there is one."""
    params = dict(cfg.xgboost)
    params["random_state"] = cfg.seed
    if num_class is not None:
        params["objective"] = "multi:softprob"
        params["num_class"] = num_class
    has_val = x_val is not None and len(x_val) > 0
    if has_val:
        params["early_stopping_rounds"] = cfg.early_stopping_rounds
    model = XGBClassifier(**params)
    model.fit(x_train, y_train, eval_set=[(x_val, y_val)] if has_val else None, verbose=False)
    return model


def metrics(y_true: np.ndarray, scores: np.ndarray) -> dict[str, float | None]:
    """Binary metrics at a 0.5 threshold, plus AUROC when both classes are present."""
    pred = scores >= 0.5
    both = len(np.unique(y_true)) == 2
    return {
        "chance": float(max(y_true.mean(), 1 - y_true.mean())),
        "accuracy": float(accuracy_score(y_true, pred)),
        "macro_f1": float(f1_score(y_true, pred, average="macro", zero_division=0)),
        "mcc": float(matthews_corrcoef(y_true, pred)),
        "auroc": float(roc_auc_score(y_true, scores)) if both else None,
    }


def collapse_groups(groups: np.ndarray, y_true: np.ndarray, scores: np.ndarray) -> tuple:
    """Average scores within a behaviour group; one label and one score per group.

    Groups never mix benign and malware (the split sets those aside as
    conflicts), so the first label of each group is the group's label.
    """
    order = np.argsort(groups, kind="stable")
    keys, starts = np.unique(groups[order], return_index=True)
    sums = np.add.reduceat(scores[order], starts)
    sizes = np.diff(np.append(starts, len(order)))
    return y_true[order][starts], sums / sizes


def score_fold(
    frame: pl.DataFrame, features: np.ndarray, fold: Fold, cfg: BaselineConfig
) -> list[dict]:
    """Fit on the fold and return one result row per view."""
    y = frame[TARGET].to_numpy().astype(int)
    model = fit(cfg, features[fold.train], y[fold.train], features[fold.val], y[fold.val])
    scores = model.predict_proba(features[fold.test])[:, 1]
    y_test = y[fold.test]
    groups = frame[GROUP].to_numpy()[fold.test]
    best = int(getattr(model, "best_iteration", model.get_num_boosting_rounds() - 1)) + 1
    rows = []
    for view in VIEWS:
        yv, sv = (y_test, scores) if view == "binary" else collapse_groups(groups, y_test, scores)
        rows.append(
            {
                "experiment": fold.experiment,
                "held_out": fold.held_out,
                "view": view,
                "train_n": int(len(fold.train)),
                "test_n": int(len(yv)),
                "test_benign": int((yv == 0).sum()),
                "test_malware": int((yv == 1).sum()),
                **metrics(yv, sv),
                "best_round": best,
            }
        )
    return rows


def architecture_sanity(frame: pl.DataFrame, features: np.ndarray, cfg: BaselineConfig) -> dict:
    """Predict the architecture from the features; report how far above chance."""
    arches = sorted(frame[ARCH].unique().to_list())
    codes = frame.select(pl.col(ARCH).replace_strict({a: i for i, a in enumerate(arches)}))
    y = codes.to_series().to_numpy().astype(int)
    train = _where(frame, pl.col(SPLIT) == "train")
    val = _where(frame, pl.col(SPLIT) == "val")
    test = _where(frame, pl.col(SPLIT) == "test")
    model = fit(cfg, features[train], y[train], features[val], y[val], num_class=len(arches))
    pred = model.predict(features[test])
    y_test = y[test]
    share = np.bincount(y_test, minlength=len(arches)) / len(y_test)
    best = int(getattr(model, "best_iteration", model.get_num_boosting_rounds() - 1)) + 1
    return {
        "experiment": SANITY,
        "held_out": "all",
        "view": "binary",
        "train_n": int(len(train)),
        "test_n": int(len(test)),
        "test_benign": int((frame[TARGET].to_numpy()[test] == 0).sum()),
        "test_malware": int((frame[TARGET].to_numpy()[test] == 1).sum()),
        "chance": float(share.max()),
        "accuracy": float(accuracy_score(y_test, pred)),
        "macro_f1": float(f1_score(y_test, pred, average="macro", zero_division=0)),
        "mcc": float(matthews_corrcoef(y_test, pred)),
        "auroc": None,
        "best_round": best,
    }


def run(
    binaries: pl.DataFrame,
    assignment: pl.DataFrame,
    vocabulary: list[str],
    cfg: BaselineConfig,
) -> pl.DataFrame:
    """All three experiments on one feature store; one row per fold and view."""
    frame = live_binaries(binaries, assignment)
    features = featurize(frame, vocabulary, cfg.features)
    rows: list[dict] = []
    for fold in in_architecture_folds(frame) + leave_one_out_folds(frame):
        rows.extend(score_fold(frame, features, fold, cfg))
    rows.append(architecture_sanity(frame, features, cfg))
    return pl.DataFrame(rows, schema_overrides={"auroc": pl.Float64}).select(RESULT_COLUMNS)


def first_window(
    first: pl.DataFrame,
    assignment: pl.DataFrame,
    vocabulary: list[str],
    cfg: BaselineConfig,
    calls: int = WINDOW,
    drop: tuple[str, ...] = (),
    label: str | None = None,
) -> pl.DataFrame:
    """Run the three experiments on a first-``calls`` store under prefixed experiment names.

    The prefix is ``label``, by default ``first-<calls>``. ``first`` must
    describe at most ``calls`` calls of each binary. The check exists
    because every store has the same schema, and passing the wrong one
    would produce another store's results under this name. ``drop``
    removes calls from the features; a name outside the vocabulary
    raises, so a misspelt call cannot leave the features unchanged.
    """
    if (first["windows"] > calls).any():
        raise ValueError(f"first-window store has binaries with more than {calls} calls")
    unknown = set(drop) - set(vocabulary)
    if unknown:
        raise ValueError(f"cannot drop calls outside the vocabulary: {sorted(unknown)}")
    kept = [v for v in vocabulary if v not in set(drop)]
    results = run(first, assignment, kept, cfg)
    prefix = f"{label or f'{FIRST_WINDOW}-{calls}'} "
    return results.with_columns((pl.lit(prefix) + pl.col("experiment")).alias("experiment"))


def compare(results: pl.DataFrame, labels: list[str], metric: str = "mcc") -> pl.DataFrame:
    """One ``metric`` per run, side by side: the whole trace, then each labelled run.

    One row per experiment, held-out architecture and view. Every run
    must score the same binaries, since only the features differ; a fold
    whose test count differs from the whole trace's raises.
    """
    keys = ["experiment", "held_out", "view"]
    table = results.filter(pl.col("experiment").is_in(list(EXPERIMENTS))).select(
        *keys, "test_n", pl.col(metric).alias("whole")
    )
    for label in labels:
        run_ = results.filter(pl.col("experiment").str.starts_with(f"{label} ")).select(
            pl.col("experiment").str.strip_prefix(f"{label} "),
            "held_out",
            "view",
            pl.col("test_n").alias("test_n_run"),
            pl.col(metric).alias(label),
        )
        table = table.join(run_, on=keys, how="inner")
        mismatched = table.filter(pl.col("test_n") != pl.col("test_n_run"))
        if not mismatched.is_empty():
            raise ValueError(f"{mismatched.height} folds of {label} score different binaries")
        table = table.drop("test_n_run")
    return table


def _fmt(x: float | None) -> str:
    """Three decimals, or blank for a metric that was not computed."""
    return "" if x is None else f"{x:.3f}"


def render_comparison(table: pl.DataFrame) -> str:
    """Render a ``compare`` table as markdown, one column per run."""
    runs = table.columns[4:]
    out = [
        "| Experiment | Held out | View | Test | " + " | ".join(runs) + " |",
        "| --- | --- | --- | --- | " + " | ".join("---" for _ in runs) + " |",
    ]
    for r in table.iter_rows(named=True):
        cells = [r["experiment"], r["held_out"], r["view"], str(r["test_n"])]
        out.append("| " + " | ".join(cells + [_fmt(r[c]) for c in runs]) + " |")
    return "\n".join(out) + "\n"


def render_markdown(results: pl.DataFrame) -> str:
    """One table per experiment, in the order the results list them."""
    out = []
    for experiment in results["experiment"].unique(maintain_order=True).to_list():
        part = results.filter(pl.col("experiment") == experiment)
        out += [
            f"## {experiment}",
            "",
            "| Held out | View | Train | Test | Benign | Malware | Chance | Accuracy "
            "| Macro-F1 | MCC | AUROC | Rounds |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
        for r in part.iter_rows(named=True):
            auroc = "" if r["auroc"] is None else f"{r['auroc']:.3f}"
            out.append(
                f"| {r['held_out']} | {r['view']} | {r['train_n']} | {r['test_n']} "
                f"| {r['test_benign']} | {r['test_malware']} | {r['chance']:.3f} "
                f"| {r['accuracy']:.3f} | {r['macro_f1']:.3f} | {r['mcc']:.3f} | {auroc} "
                f"| {r['best_round']} |"
            )
        out.append("")
    return "\n".join(out)
