---
name: subagent-flow
description: "Dispatches independent parallel tasks to subagents without prior sequential thinking, locking model to Gemini 3.8 Flash. TRIGGERS: 'subagent-flow', 'parallel-tasks'."
disable-model-invocation: true
last_updated: "2026-10-24"
---

# ⚡ subagent-flow — Direct Subagent Parallel Dispatch

> **Purpose:** Immediately dispatch independent tasks across parallel subagents without sequential thinking planning overhead.
> **Default LLM:** Strictly enforced as `gemini-3.8-flash` unless the user specifies an alternative.

## Operational Rules

1. **Parallel Dispatch:** Break work into self-contained tasks (e.g., disparate directory searches, parallel test runs, independent module audits).
2. **Model Locking:** Every child subagent invocation (`task` tool) **must** explicitly pass `model: "gemini-3.8-flash"`. Never omit `model` to avoid silent fallback to `gpt-5.6-luna`.
3. **No Prior Overhead:** Bypasses `sequentialthinking` and launches directly into parallel subagent execution.
4. **Auto-Trigger Condition:** Wide searches across 3+ unrelated directories or running parallel test/build verification automatically activates this workflow.
