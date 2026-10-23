---
title: MCP Setup, Verification & Troubleshooting
description: Complete setup and troubleshooting guide for running mlaas-search and sequentialthinking MCP servers
keywords:
- MCP
- Model Context Protocol
- mlaas-search
- sequentialthinking
- troubleshooting
- config
category: guide
classification: 🟢🛡️ General
last_updated: '2026-10-11'
author: thatsafact
ai_search_aliases:
- mcp setup
- mcp config
- mcp troubleshooting
- configure mcp servers
---

# MCP Setup, Verification & Troubleshooting

> **TL;DR:** Step-by-step setup and verification instructions for running Model Context Protocol (MCP) servers across GitHub Copilot CLI and VS Code.
> **Use this for:** Configuring, verifying, or debugging MCP server connections and virtualenv Python interpreter settings.

How to run the `mlaas-search` (this repo's search router) and `sequentialthinking` MCP servers in each client.

## Prerequisites

- `.venv` with `mcp>=2.0` (currently 2.3.0): `.venv/bin/python3 -m pip install -r requirements.txt`
- `rg` (ripgrep) on PATH: `brew install ripgrep`
- Workspace indexed into `.chroma/`: `.venv/bin/python3 scripts/index_workspace.py --workspace . --db-path .chroma`
- Docker (only for `sequentialthinking`)

## Critical: use the virtualenv interpreter

`scripts/search_server.py` imports `mcp`, which is installed only in `.venv`. A config that launches bare `python3` runs the system interpreter and the server dies before the MCP handshake:

```
ModuleNotFoundError: No module named 'mcp'
MCP server process exited before completing the MCP initialize handshake (exit code 1)
```

Always set `command` to the absolute venv path (a client's working directory is not the repo, and clients differ in whether they expand variables). The server itself resolves `.chroma/` and the ripgrep root from its own file location, so the client's working directory does not matter.

## Path rule: local files, never committed

Variable expansion is not portable across clients: `${workspaceFolder}` works only in a workspace `.vscode/mcp.json`, and `${env:MLAAS_ROOT}` is empty when VS Code is launched from the Dock or when a client does not expand variables, so the server fails to start. Therefore:

- **Workspace `.vscode/mcp.json`:** use `${workspaceFolder}`.
- **User-level configs** (`~/.copilot/mcp-config.json`, VS Code user `mcp.json`, Claude Desktop): write the literal absolute path for your machine (shown as `<repo-root>` below). These files live outside the repo and must never be committed or pasted into repo docs.
- **Repo `.mcp.json` and `.vscode/mcp.json`:** gitignored; keep machine paths out of any tracked file.
- **`MLAAS_ROOT`:** optional, for Python scripts run from outside the repo only (`get_repo_root()` in `scripts/common_platform.py` walks up from the script first and uses `MLAAS_ROOT` only if that fails). Do not use it in MCP configs.

On Windows the interpreter is `.venv\Scripts\python.exe`.

## Client configuration

### GitHub Copilot CLI / agent host — `~/.copilot/mcp-config.json`

```json
{
  "mcpServers": {
    "mlaas-search": {
      "command": "<repo-root>/.venv/bin/python3",
      "args": ["<repo-root>/scripts/search_server.py"],
      "description": "Hybrid search: ripgrep code search + semantic search via ChromaDB",
      "tools": ["*"]
    },
    "sequentialthinking": {
      "command": "/opt/homebrew/bin/mcp-server-sequential-thinking",
      "args": [],
      "description": "Sequential thinking for structured problem-solving and analysis",
      "tools": ["*"]
    }
  }
}
```

Verify: `copilot mcp list` should show both under "User servers".

### VS Code — user `mcp.json`

Location: `~/Library/Application Support/Code/User/mcp.json` (Command Palette → "MCP: Open User Configuration"). VS Code uses the top-level key `servers`, not `mcpServers`, and the entries need `"type": "stdio"`:

```json
{
  "servers": {
    "mlaas-search": {
      "type": "stdio",
      "command": "<repo-root>/.venv/bin/python3",
      "args": ["<repo-root>/scripts/search_server.py"]
    },
    "sequentialthinking": {
      "type": "stdio",
      "command": "/opt/homebrew/bin/mcp-server-sequential-thinking",
      "args": []
    }
  }
}
```

Reload the window after editing, then open Copilot Chat in agent mode and check the tools picker. Servers can also be started and inspected from "MCP: List Servers" (Show Output for logs).

### Claude Desktop

Same `mcpServers` shape as the Copilot CLI file, in Claude's config file, with `command` set to the venv python. Optional `timeout` (ms) and `alwaysAllow` (tool names) fields are supported there.

## Verifying a server end to end

A hand-typed `initialize` is not enough; run a real MCP client against the exact configured command from an unrelated working directory:

```python
import asyncio, json, os
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

cfg = json.load(open(os.path.expanduser("~/.copilot/mcp-config.json")))["mcpServers"]["mlaas-search"]

async def main():
    params = StdioServerParameters(command=cfg["command"], args=cfg["args"], cwd="/")
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            print([t.name for t in (await s.list_tools()).tools])
            res = await s.call_tool("get_search_stats", {})
            print(res.content[0].text[:200])

asyncio.run(main())
```

Run it with `.venv/bin/python3`. Expected tools: `search_workspace`, `search_code`, `search_semantic`, `get_search_stats`.

## Troubleshooting

| Symptom | Cause / fix |
|---------|-------------|
| `ModuleNotFoundError: No module named 'mcp'` in client logs | Config uses system `python3`. Use the `.venv/bin/python3` absolute path. |
| `ImportError: cannot import name 'ToolResult' from 'mcp.types'` | Code written for the MCP 0.x/1.x API. `search_server.py` now uses the 2.x `MCPServer` + `@mcp.tool()` API; types live in `mcp_types`. |
| `Server object has no attribute 'list_tools'` | Same: low-level `Server` decorators were removed in MCP 2.x. |
| Handshake fails, stderr is empty | Something wrote to stdout. Stdio servers must log to stderr only (`logging` to `sys.stderr`; no `print`). |
| Tools missing in VS Code | Wrong key (`mcpServers` instead of `servers`), or window not reloaded. |
| `sequentialthinking` won't start | `docker ps` must work; `docker run --rm -i mcp/sequentialthinking` should print "Sequential Thinking MCP Server running on stdio". |
| `collection not found` / empty results | Index missing or stale: re-run `scripts/index_workspace.py`. |
| First search slow (10-30 s) | ChromaDB embedding model warm-up; later searches are fast. |

Where to look for logs:

- Copilot CLI: `~/.copilot/logs/process-*.log` (search for `MCP server connection failed`; `stderr_detail` holds the traceback).
- VS Code: `~/Library/Application Support/Code/logs/<session>/window1/mcpServer.*.log`.

## Version compatibility

- MCP protocol: server answers `2024-11-05` initialize requests and works with the Copilot CLI MCP client (rust `native_connector`).
- Python SDK: 2.x API (`from mcp.server import MCPServer`). Pin `mcp>=2.0.0` in `requirements.txt`.
