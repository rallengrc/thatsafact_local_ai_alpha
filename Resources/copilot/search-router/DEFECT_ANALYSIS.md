---
title: mlaas-search — Defect Analysis
description: Root-cause defect analysis of the ripgrep wrapper, MCP server import bug, and context sizing in mlaas-search
keywords:
- defect analysis
- mlaas-search
- ripgrep bug
- MCP bug
- search router defects
category: architecture
classification: 🟢🛡️ General
last_updated: '2026-10-11'
author: thatsafact
ai_search_aliases:
- search router defect analysis
- ripgrep bug analysis
- mlaas-search defects
---

# mlaas-search — Defect Analysis

> **TL;DR:** Exhaustive defect analysis identifying critical bugs in the search router: zero ripgrep results, missing server imports, and token sizing issues.
> **Use this for:** Remediating bugs in `livetext.py`, `search_router.py`, and `search_server.py`.

> What is wrong with the "hybrid ripgrep + semantic" search system in
> `scripts/` (a.k.a. *mlaas-search*): `search_router.py`, `mcp_search_tools.py`,
> `search_server.py`, `mcp_search_router.py`, `mcp_tool_adapter.py`,
> `livetext.py`, `vectordb_provider.py`, `index_workspace.py`.
>
> Method: ran each entry point end-to-end (Python 3.14 venv at `.venv/`,
> chromadb 0.4+, ripgrep `rg` 14) and inspected the code. Unit tests report
> "passing," but the tests mock the vector layer and don't exercise the real
> ripgrep path — so they miss the bugs below. Full suite: **118 passed, 1 failed**.
>
> Date: 2026-10-10. Environment: macOS, `rg` at `/opt/homebrew/bin/rg`,
> workspace is a git repo (`.git` present), `.chroma/` has 45 indexed docs.

---

## TL;DR

The system *claims* "hybrid ripgrep + semantic" search, but in the actual
runtime the **ripgrep half returns zero results for every query**, so it is
silently semantic-only. On top of that, the **production MCP server
(`search_server.py`) cannot even start** — it imports a symbol that doesn't
exist. And even the semantic half that does work feeds the LLM **entire files
(thousands of tokens)** instead of snippets. These are the three headline
problems; the rest are correctness and consistency bugs.

| # | Severity | Where | One-line problem |
|---|----------|-------|------------------|
| 1 | 🔴 CRITICAL | `livetext.py` / `search_router.py` | Ripgrep search returns **0 results** for every query → "hybrid" is secretly semantic-only |
| 2 | 🔴 CRITICAL | `search_server.py` | Imports `ToolResult` (nonexistent) → MCP server crashes at import; cannot start |
| 3 | 🟠 HIGH | `index_workspace.py` | Indexes **whole files** as one vector; semantic results dump entire files into LLM context |
| 4 | 🟠 HIGH | `search_router.py` `QueryAnalyzer` | Plain keyword queries route **semantic-only**, bypassing ripgrep even for exact matches |
| 5 | 🟠 HIGH | `livetext.py` `_parse_json_output` | Context lines sorted **alphabetically** + mis-assigned across matches in one file |
| 6 | 🟡 MEDIUM | `livetext.py` / `search_code` | `--max-count` is **per-file**, so `limit` is not honored (limit=5 → 265 results); `search_code` hardcodes 30 |
| 7 | 🟡 MEDIUM | `mcp_search_router` vs `search_router` vs `mcp_search_tools` | **3 divergent routers + 3 divergent tool schemas**; docs point at the wrong one |
| 8 | 🟡 MEDIUM | `search_semantic` (2 copies) | `distance`→similarity fallback differs (`0.5` vs `1.0`) → different scores for same query |
| 9 | 🟢 LOW | `test_mcp_client.py` | 1 async test **fails** (no `pytest-asyncio`); `test_sequential_thinking.py` **returns bool** (pytest anti-pattern) |

---

## 🔴 1. Ripgrep half of "hybrid" search returns 0 results (the big one)

**Symptom.** Every ripgrep-based call — `RipgrepSearcher.search()`,
`search_code()`, and `search_workspace()` without a language filter — returns an
empty list. `search_hybrid()` therefore returns semantic results only. The
"ripgrep + semantic hybrid" in the module docstrings is not real.

**Evidence.** Running `rg` the way the code runs it (from the workspace root,
no explicit path, default ignore handling) searches **0 bytes**:

```
$ ./.venv/bin/python - <<'PY'
import subprocess, os
print("CWD=", os.getcwd())
r = subprocess.run(["rg","-t","py","class"], cwd=".", capture_output=True, text=True)
print("rc=", r.returncode, "matches=", r.stdout.count(":"))
j = subprocess.run(["rg","--json","-t","py","class"], cwd=".", capture_output=True, text=True)
print("json rc=", j.returncode, "match-lines=", sum(1 for l in j.stdout.splitlines() if '"type":"match"' in l))
PY
CWD= <repo-root>
rc= 1 matches= 0
json rc= 1 match-lines= 0
# the json summary reports "bytes_searched":0  — ripgrep searched nothing.
```

But the **same binary with an explicit path works**:

```
$ rg class scripts | wc -l        → 120 matches
$ ./.venv/bin/python: subprocess ["rg","--json","--max-count","3","-C","2","-t","py","class","scripts"]
  → rc=0, 40 match-lines
```

**Why.** `RipgrepSearcher` builds the command as
`rg --json --max-count N -C C -t <types> <pattern>` with **no path argument and
no `--no-ignore`**, and runs it with `cwd=workspace_root`. In this workspace the
tree is a git repo, so ripgrep applies ignore resolution and ends up searching
0 bytes (rc=1). `RipgrepSearcher.search()` treats rc 0/1 as "no matches →
return `[]`" and only logs at `error`/`warning`, so the failure is **silent** —
the hybrid path just quietly degrades to semantic-only. (Note the shell-vs-
subprocess discrepancy: interactive `rg -t py class` in a terminal *does* find
matches here, so the code works in one context and silently produces nothing in
another — exactly the kind of environment fragility that makes this unreliable.)

**Fix (minimal, surgical).**
- Pass an explicit path to `rg`: add `str(self.workspace_root)` as the final
  argument of the command, **or** add `--no-ignore --hidden` and scope the
  search to a concrete path. Explicit path is the robust choice.
- Stop swallowing rc==1: distinguish "no matches" from "ripgrep error," and
  surface a real warning when 0 bytes are searched.
- Add a regression test that asserts a known pattern (e.g. `class`) yields >0
  results against the real tree.

---

## ✅ 2. The production MCP server can't start (bad import) — RESOLVED

> **Resolved 2026-10-10.** `search_server.py` was rewritten for the MCP 2.x SDK
> (`MCPServer` + `@mcp.tool()`), and client configs now launch it with the
> `.venv` interpreter (bare `python3` has no `mcp` package). Verified with a
> real MCP client: 4 tools listed, all 4 callable. See
> [IMPLEMENTATION_LOG.md](./IMPLEMENTATION_LOG.md#startup-incident-2026-10-10).
> The original finding is kept below for history.

**Symptom.** `search_server.py` — the "production MCP server that exposes your
search tools to clients" — crashes at import and therefore can never run.

**Evidence.**

```
$ ./.venv/bin/python -c "import sys; sys.path.insert(0,'scripts'); import search_server"
ImportError: cannot import name 'ToolResult' from 'mcp.types'
```

The installed MCP SDK has `CallToolResult` and `TextContent`, **not**
`ToolResult`:

```
has Tool: True | has TextContent: True | has ToolResult: False | has CallToolResult: True
```

`search_server.py` also annotates `async def call_tool(...) -> ToolResult` and
constructs `ToolResult(content=[...], isError=...)` — none of which exist.

**Fix.** Replace `ToolResult` with the SDK's actual return type
(`CallToolResult`/`list[TextContent]` per your `mcp` version) and fix the
return-type annotation, then add an import smoke test to the suite.

---

## 🟠 3. Semantic search returns entire files (no chunking)

**Symptom.** `index_workspace.WorkspaceIndexer.to_doc()` stores the **whole file
content as a single document** (`"text": self.content`). A semantic query then
returns that entire file, and `curate_for_llm=True` (which is the *default*)
passes it straight to the LLM.

**Evidence.** Real query, real index (45 docs):

```
$ ./.venv/bin/python scripts/mcp_search_tools.py --hybrid "how to deploy kubernetes" --limit 3
"content": "#!/usr/bin/env python3\n\"\"\"mcp_search_router.py — ...\n" ...  # entire ~11 KB file
```

The single "result" is the full 11 KB source of `mcp_search_router.py`. For
188-page PDFs or large docs this is a multi-thousand-token blob per hit, and
`LLMCurator`'s "token" estimate (`len*0.25`) is a rough guess, not a real
tokenizer — so "fits the context window" is not guaranteed.

**Fix.** Chunk on index (e.g. ~500–1000 token windows with overlap) and store a
per-chunk `line_start`/`line_end` in metadata; have `get_context`/curation
return the matching chunk + a few surrounding lines, not the file.

---

## 🟠 4. Query routing sends keyword queries to semantic-only

`QueryAnalyzer.analyze()` classifies a query by regex chars / code keywords /
"natural language," and `search_hybrid` only runs ripgrep for
`KEYWORD/REGEX/CODE/HYBRID` and only runs semantic for `SEMANTIC/HYBRID`.
The result: ordinary keyword queries get **semantic-only** and skip ripgrep —
the wrong tool for exact-match intent.

**Evidence.**

```
'kubernetes'        -> semantic
'kubernetes GPU'    -> semantic
'docker'            -> semantic
'import'            -> code
'class.*Base'       -> regex
'how do i deploy a pod' -> semantic
```

`"kubernetes"` and `"docker"` — classic exact/keyword lookups — never touch
ripgrep. And the "natural language" rule is `(... ) or not is_regex`, so almost
any non-regex query is "natural," which further starves the keyword/regex
branches.

**Fix.** Route by intent: run ripgrep for anything that is not unambiguously
semantic, and only skip semantic for pure code/regex; or just always run both
and rank. Drop the `not is_regex` shortcut.

---

## 🟠 5. Ripgrep context parsing is wrong (ordering + assignment)

In `livetext._parse_json_output`:

- **Context is string-sorted, not line-sorted.** `context_before.sort()` /
  `context_after.sort()` sort the *text lines* alphabetically, so the "context"
  around a match is scrambled and not in file order.
- **Context-to-match assignment is O(n·m) and ambiguous.** For each `context`
  event it loops over *all* matches in the same file and appends to whichever
  match's line is nearer — so with multiple matches in one file, context lines
  get attached to the wrong match (and duplicate).
- **`--max-count` is per-file, not global** (see #6), so "context" windows and
  the requested `limit` don't correspond.

**Fix.** Track each context event by `line_number` and bucket it against the
nearest match boundary using the numeric line number (not string sort), and cap
to a true global limit.

---

## 🟡 6. `limit` is not honored (per-file `--max-count`) + `search_code` ignores its arg

`_build_rg_command` uses `--max-count N`, which is ripgrep's **per-file** cap.
With many matching files the total blows past `N`. Also `search_code` hardcodes
`limit=30` and ignores any caller limit.

**Evidence.**

```
$ ./.venv/bin/python scripts/search_router.py
Example 2: Code Search (ripgrep only)   "def " python  limit=5
Found 265 results          # asked for 5, got 265
```

**Fix.** Either post-process to a true global cap (slice after dedup), or drive
the cap with a global limit instead of `--max-count`, and make `search_code`
respect its `limit` parameter.

---

## 🟡 7. Three divergent routers and three divergent tool schemas

The codebase has **no single source of truth** for "the search tool":

- `mcp_search_router.py` — `SearchRouter` (semantic-only; returns provider
  dicts) + `HTTPSearchServer` + CLI. This is the file the docs
  (`.github/copilot-instructions.md`, `WORKSPACE_INDEXING.md`, etc.) tell users
  to run for `--query`, `--serve`, `--stats`.
- `search_router.py` — `UnifiedSearchRouter` (hybrid; returns `SearchResult`
  objects with a `score` field).
- `mcp_search_tools.py` — `MCPSearchTools` (hybrid; 4 tools) — the one the MCP
  server actually wires.
- `mcp_tool_adapter.py` — `MCPSearchAdapter` wrapping the **semantic-only**
  `SearchRouter`, with its **own** 3-tool schema
  (`search_workspace`/`get_workspace_context`/`get_workspace_stats`).

So there are **3 different `MCP_TOOLS` definitions** (3 vs 3 vs 4 tools,
different names, different result shapes: `similarity` vs `score` vs raw
provider dict). The HTTP/CLI path users are pointed at is not the same object as
the MCP path, and they don't share result schemas.

**Fix.** Pick one router + one `MCP_TOOLS`/result schema; delete or
re-export the others; point all docs at the canonical entry point.

---

## 🟡 8. Inconsistent `distance`→`similarity` fallback

Two "semantic search" implementations disagree on the default when `distance` is
missing: `search_router.UnifiedSearchRouter.search_semantic` uses
`1.0 - match.get("distance", 0.5)` (→ 0.5), while
`mcp_search_tools.MCPSearchTools.search_semantic` uses
`1 - r.get("distance", 1)` (→ 0.0). Same query, different scores depending on
entry point.

**Fix.** Centralize the conversion in the provider (`vectordb_provider` already
returns `similarity`); have callers use that field directly.

---

## 🟢 9. Test-suite gaps

- `scripts/test_mcp_client.py::test_search_tools` **fails**: it's an `async
  def` test and the venv has no async plugin
  (`"async def functions are not natively supported"`). The suite is not green.
- `scripts/test_sequential_thinking.py::test_sequential_thinking_server`
  **returns a bool** (`return True/False`), which pytest rejects
  (`PytestReturnNotNoneWarning`) and which makes the "pass/fail" signal
  unreliable.
- The 118 "passing" tests largely **mock the vector layer and don't exercise the
  real ripgrep path**, which is why defects #1 and #3 slip through.

**Fix.** Install `pytest-asyncio` (or make the async test a sync wrapper),
convert the bool-returning test to `assert`, and add a real-ripgrep integration
test (assert >0 matches for a known pattern).

---

## Suggested fix order

1. **#1 + #6** — make ripgrep actually run and honor `limit` (unblocks the
   "hybrid" promise). Highest value.
2. **#2** — fix the `ToolResult` import so the MCP server can start.
3. **#3** — chunk on index; stop dumping whole files into context.
4. **#4** — fix query routing.
5. **#5 + #8** — correct context parsing and unify the score conversion.
6. **#7** — collapse to one router + one tool schema.
7. **#9** — green the suite and add real integration tests.

All findings above are reproducible from `mlaas/` with
`.venv/bin/python <command>`. No changes were made to source in producing this
analysis.
