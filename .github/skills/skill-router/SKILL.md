---
name: skill-router
description: "Dynamically discover and apply internal procedural skills from subrepos on demand without prompt context bloat. TRIGGERS: 'find-skill', 'skill-router', 'need a skill'."
disable-model-invocation: true
last_updated: "2026-10-24"
---

# 🧠 Skill Router — On-Demand Dynamic Skill Retrieval

> **Purpose:** Retrieve and apply specialized agent skills on the fly from internal catalogs (`code/superpowers/skills`, `code/flyte-agent-plugins`, `code/awesome-copilot`) without bloating the prompt context window.

## Workflow Rules

1. **Check Native First:** If a matching skill already exists in `<available_skills>`, invoke it directly.
2. **Dynamic Internal Discovery:** If a prompt requires specialized workflows (e.g. Flyte AWS deployment, deep brainstorming, niche debugging):
   - Call the `find_skill` MCP tool or execute:
     ```python
     .venv/bin/python3 -c "from search_router.mcp_search_tools import MCPSearchTools; print(MCPSearchTools().find_skill('<topic>')['lean_markdown'])"
     ```
3. **Execute Distilled Markdown:** Follow the returned distilled (≤100L) workflow immediately for the turn.
4. **Deep Reference:** If full verbose context is needed, read the file path specified in `source_path`.
