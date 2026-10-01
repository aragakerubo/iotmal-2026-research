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

**Revision (2026-10-01).** The unit of the split is now a behaviour
group rather than a hash: all binaries of one architecture whose summed
canonical syscall vectors are identical go to the same side. The
near-duplicate scan showed that identical traces under different hashes
are common (1,687 ARM benign binaries share one trace; 190 x86 Mirai
binaries share another), and a hash-grouped split would place copies
of the same trace on both sides. Grouping by exact vector subsumes
grouping by hash, since one hash always gives one vector. A group whose
binaries carry more than one label (three signatures on ARM, one on
x86) is set aside as a conflict and neither trained on nor scored. The
assignment is in `configs/split.yaml` and `data/splits/`, and
`tests/test_split.py` asserts that no group and no hash crosses a
split within an architecture.

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

**Note (2026-09-26).** The released STRACE files hold no nulls: the
fill was applied before release. If the row-level scan's fill check
shows a single repeated non-integer value in a `double` count column,
that value is the mean the authors filled with, and this decision is
carried out by mapping that value back to zero rather than by filling
nulls. If the check shows no non-integer values, the release was
zero-filled already and there is nothing to do.

## D6: One syscall vocabulary across architectures, by alias table and prefix rule

Every raw `Call_<syscall>` column is resolved to one of 132 canonical
names or dropped, by `configs/syscall_canonical.yaml` and the rules in
`iotmal.canonical`: an ABI-specific alias (`mmap2`, `fstat64`,
`getuid32`, `_llseek`, `set_tls`, ARM's undecoded `syscall_0x193`) is
summed into its canonical column; a truncated name (`readlin`, `wri`)
is folded into the one canonical name it is a prefix of, and dropped
when it is a prefix of several; every other name is its own canonical
column. A canonical name with no source column on an architecture is
zero there. The per-column outcome is committed in
`data/syscall_resolution.csv`.

**Why.** The four STRACE files have 130 to 135 columns each and 181
distinct names between them, and the differences are almost entirely
naming: the 32-bit ABIs expose the same calls under different entry
points, and a model given the raw columns can tell architectures apart
by which columns are non-zero. The alias table removes the naming
signal so what remains is behaviour. The prefix rule is mechanical so
a reviewer can check every fold; eight fragments fold, fifteen drop,
and the dropped ones are single letters or ambiguous stems whose counts
cannot be attributed.

**What it does not remove.** Forty-odd canonical calls occur on some
architectures and not others (`cacheflush` never on x86, `statx` never
on ARM in this data). Those are real behavioural differences of the
binaries and libcs, not naming, and they stay. Whether a model can
still fingerprint the architecture from them is measured by the
architecture-sanity classifier in the split step.

**Revisit if** the sanity classifier scores far above chance on the
canonical columns; then the semantic-group representation (file,
network, process, memory, time, signal) replaces this vocabulary as the
model input.

## D7: Family classification covers four classes; the rest is a case study

The family experiment uses Benign, Mirai, DarkNexus and Gafgyt. A class
enters only with at least ten distinct binaries on every architecture
it is evaluated on. Generic is excluded as a catch-all label rather than
a family. Tsunami, Agent and Rudedevil are reported as a leakage case
study: under a row-level split a model "learns" a one-binary class by
memorising that binary, which is what the dataset paper's per-class
numbers on these classes measure.

**Why.** Binaries per class in the STRACE files (data/VERIFICATION.md):
Benign 1,980 to 2,617 per architecture, Mirai 1,534 to 2,795, DarkNexus
40 to 91, Gafgyt 5 to 29, Generic 2 to 29, Tsunami 3 (ARM only), Agent
1 (ARM, MIPSEL), Rudedevil 1 (MIPSEL). Gafgyt on ARM has five binaries
and stays in with that caveat stated; anything smaller cannot support
a held-out estimate at all. Binary detection is unaffected: about 7,900
malware binaries against 9,700 benign, of which roughly 7,600 are Mirai,
which the paper states in its abstract.

**Revisit if** a later release of the dataset adds binaries to the
small families.


## D8: Inert executions are excluded, and the ARM sandbox mostly produced them

A binary whose whole trace has fewer than 64 system calls and no
network call (`socket`, `connect`, `bind`, `listen`, `accept`, `send`,
`sendto`, `sendmsg`, `recv`, `recvfrom`, `recvmsg`) is inert: it never
reached its own logic. Inert binaries are excluded from training and
from every metric, and counted per class and architecture in
`data/SPLIT.md`.

**Why.** On ARM, 1,687 of 1,980 benign binaries produced one identical
trace of about 35 calls: a dynamic loader mapping shared libraries,
one `writev` (an error message), and `exit_group`. 560 of 2,795 ARM
Mirai binaries produced another: `execve`, `getpid`, `writev`,
`exit_group`, a statically linked bot that printed and quit. Neither
trace contains behaviour, so a label attached to it is a label on an
exit code, and a model scored on them would be scored on whether it
recognises a loader failure. The other three architectures have no
such groups. The ARM figures the dataset paper reports are therefore
largely measurements of samples that did not run, which the paper we
write states as a finding and the dataset's authors should hear about.

**What it does not settle.** The inert benign trace is a dynamic
loader and the inert Mirai trace has none, which suggests a shortcut
present on every architecture: the generated benign programs were
compiled against OpenWrt's shared libc, while honeypot malware is
mostly statically linked, so the first twenty calls of a trace may
already name the class. The first-window-only baseline in the
experiment list measures this.

**Revisit if** a repaired ARM run of the dataset is released, or if
the first-window baseline shows the threshold of 64 calls cuts into
binaries that did run.