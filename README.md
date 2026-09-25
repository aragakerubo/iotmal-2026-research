# iotmal-2026-research

Lightweight neural networks that detect IoT malware on a CPU architecture
they were never trained on, evaluated on the
[CIC-YNU-IoTMal 2026](https://www.unb.ca/cic/datasets/ynu-iot-2026.html)
dataset with hash-grouped, leave-one-architecture-out splits.

## Layout

| Path | Holds |
| --- | --- |
| `src/iotmal/` | The package: paths, data loading, canonicalisation, splits, models |
| `tests/` | pytest suite; `make check` must pass on every branch |
| `scripts/` | One-off scripts run by hand or inside a Processing job |
| `jobs/` | SageMaker job launchers |
| `configs/` | YAML: syscall mappings, sweep definitions |
| `data/` | Small committed artifacts: manifests, column inventories, split files |
| `docs/` | `decisions.md` (the D-numbers), dataset notes, experiment specs |

Raw data is not committed. It lives in the project bucket under
`raw/Yokohama/`.

## Getting started

```bash
python -m venv .venv && source .venv/bin/activate
make install          # package plus dev tools
make check            # ruff and pytest
make install-aws      # on the Studio space: adds boto3, s3fs, sagemaker
```

## How changes arrive

One branch per step, one commit per branch, delivered as a patch and
applied with `git am`; see `docs/decisions.md` D1.
