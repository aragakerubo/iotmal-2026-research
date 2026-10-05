# Working in this repository

Read this before touching anything. It is the handover from the chat
thread that built steps 1 to 10, and it is how the two researchers on
this project expect every change to arrive.

## What the project is

Cross-architecture IoT malware detection on CIC-YNU-IoTMal 2026: can a
small model trained on three CPU architectures detect malware on a
fourth it has never seen. The plan of record is `docs/plans/plan.md`
(read its change log first), the numbered decisions are
`docs/decisions.md` (cite them as D1, D2 and so on; never renumber),
and what the data files actually contain is `docs/dataset_notes.md`.
When a change touches a decision, status, date or risk, edit
`docs/plans/plan.md` in the same commit and add a change-log row.

## Where things run

This repository is checked out on a SageMaker Studio JupyterLab space.
The raw parquet is in S3 under `raw/Yokohama/` and is read with
`pyarrow.fs` (never s3fs; its aiobotocore pin conflicts with the boto3
that sagemaker wants). The per-binary feature store is
`data/binaries/*_strace.parquet` locally and
`features/binaries/` in the bucket; it is gitignored. Scans over the
raw files take ten to twenty minutes and read every row once, so run
them on purpose, not casually. Python is 3.12 or later. Install with
`make install-aws` here, `make install` elsewhere.

## How a change is made

One step at a time, small enough to review in one sitting. Each step
is its own branch named `feat/<slug>`, `fix/<slug>`, `chore/<slug>` or
`docs/<slug>`, carrying exactly one commit. Before committing, run
`make check` (ruff lint, ruff format check, pytest) and make it green.
Then push the branch; a human squash-merges it into `main`. Never
commit to `main` directly, never force-push, never rewrite a pushed
branch.

The commit subject is a Conventional Commit:
`type(scope): imperative summary`. The body says what changed and why
in a few sentences, then ends with a line of the form
`Files: N (up X). Tests: N (up Y). D# added|revised|unchanged.` where
the counts are `git ls-files | wc -l` and the pytest total.

## How code is written

Every module and every public function has a docstring that says what
it is for and the one or two facts a reader needs. Comments explain
the data or the decision, not the syntax. Ruff enforces `E`, `F`, `I`
and `D` at line length 100; tests are exempt from `D` because their
names are the documentation. Polars for frames, pyarrow for parquet
and S3, YAML in `configs/` for anything a reader might want to change
without reading code, with a comment block at the top of each YAML
explaining every key.

Tests come with the code, in `tests/test_<module>.py`, on small
synthetic frames built in the test file. A new rule gets a test that
fails without it: prove it by breaking the rule once, watching the
test fail, and restoring it. Coverage of `src/iotmal/` is reported by
`make coverage`; the S3 branches are the only accepted gaps.

## The write-up

Every step ships with a markdown write-up beside the code, delivered to
the other researcher, in this order: branch name, which decisions it
traces to, file and test counts at the end of the step, coverage, new
dependencies if any; what the step does and why, with every assumption
stated and every deviation from what was promised flagged; the
essential code (Green); the tests as a table of name and what it holds
(Red); a walkthrough of what to run and what to expect; the break test
and its output; the file list; the commit subject; a summary that ends
by naming the next step. Prose, not bullet fragments. No em-dashes. No
contrastive framing ("not X but Y"). Define a technical term in the
sentence that first uses it.

## What is settled and what is open

Settled: splits are by behaviour group within an architecture, inert
binaries (fewer than 64 calls, no network call) are excluded, the
evaluation unit is the binary, test binaries are unseen in every
experiment, leave-one-architecture-out scores the whole held-out
architecture (D2, D8, D9). The XGBoost baselines in `data/BASELINE.md`
transfer almost perfectly across architectures, which means the
dataset's benign class is probably separable by a shortcut. The
first-window experiments (`feat/first-window`,
`feat/first-window-prefix`) measured it: each binary's first ten system
calls alone match the whole trace on every fold, the network calls play
no part, and after five calls every benign binary on an architecture
has one identical window (`data/FIRST_WINDOW.md`, `docs/dataset_notes.md`).

Open: the device budget and the ARM board, the venue, the semantic
syscall groups (`configs/syscall_groups.yaml`), the leakage experiment
spec (`docs/experiment_h3_leakage.md`), and whether the paper's claim
is the lightweight model or the benchmark critique. Do not settle an
open question on your own; write the options into the write-up and
ask.

## Working style

Dissect the request before acting and state the interpretation you
took. If more than one reading exists, present them. If something is
unclear, stop and ask rather than guess. If a simpler approach exists,
say so, and push back when a request looks like a mistake. State
assumptions explicitly. No emojis.
