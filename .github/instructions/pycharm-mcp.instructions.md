---
description: 'Operational rules for PyCharm MCP tool usage with mandatory zero-friction fallback to native VS Code tools for Python and Jupyter files.'
applyTo: '**/*.py, **/*.ipynb'
---

# PyCharm MCP Tool Usage & VS Code Native Fallback Rules

> **Core Principle:** PyCharm MCP integration is strictly opportunistic. VS Code native functionality is the primary baseline and must never be impeded.

---

## 1. Mandatory Fallback Rules

1. **No Hard Dependencies:** Never treat PyCharm MCP as a prerequisite for development, testing, building, searching, or editing. All tasks must be fully solvable using standard VS Code tools, Pylance, and terminal scripts.
2. **One-Strike Failover:**
   - If a PyCharm MCP tool is not present in the active tool declarations, use the native VS Code tool immediately without complaint.
   - If a PyCharm MCP tool call fails with a connection error, timeout, or unexpected exception, immediately fall back to the equivalent native tool (`problems`, `pylanceLSP`, `execution_subagent`, `runTests`, etc.).
   - Do not retry failing PyCharm MCP calls in a loop.
3. **No Unsolicited Prompts:** Do not prompt the user to "start PyCharm" or "open the project in PyCharm" unless the user specifically asked about configuring or diagnosing the PyCharm MCP connection.
4. **Path & Environment Standards:**
   - Always pass `projectPath` as a valid absolute path when calling PyCharm MCP tools.
   - Ensure file paths are normalized POSIX paths (`path/to/file.py`).
5. **Execution Tools Priority:**
   - For running terminal commands, builds, or tests, prioritize direct tools (`bash`, `runTests`) over PyCharm terminal commands unless the user explicitly requests running a PyCharm run configuration. Never delegate to subagents.
