---
title: Sequential Thinking Integration Guide
description: Integration patterns and best practices for combining the sequential thinking MCP server with search tools
keywords:
- sequential thinking
- reasoning
- MCP
- search router
- integration
- problem-solving
category: guide
classification: 🟢🛡️ General
last_updated: '2026-10-11'
author: thatsafact
ai_search_aliases:
- sequential thinking guide
- how to use seq-think
- sequential thinking mcp
---

# Sequential Thinking Integration

> **TL;DR:** Guide explaining how the `sequentialthinking` MCP server structures complex problem-solving, architectural design, and debugging alongside search.
> **Use this for:** Structuring multi-step analysis, plan revisions, hypothesis testing, and deep-dive problem solving.

The `sequentialthinking` MCP server complements the search router: search finds what exists, sequential thinking structures the reasoning about it. Server install/config lives in [MCP_SETUP.md](./MCP_SETUP.md); search tools in [TOOLS_REFERENCE.md](./search-router/TOOLS_REFERENCE.md).

## Server

- Image: `mcp/sequentialthinking` (Node.js; source: <https://github.com/modelcontextprotocol/servers/tree/main/src/sequentialthinking>)
- Tool: `sequentialthinking`
- Parameters: `thought`, `thoughtNumber`, `totalThoughts`, `nextThoughtNeeded`; optional `isRevision`, `revisesThought`, `branchFromThought`, `branchId`, `needsMoreThoughts`
- Smoke test: `.venv/bin/python3 scripts/test_sequential_thinking.py`

Best for architecture design, multi-step analysis, planning with alternatives, and debugging workflows. Estimates can be revised as thinking proceeds (`totalThoughts` can grow, earlier thoughts can be revised or branched).

## How the two servers work together

| Scenario | Search | Sequential thinking | Outcome |
|----------|--------|---------------------|---------|
| Quick lookup | ✅ | — | Direct answer |
| Complex analysis | Narrows scope | ✅ Steps | Structured solution |
| Architecture design | Finds existing patterns | ✅ Plans with revisions | Iterated design |
| Multi-file debugging | ✅ Finds related code | ✅ Tracks the failure path | Root cause |
| Code review prep | ✅ Similar code | ✅ Weighs alternatives | Review context |

Patterns:

1. **Lookup → understand:** `search_workspace` for the code, then reason about how it works.
2. **Design with analysis:** start thinking; at each step call `search_code` for existing implementations; revise earlier steps when search contradicts an assumption.
3. **Debug:** `search_code` for the failing function, `search_semantic` for its error handling, then trace the failure step by step.

CLI examples:

```bash
copilot mcp list
copilot -i "Design a caching layer for API responses, use sequential thinking"
copilot --reasoning-effort high -p "Analyze this design"
```

## Constraints

| Constraint | Mitigation |
|------------|------------|
| Docker required | `docker ps` must work before starting a client |
| Protocol version mismatch makes tools disappear | Both servers speak MCP `2024-11-05` and newer |
| First semantic search is slow | Embedding warm-up; cached afterwards |
| Absolute paths differ per OS | Use absolute paths in each client config |
