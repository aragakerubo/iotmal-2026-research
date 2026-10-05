# Experiment H3: leakage from row-level splits

Status: draft, 2026-10-05. Every section marked **Decision** is open
and waits for the researchers; each lists the options and a
recommendation. Nothing here is implemented yet.

## The question

H3 (`docs/plans/plan.md`, Research question) says that the row-level
random split used by the dataset paper overstates accuracy compared
with a split that keeps every binary whole, and that the size of the
gap is a finding in its own right. A row-level split puts rows of one
binary on both sides; because consecutive STRACE rows share nineteen of
their twenty calls (`docs/dataset_notes.md`, "Rows grow, then slide"),
a test row's near-twin is almost always in training.

## Why the plan's version cannot show a gap

The plan describes H3 as XGBoost on a row-level split against a
behaviour-grouped split, on the detection task. On the per-binary
feature store, the grouped split already scores MCC 0.995 to 1.000 on
every in-architecture fold (`data/BASELINE.md`). A row-level split
cannot score higher than 1.000, so on that unit the gap is pinned near
zero by the ceiling, whatever the leak. The first-window experiments
explain the ceiling: the class is named by program start-up within ten
calls (`data/FIRST_WINDOW.md`). Leakage can only show where the grouped
score has room below 1.

A single STRACE row from the middle of a trace has that room, because
it does not contain start-up. It is also the unit the dataset paper
classified, so a gap measured there speaks directly to the paper's
numbers.

## Feasibility check

A throwaway check, not committed as code, read two row groups per
architecture (the first and the middle one, about 8 percent of the
rows), dropped the first binary of each group in case it began in the
previous group, kept rows after the twentieth (so no window contains
start-up), and sampled up to 50 of them per live binary with a fixed
seed. It trained XGBoost with `configs/baseline.yaml` on counts divided
by twenty, in architecture, once on the committed split assignment
(binaries kept whole) and once on a 70/10/20 random split of the rows,
and scored at a fixed 0.5:

| Arch | Split | Test windows | Window MCC | Window AUROC | Binary MCC |
| --- | --- | --- | --- | --- | --- |
| arm | grouped | 2,508 | 0.989 | 0.999 | 1.000 |
| arm | row-random | 2,540 | 0.985 | 0.999 | 0.993 |
| mips | grouped | 5,477 | 0.911 | 0.997 | 0.882 |
| mips | row-random | 4,839 | 0.968 | 0.999 | 0.984 |
| mipsel | grouped | 5,500 | 0.935 | 0.999 | 0.949 |
| mipsel | row-random | 6,049 | 0.971 | 0.999 | 1.000 |
| x86 | grouped | 6,601 | 0.928 | 0.995 | 0.931 |
| x86 | row-random | 6,161 | 0.963 | 0.999 | 0.985 |

Binary MCC averages each test binary's window scores. The sample is
skewed: two row groups hold 150 to 540 benign binaries per architecture
against 72 to 121 malware, and one seed was run. The numbers are
indicative only. They show that mid-trace windows sit below the
ceiling on MIPS, MIPSEL and x86, that the row-random split scores 3 to
6 MCC points higher there, and that ARM shows no gap. The real
experiment replaces this table.

## What earlier decisions already fix

Inert binaries are excluded (D8). The grouped split is the committed
behaviour-grouped assignment in `data/splits/` (D2); no new grouped
split is drawn. Thresholds are chosen on validation rows of the same
split (D9 revision). The model is XGBoost with `configs/baseline.yaml`,
so H3 isolates the split and changes nothing else. Every split is
within one architecture, since leave-one-architecture-out never puts
rows of one binary on both sides and has no row leak to measure.

## Decisions

**Decision A, input unit.** (1) Rows after the twentieth only, so
start-up is never in a window. (2) Every row, as the dataset paper did.
(3) Both, reported side by side. Recommendation: (3). The paper's
setting is (2) and is the number a reader will compare with; (1) is
where the gap has room to show, as the check suggests.

**Decision B, splits compared.** (1) Row-random against
behaviour-grouped, as the plan says. (2) Row-random, hash-grouped (the
original D2) and behaviour-grouped. Recommendation: (2). The step from
row to hash measures the leak of a binary's own neighbouring rows; the
step from hash to behaviour group measures the leak through identical
binaries under different hashes (190 x86 Mirai builds share one trace),
which is a second finding the paper can state separately.

**Decision C, sampling.** (1) All rows, about 105 million across the
four files, which needs the window-level feature store the plan puts
in a Processing job. (2) A fixed cap of K rows per binary, drawn
uniformly with a seed from the rows the input unit allows. With
K = 100 that is at most 1.4 million rows over the 14,176 live
binaries, built in one pass on the
notebook in a few minutes, like the first-window scan. Recommendation:
(2) with K = 100, and one rerun at K = 25 to show the gap does not
depend on K. A cap also stops the longest Mirai binaries, up to 184,253
rows, from being most of the data (`docs/dataset_notes.md`, "Binaries,
not rows"); the row-random split is drawn over the same capped sample,
so both splits see identical rows.

**Decision D, metrics.** (1) Window-level only, for comparability with
the dataset paper. (2) Window-level and binary-level (each test
binary's mean window score, the unit of D9), both with the group view.
Recommendation: (2), window-level stated first in the H3 result,
because the claim is about the paper's row-level numbers, and
binary-level beside it, because the binary is our unit.

**Decision E, task.** (1) Detection only. (2) Detection, and family
classification on the four D7 classes as a second table. The family
task is harder and has more room below the ceiling, so the gap may be
larger there. Recommendation: (1) now, (2) when the family experiment
is run in week 8, so that it reuses this code instead of growing it.

**Decision F, seeds.** The fix to the split (`fix/split-determinism`)
measured about two MCC points of draw-to-draw variation on ARM, which
is the order of the gap the check suggests. (1) One seed. (2) Five
seeds of the row-random split and of the window sample, with the
grouped split fixed by `data/splits/`. Recommendation: (2), reporting
the mean and the range, so a gap of three points can be told from
noise.

## Outputs, once the decisions are made

A sample scan, `scripts/window_sample_scan.py`, writing
`data/windows/<arch>_sample_strace.parquet` (gitignored) and the same
under `features/windows/` in the bucket; a module `iotmal.leakage`
building the three splits over the sample and scoring them with the
`iotmal.baseline` routines; `scripts/run_leakage.py` writing
`data/leakage/results.csv` and `data/LEAKAGE.md`; tests on small
synthetic frames in `tests/test_leakage.py`, including one proving that
no binary crosses the grouped splits and that the row-random split
does put rows of one binary on both sides.

## How to read the result

A gap near zero on every architecture would mean the paper's row-level
numbers are not inflated by leakage on this dataset, and the paper
would say so. A gap of several points on rows after the twentieth, and
a smaller one on every row, would mean leakage inflates the paper's
numbers only where start-up does not already decide the class. ARM is
expected to show the least, since its live binaries are few and its
mid-trace windows already sit near the ceiling in the check.
