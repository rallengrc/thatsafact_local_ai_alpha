---
title: "Search Router v2 Architecture Diagram"
description: "Architecture diagram showing multi-index query intent classification, 4-engine retrieval, AST span containment, and Reciprocal Rank Fusion"
keywords: [search router, tantivy, graphify, chromadb, ripgrep, architecture diagram, plantuml]
category: reference
classification: 🟢🛡️ General
last_updated: "2026-10-11"
author: thatsafact
related:
  - ../copilot/search-router/SEARCH_ROUTER_PLAN.md
  - ../copilot/search-router/TOOLS_REFERENCE.md
---

# Search Router v2 Architecture Diagram

> **TL;DR:** Visual architectural representation of Search Router v2's 3-phase multi-index pipeline: (1) Query Intent Pre-Routing, (2) 4-Engine Retrieval (Tantivy, Graphify, Ripgrep, ChromaDB), and (3) Postprocessing Fusion (AST Span Containment, RRF, and LLM Token Curation).

## 🖼️ Diagram Preview

![Search Router v2 Architecture](search-router-v2-architecture.png)

## 📋 Diagram Source Files

- **PlantUML Specification:** [search-router-v2-architecture.puml](./search-router-v2-architecture.puml)
- **Rendered PNG:** [search-router-v2-architecture.png](./search-router-v2-architecture.png)
- **Mermaid Specification:** [search-router-v2-architecture.mmd](./search-router-v2-architecture.mmd)
