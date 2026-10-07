# Leakage (H3)

**Measured on the previous split.** These results were produced before
`fix/stable-signatures` (2026-10-07) re-dealt the split on stable group
ids. They stand as the H3 measurement until the planned rerun as a
managed-spot job, which also raises the round cap and re-deals the
grouped splits per seed.

Run on 2026-10-05 with units {'mid': 21, 'all': 1}, cap 100 over seeds [0, 1, 2, 3, 4] and cap 25 on seed 0; XGBoost {'n_estimators': 400, 'max_depth': 6, 'learning_rate': 0.1, 'subsample': 0.8, 'colsample_bytree': 0.8, 'min_child_weight': 1, 'tree_method': 'hist'}, early stopping after 30 rounds. See `docs/experiment_h3_leakage.md` and D10.

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

## mid rows, cap 100, binary view

| Arch | Seeds | Row-random MCC | Hash-grouped MCC | Behaviour-grouped MCC | Row gap | Identity gap | Row-random AUROC | Behaviour-grouped AUROC |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arm | 5 | 0.995 (0.989 to 0.996) | 0.963 (0.963 to 0.963) | 0.986 (0.966 to 1.000) | +0.032 | -0.023 | 1.000 | 1.000 |
| mips | 5 | 0.995 (0.994 to 0.995) | 0.993 (0.992 to 0.995) | 0.994 (0.992 to 0.995) | +0.001 | -0.001 | 1.000 | 1.000 |
| mipsel | 5 | 0.997 (0.995 to 0.998) | 0.996 (0.992 to 0.997) | 0.988 (0.987 to 0.989) | +0.001 | +0.008 | 1.000 | 1.000 |
| x86 | 5 | 0.998 (0.998 to 0.999) | 0.992 (0.992 to 0.995) | 0.995 (0.995 to 0.997) | +0.006 | -0.003 | 1.000 | 1.000 |

## mid rows, cap 100, group view

| Arch | Seeds | Row-random MCC | Hash-grouped MCC | Behaviour-grouped MCC | Row gap | Identity gap | Row-random AUROC | Behaviour-grouped AUROC |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arm | 5 | 0.995 (0.989 to 0.996) | 0.963 (0.963 to 0.963) | 0.985 (0.963 to 1.000) | +0.032 | -0.022 | 1.000 | 1.000 |
| mips | 5 | 0.995 (0.994 to 0.995) | 0.993 (0.992 to 0.995) | 0.994 (0.992 to 0.995) | +0.001 | -0.001 | 1.000 | 1.000 |
| mipsel | 5 | 0.997 (0.995 to 0.998) | 0.996 (0.992 to 0.997) | 0.988 (0.986 to 0.989) | +0.001 | +0.008 | 1.000 | 1.000 |
| x86 | 5 | 0.998 (0.998 to 0.999) | 0.992 (0.992 to 0.994) | 0.995 (0.994 to 0.997) | +0.006 | -0.003 | 1.000 | 1.000 |

## mid rows, cap 100, window view

| Arch | Seeds | Row-random MCC | Hash-grouped MCC | Behaviour-grouped MCC | Row gap | Identity gap | Row-random AUROC | Behaviour-grouped AUROC |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arm | 5 | 0.974 (0.971 to 0.975) | 0.931 (0.929 to 0.933) | 0.982 (0.980 to 0.983) | +0.042 | -0.051 | 0.999 | 0.999 |
| mips | 5 | 0.987 (0.987 to 0.988) | 0.984 (0.983 to 0.984) | 0.985 (0.984 to 0.985) | +0.003 | -0.001 | 0.999 | 0.999 |
| mipsel | 5 | 0.990 (0.990 to 0.990) | 0.990 (0.990 to 0.990) | 0.968 (0.966 to 0.972) | -0.000 | +0.022 | 1.000 | 0.999 |
| x86 | 5 | 0.988 (0.987 to 0.989) | 0.983 (0.983 to 0.984) | 0.988 (0.988 to 0.988) | +0.005 | -0.005 | 1.000 | 0.999 |

## mid rows, cap 25, binary view

| Arch | Seeds | Row-random MCC | Hash-grouped MCC | Behaviour-grouped MCC | Row gap | Identity gap | Row-random AUROC | Behaviour-grouped AUROC |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arm | 1 | 0.993 (0.993 to 0.993) | 0.963 (0.963 to 0.963) | 0.982 (0.982 to 0.982) | +0.030 | -0.019 | 1.000 | 1.000 |
| mips | 1 | 0.993 (0.993 to 0.993) | 0.995 (0.995 to 0.995) | 0.997 (0.997 to 0.997) | -0.002 | -0.003 | 1.000 | 1.000 |
| mipsel | 1 | 0.995 (0.995 to 0.995) | 0.989 (0.989 to 0.989) | 0.989 (0.989 to 0.989) | +0.005 | +0.000 | 1.000 | 1.000 |
| x86 | 1 | 0.995 (0.995 to 0.995) | 0.992 (0.992 to 0.992) | 0.997 (0.997 to 0.997) | +0.003 | -0.006 | 1.000 | 1.000 |

## mid rows, cap 25, group view

| Arch | Seeds | Row-random MCC | Hash-grouped MCC | Behaviour-grouped MCC | Row gap | Identity gap | Row-random AUROC | Behaviour-grouped AUROC |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arm | 1 | 0.993 (0.993 to 0.993) | 0.963 (0.963 to 0.963) | 0.981 (0.981 to 0.981) | +0.030 | -0.019 | 1.000 | 1.000 |
| mips | 1 | 0.993 (0.993 to 0.993) | 0.995 (0.995 to 0.995) | 0.997 (0.997 to 0.997) | -0.002 | -0.003 | 1.000 | 1.000 |
| mipsel | 1 | 0.995 (0.995 to 0.995) | 0.989 (0.989 to 0.989) | 0.989 (0.989 to 0.989) | +0.005 | +0.000 | 1.000 | 1.000 |
| x86 | 1 | 0.995 (0.995 to 0.995) | 0.992 (0.992 to 0.992) | 0.997 (0.997 to 0.997) | +0.003 | -0.006 | 1.000 | 1.000 |

## mid rows, cap 25, window view

| Arch | Seeds | Row-random MCC | Hash-grouped MCC | Behaviour-grouped MCC | Row gap | Identity gap | Row-random AUROC | Behaviour-grouped AUROC |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arm | 1 | 0.963 (0.963 to 0.963) | 0.923 (0.923 to 0.923) | 0.977 (0.977 to 0.977) | +0.040 | -0.054 | 0.999 | 0.999 |
| mips | 1 | 0.986 (0.986 to 0.986) | 0.983 (0.983 to 0.983) | 0.984 (0.984 to 0.984) | +0.003 | -0.001 | 0.999 | 0.999 |
| mipsel | 1 | 0.989 (0.989 to 0.989) | 0.990 (0.990 to 0.990) | 0.980 (0.980 to 0.980) | -0.001 | +0.010 | 1.000 | 0.999 |
| x86 | 1 | 0.986 (0.986 to 0.986) | 0.982 (0.982 to 0.982) | 0.986 (0.986 to 0.986) | +0.004 | -0.004 | 0.999 | 0.999 |

## all rows, cap 100, binary view

| Arch | Seeds | Row-random MCC | Hash-grouped MCC | Behaviour-grouped MCC | Row gap | Identity gap | Row-random AUROC | Behaviour-grouped AUROC |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arm | 5 | 0.996 (0.993 to 0.996) | 0.963 (0.963 to 0.963) | 0.944 (0.935 to 0.950) | +0.032 | +0.019 | 1.000 | 1.000 |
| mips | 5 | 0.993 (0.991 to 0.994) | 0.992 (0.992 to 0.992) | 0.995 (0.995 to 0.997) | +0.001 | -0.003 | 1.000 | 1.000 |
| mipsel | 5 | 0.996 (0.995 to 0.996) | 0.996 (0.992 to 0.997) | 0.986 (0.984 to 0.987) | -0.000 | +0.010 | 1.000 | 1.000 |
| x86 | 5 | 0.997 (0.996 to 0.998) | 0.992 (0.992 to 0.992) | 0.997 (0.997 to 0.997) | +0.005 | -0.005 | 1.000 | 1.000 |

## all rows, cap 100, group view

| Arch | Seeds | Row-random MCC | Hash-grouped MCC | Behaviour-grouped MCC | Row gap | Identity gap | Row-random AUROC | Behaviour-grouped AUROC |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arm | 5 | 0.996 (0.993 to 0.996) | 0.963 (0.963 to 0.963) | 0.974 (0.963 to 0.981) | +0.033 | -0.011 | 1.000 | 1.000 |
| mips | 5 | 0.994 (0.993 to 0.995) | 0.992 (0.992 to 0.992) | 0.995 (0.995 to 0.997) | +0.002 | -0.003 | 1.000 | 1.000 |
| mipsel | 5 | 0.996 (0.996 to 0.997) | 0.996 (0.992 to 0.997) | 0.986 (0.984 to 0.986) | +0.000 | +0.010 | 1.000 | 1.000 |
| x86 | 5 | 0.997 (0.997 to 0.999) | 0.992 (0.992 to 0.992) | 0.997 (0.997 to 0.997) | +0.006 | -0.005 | 1.000 | 1.000 |

## all rows, cap 100, window view

| Arch | Seeds | Row-random MCC | Hash-grouped MCC | Behaviour-grouped MCC | Row gap | Identity gap | Row-random AUROC | Behaviour-grouped AUROC |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arm | 5 | 0.967 (0.964 to 0.971) | 0.931 (0.928 to 0.934) | 0.979 (0.975 to 0.982) | +0.036 | -0.047 | 0.999 | 0.999 |
| mips | 5 | 0.986 (0.986 to 0.987) | 0.983 (0.982 to 0.984) | 0.984 (0.984 to 0.985) | +0.003 | -0.001 | 0.999 | 0.999 |
| mipsel | 5 | 0.989 (0.989 to 0.990) | 0.989 (0.989 to 0.990) | 0.966 (0.966 to 0.966) | -0.000 | +0.023 | 1.000 | 0.999 |
| x86 | 5 | 0.987 (0.986 to 0.988) | 0.982 (0.982 to 0.982) | 0.985 (0.985 to 0.986) | +0.005 | -0.003 | 1.000 | 0.999 |

## all rows, cap 25, binary view

| Arch | Seeds | Row-random MCC | Hash-grouped MCC | Behaviour-grouped MCC | Row gap | Identity gap | Row-random AUROC | Behaviour-grouped AUROC |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arm | 1 | 0.989 (0.989 to 0.989) | 0.963 (0.963 to 0.963) | 0.950 (0.950 to 0.950) | +0.026 | +0.013 | 0.999 | 1.000 |
| mips | 1 | 0.993 (0.993 to 0.993) | 0.992 (0.992 to 0.992) | 0.992 (0.992 to 0.992) | +0.001 | +0.000 | 1.000 | 1.000 |
| mipsel | 1 | 0.995 (0.995 to 0.995) | 0.997 (0.997 to 0.997) | 0.984 (0.984 to 0.984) | -0.003 | +0.013 | 1.000 | 1.000 |
| x86 | 1 | 0.997 (0.997 to 0.997) | 0.992 (0.992 to 0.992) | 0.997 (0.997 to 0.997) | +0.004 | -0.005 | 1.000 | 1.000 |

## all rows, cap 25, group view

| Arch | Seeds | Row-random MCC | Hash-grouped MCC | Behaviour-grouped MCC | Row gap | Identity gap | Row-random AUROC | Behaviour-grouped AUROC |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arm | 1 | 0.989 (0.989 to 0.989) | 0.963 (0.963 to 0.963) | 0.981 (0.981 to 0.981) | +0.026 | -0.019 | 0.999 | 1.000 |
| mips | 1 | 0.993 (0.993 to 0.993) | 0.992 (0.992 to 0.992) | 0.995 (0.995 to 0.995) | +0.001 | -0.003 | 1.000 | 1.000 |
| mipsel | 1 | 0.995 (0.995 to 0.995) | 0.997 (0.997 to 0.997) | 0.984 (0.984 to 0.984) | -0.003 | +0.014 | 1.000 | 1.000 |
| x86 | 1 | 0.997 (0.997 to 0.997) | 0.992 (0.992 to 0.992) | 0.997 (0.997 to 0.997) | +0.005 | -0.005 | 1.000 | 1.000 |

## all rows, cap 25, window view

| Arch | Seeds | Row-random MCC | Hash-grouped MCC | Behaviour-grouped MCC | Row gap | Identity gap | Row-random AUROC | Behaviour-grouped AUROC |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| arm | 1 | 0.945 (0.945 to 0.945) | 0.921 (0.921 to 0.921) | 0.948 (0.948 to 0.948) | +0.025 | -0.028 | 0.998 | 0.999 |
| mips | 1 | 0.985 (0.985 to 0.985) | 0.981 (0.981 to 0.981) | 0.983 (0.983 to 0.983) | +0.005 | -0.002 | 0.999 | 0.999 |
| mipsel | 1 | 0.987 (0.987 to 0.987) | 0.990 (0.990 to 0.990) | 0.962 (0.962 to 0.962) | -0.003 | +0.028 | 0.999 | 0.998 |
| x86 | 1 | 0.985 (0.985 to 0.985) | 0.981 (0.981 to 0.981) | 0.984 (0.984 to 0.984) | +0.003 | -0.003 | 0.999 | 0.999 |
