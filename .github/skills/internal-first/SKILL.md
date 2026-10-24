---
name: internal-first
description: "Sticky mode controlling local multi-index search injection (RRF across Tantivy, Graphify, Ripgrep, ChromaDB) before LLM tool calling. TRIGGERS: 'internal-first', 'external-first'."
disable-model-invocation: true
last_updated: "2026-10-24"
---

# 🔍 internal-first / external-first — Sticky Local Search Router Gate

> **Purpose:** Controls whether local Search Router v2 (Tantivy + Graphify + Ripgrep + ChromaDB) pre-routes queries and injects code snippets into LLM context before tool execution.

## Sticky Mode States

| Trigger | State | Behavior |
|---------|-------|----------|
| `internal-first` | **Active (Sticky)** | Runs local multi-index search with RRF scoring on Apple Silicon (<50ms). Pre-injects top-5 snippets (≤1,500 tokens) into prompt. Persists until changed. |
| `external-first` | **Inactive (Sticky)** | Bypasses local RRF pre-injection. Returns to default direct on-demand tool execution (`grep`, `view`, etc.). Persists until changed. |

## Execution Contract

1. **Local Pre-Routing:** When `internal-first` is active, run `.venv/bin/python3 scripts/search_router/search.py --query "<query>" --limit 5` or direct python router call.
2. **Context Budget:** Hard ceiling of ≤1,500 tokens / 5 snippets to prevent "lost in the middle" context degradation.
3. **Zero Cloud Tokens:** All retrieval runs on local M-series silicon before sending the query to the primary model.
