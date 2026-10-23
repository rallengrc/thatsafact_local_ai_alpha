#!/usr/bin/env python3
"""
mcp_speed_bench.py — Latency benchmark for the mlaas-search MCP server.

Measures, over the real stdio transport (the same launch a VS Code / Copilot CLI
client uses), how long each operation takes:

  * cold start   — spawn the server process + MCP initialize handshake
  * warm calls   — per-tool call_tool latency with a warm connection + warmup

It launches a *fresh* process for every cold-start sample so the number reflects
real "the client starts the server" cost, and reuses one connection for the warm
samples so they reflect steady-state per-call cost (not process spawn).

Usage:
  .venv/bin/python scripts/mcp_speed_bench.py
  .venv/bin/python scripts/mcp_speed_bench.py --iterations 10 --cold 3
  .venv/bin/python scripts/mcp_speed_bench.py --json out.json
"""
import argparse
import asyncio
import json
import os
import statistics
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from common_platform import get_repo_root, get_venv_python, ensure_venv_site_packages

REPO_ROOT = get_repo_root(HERE)
ensure_venv_site_packages(REPO_ROOT)
SERVER = os.path.join(str(REPO_ROOT), "scripts", "search_server.py")


def _server_command() -> str:
    return str(get_venv_python(REPO_ROOT))


# (tool_name, arguments) pairs to warm-call.
WARM_TOOLS = [
    ("get_search_stats", {}),
    ("search_code", {"pattern": "class", "language": "python", "limit": 5}),
    ("search_semantic", {"query": "how to deploy a kubernetes cluster", "limit": 3}),
    ("search_symbols", {"query": "search"}),
    ("search_everything", {"query": "deploy kubernetes"}),
    ("search_workspace", {"query": "kubernetes deployment", "limit": 5, "curate_for_llm": True}),
]


def _stats(samples: list[float]) -> dict:
    if not samples:
        return {}
    s = sorted(samples)
    return {
        "n": len(s),
        "min_ms": round(s[0] * 1000, 1),
        "p50_ms": round(statistics.median(s) * 1000, 1),
        "p90_ms": round(_percentile(s, 90) * 1000, 1),
        "mean_ms": round(statistics.mean(s) * 1000, 1),
        "max_ms": round(s[-1] * 1000, 1),
    }


def _percentile(sorted_vals: list[float], pct: float) -> float:
    if not sorted_vals:
        return 0.0
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    k = (len(sorted_vals) - 1) * (pct / 100.0)
    lo = int(k)
    hi = min(lo + 1, len(sorted_vals) - 1)
    frac = k - lo
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * frac


async def _measure_cold() -> float:
    """Fresh process: time spawn + initialize + first list_tools.

    Uses the same nested `async with` lifecycle as the working smoke test —
    manually tearing the transports down out of order causes "Connection
    closed", so we time the whole connect-and-list block instead.
    """
    from mcp.client.session import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client

    params = StdioServerParameters(
        command=_server_command(), args=[SERVER], cwd="/"
    )
    t0 = time.perf_counter()
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            await session.list_tools()
    return time.perf_counter() - t0


async def _measure_warm(args) -> dict:
    """One connection, warmup, then N timed iterations per tool."""
    from mcp.client.session import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client

    params = StdioServerParameters(
        command=_server_command(), args=[SERVER], cwd="/"
    )
    results: dict[str, dict] = {}
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            await session.list_tools()

            for name, call_args in WARM_TOOLS:
                # Warmup: prime embedding model / caches before timing.
                try:
                    await session.call_tool(name, call_args)
                except Exception as e:  # noqa: BLE001
                    print(f"  [warmup] {name}: {type(e).__name__}: {e}")

                samples: list[float] = []
                ok = 0
                last_err = None
                for _ in range(args.iterations):
                    t0 = time.perf_counter()
                    try:
                        res = await session.call_tool(name, call_args)
                        ok += 1
                        _ = res.content[0].text  # touch payload (not lazy)
                        samples.append(time.perf_counter() - t0)
                    except Exception as e:  # noqa: BLE001
                        last_err = f"{type(e).__name__}: {e}"
                results[name] = {
                    "ok": ok,
                    "iterations": args.iterations,
                    "stats": _stats(samples),
                    "error": last_err,
                }
    return results


async def _main(args) -> int:
    print("=" * 68)
    print("mlaas-search MCP server — latency benchmark (stdio transport)")
    print(f"server: {SERVER}")
    print(f"interp: {_server_command()}")
    print("=" * 68)

    # ---- Cold start: fresh process each sample ----
    print(f"\n[1] COLD START (spawn + initialize + list_tools), "
          f"{args.cold} fresh processes:")
    cold = []
    for i in range(args.cold):
        try:
            dt = await _measure_cold()
            cold.append(dt)
            print(f"  cold #{i + 1}: {dt * 1000:8.1f} ms")
        except Exception as e:  # noqa: BLE001
            print(f"  cold #{i + 1}: FAILED — {type(e).__name__}: {e}")
    cold_stats = _stats(cold)
    print(f"  -> min {cold_stats.get('min_ms','-')}  "
          f"p50 {cold_stats.get('p50_ms','-')}  "
          f"max {cold_stats.get('max_ms','-')}  ms")

    # ---- Warm per-tool calls on one connection ----
    print(f"\n[2] WARM CALLS (1 connection, {args.iterations} iters, "
          "1 warmup each):")
    warm = await _measure_warm(args)
    header = f"  {'tool':<18}{'n':>3}{'min':>9}{'p50':>9}{'p90':>9}{'max':>9}  err"
    print(header)
    print("  " + "-" * (len(header) - 2))
    for name, call_args in WARM_TOOLS:
        r = warm.get(name, {})
        st = r.get("stats", {})
        ok = r.get("ok", 0)
        it = r.get("iterations", 0)
        err = r.get("error")
        row = (
            f"  {name:<18}{ok}/{it:<2}"
            f"{st.get('min_ms','-'):>9}"
            f"{st.get('p50_ms','-'):>9}"
            f"{st.get('p90_ms','-'):>9}"
            f"{st.get('max_ms','-'):>9}"
        )
        if err:
            row += f"  {err}"
        print(row)

    report = {
        "server": SERVER,
        "interpreter": _server_command(),
        "cold_start_ms": cold_stats,
        "warm_calls": {
            name: {
                "arguments": call_args,
                "ok": warm.get(name, {}).get("ok", 0),
                "iterations": warm.get(name, {}).get("iterations", args.iterations),
                "stats": warm.get(name, {}).get("stats", {}),
                "error": warm.get(name, {}).get("error"),
            }
            for name, call_args in WARM_TOOLS
        },
    }
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"\n[3] JSON report written to {args.json}")

    # Verdict
    any_err = any(v.get("error") for v in warm.values()) or not cold
    print("\n" + ("PASS — all tools responded, cold start measured."
          if not any_err else "WARN — some operations failed; see 'err' above."))
    return 0 if not any_err else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iterations", type=int, default=5,
                    help="warm call_tool iterations per tool (default 5)")
    ap.add_argument("--cold", type=int, default=3,
                    help="cold-start samples (fresh processes, default 3)")
    ap.add_argument("--json", default=None,
                    help="write a JSON report to this path")
    args = ap.parse_args()
    sys.exit(asyncio.run(_main(args)))
