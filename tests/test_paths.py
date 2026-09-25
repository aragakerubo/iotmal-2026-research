"""The path constants point at the repo, not at the working directory."""

import os
from pathlib import Path

from iotmal import paths


def test_repo_root_is_the_directory_holding_pyproject():
    assert (paths.REPO_ROOT / "pyproject.toml").is_file()
    assert (paths.REPO_ROOT / "src" / "iotmal").is_dir()


def test_the_named_directories_hang_off_the_root():
    assert paths.DATA_DIR == paths.REPO_ROOT / "data"
    assert paths.CONFIG_DIR == paths.REPO_ROOT / "configs"
    assert paths.DOCS_DIR == paths.REPO_ROOT / "docs"


def test_the_root_does_not_move_with_the_working_directory(tmp_path, monkeypatch):
    before = paths.REPO_ROOT
    monkeypatch.chdir(tmp_path)
    assert Path(os.getcwd()) == tmp_path
    assert paths.REPO_ROOT == before


def test_ensure_dir_creates_missing_parents_and_is_idempotent(tmp_path):
    target = tmp_path / "a" / "b" / "c"
    assert paths.ensure_dir(target) == target
    assert target.is_dir()
    assert paths.ensure_dir(target) == target  # second call is a no-op
