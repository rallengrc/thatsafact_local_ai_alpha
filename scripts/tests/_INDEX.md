---
title: Test Suite Index
description: Index of unit and integration test modules covering search routing, indexing, MCP tools, and reasoning
keywords:
- test suite
- pytest
- unit tests
- integration tests
- indexing tests
- search tests
category: index
classification: 🟢🛡️ General
last_updated: '2026-10-20'
author: thatsafact
ai_search_aliases:
- test suite index
- pytest scripts
- run tests
---

# Test Suite Index

> **TL;DR:** Comprehensive test suite containing 119 unit and integration tests across all workspace subsystems.
> **Use this for:** Verifying code changes, checking test coverage, and validating search accuracy.

## Contents

| File / Folder | Description | Keywords |
|---------------|-------------|----------|
| 🐍 [`test_indexing.py`](test_indexing.py) | Unit tests for WorkspaceIndexer, ChromaDBProvider, and MCP tool adapter (21 tests) | indexing tests, chromadb tests, pytest |
| 🐍 [`test_search_router.py`](test_search_router.py) | Unit tests for UnifiedSearchRouter, query analyzer, deduplicator, ranker, and curator (20 tests) | search router tests, unit tests, pytest |
| 🐍 [`test_livetext.py`](test_livetext.py) | Unit tests for RipgrepSearcher code-aware search and context extraction (16 tests) | livetext tests, ripgrep tests, pytest |
| 🐍 [`test_mcp_search_tools.py`](test_mcp_search_tools.py) | Unit tests for MCPSearchTools tool definitions and handlers (10 tests) | mcp search tools tests, tool tests |
| 🐍 [`test_mcp_client.py`](test_mcp_client.py) | Integration tests verifying MCP client connections to the search server | mcp client tests, integration tests |
| 🐍 [`test_sequential_thinking.py`](test_sequential_thinking.py) | Smoke tests verifying sequential thinking server execution | sequential thinking tests, reasoning tests |
| 🐍 [`test_mcp_smoke.py`](test_mcp_smoke.py) | End-to-end smoke tests for MCP search tools via stdio client | mcp smoke tests, e2e tests |
| 🐍 [`test_phase6_search.py`](test_phase6_search.py) | Multi-engine search tests for Tantivy, Graphify, and hybrid router (52 tests) | phase 6 tests, tantivy tests, graphify tests |
| 🐍 [`test_sqlite_mcp.py`](test_sqlite_mcp.py) | Unit and integration tests for SQLite MCP server and query tools (20 tests) | sqlite tests, mcp tests |
| 🐍 [`test_client_term_scan.py`](test_client_term_scan.py) | Tests for the client-neutral content scanner and the private-scope label helper (19 tests) | client neutral tests, scanner tests |
| 🐍 [`test_common_platform.py`](test_common_platform.py) | Tests for cross-platform utilities, path normalization, venv discovery, and dynamic root resolution (44 tests) | common platform tests, cross-platform |
| 🐍 [`test_prompt_telemetry.py`](test_prompt_telemetry.py) | Tests for prompt telemetry ingestion engine, FTS5 sync, and doc attribution | telemetry tests, prompt tests |
| 🐍 [`test_private_config.py`](test_private_config.py) | Tests for private generator config loading and validation | private config tests, generator tests |
