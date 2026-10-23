# Cross-Platform Python Patterns & Lessons Learned

> **Context:** Reference implementation patterns derived from a contributor's Windows compatibility commits and the 50-script modernization across MLaaS.

---

## 1. Lessons Learned from a Contributor's Commits

### Directory Links & Junctions (`setup_memory_link.py`, `7bf8d40`)
On Windows, standard symbolic links require elevated administrator privileges or Developer Mode.
- **Pattern:** Create NTFS junctions on Windows via `subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)])`.
- **Directory Deletion:** Windows marks some junction files read-only. Standard `shutil.rmtree` raises `PermissionError`. Always supply an error callback to reset permissions:
  ```python
  def on_rm_error(func, path, _exc):
      os.chmod(path, stat.S_IWRITE)
      func(path)
  shutil.rmtree(path, onerror=on_rm_error)
  ```

### Multi-OS Path Slugification (`7bf8d40`)
Path separators differ (`/` vs `\`), and Windows drive letters contain colons (`C:\`).
- **Pattern:** Replace both colons and backslashes alongside forward slashes:
  ```python
  slug = "".join("-" if c in ':/\\' else c for c in raw_path)
  ```

---

## 2. Windows 11 Failure Modes Observed in Codebase

### Failure Mode 1: Character Encoding (`UnicodeDecodeError`)
- **Root Cause:** Windows Python defaults to ANSI code pages (e.g., `cp1252` on English systems, `ms932` on Japanese systems).
- **Impact:** Unencoded `open()`, `read_text()`, or `subprocess.run()` crashes on Unicode emojis (🟢, 🛡️, 📌), smart quotes, or accented letters.
- **Resolution:** Explicitly declare `encoding="utf-8"` and `errors="replace"` on every text read and write.

### Failure Mode 2: Search Index Path Desynchronization
- **Root Cause:** Windows `Path.relative_to()` produces backslashes (e.g., `scripts\search_router\livetext.py`).
- **Impact:** Search Router deduplication maps and Reciprocal Rank Fusion (RRF) calculate keys using string paths (`f"{path}:{line}"`). Backslashes vs forward slashes cause duplicate results, score dilution, and broken markdown links.
- **Resolution:** Always invoke `.as_posix()` or `normalize_posix_path(p)` before storing or comparing paths.

### Failure Mode 3: Virtual Environment Layout Discrepancies
- **Root Cause:** POSIX stores the interpreter in `.venv/bin/python3` and packages in `.venv/lib/python{ver}/site-packages`. Windows stores the interpreter in `.venv\Scripts\python.exe` and packages directly in `.venv\Lib\site-packages`.
- **Impact:** Hardcoded Unix paths immediately fail with `FileNotFoundError` or `ModuleNotFoundError`.
- **Resolution:** Call `get_venv_python()` and `ensure_venv_site_packages()` from `scripts/common_platform.py`.

### Failure Mode 4: Hardcoded OS Paths (`/tmp` and `~/Library/...`)
- **Root Cause:** Windows has no `/tmp` directory (fails with `FileNotFoundError`). VS Code user settings and Copilot state live under `%APPDATA%\Code\User` and `%USERPROFILE%\.copilot`.
- **Resolution:** Use `tempfile.gettempdir()` for temporary scratch files, and `get_vscode_user_dir()` / `get_copilot_dir()` for application state.

### Failure Mode 5: `os.execv` Process Replacement
- **Root Cause:** On Windows, `os.execv` does not replace the calling process in place like POSIX `execve`. It can leave child handles or terminate abruptly with `OSError`.
- **Resolution:** Wrap `os.execv` in a `try...except OSError` block that falls back to `subprocess.call` and exits with the child's returncode.

---

## 3. Concrete Before / After Code Reference

```python
# ❌ INCORRECT (Breaks on Windows 11)
REPO_ROOT = "/Users/username/mlaas"
VENV_PY = os.path.join(REPO_ROOT, ".venv", "bin", "python3")
with open("doc.md", "r") as f:
    text = f.read()
doc_id = str(Path("scripts/probe.py").relative_to(REPO_ROOT))
temp_file = "/tmp/scratch.html"
shutil.rmtree(temp_dir)

# ✅ CORRECT (Runs identically on macOS & Windows 11)
from common_platform import (
    get_repo_root, get_venv_python, normalize_posix_path, safe_rmtree
)
import tempfile

REPO_ROOT = get_repo_root(__file__)
VENV_PY = get_venv_python(REPO_ROOT)
with open("doc.md", "r", encoding="utf-8", errors="replace") as f:
    text = f.read()
doc_id = Path("scripts/probe.py").relative_to(REPO_ROOT).as_posix()
temp_file = Path(tempfile.gettempdir()) / "scratch.html"
safe_rmtree(temp_dir)
```
