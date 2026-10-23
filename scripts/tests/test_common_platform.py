#!/usr/bin/env python3
"""
test_common_platform.py — Unit tests for shared cross-platform utilities.

Tests platform resolution, virtualenv discovery, path normalization,
safe tree removal, and binary discovery across simulated win32, darwin, and linux.
"""

import os
import stat
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Ensure scripts directory is in sys.path
SCRIPTS_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import common_platform
from common_platform import (
    get_current_user,
    ensure_venv_site_packages,
    find_executable,
    get_copilot_dir,
    get_repo_root,
    get_venv_python,
    get_vscode_user_dir,
    normalize_posix_path,
    safe_rmtree,
)

# Test workspace scratch dir located strictly in project workspace (no /tmp)
SCRATCH_BASE = Path(__file__).resolve().parents[2] / ".test_scratch_common_platform"


@pytest.fixture
def scratch_dir():
    """Provide an isolated scratch directory inside the workspace and clean up."""
    if SCRATCH_BASE.exists():
        safe_rmtree(SCRATCH_BASE)
    SCRATCH_BASE.mkdir(parents=True, exist_ok=True)
    yield SCRATCH_BASE
    if SCRATCH_BASE.exists():
        safe_rmtree(SCRATCH_BASE)


# ============================================================================
# 1. get_repo_root
# ============================================================================
class TestGetRepoRoot:
    """Tests for get_repo_root."""

    def test_get_repo_root_default(self):
        """Default call without arguments should return the current repository root."""
        root = get_repo_root()
        assert isinstance(root, Path)
        assert (root / ".git").exists() or (root / "scripts").exists()
        assert root == Path(__file__).resolve().parents[2]

    def test_get_repo_root_with_anchor_file(self):
        """Passing an anchor file should resolve the repo root containing it."""
        root = get_repo_root(anchor_file=Path(__file__))
        assert root == Path(__file__).resolve().parents[2]

    def test_get_repo_root_with_anchor_str(self):
        """Passing an anchor file as string should resolve correctly."""
        root = get_repo_root(anchor_file=str(Path(__file__)))
        assert root == Path(__file__).resolve().parents[2]

    def test_get_repo_root_nested_walk_up(self, scratch_dir):
        """Should walk up from deep nested directory to find directory with .git."""
        fake_repo = scratch_dir / "my_project"
        fake_git = fake_repo / ".git"
        nested_file = fake_repo / "src" / "pkg" / "module.py"

        nested_file.parent.mkdir(parents=True, exist_ok=True)
        fake_git.mkdir(parents=True, exist_ok=True)
        nested_file.write_text("# dummy", encoding="utf-8")

        resolved = get_repo_root(anchor_file=nested_file)
        assert resolved == fake_repo

    def test_get_repo_root_mcp_indicator(self, scratch_dir):
        """Should resolve root when marked by .mcp.json."""
        fake_repo = scratch_dir / "mcp_repo"
        (fake_repo / ".mcp.json").parent.mkdir(parents=True, exist_ok=True)
        (fake_repo / ".mcp.json").write_text("{}", encoding="utf-8")
        sub_file = fake_repo / "deep" / "nested" / "file.py"
        sub_file.parent.mkdir(parents=True, exist_ok=True)
        sub_file.write_text("# py", encoding="utf-8")

        resolved = get_repo_root(anchor_file=sub_file)
        assert resolved == fake_repo

    def test_get_repo_root_requirements_indicator(self, scratch_dir):
        """Should resolve root when marked by requirements.txt."""
        fake_repo = scratch_dir / "req_repo"
        (fake_repo / "requirements.txt").parent.mkdir(parents=True, exist_ok=True)
        (fake_repo / "requirements.txt").write_text("pytest", encoding="utf-8")
        sub_file = fake_repo / "src" / "main.py"
        sub_file.parent.mkdir(parents=True, exist_ok=True)
        sub_file.write_text("# py", encoding="utf-8")

        resolved = get_repo_root(anchor_file=sub_file)
        assert resolved == fake_repo

    def test_get_repo_root_dynamic_beats_env_var(self, tmp_path, monkeypatch):
        """A repo found by walking up wins over MLAAS_ROOT."""
        real = tmp_path / "real"
        other = tmp_path / "other"
        (real / ".git").mkdir(parents=True)
        (other / ".git").mkdir(parents=True)
        anchor = real / "src" / "mod.py"
        anchor.parent.mkdir(parents=True)
        anchor.write_text("# py", encoding="utf-8")
        monkeypatch.setenv("MLAAS_ROOT", str(other))

        assert get_repo_root(anchor_file=anchor) == real

    def test_get_repo_root_env_var_when_walk_fails(self, tmp_path, monkeypatch):
        """THESAFACT_AI_ROOT / MLAAS_ROOT is used only when no marker is found above the anchor."""
        env_repo = tmp_path / "env_repo"
        (env_repo / ".git").mkdir(parents=True)
        anchor = tmp_path / "loose" / "script.py"
        anchor.parent.mkdir(parents=True)
        anchor.write_text("# py", encoding="utf-8")
        monkeypatch.setenv("MLAAS_ROOT", str(env_repo))

        assert get_repo_root(anchor_file=anchor) == env_repo

        # Test THESAFACT_AI_ROOT priority
        alpha_repo = tmp_path / "alpha_repo"
        (alpha_repo / ".git").mkdir(parents=True)
        monkeypatch.setenv("THESAFACT_AI_ROOT", str(alpha_repo))
        assert get_repo_root(anchor_file=anchor) == alpha_repo

    def test_get_repo_root_env_var_without_markers_is_ignored(self, tmp_path, monkeypatch):
        """A MLAAS_ROOT that is not a repo root must not be trusted."""
        bogus = tmp_path / "bogus"
        bogus.mkdir()
        anchor = tmp_path / "loose" / "script.py"
        anchor.parent.mkdir(parents=True)
        anchor.write_text("# py", encoding="utf-8")
        monkeypatch.setenv("MLAAS_ROOT", str(bogus))

        assert get_repo_root(anchor_file=anchor) == anchor.parent

    def test_get_repo_root_fallback_when_no_indicator(self):
        """Should fall back to start directory if no git/mcp indicators found."""
        anchor = Path("/mock_isolated/sub/script.py")
        with patch.object(Path, "exists", return_value=False):
            resolved = get_repo_root(anchor_file=anchor)
            assert resolved == Path("/mock_isolated/sub")


# ============================================================================
# 2. get_venv_python
# ============================================================================
class TestGetVenvPython:
    """Tests for get_venv_python across win32 and posix."""

    def test_win32_scripts_python_exists(self, scratch_dir):
        """On win32, returns .venv/Scripts/python.exe if it exists."""
        fake_root = scratch_dir / "repo_win"
        py_exe = fake_root / ".venv" / "Scripts" / "python.exe"
        py_exe.parent.mkdir(parents=True, exist_ok=True)
        py_exe.write_text("", encoding="utf-8")

        with patch("sys.platform", "win32"):
            result = get_venv_python(fake_root)
            assert result == py_exe

    def test_win32_fallback_to_sys_executable(self, scratch_dir):
        """On win32, if .venv/Scripts/python.exe does not exist, fall back to sys.executable."""
        fake_root = scratch_dir / "repo_win_empty"
        fake_root.mkdir(parents=True, exist_ok=True)

        with patch("sys.platform", "win32"):
            result = get_venv_python(fake_root)
            assert result == Path(sys.executable)

    def test_posix_bin_python3_exists(self, scratch_dir):
        """On darwin/linux, returns .venv/bin/python3 if it exists."""
        fake_root = scratch_dir / "repo_posix"
        py3 = fake_root / ".venv" / "bin" / "python3"
        py3.parent.mkdir(parents=True, exist_ok=True)
        py3.write_text("", encoding="utf-8")

        with patch("sys.platform", "darwin"):
            result = get_venv_python(fake_root)
            assert result == py3

    def test_posix_bin_python_fallback_exists(self, scratch_dir):
        """On darwin/linux, if python3 does not exist but python exists, returns .venv/bin/python."""
        fake_root = scratch_dir / "repo_posix_py"
        py = fake_root / ".venv" / "bin" / "python"
        py.parent.mkdir(parents=True, exist_ok=True)
        py.write_text("", encoding="utf-8")

        with patch("sys.platform", "linux"):
            result = get_venv_python(fake_root)
            assert result == py

    def test_posix_fallback_to_sys_executable(self, scratch_dir):
        """On posix, if neither exists, fall back to sys.executable."""
        fake_root = scratch_dir / "repo_posix_empty"
        fake_root.mkdir(parents=True, exist_ok=True)

        with patch("sys.platform", "darwin"):
            result = get_venv_python(fake_root)
            assert result == Path(sys.executable)

    def test_default_repo_root_used_when_none(self):
        """When repo_root is None, uses get_repo_root()."""
        # Under active repo, .venv/bin/python3 or python exists
        result = get_venv_python(None)
        assert isinstance(result, Path)
        assert result.exists()


# ============================================================================
# 3. ensure_venv_site_packages
# ============================================================================
class TestEnsureVenvSitePackages:
    """Tests for ensure_venv_site_packages."""

    def test_windows_lib_site_packages(self, scratch_dir):
        """Windows .venv/Lib/site-packages should be added to sys.path."""
        fake_root = scratch_dir / "repo_sp_win"
        sp = fake_root / ".venv" / "Lib" / "site-packages"
        sp.mkdir(parents=True, exist_ok=True)

        sp_str = str(sp)
        if sp_str in sys.path:
            sys.path.remove(sp_str)

        ensure_venv_site_packages(fake_root)
        assert sp_str in sys.path
        assert sys.path[0] == sp_str

        # Calling again should not duplicate
        ensure_venv_site_packages(fake_root)
        assert sys.path.count(sp_str) == 1

        sys.path.remove(sp_str)

    def test_unix_versioned_lib_site_packages(self, scratch_dir):
        """Unix .venv/lib/python*/site-packages should be added to sys.path."""
        fake_root = scratch_dir / "repo_sp_unix"
        sp = fake_root / ".venv" / "lib" / "python3.14" / "site-packages"
        sp.mkdir(parents=True, exist_ok=True)

        sp_str = str(sp)
        if sp_str in sys.path:
            sys.path.remove(sp_str)

        ensure_venv_site_packages(fake_root)
        assert sp_str in sys.path
        assert sys.path[0] == sp_str

        sys.path.remove(sp_str)

    def test_nonexistent_site_packages_ignored(self, scratch_dir):
        """Non-existent candidate folders must not be added to sys.path."""
        fake_root = scratch_dir / "repo_sp_none"
        fake_root.mkdir(parents=True, exist_ok=True)

        before = list(sys.path)
        ensure_venv_site_packages(fake_root)
        assert sys.path == before


# ============================================================================
# 4. get_vscode_user_dir
# ============================================================================
class TestGetVscodeUserDir:
    """Tests for get_vscode_user_dir."""

    def test_win32_with_appdata(self):
        """On win32 with APPDATA env set, uses APPDATA / Code / User."""
        custom_appdata = "D:\\AppData\\Roaming"
        with patch("sys.platform", "win32"), patch.dict(os.environ, {"APPDATA": custom_appdata}):
            expected = Path(custom_appdata) / "Code" / "User"
            assert get_vscode_user_dir() == expected

    def test_win32_with_empty_appdata(self):
        """On win32 with empty APPDATA, falls back to home."""
        with patch("sys.platform", "win32"), patch.dict(os.environ, {"APPDATA": ""}):
            expected = Path.home() / "AppData" / "Roaming" / "Code" / "User"
            assert get_vscode_user_dir() == expected

    def test_win32_without_appdata(self):
        """On win32 without APPDATA env, falls back to home / AppData / Roaming / Code / User."""
        env = dict(os.environ)
        env.pop("APPDATA", None)
        with patch("sys.platform", "win32"), patch.dict(os.environ, env, clear=True):
            expected = Path.home() / "AppData" / "Roaming" / "Code" / "User"
            assert get_vscode_user_dir() == expected

    def test_darwin(self):
        """On darwin, uses ~/Library/Application Support/Code/User."""
        with patch("sys.platform", "darwin"):
            expected = Path.home() / "Library" / "Application Support" / "Code" / "User"
            assert get_vscode_user_dir() == expected

    def test_linux(self):
        """On linux, uses ~/.config/Code/User."""
        with patch("sys.platform", "linux"):
            expected = Path.home() / ".config" / "Code" / "User"
            assert get_vscode_user_dir() == expected


# ============================================================================
# 5. get_copilot_dir
# ============================================================================
class TestGetCopilotDir:
    """Tests for get_copilot_dir."""

    def test_win32_with_userprofile(self):
        """On win32 with USERPROFILE env, uses USERPROFILE / .copilot."""
        custom_profile = "C:\\Users\\MockUser"
        with patch("sys.platform", "win32"), patch.dict(os.environ, {"USERPROFILE": custom_profile}):
            expected = Path(custom_profile) / ".copilot"
            assert get_copilot_dir() == expected

    def test_win32_with_empty_userprofile(self):
        """On win32 with empty USERPROFILE, falls back to Path.home() / .copilot."""
        with patch("sys.platform", "win32"), patch.dict(os.environ, {"USERPROFILE": ""}):
            expected = Path.home() / ".copilot"
            assert get_copilot_dir() == expected

    def test_win32_without_userprofile(self):
        """On win32 without USERPROFILE env, falls back to Path.home() / .copilot."""
        env = dict(os.environ)
        env.pop("USERPROFILE", None)
        with patch("sys.platform", "win32"), patch.dict(os.environ, env, clear=True):
            expected = Path.home() / ".copilot"
            assert get_copilot_dir() == expected

    def test_darwin_and_posix(self):
        """On darwin/posix, uses Path.home() / .copilot."""
        with patch("sys.platform", "darwin"):
            expected = Path.home() / ".copilot"
            assert get_copilot_dir() == expected


# ============================================================================
# 6. normalize_posix_path
# ============================================================================
class TestNormalizePosixPath:
    """Tests for normalize_posix_path."""

    def test_converts_windows_backslashes(self):
        """Converts backslashes to forward slashes."""
        raw = r"scripts\automation\probe.py"
        assert normalize_posix_path(raw) == "scripts/automation/probe.py"

    def test_handles_windows_drive_letters(self):
        """Converts Windows drive paths with backslashes."""
        raw = r"C:\Projects\mlaas\scripts\search_server.py"
        assert normalize_posix_path(raw) == "C:/Projects/mlaas/scripts/search_server.py"

    def test_preserves_posix_paths(self):
        """Leaves already posix paths unchanged."""
        raw = "scripts/search_router/livetext.py"
        assert normalize_posix_path(raw) == raw

    def test_accepts_path_object(self):
        """Works seamlessly when passed a Path instance."""
        p = Path("foo") / "bar" / "baz.txt"
        assert normalize_posix_path(p) == "foo/bar/baz.txt"


# ============================================================================
# 7. safe_rmtree
# ============================================================================
class TestSafeRmtree:
    """Tests for safe_rmtree."""

    def test_removes_normal_directory(self, scratch_dir):
        """Removes a normal directory tree."""
        target_dir = scratch_dir / "to_delete"
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / "file.txt").write_text("hello", encoding="utf-8")
        (target_dir / "subdir").mkdir()
        (target_dir / "subdir" / "nested.txt").write_text("nested", encoding="utf-8")

        assert target_dir.exists()
        safe_rmtree(target_dir)
        assert not target_dir.exists()

    def test_removes_readonly_file(self, scratch_dir):
        """Removes directory containing read-only file (clears stat.S_IWRITE)."""
        target_dir = scratch_dir / "readonly_test"
        target_dir.mkdir(parents=True, exist_ok=True)
        ro_file = target_dir / "locked.txt"
        ro_file.write_text("locked", encoding="utf-8")

        # Set read-only bit
        os.chmod(ro_file, stat.S_IREAD)

        safe_rmtree(target_dir)
        assert not target_dir.exists()

    def test_nonexistent_path_no_error(self, scratch_dir):
        """Calling safe_rmtree on non-existent path is a silent no-op."""
        missing = scratch_dir / "does_not_exist"
        safe_rmtree(missing)  # Should not raise

    def test_single_file_removal(self, scratch_dir):
        """If called on a file, safely removes it."""
        single_file = scratch_dir / "standalone.txt"
        single_file.write_text("data", encoding="utf-8")
        safe_rmtree(single_file)
        assert not single_file.exists()

    def test_symlink_removal(self, scratch_dir):
        """Removes a symlink without deleting target file or directory."""
        target_file = scratch_dir / "real_file.txt"
        target_file.write_text("real content", encoding="utf-8")
        link_file = scratch_dir / "symlink.txt"
        try:
            link_file.symlink_to(target_file)
        except OSError:
            pytest.skip("Symlink creation not supported in this environment")

        assert link_file.is_symlink()
        safe_rmtree(link_file)
        assert not link_file.exists()
        assert target_file.exists()


# ============================================================================
# 8. find_executable
# ============================================================================
class TestFindExecutable:
    """Tests for find_executable."""

    def test_finds_in_path(self):
        """Finds a standard executable present in PATH."""
        with patch("shutil.which", return_value="/usr/local/bin/rg"):
            assert find_executable("rg") == "/usr/local/bin/rg"

    def test_gui_launch_path_falls_back_to_package_manager_dirs(self, tmp_path):
        """A GUI-launched client has a minimal PATH; common bin dirs are still searched."""
        fake = tmp_path / "rg"
        fake.write_text("#!/bin/sh\n", encoding="utf-8")
        fake.chmod(0o755)
        with patch("sys.platform", "darwin"), patch("shutil.which", side_effect=lambda cmd, path=None: str(fake) if path and str(tmp_path) in path else None):
            with patch("common_platform._FALLBACK_BIN_DIRS", (str(tmp_path),)):
                assert find_executable("rg") == str(fake)

    def test_finds_with_exe_appended(self):
        """Finds executable when name.exe is found by shutil.which."""
        def mock_which(cmd):
            if cmd == "rg.exe":
                return "C:\\bin\\rg.exe"
            return None

        with patch("shutil.which", side_effect=mock_which):
            assert find_executable("rg") == "C:\\bin\\rg.exe"

    def test_finds_with_exe_already_supplied(self):
        """Finds executable when name already has .exe."""
        with patch("shutil.which", return_value="C:\\bin\\rg.exe"):
            assert find_executable("rg.exe") == "C:\\bin\\rg.exe"

    def test_win32_tesseract_exe_default_path(self):
        """On win32, if tesseract.exe not in PATH, checks Program Files default."""
        with patch("sys.platform", "win32"), patch("shutil.which", return_value=None):
            with patch.object(Path, "exists", return_value=True):
                res = find_executable("tesseract.exe")
                assert res == "C:/Program Files/Tesseract-OCR/tesseract.exe"

    def test_win32_tesseract_default_path(self):
        """On win32, if tesseract not in PATH, checks Program Files default."""
        with patch("sys.platform", "win32"), patch("shutil.which", return_value=None):
            with patch.object(Path, "exists", return_value=True):
                res = find_executable("tesseract")
                assert res == "C:/Program Files/Tesseract-OCR/tesseract.exe"

    def test_win32_tesseract_not_found(self):
        """On win32, if tesseract not in PATH and not in Program Files, returns None."""
        with patch("sys.platform", "win32"), patch("shutil.which", return_value=None):
            with patch.object(Path, "exists", return_value=False):
                assert find_executable("tesseract") is None

    def test_not_found_returns_none(self):
        """Returns None when binary cannot be located."""
        with patch("shutil.which", return_value=None):
            assert find_executable("completely_nonexistent_bin_xyz") is None


class TestGetCurrentUser:
    def test_returns_getpass_user(self):
        with patch("getpass.getuser", return_value="alice"):
            assert get_current_user() == "alice"

    def test_slugifies_unsafe_characters(self):
        with patch("getpass.getuser", return_value="DOMAIN\\Bob Smith"):
            assert get_current_user() == "DOMAIN_Bob_Smith"

    def test_falls_back_to_default_when_lookup_fails(self):
        with patch("getpass.getuser", side_effect=KeyError("no user")):
            assert get_current_user() == "user"
            assert get_current_user(default="dev") == "dev"

    def test_empty_name_uses_default(self):
        with patch("getpass.getuser", return_value="..."):
            assert get_current_user() == "user"
