---
name: speed-test
description: "Run latency benchmarks across Search Router v2 engines (Tantivy, Graphify, ChromaDB, Ripgrep, Hybrid) for regression and SLA checks. TRIGGERS: 'speed-test', 'benchmark search', 'search latency'."
last_updated: "2026-10-11"
---

# ⚡ Speed Test — Search Router Performance & SLA Benchmark

> **Purpose:** Measure search latency across all 4 search engines + hybrid router, compare against baseline targets, and enforce performance SLAs.

## Triggers
- `speed-test`
- `benchmark search`
- `test search router`
- `search latency`
- `test speed`

## Quick Summary
The Search Router v2 coordinates 4 specialized engines. Speed Test validates sub-millisecond keyword retrieval, AST symbol indexing, and vector similarity before and after code changes.

```bash
# Run full automated benchmark suite
.venv/bin/python3 scripts/search_router/speed_test.py
```

## Dispatch Table

| Mode | Command | Target Engine | SLA Target |
|---|---|---|---|
| **Full Suite** | `.venv/bin/python3 scripts/search_router/speed_test.py` | All 5 subsystems | All pass |
| **Broad Inverted** | `.../speed_test.py --engine tantivy` | Tantivy BM25 | < 10 ms (p50) |
| **AST Symbol** | `.../speed_test.py --engine graphify` | Graphify AST Graph | < 25 ms (p50) |
| **Regex Code** | `.../speed_test.py --engine ripgrep` | Ripgrep Livetext | < 80 ms (p50) |
| **Vector Semantic** | `.../speed_test.py --engine chromadb` | ChromaDB Vector | < 300 ms (p50) |
| **Hybrid Router** | `.../speed_test.py --engine hybrid` | Multi-Engine Fusion | < 400 ms (p50) |
| **JSON Export** | `.../speed_test.py --json` | CI / Automated Testing | Structured JSON |

## SLA Targets & Baseline Margins

| Engine | Baseline p50 | SLA Target | Margin |
|---|---|---|---|
| **Tantivy BM25** | 0.10 ms | < 10.0 ms | 100x faster |
| **Graphify AST** | 0.26 ms | < 25.0 ms | 96x faster |
| **Ripgrep Code** | 9.65 ms | < 80.0 ms | 8x faster |
| **Hybrid Unified** | 34.59 ms | < 400.0 ms | 11x faster |
| **ChromaDB Vector** | 46.28 ms | < 300.0 ms | 6.5x faster |

## Execution Protocol

1. **Warmup:** Execute 2 unmeasured warmup queries per engine to populate caches.
2. **Measurement:** Run 5 high-resolution iterations (`time.perf_counter()`).
3. **Evaluation:** Calculate p50, min, max, and avg. Flag any metric exceeding target as `⚠️ SLOW`.
4. **Report:** Output a clean tabular report with SLA status badges (`✅ PASS` / `⚠️ SLOW`).

📄 **See Also:**
- `.github/skills/speed-test/references/baseline-benchmarks.md` — Authoritative baseline tables & test environment
- `Resources/copilot/search-router/SEARCH_ROUTER_PLAN.md` — Multi-index architecture & design decisions
- `Resources/copilot/search-router/TOOLS_REFERENCE.md` — API schemas for all 6 MCP search tools
