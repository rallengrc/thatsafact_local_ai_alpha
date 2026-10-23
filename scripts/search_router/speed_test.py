#!/usr/bin/env python3
"""
speed_test.py — High-precision latency and throughput benchmark for Search Router v2.

Tests all 4 search engines (Tantivy, Graphify, ChromaDB, Ripgrep) and the unified
hybrid router across representative query workloads.

Usage:
    .venv/bin/python3 scripts/search_router/speed_test.py
    .venv/bin/python3 scripts/search_router/speed_test.py --engine tantivy
    .venv/bin/python3 scripts/search_router/speed_test.py --json
"""

import argparse
import json
import logging
import os
import statistics
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_SCRIPTS_DIR = os.path.dirname(_CURRENT_DIR)
_INDEXING_DIR = os.path.join(_SCRIPTS_DIR, "indexing")
_REPO_ROOT = os.path.dirname(_SCRIPTS_DIR)
_GRAPHIFY_DIR = os.path.join(_REPO_ROOT, "code", "graphify")

for _d in [_CURRENT_DIR, _INDEXING_DIR, _SCRIPTS_DIR, _GRAPHIFY_DIR]:
    if _d not in sys.path and os.path.exists(_d):
        sys.path.insert(0, _d)

from common_platform import ensure_venv_site_packages

ensure_venv_site_packages(Path(_REPO_ROOT))

from search_router import UnifiedSearchRouter
from mcp_search_tools import MCPSearchTools

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")

# Representative benchmark suites
BENCHMARK_WORKLOADS = {
    "tantivy_bm25": [
        ("kubernetes GPU", {}),
        ("Burstable MLaaS SOW", {}),
        ("architecture EKS", {}),
        ("surrogate model training", {}),
    ],
    "graphify_ast": [
        ("UnifiedSearchRouter", {"kind": "class"}),
        ("QueryAnalyzer", {"kind": "class"}),
        ("extract_python", {"kind": "function"}),
        ("TantivySearcher", {}),
    ],
    "chromadb_semantic": [
        ("how does burstable GPU orchestration work", {}),
        ("cost accelerator electrification financial model", {}),
        ("hybrid search router deduplication", {}),
    ],
    "ripgrep_code": [
        ("def search_hybrid", {"language": "python"}),
        ("class .*Indexer", {"language": "python"}),
        ("TANTIVY_AVAILABLE", {"language": "python"}),
    ],
    "hybrid_unified": [
        ("def search_symbols", {"curate_for_llm": True}),
        ("kubernetes burstable architecture", {"curate_for_llm": True}),
        ("how Karpenter handles GPU scale up", {"curate_for_llm": True}),
    ],
}

# SLA Latency Targets (milliseconds)
SLA_TARGETS_MS = {
    "tantivy_bm25": 10.0,
    "graphify_ast": 25.0,
    "ripgrep_code": 80.0,
    "chromadb_semantic": 300.0,
    "hybrid_unified": 400.0,
}


@dataclass
class BenchmarkMetric:
    engine: str
    query: str
    iterations: int
    p50_ms: float
    min_ms: float
    max_ms: float
    avg_ms: float
    hits: int
    target_ms: float
    passed_sla: bool


class SearchSpeedTester:
    """Benchmark runner for the multi-engine search router."""

    def __init__(self, workspace_root: str = ".", iterations: int = 5, warmup: int = 2):
        self.workspace_root = workspace_root
        self.iterations = iterations
        self.warmup = warmup
        self.tools = MCPSearchTools(workspace_root=workspace_root)
        self.router = self.tools.router

    def run_benchmark(self, engine_filter: Optional[str] = None) -> List[BenchmarkMetric]:
        """Execute benchmarks across configured engines."""
        results: List[BenchmarkMetric] = []

        workloads = BENCHMARK_WORKLOADS
        if engine_filter:
            workloads = {k: v for k, v in workloads.items() if engine_filter.lower() in k.lower()}

        for engine_key, queries in workloads.items():
            for query, kwargs in queries:
                metric = self._benchmark_query(engine_key, query, kwargs)
                results.append(metric)

        return results

    def _execute_search(self, engine_key: str, query: str, kwargs: Dict[str, Any]) -> int:
        """Execute single search call and return result count."""
        if engine_key == "tantivy_bm25":
            res = self.router.search_everything(query, limit=10)
            return len(res)
        elif engine_key == "graphify_ast":
            res = self.router.search_symbols(query, limit=10, kind=kwargs.get("kind"))
            return len(res)
        elif engine_key == "chromadb_semantic":
            res = self.router.search_semantic(query, limit=10)
            return len(res)
        elif engine_key == "ripgrep_code":
            res = self.router.search_code(query, language=kwargs.get("language"), limit=10)
            return len(res)
        elif engine_key == "hybrid_unified":
            res = self.router.search_hybrid(query, limit=10, curate_for_llm=kwargs.get("curate_for_llm", False))
            return len(res)
        else:
            raise ValueError(f"Unknown engine {engine_key}")

    def _benchmark_query(self, engine_key: str, query: str, kwargs: Dict[str, Any]) -> BenchmarkMetric:
        # Warmup
        for _ in range(self.warmup):
            self._execute_search(engine_key, query, kwargs)

        # Measured runs
        durations_ms: List[float] = []
        hits = 0
        for _ in range(self.iterations):
            start = time.perf_counter()
            hits = self._execute_search(engine_key, query, kwargs)
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            durations_ms.append(elapsed_ms)

        durations_ms.sort()
        p50 = statistics.median(durations_ms)
        min_val = min(durations_ms)
        max_val = max(durations_ms)
        avg_val = statistics.mean(durations_ms)
        target = SLA_TARGETS_MS.get(engine_key, 200.0)

        return BenchmarkMetric(
            engine=engine_key,
            query=query,
            iterations=self.iterations,
            p50_ms=round(p50, 2),
            min_ms=round(min_val, 2),
            max_ms=round(max_val, 2),
            avg_ms=round(avg_val, 2),
            hits=hits,
            target_ms=target,
            passed_sla=p50 <= target,
        )


def print_report(metrics: List[BenchmarkMetric]) -> None:
    """Print clean terminal comparison table."""
    print("\n" + "=" * 90)
    print(f"{'ENGINE':<18} | {'QUERY':<32} | {'p50 (ms)':<9} | {'AVG (ms)':<9} | {'HITS':<5} | {'SLA':<6}")
    print("-" * 90)

    for m in metrics:
        sla_badge = "✅ PASS" if m.passed_sla else "⚠️ SLOW"
        short_query = m.query if len(m.query) <= 30 else m.query[:27] + "..."
        print(f"{m.engine:<18} | {short_query:<32} | {m.p50_ms:<9.2f} | {m.avg_ms:<9.2f} | {m.hits:<5} | {sla_badge}")

    print("=" * 90)

    # Engine summary
    engines = sorted(set(m.engine for m in metrics))
    print("\n--- Summary by Engine ---")
    for eng in engines:
        eng_metrics = [m for m in metrics if m.engine == eng]
        avg_p50 = statistics.mean(m.p50_ms for m in eng_metrics)
        all_passed = all(m.passed_sla for m in eng_metrics)
        target = SLA_TARGETS_MS.get(eng, 0.0)
        status = "✅ SLA Met" if all_passed else "⚠️ Under Review"
        print(f"  • {eng:<18}: Mean p50 = {avg_p50:6.2f} ms (Target: <{target:.0f} ms) [{status}]")
    print()


def main():
    parser = argparse.ArgumentParser(description="Search Router Speed Test & Benchmarking")
    parser.add_argument("--engine", type=str, default=None, help="Filter to specific engine")
    parser.add_argument("--iterations", type=int, default=5, help="Number of benchmark iterations")
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    args = parser.parse_args()

    tester = SearchSpeedTester(iterations=args.iterations)
    metrics = tester.run_benchmark(engine_filter=args.engine)

    if args.json:
        payload = [asdict(m) for m in metrics]
        print(json.dumps(payload, indent=2))
    else:
        print_report(metrics)


if __name__ == "__main__":
    main()
