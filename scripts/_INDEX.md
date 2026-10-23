---
title: Scripts & Tooling Master Index
description: 'Master index of operational Python subsystems: search routing, indexing, automation, and test suites'
keywords:
- scripts index
- Python scripts
- search router
- indexing
- automation
- test suite
- architecture
category: index
classification: 🟢🛡️ General
last_updated: '2026-10-20'
author: thatsafact
ai_search_aliases:
- scripts index
- find scripts
- python tools table
- scripts list
- subsystems
---

# Scripts & Tooling Master Index

> **TL;DR:** Modular catalog of Python scripts organized into search_router, indexing, automation, and tests subdirectories.
> **Use this for:** Discovering CLI tools, servers, batch automation, and test suites in the `scripts/` directory.

## Contents

| File / Folder | Description | Keywords |
|---------------|-------------|----------|
| 📁 [search_router/](search_router/_INDEX.md) | Hybrid ripgrep + ChromaDB search router, MCP tools, and stdio search server | search router, search_server, livetext, adapter, mcp |
| 📁 [indexing/](indexing/_INDEX.md) | Workspace document indexing CLI, ChromaDB provider abstraction, and vector database examples | indexing, chromadb, vectordb, embeddings, indexer |
| 📁 [telemetry/](telemetry/_INDEX.md) | Team prompt telemetry ingestion engine, SQLite FTS5 indexer, and analytics tools | telemetry, prompt tracking, fts5, doc attribution |
| 📁 [automation/](automation/_INDEX.md) | Documentation maintenance tools, metadata enrichers, PDF-to-MD converter, and diagnostic probes | automation, metadata, toc generator, pdf converter |
| 📁 [tests/](tests/_INDEX.md) | Comprehensive unit and integration test suite covering all subsystems (154 passing tests) | tests, pytest, unit tests, integration tests |
| 🐍 [`search_server.py`](search_server.py) | Backward-compatible trampoline to search_router/search_server.py | search server, trampoline, compatibility |
| 🐍 [`index_workspace.py`](index_workspace.py) | Backward-compatible trampoline to indexing/index_workspace.py | indexing, trampoline, compatibility |
| 🐍 [`mcp_search_router.py`](mcp_search_router.py) | Backward-compatible trampoline to search_router/mcp_search_router.py | mcp search router, trampoline, compatibility |
| 🐍 [`sqlite_server.py`](sqlite_server.py) | SQLite MCP server exposing read_query, describe_table, and performance telemetry tools | sqlite mcp, metrics db, copilot db |
| 🐍 [`mcp_speed_bench.py`](mcp_speed_bench.py) | Latency benchmark runner measuring MCP search tools across single and hybrid queries | speed bench, latency, benchmark, SLA |
| 🐍 [`conftest.py`](conftest.py) | Root pytest configuration and shared test fixtures | pytest, fixtures, configuration |
| 📄 [`CROSS_PLATFORM_PLAN.md`](CROSS_PLATFORM_PLAN.md) | Cross-platform modernization plan and authoritative Python authoring instructions for macOS and Windows 11 | cross-platform, windows, macos, authoring instructions, plan |
| 🛠️ [`find-scripts` Skill](../.github/skills/find-scripts/SKILL.md) | Lean AI skill orchestrator and protocol for auditing existing scripts before authoring new code | find scripts, anti-dupe, tooling inventory |
| 🛠️ [`client-neutral-content` Skill](../.github/skills/client-neutral-content/SKILL.md) | Keeps client commentary out of OSS-scope files; pairs with `automation/client_term_scan.py` | client neutral, oss hygiene, scrub, de-brand |
