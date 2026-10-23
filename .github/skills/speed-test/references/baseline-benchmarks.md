---
title: "Search Router v2 — Baseline Benchmarks & SLA Targets"
description: "Authoritative baseline latencies, p50 measurements, and SLA validation targets for Tantivy, Graphify, ChromaDB, Ripgrep, and Hybrid search engines."
shield: "internal"
last_updated: "2026-10-11"
keywords: [speed-test, benchmarks, search-router, tantivy, graphify, chromadb, ripgrep, sla, latency]
---

# Search Router v2 — Baseline Benchmarks & SLA Targets

> **TL;DR:** Authoritative baseline latency profiles established on 2026-10-11 across all 5 search subsystems. All engines exceed their SLAs by 4x to 100x.
> **Use this for:** Performance regression tracking, SLA audits, and search optimization.

---

## 1. Authoritative Baseline Performance

Measurements recorded across 5 iterations with 2 warmup passes on macOS Apple Silicon:

| Search Engine | Implementation | Target SLA | Baseline p50 | Baseline Avg | Hits / Query | Margin | Status |
|---|---|---|---|---|---|---|---|
| **Tantivy BM25** | Rust Inverted Index | < 10.0 ms | **0.10 ms** | 0.10 ms | 10 | 100x faster | ✅ PASS |
| **Graphify AST** | Tree-sitter Code Graph | < 25.0 ms | **0.26 ms** | 0.26 ms | 2–6 | 96x faster | ✅ PASS |
| **Ripgrep Code** | `rg` Zero-Index Scan | < 80.0 ms | **9.65 ms** | 9.68 ms | 2–12 | 8x faster | ✅ PASS |
| **Hybrid Router** | Multi-Engine + RRF Fusion | < 400.0 ms | **34.59 ms** | 35.18 ms | 6–8 | 11x faster | ✅ PASS |
| **ChromaDB Vector** | ONNX Dense Embeddings | < 300.0 ms | **46.28 ms** | 46.40 ms | 10 | 6.5x faster | ✅ PASS |

---

## 2. Test Environment Configuration

- **Host Machine:** macOS (Apple Silicon arm64)
- **Local LLM Daemon:** Ollama (`http://localhost:11434`) running `qwen3.8:27b` (NVFP4 quantization via MLX)
- **Virtual Environment:** Python 3.14 via `.venv/`
- **Indexed Corpora:**
  - **Tantivy (`.tantivy/`):** 160 markdown, code, and config documents
  - **Graphify (`.graphify/graph.json`):** 746 AST symbol nodes and 1,063 dependency edges across 34 Python files
  - **ChromaDB (`.chroma/`):** 189 high-value workspace documents
  - **Ripgrep:** Live file-system scanning across workspace root

---

## 3. SLA Pass/Fail Criteria

A search engine run fails the SLA test if any of the following occur:
1. **p50 Latency Violation:** Engine p50 exceeds its target threshold in Section 1.
2. **Empty Return on Indexed Keys:** A query for known indexed symbols (e.g. `UnifiedSearchRouter`) returns 0 hits.
3. **Cloud Egress Leak:** Local Graphify AST extraction attempts external cloud API calls instead of local Ollama (`qwen3.8:27b`).
4. **Crash or Exception:** Any unhandled exception during search execution.

---

## 4. Remediation & Diagnostics

| Symptom | Probable Cause | Corrective Action |
|---|---|---|
| Tantivy returns 0 hits | Missing or unbuilt `.tantivy/` index | Run `.venv/bin/python3 scripts/indexing/index_tantivy.py --clear` |
| Graphify returns 0 hits | Missing `.graphify/graph.json` | Run `.venv/bin/python3 scripts/indexing/index_graphify.py --clear` |
| ChromaDB latency > 300ms | Large batch query or memory pressure | Check `.chroma/` size; clear and reindex if corrupted |
| Ripgrep returns 0 hits | Pattern syntax or missing `rg` CLI | Verify `which rg` and check pattern escape characters |
