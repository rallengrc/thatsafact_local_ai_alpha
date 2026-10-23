---
title: Scripts & Tooling Master Inventory
description: Categorized reference inventory of all 46 Python scripts across search routing, indexing, automation, and test subsystems
keywords: [scripts inventory, tooling catalog, python scripts, automation, indexing, search router, pdf converter]
category: reference
classification: 🟢🛡️ General
last_updated: '2026-10-12'
author: thatsafact
ai_search_aliases: [scripts inventory, find all scripts, existing tools, script catalog, list scripts]
---

# Scripts & Tooling Master Inventory

> **TL;DR:** Authoritative directory of all 46 Python scripts in `scripts/`, organized by subsystem with CLI flags, descriptions, and trampolines.
> **Use this for:** Quickly determining which script to execute or extend instead of creating duplicate code.

---

## 1. Automation Subsystem (`scripts/automation/`)

| Script | Purpose & Capabilities | Typical CLI Invocation |
|---|---|---|
| `pdf_to_md.py` | Full PDF converter extracting text + placed images (frequency-aware running logo filter) | `.venv/bin/python scripts/automation/pdf_to_md.py input.pdf` |
| `pdf_to_md_fast.py` | High-speed text + deduplicated image gallery converter for massive (1000+ pg) PDFs | `.venv/bin/python scripts/automation/pdf_to_md_fast.py input.pdf` |
| `ocr_packt_figures.py` | Tesseract OCR for text-bearing screenshots/dashboards/logs into Markdown sidecars | `.venv/bin/python scripts/automation/ocr_packt_figures.py` |
| `insert_ocr_links.py` | Idempotent linker inserting `> 📝 OCR transcript` links under figures in markdown | `.venv/bin/python scripts/automation/insert_ocr_links.py` |
| `chunk_aws_docs.py` | Split oversized (>1.5MB) docs into retrieval chunks (`.chunks/*.md`) while keeping full doc | `.venv/bin/python scripts/automation/chunk_aws_docs.py` |
| `add_aws_frontmatter.py` | Injects compliant YAML frontmatter + TL;DR into extracted AWS Markdown guides | `.venv/bin/python scripts/automation/add_aws_frontmatter.py` |
| `generate_indices_and_master_toc.py` | Regenerates all `_INDEX.md` files across workspace and `MASTER_TOC.md` | `.venv/bin/python scripts/automation/generate_indices_and_master_toc.py` |
| `update_markdown_metadata.py` | Batch enriches Markdown files with standardized frontmatter and tags | `.venv/bin/python scripts/automation/update_markdown_metadata.py` |
| `export_memories.py` | Extracts prompt history and VS Code turns into namespaced user memory files | `.venv/bin/python scripts/automation/export_memories.py --user <name>` |
| `probe.py` | Diagnostics checking Apple Silicon hardware, MLX, and Ollama runtime status | `.venv/bin/python scripts/automation/probe.py` |
| `setup_memory_link.py` | Per-machine setup linking Claude Code's project memory directory to `memories/mlaas/` | `.venv/bin/python scripts/automation/setup_memory_link.py` |

---

## 2. Workspace Indexing Subsystem (`scripts/indexing/`)

| Script | Purpose & Capabilities | Typical CLI Invocation |
|---|---|---|
| `index_workspace.py` | Scans workspace and builds ChromaDB persistent vector database | `.venv/bin/python scripts/indexing/index_workspace.py --workspace .` |
| `index_tantivy.py` | Builds high-speed Tantivy BM25 inverted index for workspace text and code | `.venv/bin/python scripts/indexing/index_tantivy.py --workspace .` |
| `index_graphify.py` | AST & Markdown Knowledge Graph indexer (Tree-sitter Python AST + doc sections) | `.venv/bin/python scripts/indexing/index_graphify.py --workspace .` |
| `vectordb_provider.py` | Abstract provider interface (`VectorDBProvider`) and ChromaDB provider factory | Imported: `from vectordb_provider import get_provider` |
| `examples.py` | Sample patterns for ChromaDB indexing, custom collections, and searches | `.venv/bin/python scripts/indexing/examples.py` |

---

## 3. Search Router Subsystem (`scripts/search_router/`)

| Script | Purpose & Capabilities | Typical CLI Invocation |
|---|---|---|
| `search_router.py` | Unified search router fusing Ripgrep, ChromaDB, Tantivy, and Graphify AST | Imported: `from search_router import UnifiedSearchRouter` |
| `search_server.py` | Stdio MCP server exposing `search_workspace`, `search_code`, `search_semantic`, etc. | `.venv/bin/python scripts/search_router/search_server.py` |
| `livetext.py` | Ripgrep wrapper (`RipgrepSearcher`) for fast code-aware regex searching | Imported: `from livetext import RipgrepSearcher` |
| `tantivy_searcher.py` | Tantivy BM25 full-text engine interface | Imported: `from tantivy_searcher import TantivySearcher` |
| `graphify_searcher.py` | Graphify AST symbol and markdown section searcher | Imported: `from graphify_searcher import GraphifySearcher` |
| `mcp_search_router.py` | CLI query interface & HTTP search server with LLM context formatter | `.venv/bin/python scripts/search_router/mcp_search_router.py --query "..."` |
| `speed_test.py` | Engine benchmark suite measuring p50/p90/max latencies against SLAs | `.venv/bin/python scripts/search_router/speed_test.py` |
| `mcp_search_tools.py` | MCP tool definitions, JSON schemas, and handler mappings | Imported by MCP servers |
| `mcp_tool_adapter.py` | Bridges SearchRouter output to MCP formats (JSON/markdown context) | Imported by MCP servers |
| `mcp_server_integration.py` | Reference patterns for integrating MCP search tools into applications | `.venv/bin/python scripts/search_router/mcp_server_integration.py` |
| `mcp_examples.py` | 7 standalone usage examples demonstrating MCP tool calls | `.venv/bin/python scripts/search_router/mcp_examples.py` |

---

## 4. Root Trampolines & Servers (`scripts/`)

| Script | Purpose & Trampoline Target | Note |
|---|---|---|
| `search_server.py` | Trampoline to `scripts/search_router/search_server.py` | Backward compatibility for MCP clients |
| `index_workspace.py` | Trampoline to `scripts/indexing/index_workspace.py` | Backward compatibility for CLI users |
| `mcp_search_router.py` | Trampoline to `scripts/search_router/mcp_search_router.py` | Backward compatibility for CLI users |
| `sqlite_server.py` | Standalone SQLite MCP server exposing queries on metrics and copilot databases | Custom tools: `read_query`, `describe_table` |
| `mcp_speed_bench.py` | Standalone benchmark comparing Search Router MCP endpoint response times | Used for SLA verification |
| `conftest.py` | Pytest root configuration and shared fixtures for entire test suite | Pytest runner integration |

---

## 5. Test Suite (`scripts/tests/`)

Run entire suite: `.venv/bin/python -m pytest scripts/` (146 tests, all passing).
- `test_indexing.py`: ChromaDB provider & indexing (21 tests)
- `test_search_router.py`: Unified router, deduplication, ranking (20 tests)
- `test_livetext.py`: RipgrepSearcher code search (16 tests)
- `test_mcp_search_tools.py`: Tool definitions & handlers (10 tests)
- `test_mcp_client.py`: MCP client connections & schema validation (5 tests)
- `test_mcp_smoke.py`: End-to-end smoke tests for MCP tools (5 tests)
- `test_phase6_search.py`: Tantivy, Graphify, and hybrid multi-engine search (52 tests)
- `test_sqlite_mcp.py`: SQLite MCP server and query tools (20 tests)
- `test_sequential_thinking.py`: Sequential thinking tool validation (2 tests)
