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
The `first-N` tables repeat all three on each binary's first N system
calls only (its whole trace when it made fewer), with the same split and
the same binaries; `first-N-no-network` drops the socket-family calls
from the features of the N-call run.

## whole trace against first-window runs, MCC

| Experiment | Held out | View | Test | whole | first-5 | first-10 | first-15 | first-20 | first-20-no-network |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| in-architecture | arm | binary | 424 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| in-architecture | arm | group | 226 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| in-architecture | mips | binary | 836 | 0.995 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| in-architecture | mips | group | 830 | 0.995 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| in-architecture | mipsel | binary | 802 | 0.997 | 0.995 | 1.000 | 1.000 | 0.997 | 0.997 |
| in-architecture | mipsel | group | 791 | 0.997 | 0.995 | 1.000 | 1.000 | 0.997 | 0.997 |
| in-architecture | x86 | binary | 813 | 0.997 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| in-architecture | x86 | group | 766 | 0.997 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| leave-one-architecture-out | arm | binary | 1809 | 0.940 | -0.067 | 0.000 | 0.000 | 0.000 | 0.000 |
| leave-one-architecture-out | arm | group | 1515 | 0.948 | -0.081 | 0.000 | 0.000 | 0.000 | 0.000 |
| leave-one-architecture-out | mips | binary | 4182 | 0.999 | 0.998 | 1.000 | 1.000 | 1.000 | 1.000 |
| leave-one-architecture-out | mips | group | 4129 | 0.999 | 0.998 | 1.000 | 1.000 | 1.000 | 1.000 |
| leave-one-architecture-out | mipsel | binary | 4003 | 0.999 | 0.999 | 1.000 | 1.000 | 1.000 | 1.000 |
| leave-one-architecture-out | mipsel | group | 3963 | 0.999 | 0.999 | 1.000 | 1.000 | 1.000 | 1.000 |
| leave-one-architecture-out | x86 | binary | 4182 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| leave-one-architecture-out | x86 | group | 3870 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| architecture-sanity | all | binary | 2875 | 0.504 | 0.193 | 0.340 | 0.567 | 0.549 | 0.555 |

## whole trace against first-window runs, AUROC

| Experiment | Held out | View | Test | whole | first-5 | first-10 | first-15 | first-20 | first-20-no-network |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| in-architecture | arm | binary | 424 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| in-architecture | arm | group | 226 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| in-architecture | mips | binary | 836 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| in-architecture | mips | group | 830 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| in-architecture | mipsel | binary | 802 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| in-architecture | mipsel | group | 791 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| in-architecture | x86 | binary | 813 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| in-architecture | x86 | group | 766 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| leave-one-architecture-out | arm | binary | 1809 | 0.999 | 0.949 | 1.000 | 1.000 | 1.000 | 1.000 |
| leave-one-architecture-out | arm | group | 1515 | 0.999 | 0.938 | 1.000 | 1.000 | 1.000 | 1.000 |
| leave-one-architecture-out | mips | binary | 4182 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| leave-one-architecture-out | mips | group | 4129 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| leave-one-architecture-out | mipsel | binary | 4003 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| leave-one-architecture-out | mipsel | group | 3963 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| leave-one-architecture-out | x86 | binary | 4182 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| leave-one-architecture-out | x86 | group | 3870 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| architecture-sanity | all | binary | 2875 |  |  |  |  |  |  |


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

## first-5 in-architecture

| Held out | View | Train | Test | Benign | Malware | Chance | Accuracy | Macro-F1 | MCC | AUROC | Rounds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arm | binary | 1209 | 424 | 30 | 394 | 0.929 | 1.000 | 1.000 | 1.000 | 1.000 | 122 |
| arm | group | 1209 | 226 | 30 | 196 | 0.867 | 1.000 | 1.000 | 1.000 | 1.000 | 122 |
| mips | binary | 2925 | 836 | 520 | 316 | 0.622 | 1.000 | 1.000 | 1.000 | 1.000 | 93 |
| mips | group | 2925 | 830 | 520 | 310 | 0.627 | 1.000 | 1.000 | 1.000 | 1.000 | 93 |
| mipsel | binary | 2796 | 802 | 499 | 303 | 0.622 | 0.998 | 0.997 | 0.995 | 1.000 | 116 |
| mipsel | group | 2796 | 791 | 499 | 292 | 0.631 | 0.997 | 0.997 | 0.995 | 1.000 | 116 |
| x86 | binary | 2841 | 813 | 511 | 302 | 0.629 | 1.000 | 1.000 | 1.000 | 1.000 | 109 |
| x86 | group | 2841 | 766 | 511 | 255 | 0.667 | 1.000 | 1.000 | 1.000 | 1.000 | 109 |

## first-5 leave-one-architecture-out

| Held out | View | Train | Test | Benign | Malware | Chance | Accuracy | Macro-F1 | MCC | AUROC | Rounds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arm | binary | 8562 | 1809 | 150 | 1659 | 0.917 | 0.870 | 0.465 | -0.067 | 0.949 | 97 |
| arm | group | 8562 | 1515 | 150 | 1365 | 0.901 | 0.845 | 0.458 | -0.081 | 0.938 | 97 |
| mips | binary | 6846 | 4182 | 2601 | 1581 | 0.622 | 0.999 | 0.999 | 0.998 | 1.000 | 162 |
| mips | group | 6846 | 4129 | 2601 | 1528 | 0.630 | 0.999 | 0.999 | 0.998 | 1.000 | 162 |
| mipsel | binary | 6975 | 4003 | 2496 | 1507 | 0.624 | 1.000 | 1.000 | 0.999 | 1.000 | 161 |
| mipsel | group | 6975 | 3963 | 2496 | 1467 | 0.630 | 1.000 | 1.000 | 0.999 | 1.000 | 161 |
| x86 | binary | 6930 | 4182 | 2554 | 1628 | 0.611 | 1.000 | 1.000 | 1.000 | 1.000 | 162 |
| x86 | group | 6930 | 3870 | 2544 | 1326 | 0.657 | 1.000 | 1.000 | 1.000 | 1.000 | 162 |

## first-5 architecture-sanity

| Held out | View | Train | Test | Benign | Malware | Chance | Accuracy | Macro-F1 | MCC | AUROC | Rounds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all | binary | 9771 | 2875 | 1560 | 1315 | 0.291 | 0.389 | 0.364 | 0.193 |  | 197 |

## first-10 in-architecture

| Held out | View | Train | Test | Benign | Malware | Chance | Accuracy | Macro-F1 | MCC | AUROC | Rounds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arm | binary | 1209 | 424 | 30 | 394 | 0.929 | 1.000 | 1.000 | 1.000 | 1.000 | 114 |
| arm | group | 1209 | 226 | 30 | 196 | 0.867 | 1.000 | 1.000 | 1.000 | 1.000 | 114 |
| mips | binary | 2925 | 836 | 520 | 316 | 0.622 | 1.000 | 1.000 | 1.000 | 1.000 | 103 |
| mips | group | 2925 | 830 | 520 | 310 | 0.627 | 1.000 | 1.000 | 1.000 | 1.000 | 103 |
| mipsel | binary | 2796 | 802 | 499 | 303 | 0.622 | 1.000 | 1.000 | 1.000 | 1.000 | 75 |
| mipsel | group | 2796 | 791 | 499 | 292 | 0.631 | 1.000 | 1.000 | 1.000 | 1.000 | 75 |
| x86 | binary | 2841 | 813 | 511 | 302 | 0.629 | 1.000 | 1.000 | 1.000 | 1.000 | 73 |
| x86 | group | 2841 | 766 | 511 | 255 | 0.667 | 1.000 | 1.000 | 1.000 | 1.000 | 73 |

## first-10 leave-one-architecture-out

| Held out | View | Train | Test | Benign | Malware | Chance | Accuracy | Macro-F1 | MCC | AUROC | Rounds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arm | binary | 8562 | 1809 | 150 | 1659 | 0.917 | 0.917 | 0.478 | 0.000 | 1.000 | 84 |
| arm | group | 8562 | 1515 | 150 | 1365 | 0.901 | 0.901 | 0.474 | 0.000 | 1.000 | 84 |
| mips | binary | 6846 | 4182 | 2601 | 1581 | 0.622 | 1.000 | 1.000 | 1.000 | 1.000 | 126 |
| mips | group | 6846 | 4129 | 2601 | 1528 | 0.630 | 1.000 | 1.000 | 1.000 | 1.000 | 126 |
| mipsel | binary | 6975 | 4003 | 2496 | 1507 | 0.624 | 1.000 | 1.000 | 1.000 | 1.000 | 146 |
| mipsel | group | 6975 | 3963 | 2496 | 1467 | 0.630 | 1.000 | 1.000 | 1.000 | 1.000 | 146 |
| x86 | binary | 6930 | 4182 | 2554 | 1628 | 0.611 | 1.000 | 1.000 | 1.000 | 1.000 | 146 |
| x86 | group | 6930 | 3870 | 2544 | 1326 | 0.657 | 1.000 | 1.000 | 1.000 | 1.000 | 146 |

## first-10 architecture-sanity

| Held out | View | Train | Test | Benign | Malware | Chance | Accuracy | Macro-F1 | MCC | AUROC | Rounds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all | binary | 9771 | 2875 | 1560 | 1315 | 0.291 | 0.480 | 0.484 | 0.340 |  | 148 |

## first-15 in-architecture

| Held out | View | Train | Test | Benign | Malware | Chance | Accuracy | Macro-F1 | MCC | AUROC | Rounds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arm | binary | 1209 | 424 | 30 | 394 | 0.929 | 1.000 | 1.000 | 1.000 | 1.000 | 122 |
| arm | group | 1209 | 226 | 30 | 196 | 0.867 | 1.000 | 1.000 | 1.000 | 1.000 | 122 |
| mips | binary | 2925 | 836 | 520 | 316 | 0.622 | 1.000 | 1.000 | 1.000 | 1.000 | 101 |
| mips | group | 2925 | 830 | 520 | 310 | 0.627 | 1.000 | 1.000 | 1.000 | 1.000 | 101 |
| mipsel | binary | 2796 | 802 | 499 | 303 | 0.622 | 1.000 | 1.000 | 1.000 | 1.000 | 74 |
| mipsel | group | 2796 | 791 | 499 | 292 | 0.631 | 1.000 | 1.000 | 1.000 | 1.000 | 74 |
| x86 | binary | 2841 | 813 | 511 | 302 | 0.629 | 1.000 | 1.000 | 1.000 | 1.000 | 73 |
| x86 | group | 2841 | 766 | 511 | 255 | 0.667 | 1.000 | 1.000 | 1.000 | 1.000 | 73 |

## first-15 leave-one-architecture-out

| Held out | View | Train | Test | Benign | Malware | Chance | Accuracy | Macro-F1 | MCC | AUROC | Rounds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arm | binary | 8562 | 1809 | 150 | 1659 | 0.917 | 0.917 | 0.478 | 0.000 | 1.000 | 87 |
| arm | group | 8562 | 1515 | 150 | 1365 | 0.901 | 0.901 | 0.474 | 0.000 | 1.000 | 87 |
| mips | binary | 6846 | 4182 | 2601 | 1581 | 0.622 | 1.000 | 1.000 | 1.000 | 1.000 | 221 |
| mips | group | 6846 | 4129 | 2601 | 1528 | 0.630 | 1.000 | 1.000 | 1.000 | 1.000 | 221 |
| mipsel | binary | 6975 | 4003 | 2496 | 1507 | 0.624 | 1.000 | 1.000 | 1.000 | 1.000 | 221 |
| mipsel | group | 6975 | 3963 | 2496 | 1467 | 0.630 | 1.000 | 1.000 | 1.000 | 1.000 | 221 |
| x86 | binary | 6930 | 4182 | 2554 | 1628 | 0.611 | 1.000 | 1.000 | 1.000 | 1.000 | 164 |
| x86 | group | 6930 | 3870 | 2544 | 1326 | 0.657 | 1.000 | 1.000 | 1.000 | 1.000 | 164 |

## first-15 architecture-sanity

| Held out | View | Train | Test | Benign | Malware | Chance | Accuracy | Macro-F1 | MCC | AUROC | Rounds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all | binary | 9771 | 2875 | 1560 | 1315 | 0.291 | 0.654 | 0.629 | 0.567 |  | 158 |

## first-20 in-architecture

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

## first-20 leave-one-architecture-out

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

## first-20 architecture-sanity

| Held out | View | Train | Test | Benign | Malware | Chance | Accuracy | Macro-F1 | MCC | AUROC | Rounds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all | binary | 9771 | 2875 | 1560 | 1315 | 0.291 | 0.662 | 0.681 | 0.549 |  | 144 |

## first-20-no-network in-architecture

| Held out | View | Train | Test | Benign | Malware | Chance | Accuracy | Macro-F1 | MCC | AUROC | Rounds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arm | binary | 1209 | 424 | 30 | 394 | 0.929 | 1.000 | 1.000 | 1.000 | 1.000 | 100 |
| arm | group | 1209 | 226 | 30 | 196 | 0.867 | 1.000 | 1.000 | 1.000 | 1.000 | 100 |
| mips | binary | 2925 | 836 | 520 | 316 | 0.622 | 1.000 | 1.000 | 1.000 | 1.000 | 82 |
| mips | group | 2925 | 830 | 520 | 310 | 0.627 | 1.000 | 1.000 | 1.000 | 1.000 | 82 |
| mipsel | binary | 2796 | 802 | 499 | 303 | 0.622 | 0.999 | 0.999 | 0.997 | 1.000 | 78 |
| mipsel | group | 2796 | 791 | 499 | 292 | 0.631 | 0.999 | 0.999 | 0.997 | 1.000 | 78 |
| x86 | binary | 2841 | 813 | 511 | 302 | 0.629 | 1.000 | 1.000 | 1.000 | 1.000 | 73 |
| x86 | group | 2841 | 766 | 511 | 255 | 0.667 | 1.000 | 1.000 | 1.000 | 1.000 | 73 |

## first-20-no-network leave-one-architecture-out

| Held out | View | Train | Test | Benign | Malware | Chance | Accuracy | Macro-F1 | MCC | AUROC | Rounds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arm | binary | 8562 | 1809 | 150 | 1659 | 0.917 | 0.917 | 0.478 | 0.000 | 1.000 | 100 |
| arm | group | 8562 | 1515 | 150 | 1365 | 0.901 | 0.901 | 0.474 | 0.000 | 1.000 | 100 |
| mips | binary | 6846 | 4182 | 2601 | 1581 | 0.622 | 1.000 | 1.000 | 1.000 | 1.000 | 222 |
| mips | group | 6846 | 4129 | 2601 | 1528 | 0.630 | 1.000 | 1.000 | 1.000 | 1.000 | 222 |
| mipsel | binary | 6975 | 4003 | 2496 | 1507 | 0.624 | 1.000 | 1.000 | 1.000 | 1.000 | 146 |
| mipsel | group | 6975 | 3963 | 2496 | 1467 | 0.630 | 1.000 | 1.000 | 1.000 | 1.000 | 146 |
| x86 | binary | 6930 | 4182 | 2554 | 1628 | 0.611 | 1.000 | 1.000 | 1.000 | 1.000 | 365 |
| x86 | group | 6930 | 3870 | 2544 | 1326 | 0.657 | 1.000 | 1.000 | 1.000 | 1.000 | 365 |

## first-20-no-network architecture-sanity

| Held out | View | Train | Test | Benign | Malware | Chance | Accuracy | Macro-F1 | MCC | AUROC | Rounds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all | binary | 9771 | 2875 | 1560 | 1315 | 0.291 | 0.661 | 0.671 | 0.555 |  | 112 |
