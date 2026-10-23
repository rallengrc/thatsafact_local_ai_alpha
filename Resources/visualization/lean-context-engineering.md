---
title: "Lean AI Context Engineering Pattern Diagram"
description: "Architecture diagram showing orchestrator, dispatch tier, and modular reference structure for lean AI context management"
keywords: [lean context, AI context engineering, plantuml, mermaid, architecture diagram]
category: reference
classification: 🟢🛡️ General
last_updated: "2026-10-11"
author: thatsafact
related:
  - ../../.github/instructions/references/lean-rules-reference.md
  - ../copilot/lean-ai-principals.md
---

# Lean AI Context Engineering Pattern Diagram

> **TL;DR:** Visual architectural representation of the 3-layer Lean AI context engineering structure: Lean Orchestrator (≤100L) → Fast Dispatch (`applyTo`) → Modular References (≤150L). Preserves ≥80% of model context for user code and AST retrieval.

## 🖼️ Diagram Preview

![Lean AI Context Engineering Pattern](lean-context-engineering.png)

## 📋 Diagram Source Files

- **PlantUML Specification:** [lean-context-engineering.puml](./lean-context-engineering.puml)
- **Rendered PNG:** [lean-context-engineering.png](./lean-context-engineering.png)
- **Mermaid Specification:** [lean-context-engineering.mmd](./lean-context-engineering.mmd)
