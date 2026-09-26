"""Repository paths that are the same wherever a script is run from.

Every script that reads or writes inside the repo goes through these
constants instead of a relative path, so `python scripts/x.py` and
`cd scripts && python x.py` write to the same place. Inside a SageMaker
job the repo root is wherever the source bundle was unpacked, which is
still the parent of this package, so the same constants hold there.
"""

from pathlib import Path

# src/iotmal/paths.py -> src/iotmal -> src -> repo root
REPO_ROOT = Path(__file__).resolve().parent.parent.parent

DATA_DIR = REPO_ROOT / "data"
"""Small, committed data artifacts: manifests, column inventories, split files."""

CONFIG_DIR = REPO_ROOT / "configs"
"""YAML that shapes an experiment: syscall mappings, model and sweep settings."""

DOCS_DIR = REPO_ROOT / "docs"
"""Decision record, dataset notes, experiment specs."""


def ensure_dir(path: Path) -> Path:
    """Create ``path`` (and parents) if missing and return it.

    Used before writing an output so a fresh clone never fails on a
    directory that only exists once something has been written to it.
    """
    path.mkdir(parents=True, exist_ok=True)
    return path
