#!/usr/bin/env python3
"""
Backward-compatible trampoline to scripts/search_router/search_server.py
"""
import os
import sys
from pathlib import Path

_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if _CURRENT_DIR not in sys.path:
    sys.path.insert(0, _CURRENT_DIR)

from common_platform import get_repo_root, get_venv_python

_TARGET = os.path.join(_CURRENT_DIR, "search_router", "search_server.py")

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

