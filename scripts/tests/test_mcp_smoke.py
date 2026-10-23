#!/usr/bin/env python3
"""
test_mcp_smoke.py — stdio smoke test for the mlaas-search MCP server.

Launches the server exactly the way an MCP client (VS Code Copilot Chat or the
Copilot CLI) launches it: absolute venv interpreter, an unrelated working
directory, over the stdio transport — and verifies:

  1. the MCP initialize handshake completes,
  2. the expected tools are listed,
  3. a real tool call returns well-formed results.

Unlike test_mcp_client.py (which calls MCPSearchTools in-process "for
simplicity"), this exercises the actual stdio transport and the trampoline at
scripts/search_server.py, so it catches "the server won't connect" regressions
that in-process tests miss.

Run standalone:  .venv/bin/python scripts/tests/test_mcp_smoke.py
Run under pytest: .venv/bin/python -m pytest scripts/tests/test_mcp_smoke.py

No async plugin (pytest-asyncio) is required: each test is sync and drives
asyncio.run() internally, and the single server launch is memoized so the three
tests share one connection.
"""
import asyncio
import json
import os
import sys


HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.dirname(HERE)
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from common_platform import get_repo_root, get_venv_python, ensure_venv_site_packages

REPO_ROOT = get_repo_root(SCRIPTS_DIR)
ensure_venv_site_packages(REPO_ROOT)
# The trampoline is what the CLI + VS Code client configs point at; it re-execs
# the 2.x server at scripts/search_router/search_server.py.
SERVER = os.path.join(str(REPO_ROOT), "scripts", "search_server.py")

EXPECTED_TOOLS = {"search_workspace", "search_code", "search_semantic", "get_search_stats"}
TIMEOUT_S = 60


def _server_command() -> str:
    """Use the venv interpreter when present, matching the client configs."""
    return str(get_venv_python(REPO_ROOT))


async def _drive():
    from mcp.client.session import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client

    # Launch from an unrelated cwd to mimic a client; the server resolves its
    # own .chroma/ and workspace paths from its file location, so the client's
    # cwd does not matter.
    params = StdioServerParameters(
        command=_server_command(),
        args=[SERVER],
        cwd="/",
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = {t.name for t in (await session.list_tools()).tools}
            stats = await session.call_tool("get_search_stats", {})
            code = await session.call_tool(
                "search_code", {"pattern": "class", "language": "python", "limit": 3}
            )
    return tools, stats, code


_CACHE: dict = {}


def _run() -> tuple:
    """Launch the server once and share the result across the test functions."""
    if "result" not in _CACHE:
        _CACHE["result"] = asyncio.run(asyncio.wait_for(_drive(), timeout=TIMEOUT_S))
    return _CACHE["result"]


def test_mcp_server_connects_over_stdio():
    """The server completes the MCP handshake and lists the expected tools."""
    tools, _stats, _code = _run()
    missing = EXPECTED_TOOLS - tools
    assert not missing, f"server missing expected tools: {missing}"


def test_get_search_stats_reports_backend():
    """get_search_stats reports a live chromadb + ripgrep backend."""
    _tools, stats, _code = _run()
    data = json.loads(stats.content[0].text)
    assert data.get("tools", {}).get("chromadb_available") is True
    assert data.get("tools", {}).get("ripgrep_available") is True
    assert "workspace" in json.dumps(data)


def test_search_code_dispatches():
    """search_code dispatches over the wire and returns a well-formed result."""
    _tools, _stats, code = _run()
    data = json.loads(code.content[0].text)
    assert "status" in data and "results" in data, code.content[0].text


if __name__ == "__main__":
    tools, stats, code = _run()
    print("SMOKE OK — tools:", sorted(tools))
    print("get_search_stats:", json.loads(stats.content[0].text).get("tools"))
    print("search_code status:", json.loads(code.content[0].text).get("status"))
    print("PASS")
