---
title: "Cross-Platform Modernization Plan (macOS & Windows 11)"
description: "Implementation plan and authoritative authoring instructions to ensure all Python scripts run identically on macOS and Windows 11."
keywords:
  - cross-platform
  - Windows 11
  - macOS
  - Python authoring
  - pathlib
  - scripts
  - virtualenv
  - UTF-8 encoding
category: planning
last_updated: '2026-10-16'
author: thatsafact
related:
  - scripts/_INDEX.md
  - scripts/automation/setup_memory_link.py
  - .github/instructions/cross-platform-python.instructions.md
classification: 🟢🛡️ General
ai_search_aliases:
  - windows mac compatibility plan
  - cross platform python rules
  - scripts windows migration
  - windows 11 python standards
---

# 📌 Cross-Platform Modernization Plan — macOS & Windows 11

> **Execution:** Use `subagent-driven-development` (recommended) or `executing-plans`  
> **Status:** Active | **Target Scope:** 50 Python files across `scripts/` | **Verified Baseline:** 154 passing pytest tests on macOS

---

## 🎯 TL;DR

- **Goal:** Modernize all 50 Python scripts and tests in `scripts/` so they execute with 100% parity across macOS and Windows 11 without platform degradation.
- **Precedent:** Build upon the proven patterns authored by **an earlier contributor** in commits `17edfff` and `7bf8d40` (dynamic root resolution, Windows directory junctions, path slugification, and permission-safe cleanup).
- **Core Strategy:** Establish a zero-dependency platform utility (`scripts/common_platform.py`), eliminate hardcoded Unix paths (`/tmp`, `/Users/`, `bin/python3`), mandate strict UTF-8 I/O encoding, enforce POSIX path invariance (`.as_posix()`) in indexers/searchers, and establish strict **Authoring Instructions for Python**.
- **Use this for:** Guiding the step-by-step migration of existing tooling and enforcing standard patterns for all future Python authoring.

---

## 🏛️ Architecture & Global Constraints

### Architectural Overview
The `scripts/` workspace hosts four major subsystems:
1. **Search Router v2 & MCP Servers:** Hybrid multi-index search engine (Tantivy BM25 + Graphify AST + ChromaDB Semantic + Ripgrep LiveText) exposing stdio JSON-RPC MCP servers (`search_server.py`, `sqlite_server.py`).
2. **Indexing Pipelines:** AST tree-sitter extractors, Tantivy schema builders, and vector embeddings.
3. **Automation & Ingestion:** PDF converters, OCR processors, metadata synchronizers, and doc chunkers.
4. **Telemetry & Analytics:** SQLite FTS5 prompt database synchronization and doc-attribution tracking.

To operate cross-platform, these subsystems must be decoupled from Unix-specific runtime assumptions:
- **Interpreter Isolation:** Windows virtual environments locate binaries under `.venv\Scripts\python.exe` and packages under `.venv\Lib\site-packages`, whereas macOS/Linux locates them under `.venv/bin/python3` and `.venv/lib/python{ver}/site-packages`.
- **Text Encoding Gate:** Windows default encoding is ANSI/locale-specific (e.g. `cp1252`), which throws `UnicodeDecodeError` on UTF-8 emojis, symbols, and frontmatter. All file I/O and process streams must explicitly enforce UTF-8.
- **Index Path Invariance:** Document IDs, graph node paths, and search keys must always use POSIX slashes (`.as_posix()`) so indexes generated on either OS remain interoperable.

### Global Constraints & Review Focus
1. **Facts-Only Gate:** Verified exactly 50 `.py` files across `scripts/` and 154 passing tests in `scripts/tests/`. All changes must maintain 100% test pass rates on macOS while enabling Windows 11.
2. **Zero Cloud Egress:** All scripts must continue running locally; never introduce cloud dependencies or external network requirements for local operations.
3. **No Shell Lifecycle Hooks:** Do not introduce `.bashrc`, PowerShell profiles, or lifecycle hooks that fail silently.
4. **Top 5 Review Failure Modes:**
   - *Failure Mode 1:* `UnicodeDecodeError: 'charmap' codec can't decode byte` on Windows due to unencoded `read_text()`, `open()`, or `subprocess.run(text=True)`.
   - *Failure Mode 2:* `FileNotFoundError: .venv/bin/python3` when spawning background MCP servers or trampolines on Windows.
   - *Failure Mode 3:* `ModuleNotFoundError` because `.venv\Lib\site-packages` was not added to `sys.path`.
   - *Failure Mode 4:* Divergent search result deduplication and RRF fusion keys due to backslashes (`\`) vs forward slashes (`/`).
   - *Failure Mode 5:* `PermissionError` when removing directories or temp files due to Windows read-only flags or open file locks.

---

## 🔍 Case Study: Lessons from an Earlier Contributor's Groundbreaking Updates

A contributor has already updated three mission-critical scripts for Windows compatibility. These represent our gold standard:

### 1. Dynamic Workspace Root Derivation (Commit `17edfff`)
* **Problem:** `generate_indices_and_master_toc.py` and `update_markdown_metadata.py` originally hardcoded `WORKSPACE = "/Users/<user>/path/to/mlaas"`, causing fatal crashes on any other laptop or Windows machine.
* **Contributor's Solution:**
  ```python
  # Repo root, derived from this file so the script runs on any machine.
  WORKSPACE = str(Path(__file__).resolve().parents[2])
  ```
* **Lesson:** Anchor all relative paths to `Path(__file__).resolve()`. Never assume a specific directory tree or user home folder.

### 2. Junction Fallback for Non-Elevated Symlinks on Windows (Commit `7bf8d40`)
* **Problem:** In `setup_memory_link.py`, standard symlink creation (`link.symlink_to(target)`) raises `OSError` on Windows unless the user has Administrator privileges or Developer Mode enabled.
* **Contributor's Solution:**
  ```python
  def make_link(link: Path, target: Path) -> str:
      try:
          link.symlink_to(target, target_is_directory=True)
          return "symlink"
      except OSError:
          if os.name != "nt":
              raise
          # Windows without Administrator / Developer Mode: junctions need no elevation.
          subprocess.run(
              ["cmd", "/c", "mklink", "/J", str(link), str(target)],
              check=True, capture_output=True, text=True,
          )
          return "junction"
  ```
* **Lesson:** On Windows, use directory junctions (`mklink /J`) when elevated symlinks are unavailable.

### 3. Extended-Length Windows Path Prefix Handling (`\\?\`) (Commit `7bf8d40`)
* **Problem:** Windows junctions read via `os.readlink()` return paths prefixed with `\\?\` or `\\?\UNC\`, which break equality checks against standard paths.
* **Contributor's Solution:**
  ```python
  if raw.startswith("\\\\?\\UNC\\"):
      raw = "\\\\" + raw[8:]
  elif raw.startswith("\\\\?\\"):
      raw = raw[4:]
  return Path(raw)
  ```
* **Lesson:** Always normalize Windows extended prefixes before path comparison or storage.

### 4. Permission-Safe Directory Cleanup (`on_rm_error`) (Commit `7bf8d40`)
* **Problem:** `shutil.rmtree()` on Windows frequently fails with `PermissionError` when deleting git trees or cache files marked with the read-only file attribute.
* **Contributor's Solution:**
  ```python
  def on_rm_error(func, path, _exc):
      """Clear the read-only bit Windows sets on some files, then retry."""
      os.chmod(path, stat.S_IWRITE)
      func(path)

  shutil.rmtree(link, onerror=on_rm_error)
  ```
* **Lesson:** Always supply a read-only clearing error handler when cleaning up directories.

### 5. Multi-OS Path Slugification (Commit `7bf8d40`)
* **Problem:** Path separators differ (`/` vs `\`), and Windows drive letters include colons (`C:\`).
* **Contributor's Solution:**
  ```python
  base = "".join("-" if c in ':/\\' else c for c in raw)
  ```
* **Lesson:** Normalize both `:` and `\` alongside `/` when creating slugs, identifiers, or cross-platform keys.

---

## 📜 Authoritative Instructions for Authoring `.py` Files (Mac & Windows)

Every developer and AI agent creating or modifying Python scripts in `scripts/` MUST follow these mandatory rules:

### Rule 1: Always Anchor Paths to File Location
Never use string concatenation with relative directory assumptions or hardcoded roots.
```python
# ✅ CORRECT
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parents[2]  # Adjust depth appropriately
DATA_DIR = REPO_ROOT / "Resources" / "data"

# ❌ INCORRECT
REPO_ROOT = "/Users/username/mlaas"
REPO_ROOT = os.path.abspath("../../")  # Fragile if executed from arbitrary cwd
```

### Rule 2: Enforce UTF-8 on All File I/O and Subprocesses
Windows default encodings (`cp1252`, `ms932`) will crash on emojis and unicode. Always pass `encoding="utf-8"`.
```python
# ✅ CORRECT
with open(file_path, "r", encoding="utf-8", errors="replace") as f:
    text = f.read()

content = Path(file_path).read_text(encoding="utf-8", errors="replace")
Path(out_file).write_text(content, encoding="utf-8")

proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")

# ❌ INCORRECT (Crashes on Windows)
with open(file_path, "r") as f: ...
text = Path(file_path).read_text()
proc = subprocess.run(cmd, capture_output=True, text=True)
```

### Rule 3: Use `.as_posix()` for Stored Paths and Indexes
When writing relative paths to indexes (Tantivy, ChromaDB, Graphify), databases, or Markdown links, always normalize to forward slashes:
```python
# ✅ CORRECT
rel_path = file_path.relative_to(REPO_ROOT).as_posix()
doc_id = rel_path  # "scripts/automation/probe.py" on BOTH Mac and Windows

# ❌ INCORRECT
rel_path = str(file_path.relative_to(REPO_ROOT))  # Emits "scripts\automation\probe.py" on Windows
```

### Rule 4: Resolve Virtual Environment Interactively
Never hardcode `.venv/bin/python3`. Use a platform-aware resolver:
```python
# ✅ CORRECT
import sys
from pathlib import Path

def get_venv_python(repo_root: Path) -> Path:
    if sys.platform == "win32":
        candidate = repo_root / ".venv" / "Scripts" / "python.exe"
    else:
        candidate = repo_root / ".venv" / "bin" / "python3"
        if not candidate.exists():
            candidate = repo_root / ".venv" / "bin" / "python"
    return candidate if candidate.exists() else Path(sys.executable)

def ensure_venv_site_packages(repo_root: Path) -> None:
    venv = repo_root / ".venv"
    candidates = [
        venv / "Lib" / "site-packages",
        venv / "lib" / "site-packages",
    ]
    for pyver in ["3.14", "3.13", "3.12", "3.11", "3.10"]:
        candidates.append(venv / "lib" / f"python{pyver}" / "site-packages")
    for sp in candidates:
        if sp.exists() and str(sp) not in sys.path:
            sys.path.insert(0, str(sp))

# ❌ INCORRECT (Fails completely on Windows)
VENV_PYTHON = os.path.join(REPO_ROOT, ".venv", "bin", "python3")
sp = os.path.join(REPO_ROOT, ".venv", "lib", "python3.14", "site-packages")
```

### Rule 5: Resolve Binaries via `shutil.which`
Do not assume `rg` or `tesseract` are in Unix `$PATH`. On Windows they may be `rg.exe` or installed in `Program Files`:
```python
# ✅ CORRECT
import shutil

def find_ripgrep() -> str | None:
    return shutil.which("rg") or shutil.which("rg.exe")

def find_tesseract() -> str | None:
    cmd = shutil.which("tesseract") or shutil.which("tesseract.exe")
    if not cmd and sys.platform == "win32":
        default_win = Path("C:/Program Files/Tesseract-OCR/tesseract.exe")
        if default_win.exists():
            return str(default_win)
    return cmd

# ❌ INCORRECT
subprocess.run(["rg", "--version"])  # Fails if rg is not in PATH or named rg.exe
```

### Rule 6: Locate OS-Specific Local App Data
When accessing VS Code or Copilot local user state:
```python
# ✅ CORRECT
import os, sys
from pathlib import Path

def get_vscode_user_dir() -> Path:
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        return Path(appdata) / "Code" / "User" if appdata else Path.home() / "AppData" / "Roaming" / "Code" / "User"
    elif sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Code" / "User"
    else:  # Linux
        return Path.home() / ".config" / "Code" / "User"

# ❌ INCORRECT
VS = os.path.expanduser("~/Library/Application Support/Code/User")  # macOS only
```

### Rule 7: Use `tempfile.gettempdir()`, Never `/tmp`
```python
# ✅ CORRECT
import tempfile
from pathlib import Path

temp_dir = Path(tempfile.gettempdir())
html_scratch = temp_dir / f"{slug}.html"

# ❌ INCORRECT
html_scratch = f"/tmp/{slug}.html"  # Does not exist on Windows
```

---

## 📊 Comprehensive Audit of All 50 Python Scripts in `scripts/`

| Subsystem | Script Path | Current Status | Issues Identified for Windows 11 |
|---|---|---|---|
| **Root** | `scripts/conftest.py` | 🟢 Clean | None; already uses `os.path.abspath` and `os.path.join`. |
| **Root** | `scripts/index_workspace.py` | 🟡 Needs Update | Trampoline uses `os.execv`. Add Windows `sys.executable` execution fallback. |
| **Root** | `scripts/mcp_search_router.py` | 🟡 Needs Update | Trampoline uses `os.execv`. Add Windows `sys.executable` execution fallback. |
| **Root** | `scripts/search_server.py` | 🟡 Needs Update | Trampoline uses `os.execv`. Add Windows `sys.executable` execution fallback. |
| **Root** | `scripts/mcp_speed_bench.py` | 🔴 Needs Fix | Hardcodes `.venv/bin/python3`; unencoded `open(args.json, "w")`. |
| **Root** | `scripts/sqlite_server.py` | 🔴 Needs Fix | Hardcodes `.venv/bin/python3` and `lib/python*/site-packages`; hardcodes `~/.copilot` without `%USERPROFILE%` fallback. |
| **Automation** | `scripts/automation/__init__.py` | 🟢 Clean | Empty package marker. |
| **Automation** | `scripts/automation/setup_memory_link.py` | 🟢 Model Script | **Updated by a contributor.** Full Windows junction & `stat.S_IWRITE` support. |
| **Automation** | `scripts/automation/generate_indices_and_master_toc.py` | 🟢 Updated | **Updated by a contributor.** Uses `Path(__file__)`. Update CLI cheat sheet to cross-platform syntax. |
| **Automation** | `scripts/automation/update_markdown_metadata.py` | 🟢 Updated | **Updated by a contributor.** Uses `Path(__file__)` and UTF-8 encoding. |
| **Automation** | `scripts/automation/export_memories.py` | 🔴 Needs Fix | Hardcodes `~/Library/Application Support/Code/User`. Needs `get_vscode_user_dir()`. |
| **Automation** | `scripts/automation/probe.py` | 🔴 Needs Fix | Hardcodes `~/Library/Application Support/Code/User`. Needs `get_vscode_user_dir()`. |
| **Automation** | `scripts/automation/pdf_to_md.py` | 🟡 Needs Update | Error string outputs Unix `.venv/bin/python` commands; normalize image link checks. |
| **Automation** | `scripts/automation/pdf_to_md_fast.py` | 🟢 Clean | Standard PyMuPDF logic. |
| **Automation** | `scripts/automation/convert_eks_bpg_fast.py` | 🔴 Needs Fix | Hardcodes `lib/python{pyver}/site-packages`. Needs `Lib/site-packages`. |
| **Automation** | `scripts/automation/chunk_aws_docs.py` | 🟢 Clean | Uses `Path` and explicit `encoding="utf-8"`. |
| **Automation** | `scripts/automation/add_aws_frontmatter.py` | 🔴 Needs Fix | `md.read_text()` and `md.write_text()` lack `encoding="utf-8"`. |
| **Automation** | `scripts/automation/insert_ocr_links.py` | 🔴 Needs Fix | `MANIFEST.read_text()` and `MD.read_text()` lack `encoding="utf-8"`; raw `/` split. |
| **Automation** | `scripts/automation/ocr_packt_figures.py` | 🔴 Needs Fix | `MANIFEST.read_text()` lacks encoding; `TESS = "tesseract"` needs `shutil.which`; subprocess lacks UTF-8. |
| **Automation** | `scripts/automation/ingest_aws_ray_blogs.py` | 🔴 Needs Fix | Hardcodes `/tmp/{slug}.html`. Replace with `tempfile.gettempdir()`. |
| **Indexing** | `scripts/indexing/__init__.py` | 🟢 Clean | Module exports. |
| **Indexing** | `scripts/indexing/vectordb_provider.py` | 🟢 Clean | Uses `Path(db_path)` and ChromaDB client abstraction. |
| **Indexing** | `scripts/indexing/index_workspace.py` | 🔴 Needs Fix | Emits `str(file.relative_to())` (backslashes on Windows). Needs `.as_posix()`. |
| **Indexing** | `scripts/indexing/index_tantivy.py` | 🔴 Needs Fix | Emits Windows backslashes into Tantivy `doc_id` and `path`. Needs `.as_posix()`. |
| **Indexing** | `scripts/indexing/index_graphify.py` | 🔴 Needs Fix | Node IDs and AST paths need `.as_posix()` normalization. |
| **Indexing** | `scripts/indexing/examples.py` | 🟢 Clean | CLI usage examples. |
| **Search Router** | `scripts/search_router/__init__.py` | 🟢 Clean | Module exports. |
| **Search Router** | `scripts/search_router/livetext.py` | 🔴 Needs Fix | `rg` needs `shutil.which("rg") or shutil.which("rg.exe")`; `subprocess.run(text=True)` needs UTF-8. |
| **Search Router** | `scripts/search_router/search_router.py` | 🔴 Needs Fix | `ResultDeduplicator` and RRF keys fail on mixed slashes. Normalize `res.path.replace("\\", "/")`. |
| **Search Router** | `scripts/search_router/search_server.py` | 🔴 Needs Fix | Hardcodes `.venv/bin/python3` and `lib/python*/site-packages`. |
| **Search Router** | `scripts/search_router/tantivy_searcher.py` | 🟢 Clean | Uses `Path` and Tantivy schema builder. |
| **Search Router** | `scripts/search_router/graphify_searcher.py` | 🟡 Needs Update | Normalize node ID path keys with `.as_posix()`. |
| **Search Router** | `scripts/search_router/mcp_search_tools.py` | 🟢 Clean | Pure routing layer over tools. |
| **Search Router** | `scripts/search_router/mcp_tool_adapter.py` | 🟢 Clean | In-process adapter. |
| **Search Router** | `scripts/search_router/mcp_server_integration.py` | 🟡 Needs Update | Subprocess call needs `REPO_ROOT` path resolution and `encoding="utf-8"`. |
| **Search Router** | `scripts/search_router/speed_test.py` | 🔴 Needs Fix | Hardcodes `lib/python*/site-packages`. |
| **Search Router** | `scripts/search_router/mcp_examples.py` | 🟢 Clean | Sample queries. |
| **Telemetry** | `scripts/telemetry/__init__.py` | 🟢 Clean | Module exports. |
| **Telemetry** | `scripts/telemetry/sync_prompts_db.py` | 🟡 Needs Update | `DOC_PATH_RE` expects `/`. Allow `\` in path regex and normalize citations. |
| **Tests** | `scripts/tests/__init__.py` | 🟢 Clean | Module exports. |
| **Tests** | `scripts/tests/test_indexing.py` | 🟢 Clean | All 21 tests passing. |
| **Tests** | `scripts/tests/test_livetext.py` | 🔴 Needs Fix | `test_file.write_text()` in real search test lacks `encoding="utf-8"`. |
| **Tests** | `scripts/tests/test_mcp_client.py` | 🟢 Clean | In-process MCP client tests. |
| **Tests** | `scripts/tests/test_mcp_search_tools.py` | 🟢 Clean | Tool definition tests. |
| **Tests** | `scripts/tests/test_mcp_smoke.py` | 🔴 Needs Fix | Hardcodes `.venv/bin/python3`; uses `cwd="/"`. |
| **Tests** | `scripts/tests/test_phase6_search.py` | 🔴 Needs Fix | Hardcodes `TantivySearcher("/tmp/nonexistent_tantivy_index_path")`. |
| **Tests** | `scripts/tests/test_prompt_telemetry.py` | 🟢 Clean | Uses `tmp_path` and `encoding="utf-8"`. |
| **Tests** | `scripts/tests/test_search_router.py` | 🟢 Clean | Router tests. |
| **Tests** | `scripts/tests/test_sequential_thinking.py` | 🟡 Needs Update | Subprocess call needs `encoding="utf-8"`. |
| **Tests** | `scripts/tests/test_sqlite_mcp.py` | 🟢 Clean | All 11 tests passing. |

---

## 🛠️ Implementation Plan: Step-by-Step Modernization

### Task 1: Create Shared Platform Utilities (`scripts/common_platform.py`)

**Files:**
- Create: `scripts/common_platform.py`
- Test: `scripts/tests/test_common_platform.py`

**Interfaces:**
- Consumes: Standard library only (`os`, `sys`, `pathlib`, `shutil`, `tempfile`, `stat`)
- Produces:
  - `get_repo_root() -> Path`
  - `get_venv_python(repo_root: Path | None = None) -> Path`
  - `ensure_venv_site_packages(repo_root: Path | None = None) -> None`
  - `get_vscode_user_dir() -> Path`
  - `get_copilot_dir() -> Path`
  - `normalize_posix_path(path: str | Path) -> str`
  - `safe_rmtree(path: Path | str) -> None`
  - `find_executable(name: str) -> str | None`

- [ ] **Step 1:** Write failing unit tests in `scripts/tests/test_common_platform.py` verifying behavior across simulated `win32` and `darwin` environments.
- [ ] **Step 2:** Implement `scripts/common_platform.py` with full type hints and docstrings.
- [ ] **Step 3:** Run `pytest scripts/tests/test_common_platform.py -v` to pass.
- [ ] **Step 4:** Commit: `feat(scripts): add common_platform utility for Windows and Mac interoperability`

---

### Task 2: Modernize Core MCP Servers & Process Trampolines

**Files:**
- Modify: `scripts/search_server.py:1-15`
- Modify: `scripts/index_workspace.py:1-15`
- Modify: `scripts/mcp_search_router.py:1-15`
- Modify: `scripts/sqlite_server.py:18-35`
- Modify: `scripts/search_router/search_server.py:18-35`
- Modify: `scripts/mcp_speed_bench.py:20-30, 201`
- Test: `scripts/tests/test_mcp_smoke.py`, `scripts/tests/test_sqlite_mcp.py`

**Interfaces:**
- Consumes: `scripts/common_platform.py` (`get_venv_python`, `ensure_venv_site_packages`, `get_vscode_user_dir`, `get_copilot_dir`)
- Produces: Resilient stdio MCP server processes that start cleanly on Windows 11 and macOS under `.venv`.

- [ ] **Step 1:** Update `scripts/sqlite_server.py` to use `get_venv_python()`, `ensure_venv_site_packages()`, and dynamic `DEFAULT_COPILOT_DB`.
- [ ] **Step 2:** Update `scripts/search_router/search_server.py` and `scripts/search_server.py` trampoline.
- [ ] **Step 3:** Update `scripts/mcp_speed_bench.py` with UTF-8 encoding on JSON output and dynamic venv resolution.
- [ ] **Step 4:** Run `.venv/bin/python3 scripts/tests/test_mcp_smoke.py` and pytest suite.
- [ ] **Step 5:** Commit: `fix(mcp): resolve virtualenv python and site-packages cross-platform`

---

### Task 3: Enforce POSIX Path Invariance Across Indexing & Search Router

**Files:**
- Modify: `scripts/indexing/index_workspace.py:240-250`
- Modify: `scripts/indexing/index_tantivy.py:160-175`
- Modify: `scripts/indexing/index_graphify.py:140-160`
- Modify: `scripts/search_router/livetext.py:100-120, 150-165`
- Modify: `scripts/search_router/search_router.py:220-240, 310-330`
- Modify: `scripts/search_router/speed_test.py:25-35`
- Test: `scripts/tests/test_indexing.py`, `scripts/tests/test_livetext.py`, `scripts/tests/test_search_router.py`

**Interfaces:**
- Consumes: `file_path.relative_to(root).as_posix()`, `shutil.which("rg")`
- Produces: Unified forward-slash index keys and deduplication keys across all platforms.

- [ ] **Step 1:** Update `index_workspace.py`, `index_tantivy.py`, and `index_graphify.py` to record `as_posix()` relative paths.
- [ ] **Step 2:** Update `livetext.py` to use `find_executable("rg")` and pass `encoding="utf-8", errors="replace"` to `subprocess.run`.
- [ ] **Step 3:** Update `search_router.py` `ResultDeduplicator` and `ResultRanker.reciprocal_rank_fusion` to normalize result paths before grouping.
- [ ] **Step 4:** Run `.venv/bin/python3 -m pytest scripts/tests/test_indexing.py scripts/tests/test_livetext.py scripts/tests/test_search_router.py -v`.
- [ ] **Step 5:** Commit: `fix(search): enforce posix path invariance and UTF-8 ripgrep execution`

---

### Task 4: Modernize Automation Scripts & File Encoding

**Files:**
- Modify: `scripts/automation/export_memories.py:28-40`
- Modify: `scripts/automation/probe.py:15-20`
- Modify: `scripts/automation/ingest_aws_ray_blogs.py:275-285`
- Modify: `scripts/automation/add_aws_frontmatter.py:90-105`
- Modify: `scripts/automation/insert_ocr_links.py:18-35, 60`
- Modify: `scripts/automation/ocr_packt_figures.py:40-50, 70-80, 95-105`
- Modify: `scripts/automation/convert_eks_bpg_fast.py:12-20`
- Modify: `scripts/automation/generate_indices_and_master_toc.py:835-850`
- Test: Run `--dry-run` or check syntax across all modified automation scripts.

**Interfaces:**
- Consumes: `tempfile.gettempdir()`, `get_vscode_user_dir()`, `encoding="utf-8"`
- Produces: Robust, platform-independent batch utilities.

- [x] **Step 1:** Update `export_memories.py` and `probe.py` with multi-OS VS Code directory paths.
- [x] **Step 2:** Replace `/tmp/{slug}.html` in `ingest_aws_ray_blogs.py` with `Path(tempfile.gettempdir()) / f"{slug}.html"`.
- [x] **Step 3:** Add explicit `encoding="utf-8"` to all `read_text()` and `write_text()` calls in `add_aws_frontmatter.py`, `insert_ocr_links.py`, and `ocr_packt_figures.py`.
- [x] **Step 4:** Add Windows executable fallback for Tesseract in `ocr_packt_figures.py`.
- [x] **Step 5:** Commit: `fix(automation): eliminate hardcoded Unix paths and enforce UTF-8 file I/O`

---

### Task 5: Telemetry Synchronization & Test Suite Parity

**Files:**
- Modify: `scripts/telemetry/sync_prompts_db.py:28-35`
- Modify: `scripts/tests/test_livetext.py:375-400`
- Modify: `scripts/tests/test_phase6_search.py:60-65`
- Modify: `scripts/tests/test_mcp_smoke.py:25-35, 45-55`
- Modify: `scripts/tests/test_sequential_thinking.py:25-35, 65-75`
- Test: Full pytest suite execution.

**Interfaces:**
- Consumes: Cross-platform temp dirs and regex path patterns.
- Produces: 100% test passing rate on both Mac and Windows environments.

- [ ] **Step 1:** Update `test_phase6_search.py` to use `tempfile.gettempdir()` instead of `/tmp/nonexistent_tantivy_index_path`.
- [ ] **Step 2:** Update `test_mcp_smoke.py` to resolve venv python and use valid cross-platform working directories.
- [ ] **Step 3:** Add `encoding="utf-8"` to `test_livetext.py` file fixtures.
- [ ] **Step 4:** Run `.venv/bin/python3 -m pytest scripts/tests/ -v` to confirm all 154+ tests pass.
- [ ] **Step 5:** Commit: `test(scripts): harden test suite for cross-platform execution`

---

## 🔬 Verification Matrix & Validation Gates

Run these verification gates to validate cross-platform compliance:

```bash
# 1. Full Pytest Suite (Mac & Windows PowerShell)
# macOS / Linux:
.venv/bin/python3 -m pytest scripts/tests/ -v
# Windows 11 (PowerShell):
& .venv\Scripts\python.exe -m pytest scripts/tests/ -v

# 2. Search Router Speed & SLA Benchmark
# macOS / Linux:
.venv/bin/python3 scripts/search_router/speed_test.py
# Windows 11:
& .venv\Scripts\python.exe scripts\search_router\speed_test.py

# 3. Real stdio MCP Smoke Test
# macOS / Linux:
.venv/bin/python3 scripts/tests/test_mcp_smoke.py
# Windows 11:
& .venv\Scripts\python.exe scripts\tests\test_mcp_smoke.py

# 4. Multi-Index Verification
# macOS / Linux:
.venv/bin/python3 scripts/indexing/index_tantivy.py --stats
.venv/bin/python3 scripts/indexing/index_graphify.py --stats
# Windows 11:
& .venv\Scripts\python.exe scripts\indexing\index_tantivy.py --stats
& .venv\Scripts\python.exe scripts\indexing\index_graphify.py --stats

# 5. Telemetry Ingestion
# macOS / Linux:
.venv/bin/python3 scripts/telemetry/sync_prompts_db.py --stats
# Windows 11:
& .venv\Scripts\python.exe scripts\telemetry\sync_prompts_db.py --stats
```

---

## 🚀 Execution Handoff

Plan saved to [scripts/CROSS_PLATFORM_PLAN.md](./CROSS_PLATFORM_PLAN.md).

**Execution options:**
1. **Subagent-Driven** (recommended) — Fresh agent per task with targeted spec and quality gate.
2. **Inline Execution** — Execute sequentially in current session with ledger tracking.
