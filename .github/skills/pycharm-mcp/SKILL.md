---
name: pycharm-mcp
description: "Opportunistically leverage JetBrains PyCharm MCP server tools from VS Code with zero-friction fallback to native VS Code tools when PyCharm is absent, offline, or unconfigured. TRIGGERS: 'pycharm mcp', 'pycharm tools', 'jetbrains mcp', 'ide inspection', 'pycharm fallback'."
---

# PyCharm MCP Server — Opportunistic Integration & Fallback

> **The Fallback Law:** PyCharm MCP is an opportunistic accelerator, **NEVER a blocker**. If the PyCharm MCP server is offline, unconfigured, or returns an error/timeout, proceed immediately using native VS Code built-in tools. Never stall or fail an operation because PyCharm is absent.

---

## ⚡ Tool Dispatch & Fallback Matrix

| Domain | PyCharm MCP Tool (If Online) | Native VS Code Tool (Default / Fallback) |
|---|---|---|
| **File Inspections / Lint** | `get_file_problems`, `lint_files` | `problems`, `pylanceLSP textDocument/diagnostic` |
| **Call Hierarchy** | `analyze_calls` (`INCOMING_CALLS`/`OUTGOING_CALLS`) | `pylanceLSP callHierarchy`, `usages` |
| **Symbol Info & Doc** | `get_symbol_info` | `pylanceLSP textDocument/hover`, `definition` |
| **Run Configurations** | `execute_run_configuration`, `get_run_configurations` | `runTask`, `runTests`, `execution_subagent` |
| **Refactoring** | `rename_refactoring` | `pylanceInvokeRefactoring`, `edit` |
| **Code Formatting** | `reformat_file` | `pylanceInvokeRefactoring`, workspace formatter |
| **Directory Tree** | `list_directory_tree` | `glob`, `view` |
| **Jupyter Notebooks** | `run_notebook_cell`, `read_notebook_cell`, `edit_notebook` | `runNotebookCell`, `readNotebookCellOutput`, `editNotebook` |
| **Python Environment** | `get_python_environment`, `configure_python_interpreter` | `pylancePythonEnvironments`, `getPythonEnvironmentInfo` |
| **Database Queries** | `execute_sql_query`, `preview_table_data` | `sqlite-read_query`, `sql` |
| **Terminal / CLI** | `execute_terminal_command` | `bash`, native terminal tools |
| **VCS / Git Status** | `git_status`, `get_repositories` | `bash` (`git status`), built-in git tools |

---

## 🛡️ Fallback Execution Protocol

1. **Check Availability:** When a PyCharm MCP tool is requested or applicable, check if registered in the current tool inventory.
2. **One-Strike Failover:** If the tool is missing from the active tool registry, returns a connection refusal, times out, or fails:
   - Do **NOT** retry in a loop.
   - Do **NOT** ask the user to start PyCharm unless explicitly requested.
   - Switch immediately to the corresponding Native VS Code tool in the matrix above.
3. **Preserve Native Behavior:** All standard workflows (diagnostics, testing, formatting, file edits) must function out-of-the-box in standalone VS Code.

---

## 📄 See Also

- 📄 [pycharm-mcp-integration.md](./references/pycharm-mcp-integration.md) — Transport configuration, setup guide, and failover state machine.
- 📄 [pycharm_mcp.md](../../../Resources/copilot/pycharm_mcp.md) — Full PyCharm MCP server tool specifications and parameter catalog.
- 📄 [pycharm-mcp.instructions.md](../../instructions/pycharm-mcp.instructions.md) — Auto-applying operational rules for PyCharm tool usage.
