# Week 1

Written 2026-09-20, closed out 2026-09-28, moved into the repository 2026-10-05.

Week 1 ran 2026-09-22 to 2026-09-28. Closed out 2026-09-28: the Researcher A and B tracks were dropped after day two, since all code and reasoning flow through one thread and land in the repository as one patch per step (D1). This file is the record of what happened and what carried over.

## What landed

Six repository steps, each a branch, one commit, a write-up and `make check` green, squash-merged to `main`.

| Step | Branch | What it settled |
| --- | --- | --- |
| 1 | `chore/scaffold` | Package, `make check`, D1 to D4 |
| 2 | `feat/manifest` | Footer scan of all 12 files; Unknown counted per file; the authors' `combined.csv` reproduces Table 5; D5 |
| 3 | `feat/verify` | Row-level scan: hash on every row, every binary one block in every file, class counts, no nulls in STRACE |
| 4 | `feat/verify-fill` | Binaries per class; no mean-fill in the release (D5 needs no code); rows per binary 3 to 184,253 |
| 5 | `feat/canonical` | 181 raw syscall names to 132 canonical columns by alias table and prefix rule; D6 |
| 6 | `feat/dedup` | Per-binary feature store and three duplicate signatures; D7 (four family classes) |

Infrastructure: budget alarms, IAM users, execution role, S3 bucket with the data under `raw/Yokohama/`, Studio domain and JupyterLab space. Every scan so far ran on the notebook; no SageMaker job has been needed yet.

## Exit criteria, as they stood on Friday

- [x] Budget alarms in place.
- [x] All twelve parquet files in S3 with sizes and row counts in `data/MANIFEST.md`.
- [x] `data/VERIFICATION.md`: hash present, contiguous, Unknown per file, binaries per class.
- [x] `configs/syscall_canonical.yaml` covers every raw column; `make check` passes.
- [ ] `data/pcap_columns.csv` with a keep decision per column. Superseded: the released PCAP features carry no address, port or hostname, so the decision reduces to an ablation of `DNS` and `Time_To_Live`, recorded in `docs/dataset_notes.md`.
- [ ] Device budget written into Scope with the ARM board named. Carried over.
- [ ] Venue chosen, deadline and page limit written into Scope. Carried over.
- [x] Space stopped between sessions; spend under $15.

## Carried into week 2

Four items from the original B track that are not yet in the repository, to be delivered as one documentation step: the device budget (needs the ARM board), the venue shortlist, `configs/syscall_groups.yaml` (the semantic-group mapping over the 132 canonical names), and `docs/experiment_h3_leakage.md` (the protocol for the leakage experiment). Plus the near-duplicate scan results from step 6, which decide the grouping key for the split.
