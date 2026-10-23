---
name: cross-platform-python
description: "Author, audit, and verify Python for macOS, Linux and Windows 11 compatibility (UTF-8, as_posix paths, venv resolution, common_platform reuse). TRIGGERS: 'cross-platform', 'windows compatibility', 'fix windows', 'mac and windows'."
---

# Cross-Platform Python (macOS & Windows 11)

> **Universal Law:** All Python scripts must execute identically on macOS, Linux, and Windows 11 without platform crashes, missing encodings, or slash mismatches.

---

## ⚡ Quick Dispatch & Audit Checklist

When authoring or reviewing any Python code:

| Area | Anti-Pattern (Fails on Windows) | Compliant Solution |
|---|---|---|
| **Platform Utility** | Rewriting platform branches | `from common_platform import ...` |
| **Repo Root Anchor** | `os.getcwd()` or hardcoded `/Users/...` | `get_repo_root(__file__)` or `Path(__file__).resolve().parents[n]` |
| **File I/O** | `open(f, "r")` or `read_text()` | `open(f, "r", encoding="utf-8", errors="replace")` |
| **Subprocesses** | `subprocess.run(..., text=True)` | `subprocess.run(..., text=True, encoding="utf-8", errors="replace")` |
| **Path Invariance** | `str(path.relative_to(root))` | `path.relative_to(root).as_posix()` or `normalize_posix_path(p)` |
| **Repo Root / Links** | `"/Users/<name>/mlaas"` or absolute markdown links | Relative links in docs; `get_repo_root(__file__)` in code; `MLAAS_ROOT` env var only as last resort |
| **Virtualenv Python** | `.venv/bin/python3` | `get_venv_python()` (.venv/Scripts/python.exe on win32) |
| **Site-Packages** | `lib/python{ver}/site-packages` | `ensure_venv_site_packages()` (adds Lib/site-packages) |
| **CLI Binaries** | Bare `"rg"` or `"tesseract"` | `find_executable("rg")` (checks .exe and Program Files) |
| **User Data Dirs** | `~/Library/Application Support/Code/User` | `get_vscode_user_dir()`, `get_copilot_dir()` |
| **Temp Scratch** | Hardcoded `f"/tmp/{slug}"` | `Path(tempfile.gettempdir()) / slug` |
| **Directory Cleanup**| Bare `shutil.rmtree(dir)` | `safe_rmtree(dir)` (clears `stat.S_IWRITE` on read-only files) |
| **Trampolines** | Bare `os.execv(...)` | `try: os.execv(...) except OSError: sys.exit(subprocess.call(...))` |

---

## 🛠️ Verification & Test Protocol

Run test validation using the platform virtualenv:

```bash
# macOS / Linux
.venv/bin/python3 -m pytest scripts/tests/ -v

# Windows 11 (PowerShell / Command Prompt)
.venv\Scripts\python.exe -m pytest scripts\tests\ -v
```

---

## 📄 See Also

- 📄 [rules-and-patterns.md](./references/rules-and-patterns.md) — Detailed code patterns, Windows failure modes, and contributor implementation lessons.
- 📄 [common_platform.py](../../../scripts/common_platform.py) — Zero-dependency cross-platform utility implementation.
- 📄 [CROSS_PLATFORM_PLAN.md](../../../scripts/CROSS_PLATFORM_PLAN.md) — Comprehensive 50-script modernization plan and audit catalog.
- 📄 [cross-platform-python.instructions.md](../../instructions/cross-platform-python.instructions.md) — Auto-applying rules for all `**/*.py` files.
