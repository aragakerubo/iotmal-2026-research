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

**Revision (2026-10-05).** The code is now written in the repository's
own checkout on the Studio space, so the patch file is no longer the
carrier; the branch is. Everything else stands: one step per branch,
one commit per branch, `make check` green before push, a write-up per
step, squash-merge by a human. `CLAUDE.md` holds the working agreement.

**Revision (2026-10-07).** A coding session asks a researcher before it
pushes a branch. On a yes it pushes and opens the pull request with the
GitHub CLI (`gh`); it squash-merges and deletes the branch only after a
second yes, and a researcher may still merge on GitHub instead. Pushing
publishes the work and merging changes `main`, so each needs a person's
say-so. The 17 branches merged before this revision were never deleted.

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
grouping by hash, since one hash always gives one vector. A group that
holds both benign and malicious binaries is set aside as a conflict and
neither trained on nor scored; two malware labels on one trace (190 x86
Mirai binaries share theirs with one labelled Generic) agree on the
detection target and stay in. After inert binaries are removed no
conflict remains on any architecture. The
assignment is in `configs/split.yaml` and `data/splits/`, and
`tests/test_split.py` asserts that no group and no hash crosses a
split within an architecture.

**Revision (2026-10-05).** A group whose binaries carry two malware
families is dealt once, under the family that holds most of its
binaries. The deal is stratified by family, and the 190 Mirai and one
Generic binary that share one x86 trace were dealt separately, once in
each family; they agreed by chance until the inert correction in D8
shifted the random draws, after which the check refused the split.

**Revision (2026-10-05, second).** Each architecture's family is dealt
with its own random generator, seeded from the configured seed and a
CRC-32 of `arch/family`. Until now every family drew from one stream in
the order the families first appeared, so a change to one family
re-dealt the families after it. Regenerating the split under this rule
re-dealt every family once more. Leave-one-architecture-out MCC on ARM
moved from 0.956 to 0.940 on the same test binaries, which puts the
split's own draw-to-draw variation on ARM at about two MCC points.

**Revision (2026-10-07).** A behaviour group's id is now a 64-bit
BLAKE2b checksum of the binary's summed count vector, computed with
Python's standard library (`dedup.stable_hash`). It used polars'
`hash()`, which polars does not keep stable between versions; when the
Studio space was reinstalled with polars 2.0 every group id changed, and
because groups are dealt in id order, about 40 percent of binaries
changed side with no change to the data. The split was regenerated once
on the new ids, and rebuilding it under polars 1.44 gives the same
files. The profile signature is now built from integer hundredths
rounded half up, for the same reason. The re-deal moved ARM's
in-architecture MCC from 1.000 to 0.934 and its leave-one-out MCC from
0.940 to 0.969, which is the size of draw noise on a fold with 30
benign test binaries.

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

**Why.** On ARM, 1,830 of 1,980 benign binaries, 1,212 of 2,795 Mirai
binaries and 50 of 91 DarkNexus binaries are inert under this rule,
against at most 7 percent of any class on the other three
architectures (`data/SPLIT.md`). The two largest identical groups show what the inert
traces are. 1,687 of the benign binaries produced one identical trace
of 16 calls: a dynamic loader mapping shared libraries,
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

**Revision (2026-10-05).** The rule is unchanged; its arithmetic was
wrong. A binary with `w` STRACE rows made `w` calls, not `w + 19`
(`docs/dataset_notes.md`, "Rows grow, then slide"), so the code
treated a trace of 45 to 63 calls as 64 or more and kept it live.
Applied as written, the rule sets aside 25 more benign binaries: MIPS
goes from 8 to 16 inert, MIPSEL from 6 to 15, x86 from 8 to 16. ARM and
every malware class are unchanged. The splits and the baseline were
regenerated in `fix/trace-length`.
## D9: One evaluation protocol for every model, with the whole held-out architecture as the test set

Every model, from the XGBoost reference in `iotmal.baseline` to the
neural models that follow, is scored under the same three experiments
on the per-binary unit. In-architecture trains on one architecture's
`train` binaries, stops early on its `val` binaries and scores its
`test` binaries. Leave-one-architecture-out trains on the `train`
binaries of three architectures, stops early on their `val` binaries,
and scores every live binary of the fourth. Architecture-sanity trains
a classifier to name the architecture from the same features and
reports its accuracy against the majority share. Each detection fold
is reported per binary and per behaviour group, where binaries with
one exact syscall vector count once with their mean score. The
metrics are accuracy, macro-F1, MCC and AUROC, with the test set's
majority share printed beside them as chance.

**Why.** A binary the split labels `test` is unseen in every
experiment, so the in-architecture and cross-architecture numbers for
one architecture are scored on populations that overlap and the gap
between them is the paper's result rather than an artefact of
different test sets. Scoring the whole held-out architecture rather
than its `test` column is what makes the ARM fold usable: ARM has 150
live benign binaries in total (D8), and a fifth of them would not
support an estimate. Training on the other architectures' `train` and
`val` rows only, rather than on everything, costs about a fifth of the
training data and buys the comparability above. The group view exists
because 190 identical x86 Mirai builds would otherwise count 190 times
in one test set and once in the training set of every other fold.

**Revisit if** a model's `val` behaviour on three architectures proves
a poor guide to stopping on the fourth; then the stopping rule, not the
test set, changes.

**Revision (2026-10-05).** Accuracy, macro-F1 and MCC are taken at the
decision threshold that maximises MCC on the fold's own `val` binaries:
for leave-one-architecture-out, the training architectures' `val`
binaries, so the held-out architecture never sets its own cut-off.
Candidates are the midpoints between consecutive distinct validation
scores, and ties go to the one closest to 0.5. MCC at the fixed 0.5
is reported beside it, and the chosen threshold is recorded per fold.
The change was made because the first-window model ranks every ARM
binary correctly when ARM is held out (AUROC 1.000) and still scores
MCC 0 at 0.5, with ARM benign binaries between 0.58 and 0.72. The rule
does not repair that fold: the training architectures' validation
binaries are cleanly separated around 0.5, so every chosen threshold
lies between 0.49 and 0.69 on the leave-one-out folds, and ARM's MCC is
unchanged. A threshold learned without the held-out architecture cannot
know that its scores are shifted; the ranking transfers across
architectures and the score scale does not, which the paper reports.

## D10: H3 is measured on sampled single windows, three splits, five seeds

The leakage experiment (H3) scores single STRACE rows, the unit the
dataset paper classified, and compares three splits of the same rows
within each architecture: row-random, as the paper split them;
hash-grouped, which keeps each binary on one side (the original D2);
and behaviour-grouped, the committed split (D2 revised). Rows are drawn
per binary up to a cap of 100, uniformly with a seed, in two units:
`mid`, rows 21 on, which hold no program start-up, and `all`, every
row. Five seeds vary the sample and the row-random split; a cap of 25
on the first seed checks that the result does not depend on the cap.
Each fold is scored per window, per binary and per behaviour group,
with the model and threshold rule of D9. `configs/leakage.yaml` holds
the settings and `docs/experiment_h3_leakage.md` the reasoning.

**Why.** On the per-binary feature store the grouped split already
scores MCC 0.995 to 1.000, so a gap measured there is pinned at zero by
the ceiling. Single windows are the paper's unit, and mid-trace windows
remove the start-up shortcut the first-window experiments found. The
cap keeps the longest Mirai binaries from dominating and makes the
experiment fit the notebook. Hash-grouped sits between the other two
so the leak through a binary's own rows and the leak through identical
binaries are measured separately. Five seeds, because the split's own
draw-to-draw variation (D2) is about the size of the effect expected.

**Revisit if** the gap depends on the cap, or family classification
(D7) is run, which the spec defers to week 8.
