#!/usr/bin/env python3
"""
local_runner.py — Standalone verification runner for Hello MLaaS Burst.

Runs the surrogate ML pipeline locally on macOS Apple Silicon or On-Prem VM
without requiring active Kubernetes clusters or cloud credentials.

Usage:
  python3 local_runner.py             # Quick verification pipeline run
  python3 local_runner.py --benchmark # Run comparative benchmark (Old vs New) & write to SQLite
"""

import sys
import os
import time
import argparse

# Ensure current folder is in python path
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if _CURRENT_DIR not in sys.path:
    sys.path.insert(0, _CURRENT_DIR)

from workflow import surrogate_pipeline, FLYTE_AVAILABLE, RAY_AVAILABLE
from benchmark_runner import run_comparative_benchmark


def run_quick_verification():
    print("=" * 76)
    print("🚀 HELLO MLAAS BURST: LOCAL TEST & VERIFICATION RUNNER")
    print("   Testing Flyte macro-DAG + Ray micro-distributed compute")
    print(f"   Environment: Flytekit={FLYTE_AVAILABLE} | Ray={RAY_AVAILABLE}")
    print("=" * 76)

    num_samples = 2400
    num_workers = 4

    print(f"\n[1/3] Generating synthetic airfoil mesh data ({num_samples} samples)...")
    print(f"[2/3] Dispatching distributed surrogate training across {num_workers} workers...")
    print("[3/3] Evaluating physics fidelity vs ground-truth CFD baseline...\n")

    start_wall = time.perf_counter()
    results = surrogate_pipeline(
        num_samples=num_samples,
        num_ray_workers=num_workers,
        env_mode="local",
    )
    total_time = time.perf_counter() - start_wall

    print("=" * 76)
    print("✅ EXECUTION SUCCESSFUL!")
    print(f"   Total Pipeline Wall Time : {total_time:.3f} seconds")
    print("=" * 76)
    print("📊 Validation & ROI Metrics:")
    for key, val in results.items():
        print(f"   • {key:<25}: {val}")
    print("=" * 76)
    print("\n💡 Architectural Insight:")
    print("   • Notice how the surrogate training completed in sub-second time.")
    print("   • For rigorous side-by-side performance benchmarking vs the 'Old Way'")
    print("     and SQLite metrics recording, run:")
    print("     python3 local_runner.py --benchmark")
    print("=" * 76)


def main():
    parser = argparse.ArgumentParser(description="Hello MLaaS Burst Local Runner")
    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="Run comprehensive Old Way vs New Way benchmark with SQLite metrics logging",
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=200000,
        help="Number of samples for benchmark run (default: 200,000)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Number of workers for benchmark run (default: 4)",
    )
    args = parser.parse_args()

    if args.benchmark:
        run_comparative_benchmark(num_samples=args.samples, num_workers=args.workers)
    else:
        run_quick_verification()


if __name__ == "__main__":
    main()
