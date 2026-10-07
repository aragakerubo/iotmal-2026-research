# Baselines

Run on 2026-10-07 with seed 20260922, features `profile`, XGBoost {'n_estimators': 400, 'max_depth': 6, 'learning_rate': 0.1, 'subsample': 0.8, 'colsample_bytree': 0.8, 'min_child_weight': 1, 'tree_method': 'hist'}, early stopping after 30 rounds.

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

## whole trace against first-window runs, MCC at the validation threshold

| Experiment | Held out | View | Test | whole | first-5 | first-10 | first-15 | first-20 | first-20-no-network |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| in-architecture | arm | binary | 363 | 0.934 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| in-architecture | arm | group | 320 | 0.933 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| in-architecture | mips | binary | 836 | 0.997 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| in-architecture | mips | group | 830 | 0.997 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| in-architecture | mipsel | binary | 801 | 0.997 | 1.000 | 1.000 | 1.000 | 0.997 | 0.997 |
| in-architecture | mipsel | group | 790 | 0.997 | 1.000 | 1.000 | 1.000 | 0.997 | 0.997 |
| in-architecture | x86 | binary | 849 | 0.998 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| in-architecture | x86 | group | 799 | 0.997 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| leave-one-architecture-out | arm | binary | 1809 | 0.969 | -0.067 | 0.000 | 0.000 | 0.000 | 0.000 |
| leave-one-architecture-out | arm | group | 1515 | 0.975 | -0.081 | 0.000 | 0.000 | 0.000 | 0.000 |
| leave-one-architecture-out | mips | binary | 4182 | 0.999 | 0.998 | 1.000 | 1.000 | 1.000 | 1.000 |
| leave-one-architecture-out | mips | group | 4129 | 0.999 | 0.998 | 1.000 | 1.000 | 1.000 | 1.000 |
| leave-one-architecture-out | mipsel | binary | 4003 | 0.999 | 0.999 | 1.000 | 1.000 | 1.000 | 1.000 |
| leave-one-architecture-out | mipsel | group | 3963 | 0.999 | 0.999 | 1.000 | 1.000 | 1.000 | 1.000 |
| leave-one-architecture-out | x86 | binary | 4182 | 0.998 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| leave-one-architecture-out | x86 | group | 3870 | 0.998 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| architecture-sanity | all | binary | 2849 | 0.512 | 0.253 | 0.331 | 0.545 | 0.534 | 0.535 |

## whole trace against first-window runs, MCC at 0.5

| Experiment | Held out | View | Test | whole | first-5 | first-10 | first-15 | first-20 | first-20-no-network |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| in-architecture | arm | binary | 363 | 0.905 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| in-architecture | arm | group | 320 | 0.903 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| in-architecture | mips | binary | 836 | 0.995 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| in-architecture | mips | group | 830 | 0.995 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| in-architecture | mipsel | binary | 801 | 0.997 | 1.000 | 1.000 | 1.000 | 0.997 | 0.997 |
| in-architecture | mipsel | group | 790 | 0.997 | 1.000 | 1.000 | 1.000 | 0.997 | 0.997 |
| in-architecture | x86 | binary | 849 | 0.998 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| in-architecture | x86 | group | 799 | 0.997 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| leave-one-architecture-out | arm | binary | 1809 | 0.959 | -0.067 | 0.000 | 0.000 | 0.000 | 0.000 |
| leave-one-architecture-out | arm | group | 1515 | 0.965 | -0.081 | 0.000 | 0.000 | 0.000 | 0.000 |
| leave-one-architecture-out | mips | binary | 4182 | 0.999 | 0.998 | 1.000 | 1.000 | 1.000 | 1.000 |
| leave-one-architecture-out | mips | group | 4129 | 0.999 | 0.998 | 1.000 | 1.000 | 1.000 | 1.000 |
| leave-one-architecture-out | mipsel | binary | 4003 | 1.000 | 0.999 | 1.000 | 1.000 | 1.000 | 1.000 |
| leave-one-architecture-out | mipsel | group | 3963 | 1.000 | 0.999 | 1.000 | 1.000 | 1.000 | 1.000 |
| leave-one-architecture-out | x86 | binary | 4182 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| leave-one-architecture-out | x86 | group | 3870 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| architecture-sanity | all | binary | 2849 |  |  |  |  |  |  |

## whole trace against first-window runs, AUROC

| Experiment | Held out | View | Test | whole | first-5 | first-10 | first-15 | first-20 | first-20-no-network |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| in-architecture | arm | binary | 363 | 0.999 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| in-architecture | arm | group | 320 | 0.999 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| in-architecture | mips | binary | 836 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| in-architecture | mips | group | 830 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| in-architecture | mipsel | binary | 801 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| in-architecture | mipsel | group | 790 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| in-architecture | x86 | binary | 849 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| in-architecture | x86 | group | 799 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| leave-one-architecture-out | arm | binary | 1809 | 1.000 | 0.949 | 1.000 | 1.000 | 1.000 | 1.000 |
| leave-one-architecture-out | arm | group | 1515 | 1.000 | 0.938 | 1.000 | 1.000 | 1.000 | 1.000 |
| leave-one-architecture-out | mips | binary | 4182 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| leave-one-architecture-out | mips | group | 4129 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| leave-one-architecture-out | mipsel | binary | 4003 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| leave-one-architecture-out | mipsel | group | 3963 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| leave-one-architecture-out | x86 | binary | 4182 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| leave-one-architecture-out | x86 | group | 3870 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| architecture-sanity | all | binary | 2849 |  |  |  |  |  |  |


## in-architecture

| Held out | View | Train | Test | Benign | Malware | Chance | Threshold | Accuracy | Macro-F1 | MCC | MCC at 0.5 | AUROC | Rounds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arm | binary | 1262 | 363 | 30 | 333 | 0.917 | 0.305 | 0.989 | 0.966 | 0.934 | 0.905 | 0.999 | 31 |
| arm | group | 1262 | 320 | 30 | 290 | 0.906 | 0.305 | 0.988 | 0.965 | 0.933 | 0.903 | 0.999 | 31 |
| mips | binary | 2924 | 836 | 520 | 316 | 0.622 | 0.130 | 0.999 | 0.999 | 0.997 | 0.995 | 1.000 | 168 |
| mips | group | 2924 | 830 | 520 | 310 | 0.627 | 0.130 | 0.999 | 0.999 | 0.997 | 0.995 | 1.000 | 168 |
| mipsel | binary | 2800 | 801 | 499 | 302 | 0.623 | 0.494 | 0.999 | 0.999 | 0.997 | 0.997 | 1.000 | 240 |
| mipsel | group | 2800 | 790 | 499 | 291 | 0.632 | 0.494 | 0.999 | 0.999 | 0.997 | 0.997 | 1.000 | 240 |
| x86 | binary | 2913 | 849 | 511 | 338 | 0.602 | 0.466 | 0.999 | 0.999 | 0.998 | 0.998 | 1.000 | 77 |
| x86 | group | 2913 | 799 | 511 | 288 | 0.640 | 0.466 | 0.999 | 0.999 | 0.997 | 0.997 | 1.000 | 77 |

## leave-one-architecture-out

| Held out | View | Train | Test | Benign | Malware | Chance | Threshold | Accuracy | Macro-F1 | MCC | MCC at 0.5 | AUROC | Rounds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arm | binary | 8637 | 1809 | 150 | 1659 | 0.917 | 0.348 | 0.995 | 0.984 | 0.969 | 0.959 | 1.000 | 208 |
| arm | group | 8637 | 1515 | 150 | 1365 | 0.901 | 0.348 | 0.995 | 0.987 | 0.975 | 0.965 | 1.000 | 208 |
| mips | binary | 6975 | 4182 | 2601 | 1581 | 0.622 | 0.527 | 1.000 | 0.999 | 0.999 | 0.999 | 1.000 | 61 |
| mips | group | 6975 | 4129 | 2601 | 1528 | 0.630 | 0.527 | 1.000 | 0.999 | 0.999 | 0.999 | 1.000 | 61 |
| mipsel | binary | 7099 | 4003 | 2496 | 1507 | 0.624 | 0.171 | 1.000 | 1.000 | 0.999 | 1.000 | 1.000 | 212 |
| mipsel | group | 7099 | 3963 | 2496 | 1467 | 0.630 | 0.171 | 1.000 | 1.000 | 0.999 | 1.000 | 1.000 | 212 |
| x86 | binary | 6986 | 4182 | 2554 | 1628 | 0.611 | 0.151 | 0.999 | 0.999 | 0.998 | 1.000 | 1.000 | 211 |
| x86 | group | 6986 | 3870 | 2544 | 1326 | 0.657 | 0.151 | 0.999 | 0.999 | 0.998 | 1.000 | 1.000 | 211 |

## architecture-sanity

| Held out | View | Train | Test | Benign | Malware | Chance | Threshold | Accuracy | Macro-F1 | MCC | MCC at 0.5 | AUROC | Rounds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all | binary | 9899 | 2849 | 1560 | 1289 | 0.298 |  | 0.644 | 0.690 | 0.512 |  |  | 130 |

## first-5 in-architecture

| Held out | View | Train | Test | Benign | Malware | Chance | Threshold | Accuracy | Macro-F1 | MCC | MCC at 0.5 | AUROC | Rounds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arm | binary | 1262 | 363 | 30 | 333 | 0.917 | 0.502 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 132 |
| arm | group | 1262 | 320 | 30 | 290 | 0.906 | 0.502 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 132 |
| mips | binary | 2924 | 836 | 520 | 316 | 0.622 | 0.500 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 92 |
| mips | group | 2924 | 830 | 520 | 310 | 0.627 | 0.500 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 92 |
| mipsel | binary | 2800 | 801 | 499 | 302 | 0.623 | 0.501 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 97 |
| mipsel | group | 2800 | 790 | 499 | 291 | 0.632 | 0.501 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 97 |
| x86 | binary | 2913 | 849 | 511 | 338 | 0.602 | 0.420 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 122 |
| x86 | group | 2913 | 799 | 511 | 288 | 0.640 | 0.420 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 122 |

## first-5 leave-one-architecture-out

| Held out | View | Train | Test | Benign | Malware | Chance | Threshold | Accuracy | Macro-F1 | MCC | MCC at 0.5 | AUROC | Rounds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arm | binary | 8637 | 1809 | 150 | 1659 | 0.917 | 0.481 | 0.870 | 0.465 | -0.067 | -0.067 | 0.949 | 95 |
| arm | group | 8637 | 1515 | 150 | 1365 | 0.901 | 0.481 | 0.845 | 0.458 | -0.081 | -0.081 | 0.938 | 95 |
| mips | binary | 6975 | 4182 | 2601 | 1581 | 0.622 | 0.478 | 0.999 | 0.999 | 0.998 | 0.998 | 1.000 | 110 |
| mips | group | 6975 | 4129 | 2601 | 1528 | 0.630 | 0.478 | 0.999 | 0.999 | 0.998 | 0.998 | 1.000 | 110 |
| mipsel | binary | 7099 | 4003 | 2496 | 1507 | 0.624 | 0.503 | 1.000 | 1.000 | 0.999 | 0.999 | 1.000 | 110 |
| mipsel | group | 7099 | 3963 | 2496 | 1467 | 0.630 | 0.503 | 1.000 | 1.000 | 0.999 | 0.999 | 1.000 | 110 |
| x86 | binary | 6986 | 4182 | 2554 | 1628 | 0.611 | 0.505 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 110 |
| x86 | group | 6986 | 3870 | 2544 | 1326 | 0.657 | 0.505 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 110 |

## first-5 architecture-sanity

| Held out | View | Train | Test | Benign | Malware | Chance | Threshold | Accuracy | Macro-F1 | MCC | MCC at 0.5 | AUROC | Rounds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all | binary | 9899 | 2849 | 1560 | 1289 | 0.298 |  | 0.418 | 0.411 | 0.253 |  |  | 136 |

## first-10 in-architecture

| Held out | View | Train | Test | Benign | Malware | Chance | Threshold | Accuracy | Macro-F1 | MCC | MCC at 0.5 | AUROC | Rounds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arm | binary | 1262 | 363 | 30 | 333 | 0.917 | 0.493 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 145 |
| arm | group | 1262 | 320 | 30 | 290 | 0.906 | 0.493 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 145 |
| mips | binary | 2924 | 836 | 520 | 316 | 0.622 | 0.500 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 91 |
| mips | group | 2924 | 830 | 520 | 310 | 0.627 | 0.500 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 91 |
| mipsel | binary | 2800 | 801 | 499 | 302 | 0.623 | 0.500 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 94 |
| mipsel | group | 2800 | 790 | 499 | 291 | 0.632 | 0.500 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 94 |
| x86 | binary | 2913 | 849 | 511 | 338 | 0.602 | 0.497 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 131 |
| x86 | group | 2913 | 799 | 511 | 288 | 0.640 | 0.497 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 131 |

## first-10 leave-one-architecture-out

| Held out | View | Train | Test | Benign | Malware | Chance | Threshold | Accuracy | Macro-F1 | MCC | MCC at 0.5 | AUROC | Rounds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arm | binary | 8637 | 1809 | 150 | 1659 | 0.917 | 0.499 | 0.917 | 0.478 | 0.000 | 0.000 | 1.000 | 94 |
| arm | group | 8637 | 1515 | 150 | 1365 | 0.901 | 0.499 | 0.901 | 0.474 | 0.000 | 0.000 | 1.000 | 94 |
| mips | binary | 6975 | 4182 | 2601 | 1581 | 0.622 | 0.497 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 174 |
| mips | group | 6975 | 4129 | 2601 | 1528 | 0.630 | 0.497 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 174 |
| mipsel | binary | 7099 | 4003 | 2496 | 1507 | 0.624 | 0.496 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 173 |
| mipsel | group | 7099 | 3963 | 2496 | 1467 | 0.630 | 0.496 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 173 |
| x86 | binary | 6986 | 4182 | 2554 | 1628 | 0.611 | 0.500 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 96 |
| x86 | group | 6986 | 3870 | 2544 | 1326 | 0.657 | 0.500 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 96 |

## first-10 architecture-sanity

| Held out | View | Train | Test | Benign | Malware | Chance | Threshold | Accuracy | Macro-F1 | MCC | MCC at 0.5 | AUROC | Rounds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all | binary | 9899 | 2849 | 1560 | 1289 | 0.298 |  | 0.466 | 0.478 | 0.331 |  |  | 124 |

## first-15 in-architecture

| Held out | View | Train | Test | Benign | Malware | Chance | Threshold | Accuracy | Macro-F1 | MCC | MCC at 0.5 | AUROC | Rounds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arm | binary | 1262 | 363 | 30 | 333 | 0.917 | 0.496 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 128 |
| arm | group | 1262 | 320 | 30 | 290 | 0.906 | 0.496 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 128 |
| mips | binary | 2924 | 836 | 520 | 316 | 0.622 | 0.499 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 83 |
| mips | group | 2924 | 830 | 520 | 310 | 0.627 | 0.499 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 83 |
| mipsel | binary | 2800 | 801 | 499 | 302 | 0.623 | 0.499 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 90 |
| mipsel | group | 2800 | 790 | 499 | 291 | 0.632 | 0.499 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 90 |
| x86 | binary | 2913 | 849 | 511 | 338 | 0.602 | 0.498 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 98 |
| x86 | group | 2913 | 799 | 511 | 288 | 0.640 | 0.498 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 98 |

## first-15 leave-one-architecture-out

| Held out | View | Train | Test | Benign | Malware | Chance | Threshold | Accuracy | Macro-F1 | MCC | MCC at 0.5 | AUROC | Rounds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arm | binary | 8637 | 1809 | 150 | 1659 | 0.917 | 0.500 | 0.917 | 0.478 | 0.000 | 0.000 | 1.000 | 118 |
| arm | group | 8637 | 1515 | 150 | 1365 | 0.901 | 0.500 | 0.901 | 0.474 | 0.000 | 0.000 | 1.000 | 118 |
| mips | binary | 6975 | 4182 | 2601 | 1581 | 0.622 | 0.497 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 301 |
| mips | group | 6975 | 4129 | 2601 | 1528 | 0.630 | 0.497 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 301 |
| mipsel | binary | 7099 | 4003 | 2496 | 1507 | 0.624 | 0.498 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 301 |
| mipsel | group | 7099 | 3963 | 2496 | 1467 | 0.630 | 0.498 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 301 |
| x86 | binary | 6986 | 4182 | 2554 | 1628 | 0.611 | 0.500 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 175 |
| x86 | group | 6986 | 3870 | 2544 | 1326 | 0.657 | 0.500 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 175 |

## first-15 architecture-sanity

| Held out | View | Train | Test | Benign | Malware | Chance | Threshold | Accuracy | Macro-F1 | MCC | MCC at 0.5 | AUROC | Rounds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all | binary | 9899 | 2849 | 1560 | 1289 | 0.298 |  | 0.639 | 0.621 | 0.545 |  |  | 90 |

## first-20 in-architecture

| Held out | View | Train | Test | Benign | Malware | Chance | Threshold | Accuracy | Macro-F1 | MCC | MCC at 0.5 | AUROC | Rounds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arm | binary | 1262 | 363 | 30 | 333 | 0.917 | 0.506 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 92 |
| arm | group | 1262 | 320 | 30 | 290 | 0.906 | 0.506 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 92 |
| mips | binary | 2924 | 836 | 520 | 316 | 0.622 | 0.495 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 85 |
| mips | group | 2924 | 830 | 520 | 310 | 0.627 | 0.495 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 85 |
| mipsel | binary | 2800 | 801 | 499 | 302 | 0.623 | 0.499 | 0.999 | 0.999 | 0.997 | 0.997 | 1.000 | 86 |
| mipsel | group | 2800 | 790 | 499 | 291 | 0.632 | 0.499 | 0.999 | 0.999 | 0.997 | 0.997 | 1.000 | 86 |
| x86 | binary | 2913 | 849 | 511 | 338 | 0.602 | 0.499 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 88 |
| x86 | group | 2913 | 799 | 511 | 288 | 0.640 | 0.499 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 88 |

## first-20 leave-one-architecture-out

| Held out | View | Train | Test | Benign | Malware | Chance | Threshold | Accuracy | Macro-F1 | MCC | MCC at 0.5 | AUROC | Rounds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arm | binary | 8637 | 1809 | 150 | 1659 | 0.917 | 0.497 | 0.917 | 0.478 | 0.000 | 0.000 | 1.000 | 97 |
| arm | group | 8637 | 1515 | 150 | 1365 | 0.901 | 0.497 | 0.901 | 0.474 | 0.000 | 0.000 | 1.000 | 97 |
| mips | binary | 6975 | 4182 | 2601 | 1581 | 0.622 | 0.500 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 315 |
| mips | group | 6975 | 4129 | 2601 | 1528 | 0.630 | 0.500 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 315 |
| mipsel | binary | 7099 | 4003 | 2496 | 1507 | 0.624 | 0.501 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 304 |
| mipsel | group | 7099 | 3963 | 2496 | 1467 | 0.630 | 0.501 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 304 |
| x86 | binary | 6986 | 4182 | 2554 | 1628 | 0.611 | 0.502 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 399 |
| x86 | group | 6986 | 3870 | 2544 | 1326 | 0.657 | 0.502 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 399 |

## first-20 architecture-sanity

| Held out | View | Train | Test | Benign | Malware | Chance | Threshold | Accuracy | Macro-F1 | MCC | MCC at 0.5 | AUROC | Rounds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all | binary | 9899 | 2849 | 1560 | 1289 | 0.298 |  | 0.653 | 0.682 | 0.534 |  |  | 93 |

## first-20-no-network in-architecture

| Held out | View | Train | Test | Benign | Malware | Chance | Threshold | Accuracy | Macro-F1 | MCC | MCC at 0.5 | AUROC | Rounds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arm | binary | 1262 | 363 | 30 | 333 | 0.917 | 0.504 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 92 |
| arm | group | 1262 | 320 | 30 | 290 | 0.906 | 0.504 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 92 |
| mips | binary | 2924 | 836 | 520 | 316 | 0.622 | 0.495 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 85 |
| mips | group | 2924 | 830 | 520 | 310 | 0.627 | 0.495 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 85 |
| mipsel | binary | 2800 | 801 | 499 | 302 | 0.623 | 0.500 | 0.999 | 0.999 | 0.997 | 0.997 | 1.000 | 101 |
| mipsel | group | 2800 | 790 | 499 | 291 | 0.632 | 0.500 | 0.999 | 0.999 | 0.997 | 0.997 | 1.000 | 101 |
| x86 | binary | 2913 | 849 | 511 | 338 | 0.602 | 0.499 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 91 |
| x86 | group | 2913 | 799 | 511 | 288 | 0.640 | 0.499 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 91 |

## first-20-no-network leave-one-architecture-out

| Held out | View | Train | Test | Benign | Malware | Chance | Threshold | Accuracy | Macro-F1 | MCC | MCC at 0.5 | AUROC | Rounds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arm | binary | 8637 | 1809 | 150 | 1659 | 0.917 | 0.498 | 0.917 | 0.478 | 0.000 | 0.000 | 1.000 | 116 |
| arm | group | 8637 | 1515 | 150 | 1365 | 0.901 | 0.498 | 0.901 | 0.474 | 0.000 | 0.000 | 1.000 | 116 |
| mips | binary | 6975 | 4182 | 2601 | 1581 | 0.622 | 0.500 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 164 |
| mips | group | 6975 | 4129 | 2601 | 1528 | 0.630 | 0.500 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 164 |
| mipsel | binary | 7099 | 4003 | 2496 | 1507 | 0.624 | 0.500 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 137 |
| mipsel | group | 7099 | 3963 | 2496 | 1467 | 0.630 | 0.500 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 137 |
| x86 | binary | 6986 | 4182 | 2554 | 1628 | 0.611 | 0.501 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 198 |
| x86 | group | 6986 | 3870 | 2544 | 1326 | 0.657 | 0.501 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 198 |

## first-20-no-network architecture-sanity

| Held out | View | Train | Test | Benign | Malware | Chance | Threshold | Accuracy | Macro-F1 | MCC | MCC at 0.5 | AUROC | Rounds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all | binary | 9899 | 2849 | 1560 | 1289 | 0.298 |  | 0.652 | 0.680 | 0.535 |  |  | 92 |
