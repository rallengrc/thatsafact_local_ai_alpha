---
name: mcp-security-audit
description: "Audit MCP server implementations, configs, and tool handlers against secrets exposure, command injection, path traversal, and OWASP MCP Top 10 risks."
---

# MCP Security Audit — Tool & Server Safety Gate

**Triggers:** `mcp security`, `audit mcp`, `secure tools`, `check .mcp.json`, `tool injection`

**Upstream:** Authoring or modifying MCP servers (`sqlite_server.py`, `search_server.py`)
**Downstream:** Deployment to `.mcp.json` or team tool registry

---

## Core Security Controls for MCP

MCP servers grant language models direct tool execution capabilities on the host. Any defect in tool handlers can lead to remote code execution (RCE) or data exfiltration.

```
Incoming Tool Request → Schema Validation → Injection Defense → Safe Execution
  1. No shell expansion or eval in command runners.
  2. Strict read-only SQL guards on SQLite tools (block DROP/ALTER/ATTACH/LOAD).
  3. Strict path traversal guards (os.path.commonpath, resolve absolute paths).
  4. Stdio stream hygiene: stderr for all logging, stdout ONLY for JSON-RPC.
```

---

## The Audit Checklist

| Check | Target | Defense |
| :--- | :--- | :--- |
| **Secrets Exposure** | `.mcp.json`, environment vars | Use `${ENV_VAR}` references; never hardcode tokens or keys |
| **SQL Injection** | `sqlite_server.py` queries | Force parameterized queries or strict read-only keyword verification |
| **Command Injection** | Process spawning tools | Use list-based `subprocess.Popen([cmd, arg])`, never `shell=True` |
| **Path Traversal** | File read/write tools | Validate target is within approved root (`os.path.realpath`) |
| **Stream Collisions** | Loggers, print statements | Redirect all application logging to `sys.stderr` |

---

## References

- [RCE Vectors & OWASP MCP Top 10 Reference](references/rce-and-owasp-mcp-top10.md) — Threat models and code patterns
- **Source:** `code/awesome-copilot/skills/mcp-implementation-security-review/` and `mcp-security-audit/`
