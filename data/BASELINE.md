# Baselines

Run on 2026-10-05 with seed 20260922, features `profile`, XGBoost {'n_estimators': 400, 'max_depth': 6, 'learning_rate': 0.1, 'subsample': 0.8, 'colsample_bytree': 0.8, 'min_child_weight': 1, 'tree_method': 'hist'}, early stopping after 30 rounds.

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

## in-architecture

| Held out | View | Train | Test | Benign | Malware | Chance | Accuracy | Macro-F1 | MCC | AUROC | Rounds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arm | binary | 1261 | 366 | 30 | 336 | 0.918 | 0.995 | 0.982 | 0.964 | 1.000 | 120 |
| arm | group | 1261 | 303 | 30 | 273 | 0.901 | 0.993 | 0.982 | 0.963 | 1.000 | 120 |
| mips | binary | 2931 | 838 | 522 | 316 | 0.623 | 0.998 | 0.997 | 0.995 | 1.000 | 78 |
| mips | group | 2931 | 823 | 522 | 301 | 0.634 | 0.998 | 0.997 | 0.995 | 1.000 | 78 |
| mipsel | binary | 2804 | 803 | 501 | 302 | 0.624 | 1.000 | 1.000 | 1.000 | 1.000 | 199 |
| mipsel | group | 2804 | 796 | 501 | 295 | 0.629 | 1.000 | 1.000 | 1.000 | 1.000 | 199 |
| x86 | binary | 2941 | 831 | 513 | 318 | 0.617 | 0.999 | 0.999 | 0.997 | 1.000 | 155 |
| x86 | group | 2941 | 798 | 506 | 292 | 0.634 | 0.999 | 0.999 | 0.997 | 1.000 | 155 |

## leave-one-architecture-out

| Held out | View | Train | Test | Benign | Malware | Chance | Accuracy | Macro-F1 | MCC | AUROC | Rounds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arm | binary | 8676 | 1809 | 150 | 1659 | 0.917 | 0.993 | 0.977 | 0.956 | 1.000 | 253 |
| arm | group | 8676 | 1515 | 150 | 1365 | 0.901 | 0.993 | 0.982 | 0.965 | 1.000 | 253 |
| mips | binary | 7006 | 4190 | 2609 | 1581 | 0.623 | 0.999 | 0.999 | 0.997 | 1.000 | 303 |
| mips | group | 7006 | 4137 | 2609 | 1528 | 0.631 | 0.999 | 0.999 | 0.998 | 1.000 | 303 |
| mipsel | binary | 7133 | 4012 | 2505 | 1507 | 0.624 | 1.000 | 1.000 | 0.999 | 1.000 | 216 |
| mipsel | group | 7133 | 3972 | 2505 | 1467 | 0.631 | 1.000 | 1.000 | 0.999 | 1.000 | 216 |
| x86 | binary | 6996 | 4190 | 2562 | 1628 | 0.611 | 1.000 | 1.000 | 1.000 | 1.000 | 260 |
| x86 | group | 6996 | 3878 | 2552 | 1326 | 0.658 | 1.000 | 1.000 | 1.000 | 1.000 | 260 |

## architecture-sanity

| Held out | View | Train | Test | Benign | Malware | Chance | Accuracy | Macro-F1 | MCC | AUROC | Rounds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all | binary | 9937 | 2838 | 1566 | 1272 | 0.295 | 0.632 | 0.680 | 0.497 |  | 126 |
