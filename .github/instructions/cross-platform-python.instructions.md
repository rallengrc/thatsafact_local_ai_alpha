---
description: 'Mandatory cross-platform standards for all Python files (*.py) in MLaaS across macOS, Linux, and Windows 11. Enforces UTF-8, Path.as_posix(), dynamic venv resolution, and common_platform reuse.'
applyTo: '**/*.py'
---

# Cross-Platform Python Standards (macOS, Linux, Windows 11)

> **Universal Law:** All Python code MUST execute identically across macOS, Linux, and Windows 11 without platform hardcoding or encoding crashes.

1. **Reuse `scripts/common_platform.py`:** Always import `get_repo_root`, `get_venv_python`, `ensure_venv_site_packages`, `normalize_posix_path`, `find_executable`, and `safe_rmtree` instead of rolling custom logic.
2. **Dynamic Repo Anchors:** Never hardcode paths (`/Users/...`, `C:\...`) or assume `os.getcwd()`. Use `get_repo_root(__file__)`.
3. **Mandatory UTF-8:** Always specify `encoding="utf-8", errors="replace"` on `open()`, `.read_text()`, `.write_text()`, and `subprocess.run(text=True)`.
4. **POSIX Path Invariance:** Normalize all relative paths with `.as_posix()` or `normalize_posix_path()`. Never mix backslashes in search keys or SQLite lookups.
5. **Platform-Aware Venv:** Execute through the venv interpreter (`.venv/bin/python3` on Mac/Linux, `.venv\Scripts\python.exe` on Windows). Never use bare `python` or `pip`.
6. **Binary Resolution:** Discover CLI binaries with `find_executable("rg")` (resolves `.exe` on Windows).
7. **Safe Scratch & Cleanup:** Use `tempfile.gettempdir()` for scratch directories and `safe_rmtree()` for cleanup.

📄 **See Also:** [cross-platform-python-standards.md](references/cross-platform-python-standards.md) for detailed code templates and implementation rules.
