# Decisions

Numbered, never renumbered. A superseded decision keeps its number and
gains a note pointing at the one that replaced it. Each write-up's
"Traces to" line cites these.

## D1: One branch per step, one commit per branch, delivered as a patch

Every change to this repository arrives as a `git format-patch` file
holding a single commit, applied with `git am` on a branch named
`feat/`, `fix/`, `chore/` or `docs/` plus a short slug, checked with
`make check`, pushed, and squash-merged into `main`. The commit subject
is a Conventional Commit (`type(scope): imperative summary`).

**Why.** Two researchers, one of whom writes the code away from the
repo. A patch carries the author, the message and the exact tree it was
made against, so applying it is one command and a bad apply is one
`git am --abort`. Squash-merging keeps `main` one commit per step, which
is the granularity the paper's reproducibility package will cite.

**Revisit if** a third contributor joins, or a step needs more than one
commit to review sensibly.

## D2: Every split is by binary hash, never by row

Train, validation and test sets are disjoint sets of binaries (SHA-256
hashes). No sliding window from one execution ever appears on both
sides of a split. `tests/` asserts this on every split file the repo
produces.

**Why.** A row in CIC-YNU-IoTMal is a 20-syscall or 10-packet window cut
from one binary's trace, and neighbouring windows overlap. A random row
split puts near-duplicates in train and test, and the accuracy it
reports measures memorisation of individual binaries. The paper we are
writing measures the gap between the two splits as a result of its own.

**Revisit if** the dataset turns out to lack a per-row hash; then the
fallback is re-running binaries through the published sandbox to
regenerate traces with hashes attached.

## D3: STRACE and PCAP are in scope; SAR is not

The features come from the syscall-window tables and the network-window
tables. The system-activity (SAR) tables are read for verification only.

**Why.** SAR values are CPU, memory and I/O percentages whose scale
depends on how fast QEMU emulates each architecture, so they carry an
architecture signature that would need per-architecture normalisation
against a benign baseline before any cross-architecture claim could rest
on them. The dataset paper also reports SAR as the modality most
sensitive to imbalance handling. Three months and two people do not
cover that work.

**Revisit if** the STRACE and PCAP results leave headroom and a fourth
week opens up.

## D4: Compute is SageMaker AI jobs with managed spot; nothing runs idle

Preprocessing runs as Processing jobs, training as Training jobs with
`use_spot_instances=True` and checkpoints synced to S3. The only
long-lived resource is a JupyterLab space on the smallest instance with
idle shutdown, used for editing and launching.

**Why.** A job bills only while its script runs, so there is no idle
instance to forget. Managed spot returns most of SageMaker's price
premium over EC2. The models are small enough that the cost of the study
is dominated by preprocessing, which is bounded and runs a handful of
times.

**Revisit if** spot capacity for the GPU instance is unavailable for
more than a day during the training weeks; then the final runs go
on-demand and the buffer pays for it.

## D5: A missing syscall count is zero, not the column mean

When a row of `strace.parquet` has no value for a syscall column, we
treat it as zero occurrences in that window.

**Why.** The file was assembled from pieces with different column sets,
so a NaN means the syscall never appeared in the piece the row came
from. The authors' published reader fills these NaNs with the column's
global mean, which writes a dataset-wide statistic into every row and
makes "this syscall did not happen" indistinguishable from "this
syscall happened about as often as usual". Zero is what the tracer
would have recorded.

**Revisit if** the authors publish a different account of how the
pieces were merged.
