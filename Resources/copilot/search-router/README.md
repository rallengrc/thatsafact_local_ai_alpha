---
title: Search Router Subsystem Overview & Navigation Map
description: Subsystem overview and documentation index for the hybrid search router and vector index
keywords:
- search router
- navigation map
- subsystem overview
- ChromaDB
- ripgrep
category: index
classification: 🟢🛡️ General
last_updated: '2026-10-11'
author: thatsafact
ai_search_aliases:
- search router readme
- search router overview
- search router documentation
---

# MLaaS Search Router

> **TL;DR:** Subsystem README detailing the motivation, architecture, and navigation map for all search router and indexing documentation.
> **Use this for:** Orienting yourself within the search router documentation set.

Hybrid workspace search that combines **ripgrep** (exact/regex) with **ChromaDB** (semantic), curated for LLM context and exposed to MCP clients (Copilot CLI, VS Code, Claude Desktop) as four tools.

## Documents

| File | Read it for |
|------|-------------|
| [CHECKPOINT_SUMMARY.md](./CHECKPOINT_SUMMARY.md) | Authoritative milestone record (189 docs, 119 tests, live status) and v2 roadmap |
| [SEARCH_ROUTER_PLAN.md](./SEARCH_ROUTER_PLAN.md) | Complete engineering roadmap: v1 delivery & v2 Multi-Index design specs |
| [IMPLEMENTATION_LOG.md](./IMPLEMENTATION_LOG.md) | Phase status, deliverables, test results, performance, technical decisions |
| [TOOLS_REFERENCE.md](./TOOLS_REFERENCE.md) | The MCP tools: parameters, return shapes, when to use which, usage patterns |
| [WORKSPACE_INDEXING.md](./WORKSPACE_INDEXING.md) | Vector indexing operations manual (ChromaDB) and planned indexers |
| [QUICK_START.md](./QUICK_START.md) | Fast 5-minute setup and test command cheat sheet |
| [MCP_SETUP.md](../MCP_SETUP.md) | Installing, configuring and troubleshooting the MCP servers in each client |
| [SEQUENTIAL_THINKING_INTEGRATION.md](../SEQUENTIAL_THINKING_INTEGRATION.md) | How the `sequentialthinking` server complements search |
| [DEFECT_ANALYSIS.md](./DEFECT_ANALYSIS.md) | Known defects and suggested fix order |

## Architecture (v1 Hybrid + v2 Multi-Index Horizon)

```
MCP clients (Copilot CLI / VS Code / Claude Desktop)
        │  JSON-RPC over stdio
        ▼
scripts/search_router/search_server.py      MCPServer("mlaas-search"), 4 @mcp.tool() functions
        ▼
scripts/search_router/mcp_search_tools.py   MCPSearchTools: validation, serialization, language mapping
        ▼
scripts/search_router/search_router.py      UnifiedSearchRouter
  QueryAnalyzer → ResultDeduplicator → ResultRanker → LLMCurator
        ├──────────────────────┬──────────────────────┬──────────────────────┐
        ▼                      ▼                      ▼                      ▼
scripts/search_router/   scripts/indexing/      [Planned v2]           [Planned v2]
livetext.py              vectordb_provider.py   tantivy_provider.py    graphify_provider.py
RipgrepSearcher (rg)     ChromaDBProvider       Tantivy BM25 Engine    Graphify AST Engine
(Live regex/substring)   (.chroma/ 189 docs)    (Broad workspace/code) (code/ AST call graph)
```

![Search Router v2 Architecture](../../visualization/search-router-v2-architecture.png)

Query routing (`QueryAnalyzer`): Routes code symbols to Graphify AST, regex/literals to Ripgrep, broad keywords/booleans to Tantivy BM25, and natural language to ChromaDB. Results undergo AST span containment, Reciprocal Rank Fusion (RRF), and LLM token curation.

## Status

- **v2 Multi-Index Search:** Fully implemented and verified across 4 specialized engines.
- **Test Suite:** **136 / 136 tests passing** (`pytest scripts/tests/`).
- **Indexed Corpora:** **189 docs** in ChromaDB, **172 docs** in Tantivy BM25, **860 AST nodes** in Graphify.
- **Local LLM Enforcement:** 100% offline local inference via Ollama `qwen3.8:27b` on MLX (zero cloud spend).

## Quick start

```bash
cd <repo-root>                                                                  # or: cd "$MLAAS_ROOT"
.venv/bin/python3 -m pytest scripts/tests/ -v                                  # run all 136 unit tests
.venv/bin/python3 scripts/search_router/speed_test.py                         # run precision latency benchmark
.venv/bin/python3 scripts/search_router/search_server.py                       # launch MCP server on stdio
```

The server must be launched with `.venv/bin/python3`; the system `python3` has no `mcp` package. See [MCP_SETUP.md](../MCP_SETUP.md) for client configuration.

## Related files outside this folder

- Indexing: [WORKSPACE_INDEXING.md](./WORKSPACE_INDEXING.md), [INDEXING.md](./INDEXING.md)
- Contributor guidance: [.instructions.md](../../../.instructions.md), [.github/copilot-instructions.md](../../../.github/copilot-instructions.md)
