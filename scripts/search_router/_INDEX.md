---
title: Search Router Subsystem Scripts Index
description: Index of hybrid search routing, ripgrep integration, MCP server, and adapter Python scripts
keywords:
- search router
- MCP server
- ripgrep
- livetext
- hybrid search
- ChromaDB
- tools
category: index
classification: 🟢🛡️ General
last_updated: '2026-10-16'
author: thatsafact
ai_search_aliases:
- search router scripts
- search server scripts
- mcp search scripts
---

# Search Router Subsystem Scripts Index

> **TL;DR:** Index of Python modules implementing hybrid search routing, ripgrep integration, and MCP server endpoints.
> **Use this for:** Locating search algorithms, MCP tool handlers, and server entry points.

## Contents

| File / Folder | Description | Keywords |
|---------------|-------------|----------|
| 🐍 [`search_router.py`](search_router.py) | Unified hybrid search router combining keyword recall (ripgrep) and semantic precision (ChromaDB) | unified router, hybrid search, ranking, curation |
| 🐍 [`search_server.py`](search_server.py) | Production stdio MCP server exposing hybrid search tools to AI agents | MCP server, stdio, search server, agent tools |
| 🐍 [`livetext.py`](livetext.py) | RipgrepSearcher wrapper for fast code-aware search and context extraction | ripgrep, livetext, code search, regex |
| 🐍 [`mcp_search_tools.py`](mcp_search_tools.py) | MCP tool definitions for search_workspace, search_code, and search_semantic | mcp tools, handlers, tool schemas |
| 🐍 [`mcp_tool_adapter.py`](mcp_tool_adapter.py) | Adapter bridging SearchRouter to MCP tool handlers with JSON/text formats | mcp adapter, tool adapter, formats |
| 🐍 [`mcp_search_router.py`](mcp_search_router.py) | CLI and HTTP search server interface with LLM context formatting | search router CLI, HTTP server, query runner |
| 🐍 [`mcp_server_integration.py`](mcp_server_integration.py) | Integration patterns and examples for connecting MCP search tools | mcp integration, server patterns, examples |
| 🐍 [`mcp_examples.py`](mcp_examples.py) | Standalone demonstration examples calling MCP search adapter tools | mcp examples, tool demos, usage |
| 🐍 [`tantivy_searcher.py`](tantivy_searcher.py) | Tantivy BM25 inverted index search engine wrapper for ultra-fast full-text search | tantivy, BM25, full-text, inverted index |
| 🐍 [`graphify_searcher.py`](graphify_searcher.py) | Graphify AST and Knowledge Graph searcher querying code symbols and markdown sections | graphify, AST, symbols, code graph |
| 🐍 [`speed_test.py`](speed_test.py) | High-precision latency benchmark runner measuring p50/p90/max across all search engines | speed test, benchmark, SLA, latency |
