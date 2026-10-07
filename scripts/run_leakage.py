"""Score the H3 leakage experiment; write the results table.

Usage::

    python scripts/run_leakage.py                       # reads data/windows/
    python scripts/run_leakage.py s3://<bucket>/features/windows

Rebuilds every draw of ``configs/leakage.yaml`` from the whole-trace
store's row counts, takes its rows from the sample written by
scripts/window_sample_scan.py, splits them three ways within each
architecture (``iotmal.leakage``), scores XGBoost with
``configs/baseline.yaml`` on each, and writes:

* ``data/leakage/results.csv``: one row per unit, cap, seed,
  architecture, split and view; committed.
* ``data/LEAKAGE.md``: MCC per split, mean and range over seeds, with
  the two gaps, one table per unit, cap and view.

Twelve boosters per draw on up to about 400,000 rows; the run time is
printed per draw.
"""

import sys
import time
from datetime import date

import polars as pl

from iotmal import baseline, dedup, leakage, split
from iotmal.paths import DATA_DIR, ensure_dir

NOTES = """
Reading the tables. Each row of the experiment is one STRACE row, a
window over at most twenty calls. `mid` rows are drawn from the
twenty-first row of a binary on, so they hold no program start-up;
`all` rows from every row, as the dataset paper used them. Row-random
puts every row on a side at random, as the dataset paper did;
hash-grouped keeps every binary on one side; behaviour-grouped is the
committed split, which also keeps identical binaries together. The row
gap is row-random minus hash-grouped MCC, the leak through a binary's
own neighbouring rows; the identity gap is hash-grouped minus
behaviour-grouped, the leak through identical binaries. MCC is the mean
over seeds with its range in brackets, at thresholds chosen on
validation windows (window view) or validation binaries (binary and
group views). The binary view scores each test binary by the mean of
its test windows, so under row-random a binary's score comes only from
its rows that landed in test.
"""


def main(source: str | None) -> None:
    """Run every draw and write the report."""
    cfg = leakage.LeakageConfig.load()
    model_cfg = baseline.BaselineConfig.load()
    split_cfg = split.SplitConfig.load()
    vocabulary = pl.read_csv(DATA_DIR / "syscall_vocabulary.csv")["canonical"].to_list()
    whole = dedup.load_feature_store()
    plan = leakage.plan_sample(whole, cfg)
    sample = dedup.load_feature_store(source or DATA_DIR / "windows", stem="sample_strace")
    behaviour = baseline.load_assignment()
    by_hash = leakage.hash_split(whole, split_cfg)

    draws = [(u, s, cfg.cap) for u in cfg.units for s in cfg.seeds]
    draws += [(u, cfg.seeds[0], cfg.sensitivity_cap) for u in cfg.units]
    rows = []
    for unit, seed, cap in draws:
        start = time.time()
        drawn = leakage.draw(sample, plan, unit, seed, cap)
        labelled = leakage.assign_splits(drawn, behaviour, by_hash, seed, split_cfg.fractions)
        found = leakage.run_draw(labelled, vocabulary, model_cfg)
        rows += [{"unit": unit, "cap": cap, "seed": seed, **r} for r in found]
        print(f"{unit} cap {cap} seed {seed}: {labelled.height} rows, {time.time() - start:.0f}s")

    results = pl.DataFrame(rows, schema_overrides={"auroc": pl.Float64}).select(
        leakage.RESULT_COLUMNS
    )
    out = ensure_dir(DATA_DIR / "leakage")
    results.write_csv(out / "results.csv")
    table = leakage.render_markdown(leakage.summarize(results))
    (DATA_DIR / "LEAKAGE.md").write_text(
        f"# Leakage (H3)\n\nRun on {date.today().isoformat()} with units {cfg.units}, cap "
        f"{cfg.cap} over seeds {list(cfg.seeds)} and cap {cfg.sensitivity_cap} on seed "
        f"{cfg.seeds[0]}; XGBoost {model_cfg.xgboost}, early stopping after "
        f"{model_cfg.early_stopping_rounds} rounds. See `docs/experiment_h3_leakage.md` and "
        f"D10.\n{NOTES}\n{table}"
    )
    print(table)
    print("wrote data/leakage/results.csv and data/LEAKAGE.md")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
