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
The `first-window` tables repeat all three on each binary's first
twenty system calls only (its whole trace when it made fewer), with the
same split and the same binaries.

## whole trace against first window

| Experiment | Held out | View | Test | Accuracy whole | Accuracy first | MCC whole | MCC first | AUROC whole | AUROC first |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| in-architecture | arm | binary | 424 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| in-architecture | arm | group | 226 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| in-architecture | mips | binary | 836 | 0.998 | 1.000 | 0.995 | 1.000 | 1.000 | 1.000 |
| in-architecture | mips | group | 830 | 0.998 | 1.000 | 0.995 | 1.000 | 1.000 | 1.000 |
| in-architecture | mipsel | binary | 802 | 0.999 | 0.999 | 0.997 | 0.997 | 1.000 | 1.000 |
| in-architecture | mipsel | group | 791 | 0.999 | 0.999 | 0.997 | 0.997 | 1.000 | 1.000 |
| in-architecture | x86 | binary | 813 | 0.999 | 1.000 | 0.997 | 1.000 | 1.000 | 1.000 |
| in-architecture | x86 | group | 766 | 0.999 | 1.000 | 0.997 | 1.000 | 1.000 | 1.000 |
| leave-one-architecture-out | arm | binary | 1809 | 0.990 | 0.917 | 0.940 | 0.000 | 0.999 | 1.000 |
| leave-one-architecture-out | arm | group | 1515 | 0.990 | 0.901 | 0.948 | 0.000 | 0.999 | 1.000 |
| leave-one-architecture-out | mips | binary | 4182 | 1.000 | 1.000 | 0.999 | 1.000 | 1.000 | 1.000 |
| leave-one-architecture-out | mips | group | 4129 | 1.000 | 1.000 | 0.999 | 1.000 | 1.000 | 1.000 |
| leave-one-architecture-out | mipsel | binary | 4003 | 1.000 | 1.000 | 0.999 | 1.000 | 1.000 | 1.000 |
| leave-one-architecture-out | mipsel | group | 3963 | 1.000 | 1.000 | 0.999 | 1.000 | 1.000 | 1.000 |
| leave-one-architecture-out | x86 | binary | 4182 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| leave-one-architecture-out | x86 | group | 3870 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| architecture-sanity | all | binary | 2875 | 0.635 | 0.662 | 0.504 | 0.549 |  |  |

## in-architecture

| Held out | View | Train | Test | Benign | Malware | Chance | Accuracy | Macro-F1 | MCC | AUROC | Rounds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arm | binary | 1209 | 424 | 30 | 394 | 0.929 | 1.000 | 1.000 | 1.000 | 1.000 | 93 |
| arm | group | 1209 | 226 | 30 | 196 | 0.867 | 1.000 | 1.000 | 1.000 | 1.000 | 93 |
| mips | binary | 2925 | 836 | 520 | 316 | 0.622 | 0.998 | 0.997 | 0.995 | 1.000 | 192 |
| mips | group | 2925 | 830 | 520 | 310 | 0.627 | 0.998 | 0.997 | 0.995 | 1.000 | 192 |
| mipsel | binary | 2796 | 802 | 499 | 303 | 0.622 | 0.999 | 0.999 | 0.997 | 1.000 | 128 |
| mipsel | group | 2796 | 791 | 499 | 292 | 0.631 | 0.999 | 0.999 | 0.997 | 1.000 | 128 |
| x86 | binary | 2841 | 813 | 511 | 302 | 0.629 | 0.999 | 0.999 | 0.997 | 1.000 | 158 |
| x86 | group | 2841 | 766 | 511 | 255 | 0.667 | 0.999 | 0.999 | 0.997 | 1.000 | 158 |

## leave-one-architecture-out

| Held out | View | Train | Test | Benign | Malware | Chance | Accuracy | Macro-F1 | MCC | AUROC | Rounds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arm | binary | 8562 | 1809 | 150 | 1659 | 0.917 | 0.990 | 0.969 | 0.940 | 0.999 | 131 |
| arm | group | 8562 | 1515 | 150 | 1365 | 0.901 | 0.990 | 0.973 | 0.948 | 0.999 | 131 |
| mips | binary | 6846 | 4182 | 2601 | 1581 | 0.622 | 1.000 | 1.000 | 0.999 | 1.000 | 272 |
| mips | group | 6846 | 4129 | 2601 | 1528 | 0.630 | 1.000 | 1.000 | 0.999 | 1.000 | 272 |
| mipsel | binary | 6975 | 4003 | 2496 | 1507 | 0.624 | 1.000 | 1.000 | 0.999 | 1.000 | 259 |
| mipsel | group | 6975 | 3963 | 2496 | 1467 | 0.630 | 1.000 | 1.000 | 0.999 | 1.000 | 259 |
| x86 | binary | 6930 | 4182 | 2554 | 1628 | 0.611 | 1.000 | 1.000 | 1.000 | 1.000 | 194 |
| x86 | group | 6930 | 3870 | 2544 | 1326 | 0.657 | 1.000 | 1.000 | 1.000 | 1.000 | 194 |

## architecture-sanity

| Held out | View | Train | Test | Benign | Malware | Chance | Accuracy | Macro-F1 | MCC | AUROC | Rounds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all | binary | 9771 | 2875 | 1560 | 1315 | 0.291 | 0.635 | 0.677 | 0.504 |  | 126 |

## first-window in-architecture

| Held out | View | Train | Test | Benign | Malware | Chance | Accuracy | Macro-F1 | MCC | AUROC | Rounds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arm | binary | 1209 | 424 | 30 | 394 | 0.929 | 1.000 | 1.000 | 1.000 | 1.000 | 221 |
| arm | group | 1209 | 226 | 30 | 196 | 0.867 | 1.000 | 1.000 | 1.000 | 1.000 | 221 |
| mips | binary | 2925 | 836 | 520 | 316 | 0.622 | 1.000 | 1.000 | 1.000 | 1.000 | 82 |
| mips | group | 2925 | 830 | 520 | 310 | 0.627 | 1.000 | 1.000 | 1.000 | 1.000 | 82 |
| mipsel | binary | 2796 | 802 | 499 | 303 | 0.622 | 0.999 | 0.999 | 0.997 | 1.000 | 75 |
| mipsel | group | 2796 | 791 | 499 | 292 | 0.631 | 0.999 | 0.999 | 0.997 | 1.000 | 75 |
| x86 | binary | 2841 | 813 | 511 | 302 | 0.629 | 1.000 | 1.000 | 1.000 | 1.000 | 73 |
| x86 | group | 2841 | 766 | 511 | 255 | 0.667 | 1.000 | 1.000 | 1.000 | 1.000 | 73 |

## first-window leave-one-architecture-out

| Held out | View | Train | Test | Benign | Malware | Chance | Accuracy | Macro-F1 | MCC | AUROC | Rounds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arm | binary | 8562 | 1809 | 150 | 1659 | 0.917 | 0.917 | 0.478 | 0.000 | 1.000 | 95 |
| arm | group | 8562 | 1515 | 150 | 1365 | 0.901 | 0.901 | 0.474 | 0.000 | 1.000 | 95 |
| mips | binary | 6846 | 4182 | 2601 | 1581 | 0.622 | 1.000 | 1.000 | 1.000 | 1.000 | 222 |
| mips | group | 6846 | 4129 | 2601 | 1528 | 0.630 | 1.000 | 1.000 | 1.000 | 1.000 | 222 |
| mipsel | binary | 6975 | 4003 | 2496 | 1507 | 0.624 | 1.000 | 1.000 | 1.000 | 1.000 | 176 |
| mipsel | group | 6975 | 3963 | 2496 | 1467 | 0.630 | 1.000 | 1.000 | 1.000 | 1.000 | 176 |
| x86 | binary | 6930 | 4182 | 2554 | 1628 | 0.611 | 1.000 | 1.000 | 1.000 | 1.000 | 174 |
| x86 | group | 6930 | 3870 | 2544 | 1326 | 0.657 | 1.000 | 1.000 | 1.000 | 1.000 | 174 |

## first-window architecture-sanity

| Held out | View | Train | Test | Benign | Malware | Chance | Accuracy | Macro-F1 | MCC | AUROC | Rounds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all | binary | 9771 | 2875 | 1560 | 1315 | 0.291 | 0.662 | 0.681 | 0.549 |  | 144 |
