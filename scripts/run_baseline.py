"""Train and score the XGBoost baselines; write the results table.

Usage::

    python scripts/run_baseline.py                      # reads data/binaries/*.parquet
    python scripts/run_baseline.py s3://<bucket>/features/binaries

Reads the per-binary feature store (scripts/dedup_scan.py) and the split
assignment (scripts/make_splits.py), runs the in-architecture,
leave-one-architecture-out and architecture-sanity experiments from
``iotmal.baseline`` with ``configs/baseline.yaml``, and writes:

* ``data/baseline/results.csv``: one row per experiment, held-out
  architecture and view, with the metrics; committed.
* ``data/BASELINE.md``: the same as tables, with the reading notes.

Nine boosters on about 11,000 rows of 133 features: a minute or two on
the notebook, no job needed.
"""

import sys
from datetime import date

import polars as pl

from iotmal import baseline, dedup
from iotmal.paths import DATA_DIR, ensure_dir

NOTES = """
Reading the tables. Every binary the split labels `test` is unseen in
every experiment. In-architecture scores one architecture's `test`
column after training on its `train` column; leave-one-architecture-out
scores every live binary of the held-out architecture after training on
the `train` columns of the other three, so its test set is the whole
architecture, not the `test` column. The `group` view collapses binaries
with one exact syscall vector into one example with their mean score.
Chance is the share of the larger class in the test set. The
architecture-sanity row predicts the architecture itself; accuracy far
above its chance means the features still carry a sandbox signature.
"""


def main(source: str | None) -> None:
    """Run every experiment and write the report."""
    cfg = baseline.BaselineConfig.load()
    vocabulary = pl.read_csv(DATA_DIR / "syscall_vocabulary.csv")["canonical"].to_list()
    binaries = dedup.load_feature_store(source)
    assignment = baseline.load_assignment()
    results = baseline.run(binaries, assignment, vocabulary, cfg)

    out = ensure_dir(DATA_DIR / "baseline")
    results.write_csv(out / "results.csv")
    table = baseline.render_markdown(results)
    (DATA_DIR / "BASELINE.md").write_text(
        f"# Baselines\n\nRun on {date.today().isoformat()} with seed {cfg.seed}, features "
        f"`{cfg.features}`, XGBoost {cfg.xgboost}, early stopping after "
        f"{cfg.early_stopping_rounds} rounds.\n{NOTES}\n{table}"
    )
    print(table)
    print("wrote data/baseline/results.csv and data/BASELINE.md")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
