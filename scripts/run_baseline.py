"""Train and score the XGBoost baselines; write the results table.

Usage::

    python scripts/run_baseline.py                      # reads data/binaries/*.parquet
    python scripts/run_baseline.py s3://<bucket>/features/binaries

Reads the per-binary feature store (scripts/dedup_scan.py) and the split
assignment (scripts/make_splits.py), runs the in-architecture,
leave-one-architecture-out and architecture-sanity experiments from
``iotmal.baseline`` with ``configs/baseline.yaml``, then runs the same
three again on each first-N store (scripts/first_window_scan.py) and
once more on one of them without the network calls, as set in
``configs/first_window.yaml``, when the stores sit beside the
whole-trace store, and writes:

* ``data/baseline/results.csv``: one row per experiment, held-out
  architecture and view, with the metrics; committed.
* ``data/BASELINE.md``: the same as tables, with the reading notes and,
  when the first-window runs ran, MCC and AUROC side by side for the
  whole trace and every first-window run.

Fifty-four boosters on about 11,000 rows of 133 features: about a
minute on the notebook, no job needed.
"""

import sys
from datetime import date

import polars as pl

from iotmal import baseline, dedup, first_window
from iotmal.paths import DATA_DIR, ensure_dir

NOTES = """
Reading the tables. Every binary the split labels `test` is unseen in
every experiment. In-architecture scores one architecture's `test`
column after training on its `train` column; leave-one-architecture-out
scores every live binary of the held-out architecture after training on
the `train` columns of the other three, so its test set is the whole
architecture, not the `test` column. Accuracy, macro-F1 and MCC are taken at
the threshold that maximises MCC on the fold's validation binaries
(D9), printed in the Threshold column; MCC at 0.5 stands beside them.
The `group` view collapses binaries with one exact syscall vector into
one example with their mean score.
Chance is the share of the larger class in the test set. The
architecture-sanity row predicts the architecture itself; accuracy far
above its chance means the features still carry a sandbox signature.
The `first-N` tables repeat all three on each binary's first N system
calls only (its whole trace when it made fewer), with the same split and
the same binaries; `first-N-no-network` drops the socket-family calls
from the features of the N-call run.
"""


def main(source: str | None) -> None:
    """Run every experiment and write the report."""
    cfg = baseline.BaselineConfig.load()
    vocabulary = pl.read_csv(DATA_DIR / "syscall_vocabulary.csv")["canonical"].to_list()
    binaries = dedup.load_feature_store(source)
    assignment = baseline.load_assignment()
    results = baseline.run(binaries, assignment, vocabulary, cfg)
    comparison = ""
    window_cfg = first_window.FirstWindowConfig.load()
    try:
        stores = {
            n: dedup.load_feature_store(source, stem=first_window.stem(n))
            for n in window_cfg.prefixes
        }
    except FileNotFoundError:
        print("no first-window stores found; run scripts/first_window_scan.py for those runs")
    else:
        labels = []
        for n, store in stores.items():
            labels.append(f"{baseline.FIRST_WINDOW}-{n}")
            results = pl.concat(
                [results, baseline.first_window(store, assignment, vocabulary, cfg, calls=n)]
            )
        n = window_cfg.ablation_prefix
        label = f"{baseline.FIRST_WINDOW}-{n}-no-network"
        ablation = baseline.first_window(
            stores[n], assignment, vocabulary, cfg, n, window_cfg.network_calls, label
        )
        results = pl.concat([results, ablation])
        labels.append(label)
        comparison = "".join(
            f"## whole trace against first-window runs, {name}\n\n"
            + baseline.render_comparison(baseline.compare(results, labels, metric))
            + "\n"
            for metric, name in (
                ("mcc", "MCC at the validation threshold"),
                ("mcc_half", "MCC at 0.5"),
                ("auroc", "AUROC"),
            )
        )

    out = ensure_dir(DATA_DIR / "baseline")
    results.write_csv(out / "results.csv")
    table = baseline.render_markdown(results)
    (DATA_DIR / "BASELINE.md").write_text(
        f"# Baselines\n\nRun on {date.today().isoformat()} with seed {cfg.seed}, features "
        f"`{cfg.features}`, XGBoost {cfg.xgboost}, early stopping after "
        f"{cfg.early_stopping_rounds} rounds.\n{NOTES}\n{comparison}\n{table}"
    )
    print(comparison)
    print(table)
    print("wrote data/baseline/results.csv and data/BASELINE.md")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
