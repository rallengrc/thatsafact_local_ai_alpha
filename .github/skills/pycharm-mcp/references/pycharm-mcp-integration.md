---
title: "PyCharm MCP Server Integration & Failover Protocol"
description: "Reference guide for linking PyCharm MCP server with VS Code and managing zero-friction fallback."
keywords: [PyCharm, JetBrains, MCP, VSCode, Fallback, Integration, Stdio, SSE]
category: reference
last_updated: 2026-10-23
author: Copilot
related:
  - Resources/copilot/pycharm_mcp.md
  - .github/skills/pycharm-mcp/SKILL.md
classification: 🟢🛡️ General
ai_search_aliases: ["pycharm mcp failover", "pycharm mcp vscode setup", "jetbrains mcp configuration"]
---

# PyCharm MCP Server Integration & Failover Protocol

> **Purpose:** Establishes connection standards and automated failover mechanics between JetBrains PyCharm MCP server and VS Code.

---

## 1. Connection Configurations (When Ready to Enable)

PyCharm 2025.2+ supports three MCP transport mechanisms: Stdio, SSE (Server-Sent Events), and HTTP Stream.

### Stdio Transport (Recommended for Local Machine)
Configured in VS Code user or workspace settings (`.vscode/mcp.json` or Copilot MCP config):

```json
{
  "mcpServers": {
    "pycharm": {
      "command": "/Applications/PyCharm.app/Contents/bin/pycharm",
      "args": ["mcp-server"],
      "env": {
        "PROJECT_PATH": "${workspaceFolder}"
      }
    }
  }
}
```

### SSE / HTTP Stream Transport
When PyCharm runs as an IDE service with MCP enabled:

```json
{
  "servers": {
    "pycharm": {
      "type": "sse",
      "url": "http://127.0.0.1:64462/sse"
    }
  }
}
```

*(Note: Verify the active MCP SSE port via `lsof -a -p $(pgrep -f pycharm) -iTCP -sTCP:LISTEN` or the PyCharm MCP Server Settings dialog)*

---

## 2. Failover State Machine

To guarantee that VS Code workflows are never disrupted when PyCharm is closed, crashing, or unconfigured, adhere to this state machine:

```
[Tool Needed]
      │
      ▼
[Is PyCharm Tool Registered & Responsive?]
      ├── YES ──► Execute PyCharm MCP Tool
      │                 │
      │                 ├── Success ──► Return Result
      │                 └── Error / Timeout ──┐
      │                                       │
      └── NO (Offline / Missing) ─────────────┤
                                              ▼
                                 [Native VS Code Fallback]
                                              │
                                              ▼
                                   Complete Work Normally
```

---

## 3. Graceful Fallback Best Practices

1. **Silent Degradation:** If PyCharm tools are not detected in the available toolset, proceed with VS Code native tools silently. Do not emit alarmist warnings or block user workflows.
2. **Circuit Breaker:** If a call to a PyCharm MCP endpoint returns `ConnectionRefused`, HTTP `503`, or exceeds a 2-second initial ping timeout, mark the PyCharm backend as offline for the remainder of the turn and route all subsequent sub-tasks to native VS Code tooling.
3. **Parameter Invariance:** Always provide `projectPath` with normalized POSIX paths (`/path/to/project`) when communicating with PyCharm to avoid Windows/Mac path confusion.
4. **Brave Mode Awareness:** If PyCharm is connected, recommend enabling "Brave Mode" (*Run shell commands or run configurations without confirmation*) in PyCharm Settings (`Tools > MCP Server`) so automation does not pause for GUI approval prompts.
