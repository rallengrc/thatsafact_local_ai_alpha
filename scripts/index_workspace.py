#!/usr/bin/env python3
"""
Backward-compatible proxy to scripts/indexing/index_workspace.py
"""
import os
import sys
import importlib.util
from pathlib import Path

_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if _CURRENT_DIR not in sys.path:
    sys.path.insert(0, _CURRENT_DIR)

from common_platform import get_repo_root, get_venv_python, ensure_venv_site_packages

_TARGET = os.path.join(_CURRENT_DIR, "indexing", "index_workspace.py")

if __name__ == "__main__":
    repo_root = get_repo_root(_CURRENT_DIR)
    venv_py = get_venv_python(repo_root)
    venv_dir = repo_root / ".venv"
    if (sys.prefix != str(venv_dir) or ".venv" not in sys.executable) and venv_py.exists() and Path(sys.executable) != venv_py:
        py = str(venv_py)
    else:
        py = sys.executable

    try:
        os.execv(py, [py, _TARGET] + sys.argv[1:])
    except OSError:
        import subprocess
        sys.exit(subprocess.call([py, _TARGET] + sys.argv[1:]))

repo_root = get_repo_root(_CURRENT_DIR)
ensure_venv_site_packages(repo_root)

_INDEXING_DIR = os.path.join(_CURRENT_DIR, "indexing")
for _d in [_INDEXING_DIR, _CURRENT_DIR]:
    if _d not in sys.path:
        sys.path.insert(0, _d)

_spec = importlib.util.spec_from_file_location("index_workspace_impl", _TARGET)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

WorkspaceIndexer = _mod.WorkspaceIndexer
FileInfo = _mod.FileInfo
