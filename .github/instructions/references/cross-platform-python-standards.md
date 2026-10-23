---
title: "Cross-Platform Python Standards — Detailed Implementation Reference"
description: "Detailed code templates, platform fallbacks, and examples for macOS, Linux, and Windows 11 Python development."
shield: "internal"
last_updated: "2026-10-23"
keywords: [python, cross-platform, windows, macos, encoding, posix, venv]
---

# Cross-Platform Python Standards — Detailed Implementation Reference

📄 **Instruction Hub:** `.github/instructions/cross-platform-python.instructions.md`  
📄 **Core Utility:** `scripts/common_platform.py`

---

## 1. Import Organization & `common_platform` Utilities

Whenever authoring or editing Python scripts, reuse standard cross-platform utilities:

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

---

## 2. In-Depth Rule Implementations & Code Examples

### Rule 1: Dynamic Repository Root & File Anchors
Never hardcode absolute paths or assume current working directory (`os.getcwd()`).
```python
# Resolve repository root from file anchor
REPO_ROOT = Path(__file__).resolve().parents[1]  # or get_repo_root(__file__)
```
**Path resolution hierarchy:**
1. Relative links in markdown (`[doc](../Areas/doc.md)`).
2. Dynamic resolution in code via `get_repo_root(__file__)` or `${workspaceFolder}` in `.vscode/mcp.json`.
3. `MLAAS_ROOT` or `THESAFACT_AI_ROOT` environment variables only as a fallback for scripts run outside the workspace.

### Rule 2: Mandatory UTF-8 on All File I/O & Subprocesses
Windows default encodings (`cp1252`, `ms932`) throw `UnicodeDecodeError` on emojis and unicode characters.
```python
# File reading/writing
content = Path(p).read_text(encoding="utf-8", errors="replace")
Path(p).write_text(content, encoding="utf-8")

with open(p, "r", encoding="utf-8", errors="replace") as f:
    data = f.read()

# JSON serialization
with open(p, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# Subprocesses
res = subprocess.run(cmd, text=True, encoding="utf-8", errors="replace", capture_output=True)
```

### Rule 3: POSIX Path Invariance for Indexes & Databases
On Windows, `Path.relative_to()` emits backslashes (`\`), breaking search indexes (Tantivy, ChromaDB, Graphify) and SQLite keys.
```python
rel_posix = file_path.relative_to(REPO_ROOT).as_posix()
# or
rel_posix = normalize_posix_path(file_path)
```

### Rule 4: Platform-Aware Virtual Environment Resolution
- **macOS / Linux:** `.venv/bin/python3`, `.venv/lib/python*/site-packages`
- **Windows 11:** `.venv\Scripts\python.exe`, `.venv\Lib\site-packages`
Always resolve via `get_venv_python()` and `ensure_venv_site_packages()`.

### Rule 5: Executable Discovery (`rg`, `tesseract`, etc.)
CLI binaries on Windows include `.exe` and may reside in Program Files:
```python
rg_bin = find_executable("rg")  # Checks PATH, .exe extension, and platform install locations
```

### Rule 6: User & Application Directories
- **macOS:** `~/Library/Application Support/Code/User`, `~/.copilot`
- **Windows:** `%APPDATA%\Code\User`, `%USERPROFILE%\.copilot`
- **Linux:** `~/.config/Code/User`, `~/.copilot`
Always invoke `get_vscode_user_dir()` and `get_copilot_dir()`.

### Rule 7: Temp Dirs, Safe Cleanup & Process Trampolines
```python
# Cross-platform scratch directory
scratch = Path(tempfile.gettempdir()) / "mlaas_scratch"

# Directory cleanup (handles read-only files on Windows)
safe_rmtree(target_dir)

# Process trampoline fallback for Windows
try:
    os.execv(python_exe, [str(python_exe), str(script), *sys.argv[1:]])
except OSError:
    sys.exit(subprocess.call([str(python_exe), str(script), *sys.argv[1:]]))
```
