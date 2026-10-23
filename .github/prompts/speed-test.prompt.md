---
agent: agent
description: "Execute high-precision search router latency benchmarks across Tantivy, Graphify, ChromaDB, Ripgrep, and Hybrid."
triggers: ["speed-test", "benchmark search", "test search", "search speed", "test search router"]
---

# ⚡ Speed Test — Search Router Performance Benchmark

> **Alias for:** `speed-test` skill and benchmark runner
> **Use this when:** You want to measure search speed, verify performance SLAs, or detect latency regressions
> **Triggers:** `speed-test`, `benchmark search`, `test search`, `search speed`, `test search router`

Run high-resolution benchmarks across all 5 search subsystems in the workspace:

## Quick Commands

Run the full benchmark suite across all engines:

```bash
.venv/bin/python3 scripts/search_router/speed_test.py
```

Test a single search engine:

```bash
# Broad BM25 inverted index (target: <10ms)
.venv/bin/python3 scripts/search_router/speed_test.py --engine tantivy

# AST code intelligence symbol search (target: <25ms)
.venv/bin/python3 scripts/search_router/speed_test.py --engine graphify

# Zero-index live regex scan (target: <80ms)
.venv/bin/python3 scripts/search_router/speed_test.py --engine ripgrep

# Dense vector semantic similarity (target: <300ms)
.venv/bin/python3 scripts/search_router/speed_test.py --engine chromadb

# Multi-engine preprocessed hybrid router (target: <400ms)
.venv/bin/python3 scripts/search_router/speed_test.py --engine hybrid
```

Output machine-readable JSON for CI / automation:

```bash
.venv/bin/python3 scripts/search_router/speed_test.py --json
```

## Established SLA Baselines

| Engine | Baseline p50 | SLA Target | Status |
|---|---|---|---|
| **Tantivy BM25** | **0.10 ms** | < 10.0 ms | ✅ 100x faster |
| **Graphify AST** | **0.26 ms** | < 25.0 ms | ✅ 96x faster |
| **Ripgrep Code** | **9.65 ms** | < 80.0 ms | ✅ 8x faster |
| **Hybrid Unified** | **34.59 ms** | < 400.0 ms | ✅ 11x faster |
| **ChromaDB Vector** | **46.28 ms** | < 300.0 ms | ✅ 6.5x faster |

---

**Tip:** When you run `speed-test`, the benchmark measures 5 iterations per query with 2 warmups and reports `p50`, `min`, `max`, and `avg` latencies with pass/fail SLA badges.
