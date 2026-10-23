---
title: "Agent Workflows & Operations Reference"
description: "Authoritative commands for building, testing, indexing, and debugging the MLaaS search router and surrogate ML systems"
shield: "internal"
last_updated: "2026-10-11"
keywords: [workflows, commands, pytest, indexing, debugging, search-router, operations]
---

# Agent Workflows & Operations Reference

> **TL;DR:** Command reference for testing, indexing, benchmarking, and troubleshooting the MLaaS workspace systems.
> **Use this for:** Executing day-to-day development operations with `.venv` Python.

---

## 1. Test Execution Commands

Always use `.venv/bin/python3` or `.venv/bin/pytest`:

```bash
# Run complete test suite (136 tests)
.venv/bin/python3 -m pytest scripts/tests/ -v

# Run targeted test files
.venv/bin/python3 -m pytest scripts/tests/test_search_router.py -v
.venv/bin/python3 -m pytest scripts/tests/test_phase6_search.py -v
.venv/bin/python3 -m pytest scripts/tests/test_indexing.py -v
.venv/bin/python3 -m pytest scripts/tests/test_mcp_search_tools.py -v

# Run with test coverage report
.venv/bin/python3 -m pytest scripts/tests/ --cov=scripts --cov-report=term-missing
```

---

## 2. Multi-Index Maintenance Commands

```bash
# 1. Inverted BM25 Index (Tantivy): 172 docs
.venv/bin/python3 scripts/indexing/index_tantivy.py --clear
.venv/bin/python3 scripts/indexing/index_tantivy.py --stats

# 2. AST Code Knowledge Graph (Graphify): 860 nodes across 39 files
.venv/bin/python3 scripts/indexing/index_graphify.py --clear
.venv/bin/python3 scripts/indexing/index_graphify.py --stats

# 3. Dense Semantic Embeddings (ChromaDB): 189 high-value docs
.venv/bin/python3 scripts/indexing/index_workspace.py --clear --workspace . --provider chromadb --db-path .chroma
.venv/bin/python3 scripts/indexing/index_workspace.py --stats

# 4. Workspace Index & TOC Generation
.venv/bin/python3 scripts/automation/generate_indices_and_master_toc.py
```

---

## 3. Speed & Latency Benchmarks

```bash
# Run full 5-engine benchmark suite (Tantivy, Graphify, Ripgrep, ChromaDB, Hybrid)
.venv/bin/python3 scripts/search_router/speed_test.py

# Isolate single engine or export JSON
.venv/bin/python3 scripts/search_router/speed_test.py --engine tantivy
.venv/bin/python3 scripts/search_router/speed_test.py --engine graphify
.venv/bin/python3 scripts/search_router/speed_test.py --json
```

---

## 4. Troubleshooting Matrix

| Issue | Root Cause | Resolution |
|---|---|---|
| `ModuleNotFoundError` | Missing package or using system Python | Run `.venv/bin/pip install -r requirements.txt`. Never use bare `pip`. |
| Tantivy returns 0 hits | Index uninitialized or corrupted | Rebuild index: `.venv/bin/python3 scripts/indexing/index_tantivy.py --clear` |
| Graphify AST returns 0 hits | Missing `.graphify/graph.json` | Rebuild graph: `.venv/bin/python3 scripts/indexing/index_graphify.py --clear` |
| ChromaDB slow query (>300ms) | Memory thrashing or stale `.chroma/` | Run index stats and re-index workspace. |
| Ollama local LLM unreachable | Ollama daemon stopped | Check `curl http://localhost:11434/api/tags` and ensure `qwen3.8:27b` is present. |
