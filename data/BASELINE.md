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
| arm | binary | 1248 | 380 | 30 | 350 | 0.921 | 0.997 | 0.991 | 0.982 | 1.000 | 106 |
| arm | group | 1248 | 301 | 30 | 271 | 0.900 | 0.997 | 0.991 | 0.981 | 1.000 | 106 |
| mips | binary | 2925 | 836 | 520 | 316 | 0.622 | 0.999 | 0.999 | 0.997 | 1.000 | 272 |
| mips | group | 2925 | 833 | 520 | 313 | 0.624 | 0.999 | 0.999 | 0.997 | 1.000 | 272 |
| mipsel | binary | 2798 | 803 | 499 | 304 | 0.621 | 0.999 | 0.999 | 0.997 | 1.000 | 148 |
| mipsel | group | 2798 | 796 | 499 | 297 | 0.627 | 0.999 | 0.999 | 0.997 | 1.000 | 148 |
| x86 | binary | 2924 | 837 | 511 | 326 | 0.611 | 1.000 | 1.000 | 1.000 | 1.000 | 170 |
| x86 | group | 2924 | 815 | 510 | 305 | 0.626 | 1.000 | 1.000 | 1.000 | 1.000 | 170 |

## leave-one-architecture-out

| Held out | View | Train | Test | Benign | Malware | Chance | Accuracy | Macro-F1 | MCC | AUROC | Rounds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arm | binary | 8647 | 1809 | 150 | 1659 | 0.917 | 0.993 | 0.977 | 0.956 | 1.000 | 340 |
| arm | group | 8647 | 1515 | 150 | 1365 | 0.901 | 0.993 | 0.982 | 0.965 | 1.000 | 340 |
| mips | binary | 6970 | 4182 | 2601 | 1581 | 0.622 | 1.000 | 1.000 | 1.000 | 1.000 | 277 |
| mips | group | 6970 | 4129 | 2601 | 1528 | 0.630 | 1.000 | 1.000 | 1.000 | 1.000 | 277 |
| mipsel | binary | 7097 | 4003 | 2496 | 1507 | 0.624 | 1.000 | 1.000 | 0.999 | 1.000 | 246 |
| mipsel | group | 7097 | 3963 | 2496 | 1467 | 0.630 | 1.000 | 1.000 | 0.999 | 1.000 | 246 |
| x86 | binary | 6971 | 4182 | 2554 | 1628 | 0.611 | 1.000 | 1.000 | 1.000 | 1.000 | 264 |
| x86 | group | 6971 | 3870 | 2544 | 1326 | 0.657 | 1.000 | 1.000 | 1.000 | 1.000 | 264 |

## architecture-sanity

| Held out | View | Train | Test | Benign | Malware | Chance | Accuracy | Macro-F1 | MCC | AUROC | Rounds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all | binary | 9895 | 2856 | 1560 | 1296 | 0.293 | 0.621 | 0.669 | 0.482 |  | 135 |
