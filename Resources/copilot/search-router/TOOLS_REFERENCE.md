---
title: MCP Search Tools Reference
description: API schema and parameter reference for search_workspace, get_workspace_context, and get_workspace_stats
keywords:
- tools reference
- MCP tools
- search_workspace
- tool schema
- API reference
category: reference
classification: 🟢🛡️ General
last_updated: '2026-10-11'
author: thatsafact
ai_search_aliases:
- mcp tools reference
- search tools api
- search tool schemas
---

# MCP Tools Reference

> **TL;DR:** Detailed API reference defining input schemas, return types, and example payloads for all workspace MCP search tools.
> **Use this for:** Implementing or calling MCP search tools from AI agent harnesses.

Tools exposed by `scripts/search_server.py` (server name `search-router`, registered in clients as `mlaas-search`). All tools return a JSON string with a `status` field.

## `search_workspace` — hybrid

Routes the query to ripgrep, ChromaDB, or both, then deduplicates, ranks and curates.

| Parameter | Type | Default | Notes |
|-----------|------|---------|-------|
| `query` | string | required | Natural language, regex or code pattern |
| `limit` | int | 10 | 1-100 |
| `curate_for_llm` | bool | true | Trim to a token budget |
| `language` | string | none | Restrict the code half to one language |

Returns `status`, `query`, `query_type` (`KEYWORD`/`CODE`/`REGEX`/`SEMANTIC`/`HYBRID`), `routing_confidence`, `result_count`, `results[]` (`id`, `path`, `content`, `score`, source), `metadata`.

## `search_code` — ripgrep only

| Parameter | Type | Default | Notes |
|-----------|------|---------|-------|
| `pattern` | string | required | Regex or literal |
| `language` | string | none | Mapped to ripgrep file types |
| `limit` | int | 20 | |
| `context_lines` | int | 3 | 0-10 |

Returns `status`, `pattern`, `language`, `result_count`, `results[]` (`file`, `line`, `content`, `context_before`, `context_after`).

Language mapping: python→py, javascript→js, typescript→ts/tsx, rust→rs, go→go, c→c, cpp→cpp/cc/cxx/h/hpp, java→java, yaml→yaml/yml, json→json, markdown→md/markdown, shell→sh/bash.

## `search_semantic` — ChromaDB only

| Parameter | Type | Default | Notes |
|-----------|------|---------|-------|
| `query` | string | required | Natural language |
| `limit` | int | 10 | |
| `threshold` | float | 0.3 | Minimum similarity, 0.0-1.0 |

Returns `status`, `query`, `threshold`, `result_count`, `results[]` (`file`, `line`, `content`, `similarity`).

## `get_search_stats`

No parameters. Returns `tools.ripgrep_available`, `tools.chromadb_available`, and `database` (`path`, `collection`, `provider`, `stats.document_count`).

## Choosing a tool

| Need | Tool | Engine Used |
|------|------|-------------|
| General hybrid query across workspace | `search_workspace` | Multi-Index Router (Ripgrep + ChromaDB + Tantivy + Graphify) |
| Exact regex / substring in working tree | `search_code` | Ripgrep (`livetext.py`) |
| Conceptual or architectural question | `search_semantic` | ChromaDB vector index |
| AST class/function/call-graph search | `search_symbols` | Graphify AST Knowledge Graph |
| Broad BM25 search across all files | `search_everything` | Tantivy Inverted Index |
| Health, backends, and indexed counts | `get_search_stats` | Diagnostic status across all 4 engines |

---

## Live Multi-Index Tools (Phase 6)

### `search_symbols` — Graphify AST Knowledge Graph

Queries structural AST nodes (classes, functions, methods) and dependency relationships using Tree-sitter parsers and local Ollama LLM (`qwen3.8:27b`).

| Parameter | Type | Default | Notes |
|-----------|------|---------|-------|
| `query` | string | required | Class, function, method name, or pattern |
| `kind` | string | none | `class`, `function`, `method` filter |
| `file_filter` | string | none | Restrict to file path substring |
| `limit` | int | 15 | Max symbol matches |

Returns AST symbol nodes, line definitions (`L<line>`), file locations, and structural caller/callee graphs.

### `search_everything` — Tantivy BM25 Inverted Index

Fast full-text and boolean search across the entire workspace using the Rust-powered Tantivy inverted index.

| Parameter | Type | Default | Notes |
|-----------|------|---------|-------|
| `query` | string | required | Keywords or boolean expression |
| `limit` | int | 10 | 1-100 results |

Returns scored document matches with BM25 rankings, snippets, and highlights in sub-5ms latency.

---

## Usage tips

- Be specific and add a language filter for code questions.
- Keep `limit` small (5-10) to save tokens.
- Re-index workspace after adding docs: `.venv/bin/python3 scripts/indexing/index_workspace.py --workspace . --db-path .chroma`.

## Using the Python library directly

```python
from search_router.mcp_search_tools import MCPSearchTools
tools = MCPSearchTools(db_path=".chroma", workspace_root=".")
tools.search_code(pattern="def deploy", language="python", limit=5)
tools.search_semantic(query="kubernetes deployment", limit=3)
tools.search_workspace(query="deploy kubernetes", limit=5)
tools.stats()
```

Command-line entry points: `scripts/search_router/mcp_search_router.py` (`--query`, `--stats`, `--context`), `scripts/search_router/search_server.py` (stdio MCP server), and `scripts/search_router/mcp_examples.py`.
