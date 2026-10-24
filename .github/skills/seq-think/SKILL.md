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
3. End with one hypothesis, a verification step, and a single recommendation.
4. Pairs with `plan-first` (present the plan, wait for approval) and `give-options` (2–6 scored options).

## Usage

```
seq-think: should the indexer use one collection per language or one shared collection?
think deep about the Flyte ↔ Ray hand-off before implementing
```
