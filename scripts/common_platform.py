#!/usr/bin/env python3
"""
common_platform.py — Shared cross-platform utilities for macOS and Windows 11.

Provides standardized platform resolution, virtual environment discovery,
path normalization, permission-safe file operations, and executable lookup.
Uses only Python standard library modules.
"""

from __future__ import annotations

import getpass
import os
import re
import stat
import shutil
import sys
import tempfile
from pathlib import Path


def _is_repo_root(candidate: Path) -> bool:
    return (
        (candidate / ".git").exists()
        or (candidate / ".mcp.json").exists()
        or (candidate / "requirements.txt").exists()
    )


def _env_repo_root() -> Path | None:
    """Return repo root from THESAFACT_AI_ROOT, THESAFACT_LOCAL_AI_ROOT, or MLAAS_ROOT if set and points at a real repo root, else None."""
    for var in ("THESAFACT_AI_ROOT", "THESAFACT_LOCAL_AI_ROOT", "MLAAS_ROOT"):
        raw = os.environ.get(var, "").strip()
        if not raw:
            continue
        candidate = Path(os.path.expandvars(raw)).expanduser()
        try:
            candidate = candidate.resolve()
            if candidate.is_dir() and _is_repo_root(candidate):
                return candidate
        except OSError:
            continue
    return None


def get_repo_root(anchor_file: Path | str | None = None) -> Path:
    """Return the repository root.

    Resolution order: (1) walk up from anchor_file or this file looking for a
    repo marker; (2) the THESAFACT_AI_ROOT, THESAFACT_LOCAL_AI_ROOT, or MLAAS_ROOT
    environment variable, only when the walk finds nothing (e.g. a script copied outside the repo);
    (3) the start path.
    """
    if anchor_file is not None:
        start = Path(anchor_file).resolve()
        if start.is_file() or (not start.is_dir() and bool(start.suffix)):
            start = start.parent
    else:
        # common_platform.py is in scripts/, so repo root is its parent's parent
        start = Path(__file__).resolve().parent

    for candidate in [start, *start.parents]:
        if _is_repo_root(candidate):
            return candidate

    env_root = _env_repo_root()
    if env_root is not None:
        return env_root

    if anchor_file is None:
        return Path(__file__).resolve().parents[1]
    return start


def get_venv_python(repo_root: Path | None = None) -> Path:
    """Return path to virtual environment python executable.

    On win32: .venv/Scripts/python.exe.
    On POSIX (darwin/linux): .venv/bin/python3 (or .venv/bin/python).
    Falls back to Path(sys.executable) if not found.
    """
    if repo_root is None:
        repo_root = get_repo_root()

    if sys.platform == "win32":
        candidate = repo_root / ".venv" / "Scripts" / "python.exe"
    else:
        candidate = repo_root / ".venv" / "bin" / "python3"
        if not candidate.exists():
            candidate = repo_root / ".venv" / "bin" / "python"

    return candidate if candidate.exists() else Path(sys.executable)


def _is_in_sys_path(target: Path) -> bool:
    """Check if target path or an equivalent directory is already in sys.path."""
    target_str = str(target)
    for p in sys.path:
        if p == target_str:
            return True
        try:
            if target.exists() and os.path.exists(p) and os.path.samefile(target, p):
                return True
        except (OSError, ValueError):
            pass
    return False


def ensure_venv_site_packages(repo_root: Path | None = None) -> None:
    """Add virtualenv site-packages to sys.path if existing and not already present."""
    if repo_root is None:
        repo_root = get_repo_root()

    venv = repo_root / ".venv"
    candidates: list[Path] = [
        venv / "Lib" / "site-packages",
        venv / "lib" / "site-packages",
    ]
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}"
    candidates.append(venv / "lib" / f"python{py_ver}" / "site-packages")
    for ver in ["3.14", "3.13", "3.12", "3.11", "3.10", "3.9"]:
        candidates.append(venv / "lib" / f"python{ver}" / "site-packages")

    if (venv / "lib").is_dir():
        try:
            for sp in (venv / "lib").glob("python*/site-packages"):
                if sp not in candidates:
                    candidates.append(sp)
        except OSError:
            pass

    for sp in candidates:
        if sp.exists() and not _is_in_sys_path(sp):
            sys.path.insert(0, str(sp))


def get_current_user(default: str = "user") -> str:
    """Return the current OS user name as a filesystem-safe slug.

    getpass.getuser() reads LOGNAME, USER, LNAME and USERNAME, then the password
    database, so it behaves the same on macOS, Linux and Windows.
    """
    try:
        name = getpass.getuser()
    except (KeyError, OSError, ImportError):
        name = ""
    slug = re.sub(r"[^A-Za-z0-9._-]+", "_", name).strip("._-")
    return slug or default


def get_vscode_user_dir() -> Path:
    """Return OS-specific path to VS Code User data directory."""
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "Code" / "User"
        return Path.home() / "AppData" / "Roaming" / "Code" / "User"
    elif sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Code" / "User"
    else:  # Linux and other POSIX platforms
        return Path.home() / ".config" / "Code" / "User"


def get_copilot_dir() -> Path:
    """Return OS-specific path to Copilot configuration/storage directory."""
    if sys.platform == "win32":
        user_profile = os.environ.get("USERPROFILE")
        if user_profile:
            return Path(user_profile) / ".copilot"
    return Path.home() / ".copilot"


def normalize_posix_path(path: str | Path) -> str:
    """Convert backslashes to forward slashes and return a POSIX-style path string."""
    return str(path).replace("\\", "/")


def _on_rm_error(func, path_str, _exc):
    """Clear read-only attribute on Windows files and retry operation."""
    try:
        os.chmod(path_str, stat.S_IWRITE)
        func(path_str)
    except Exception:
        raise


def safe_rmtree(path: Path | str) -> None:
    """Remove directory tree safely using an onerror callback that clears stat.S_IWRITE on Windows read-only files."""
    target = Path(path)
    if not target.exists() and not target.is_symlink():
        return

    if target.is_file() or target.is_symlink():
        try:
            target.unlink()
        except OSError:
            os.chmod(target, stat.S_IWRITE)
            target.unlink()
        return

    try:
        shutil.rmtree(target, onerror=_on_rm_error)
    except TypeError:
        shutil.rmtree(target, onexc=_on_rm_error)


_FALLBACK_BIN_DIRS = (
    "/opt/homebrew/bin",
    "/usr/local/bin",
    "/home/linuxbrew/.linuxbrew/bin",
    str(Path.home() / ".local" / "bin"),
    str(Path.home() / ".cargo" / "bin"),
)


def find_executable(name: str) -> str | None:
    """Find binary in PATH using shutil.which(name) or shutil.which(f"{name}.exe").

    On win32, if name == "tesseract", also checks C:/Program Files/Tesseract-OCR/tesseract.exe.
    """
    cmd = shutil.which(name)
    if not cmd and not name.lower().endswith(".exe"):
        cmd = shutil.which(f"{name}.exe")

    if not cmd and sys.platform != "win32":
        # GUI-launched clients (VS Code from the Dock, standalone apps) get a minimal PATH without Homebrew.
        cmd = shutil.which(name, path=os.pathsep.join(_FALLBACK_BIN_DIRS))

    if not cmd and sys.platform == "win32":
        base_name = name[:-4].lower() if name.lower().endswith(".exe") else name.lower()
        if base_name == "tesseract":
            default_win = Path("C:/Program Files/Tesseract-OCR/tesseract.exe")
            if default_win.exists():
                return str(default_win)

    return cmd
