"""
test_export_memories.py — Workspace hash discovery must not rely on a hard-coded machine-specific ID.
"""

import json
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1]
for p in (str(SCRIPTS_DIR), str(SCRIPTS_DIR / "automation")):
    if p not in sys.path:
        sys.path.insert(0, p)

import export_memories as em


def make_ws(root: Path, name: str, folder_uri: str) -> None:
    d = root / name
    d.mkdir(parents=True)
    (d / "workspace.json").write_text(json.dumps({"folder": folder_uri}), encoding="utf-8")


def test_find_workspace_hash_matches_repo_folder(tmp_path, monkeypatch):
    repo = tmp_path / "my repo"
    repo.mkdir()
    storage = tmp_path / "workspaceStorage"
    make_ws(storage, "aaa111", "file:///somewhere/else")
    make_ws(storage, "bbb222", repo.resolve().as_uri())
    monkeypatch.setattr(em, "WSG", str(storage))
    assert em.find_workspace_hash(repo) == "bbb222"


def test_find_workspace_hash_none_when_absent(tmp_path, monkeypatch):
    monkeypatch.setattr(em, "WSG", str(tmp_path / "missing"))
    assert em.find_workspace_hash(tmp_path) is None


def test_find_workspace_hash_ignores_remote_and_corrupt_entries(tmp_path, monkeypatch):
    storage = tmp_path / "workspaceStorage"
    make_ws(storage, "ccc333", "vscode-remote://ssh-remote+host/home/u/repo")
    bad = storage / "ddd444"
    bad.mkdir()
    (bad / "workspace.json").write_text("{not json", encoding="utf-8")
    monkeypatch.setattr(em, "WSG", str(storage))
    assert em.find_workspace_hash(tmp_path) is None
