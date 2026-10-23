---
description: 'Mandatory cross-platform standards for all Python files (*.py) in MLaaS across macOS, Linux, and Windows 11. Enforces UTF-8 encoding, Path.as_posix() invariance, dynamic venv resolution, temp directories, safe file permissions, and scripts/common_platform.py reuse.'
applyTo: '**/*.py'
---

# Cross-Platform Python Standards (macOS, Linux, Windows 11)

> **Universal Law:** All Python code in this repository MUST execute identically across macOS, Linux, and Windows 11 with zero platform-specific hardcoding, zero encoding crashes, and zero path delimiter discrepancies.

---

## 1. Always Reuse `scripts/common_platform.py`

Whenever authoring or editing Python scripts in [scripts/](../../scripts), import standard utilities from [common_platform.py](../../scripts/common_platform.py) instead of re-implementing platform logic:

```python
from common_platform import (
    ensure_venv_site_packages,
    find_executable,
    get_copilot_dir,
    get_repo_root,
    get_venv_python,
    get_vscode_user_dir,
    normalize_posix_path,
    safe_rmtree,
)
```

If a standalone script cannot import [common_platform.py](../../scripts/common_platform.py), adhere strictly to the 7 core rules below.

---

## 2. The 7 Ironclad Rules

### Rule 1: Dynamic Repository Root & File Anchors
Never hardcode absolute paths or assume current working directory (`os.getcwd()`).
- ✅ **CORRECT:** `REPO_ROOT = Path(__file__).resolve().parents[1]` or `get_repo_root(__file__)`
- ❌ **WRONG:** `REPO_ROOT = "/Users/username/mlaas"` or `os.path.abspath("../../")`

**Path resolution order (applies to code, configs and docs):**
1. **Relative links** in markdown (`[x](../Areas/y.md)`), never `/Users/...` or `C:\Users\...`. Markdown cannot read env vars.
2. **Resolve the root dynamically** from the file (`get_repo_root(__file__)`, `${workspaceFolder}` in a workspace `.vscode/mcp.json`).
3. **`MLAAS_ROOT` env var only when 1 and 2 cannot work** (scripts run outside the repo; never in MCP configs). `get_repo_root()` already falls back to it.
The scanner (`client_term_scan.py`) reports hard-coded home paths as `personal-abs-path`.

### Rule 2: Mandatory UTF-8 on All File I/O & Subprocesses
Windows default encodings (`cp1252`, `ms932`) will throw `UnicodeDecodeError` on emojis (🟢, 🛡️, 📌) and markdown symbols.
- ✅ **CORRECT:**
  - `Path(p).read_text(encoding="utf-8", errors="replace")`
  - `Path(p).write_text(content, encoding="utf-8")`
  - `open(p, "r", encoding="utf-8", errors="replace")`
  - `subprocess.run(cmd, text=True, encoding="utf-8", errors="replace")`
  - `json.dump(data, f, ensure_ascii=False, indent=2)` with an explicit UTF-8 handle
- ❌ **WRONG:** `open(p, "r")`, `Path(p).read_text()`, or `subprocess.run(cmd, text=True)` without encoding.

### Rule 3: POSIX Path Invariance for Indexes, DBs, and URLs
On Windows, `Path.relative_to()` emits backslashes (`\`). Mixing slashes breaks search indexes (Tantivy, ChromaDB, Graphify), RRF fusion keys (`f"{path}:{line}"`), and SQLite lookups.
- ✅ **CORRECT:** `rel_path = file_path.relative_to(REPO_ROOT).as_posix()` or `normalize_posix_path(p)`
- ❌ **WRONG:** `str(file_path.relative_to(REPO_ROOT))` or `str(file_path)`

### Rule 4: Platform-Aware Virtual Environment Resolution
Never hardcode `.venv/bin/python3` or `lib/python*/site-packages`. Windows uses `.venv\Scripts\python.exe` and `.venv\Lib\site-packages`.
- ✅ **CORRECT:** Use `get_venv_python()` and `ensure_venv_site_packages()` from [common_platform.py](../../scripts/common_platform.py).
- ❌ **WRONG:** `os.path.join(REPO_ROOT, ".venv", "bin", "python3")` or manual `lib/python3.14/site-packages`.

**Running commands:** always go through the venv interpreter (`.venv/bin/python3` on macOS/Linux, `.venv\Scripts\python.exe` on Windows 11), never bare `python3`/`pip`, and never `source .venv/bin/activate && ...`. Add dependencies to `requirements.txt`, then `.venv/bin/pip install -r requirements.txt`. `ModuleNotFoundError` means the package is missing from `.venv`.

### Rule 5: Executable Discovery via `shutil.which`
CLI binaries on Windows end in `.exe` or reside in `C:\Program Files`.
- ✅ **CORRECT:** `find_executable("rg")` or `shutil.which("rg") or shutil.which("rg.exe")`
- ❌ **WRONG:** `subprocess.run(["rg", ...])` without resolving binary path.

### Rule 6: OS-Specific Local AppData & User State
VS Code and Copilot directories differ completely across platforms:
- **macOS:** `~/Library/Application Support/Code/User` and `~/.copilot`
- **Windows:** `%APPDATA%\Code\User` and `%USERPROFILE%\.copilot`
- **Linux:** `~/.config/Code/User` and `~/.copilot`
- ✅ **CORRECT:** Call `get_vscode_user_dir()` and `get_copilot_dir()`.
- ❌ **WRONG:** `Path.home() / "Library/Application Support/Code/User"`

### Rule 7: Scratch Dirs, Safe File Removal & Process Trampolines
- **Temp paths:** Never hardcode `/tmp`. Always use `tempfile.gettempdir()` or `tempfile.TemporaryDirectory()`.
- **Directory cleanup:** On Windows, read-only files cause `shutil.rmtree` to crash with `PermissionError`. Always use `safe_rmtree(path)` which clears `stat.S_IWRITE`.
- **Process trampolines:** `os.execv` behaves inconsistently on Windows. Always wrap with fallback:
  ```python
  try:
      os.execv(python_exe, [str(python_exe), str(target_script), *sys.argv[1:]])
  except OSError:
      sys.exit(subprocess.call([str(python_exe), str(target_script), *sys.argv[1:]]))
  ```

---

## 3. Reference Documentation

- Complete modernization audit and architecture: [CROSS_PLATFORM_PLAN.md](../../scripts/CROSS_PLATFORM_PLAN.md)
- Shared implementation module: [common_platform.py](../../scripts/common_platform.py)
- Unit test suite: [test_common_platform.py](../../scripts/tests/test_common_platform.py)
