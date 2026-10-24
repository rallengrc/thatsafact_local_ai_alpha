---
name: seq-think
description: "Short, typo-resistant trigger for the sequentialthinking MCP orchestrator. TRIGGERS: 'seq-think', 'think deep', 'sequence'. Invoke manually; not auto-loaded."
disable-model-invocation: true
last_updated: "2026-10-24"
---

# 🧠 seq-think — Sequential Thinking Trigger

> **Alias for:** the `sequentialthinking` MCP tool.
> **Use when:** the problem needs visible, multi-step reasoning before acting (architecture decisions, debugging with several candidate causes, any `.github/` edit per [github-authoring](../../instructions/github-authoring.instructions.md)).

## Behavior

1. Call `sequentialthinking` **before** reading files or running tools; set an initial `totalThoughts` (3–6) and revise as needed.
2. Each thought builds on, questions, or revises the last. Branch when two designs compete; mark revisions.
3. Decompose the final plan into discrete tasks.
4. Execute each task via a subagent (`task` tool), explicitly passing `model: "gemini-3.8-flash"` (unless human specifies a different model). Never leave `model` empty.
5. Pairs with `plan-first` (present plan, wait for approval) and `give-options` (2–6 scored options).

## Usage

```
seq-think: should the indexer use one collection per language or one shared collection?
think deep about the Flyte ↔ Ray hand-off before implementing
```
