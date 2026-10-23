---
title: MLaaS Master Table of Contents
description: Central master table of contents and knowledge map for the entire MLaaS workspace
keywords:
- master toc
- table of contents
- knowledge map
- index
- navigation
- MLaaS
- find
- search
- locate
category: index
classification: 🟢🛡️ General
last_updated: '2026-10-22'
author: thatsafact
ai_search_aliases:
- master toc
- table of contents
- site map
- all docs
- find any file
- workspace map
- knowledge map
---

# 🗺️ MLaaS Master Table of Contents

> **TL;DR:** Central knowledge map and master directory indexing all sections, sub-systems, project packages, reference manuals, local memories, and scripts across the MLaaS workspace.
> **Use this for:** Global discovery and navigation across the entire MLaaS knowledge base.

---

## 🧭 High-Level Workspace Architecture

The MLaaS workspace is organized into five main functional domains adhering to PARA methodology principles:

1. **[Projects/](Projects/_INDEX.md):** Runnable project packages, featuring **hello-mlaas-burst**.
2. **[Areas/](Areas/_INDEX.md):** Ongoing knowledge areas, communication standards, and organizational methodologies.
3. **[Resources/](Resources/_INDEX.md):** Reusable templates, diagram guides, and search router engineering docs.
4. **Memories/** (local only, git-ignored): Persistent AI context, user preferences, repository state, prompt histories, and architectural checkpoints.
5. **[Scripts/](scripts/_INDEX.md):** Operational Python scripts for vector indexing, MCP search routing, ripgrep scanning, and test suites.

---

## 📁 Master Directory & Index Registry

| Section / Directory | Index Link | Purpose & Highlights | Key Topics |
|---------------------|------------|----------------------|------------|
| **Root Docs** | [README.MD](README.MD) | Workspace overview, local LLM setup, and quick commands | MLaaS, Ollama, qwen3.8, indexing |
| **Code Repositories** | [CODE_REPOSITORIES.md](CODE_REPOSITORIES.md) | Catalog of 34 external reference git repositories in `code/` | Flyte, Ray, Karpenter, Tantivy, MCP, Kubernetes, clones |
| **Areas** | [Areas/_INDEX.md](Areas/_INDEX.md) | Communication standards and terminology | Lingua franca, glossary, standards |
| **Projects** | [Projects/_INDEX.md](Projects/_INDEX.md) | Master index for runnable project packages | hello-mlaas-burst, Karpenter, Ray, Flyte |
| ↳ *Hello MLaaS Burst* | [Projects/hello-mlaas-burst/README.md](Projects/hello-mlaas-burst/README.md) | Runnable Flyte + Ray surrogate modeling pipeline & 4-node KinD harness | hello-mlaas-burst, surrogate, KinD, benchmark |
| **Resources** | [Resources/_INDEX.md](Resources/_INDEX.md) | Master catalog of technical references and frameworks | Templates, Copilot, visualization, search router |
| ↳ *Templates* | [Resources/Templates/_INDEX.md](Resources/Templates/_INDEX.md) | Standardized templates for docs, meetings, and status | AI-searchable template, meeting note |
| ↳ *Copilot & Tools* | [Resources/copilot/_INDEX.md](Resources/copilot/_INDEX.md) | MCP server setup, sequential thinking, lean authoring | MCP, sequential thinking, lean AI |
| ↳ *Search Router* | [Resources/copilot/search-router/_INDEX.md](Resources/copilot/search-router/_INDEX.md) | Hybrid ripgrep + ChromaDB search router engineering docs | Quick start, roadmap, architecture |
| ↳ *Visualization* | [Resources/visualization/_INDEX.md](Resources/visualization/_INDEX.md) | Syntax reference manuals for Mermaid and PlantUML | Mermaid syntax, PlantUML syntax |
| **Scripts & Tooling** | [scripts/_INDEX.md](scripts/_INDEX.md) | Master index of Python subsystems: search routing, indexing, automation, and tests | search_router, indexing, automation, tests |
| ↳ *Search Router* | [scripts/.../search_router/_INDEX.md](scripts/search_router/_INDEX.md) | Hybrid ripgrep + ChromaDB search router, MCP tools, and stdio server | search_router, search_server, livetext, adapter |
| ↳ *Indexing* | [scripts/.../indexing/_INDEX.md](scripts/indexing/_INDEX.md) | Workspace document scanner, ChromaDB provider abstraction, and demos | index_workspace, vectordb_provider, embeddings |
| ↳ *Telemetry* | [scripts/.../telemetry/_INDEX.md](scripts/telemetry/_INDEX.md) | Team prompt telemetry ingestion engine, SQLite FTS5 indexer, and analytics | telemetry, prompt tracking, fts5, doc attribution |
| ↳ *Automation* | [scripts/.../automation/_INDEX.md](scripts/automation/_INDEX.md) | Metadata enricher, TOC/index generator, and PDF converter | update_metadata, generate_toc, pdf_to_md |
| ↳ *Tests* | [scripts/.../tests/_INDEX.md](scripts/tests/_INDEX.md) | Comprehensive test suite covering all subsystems (238 passing tests) | test_indexing, test_search_router, test_livetext, test_common_platform |

---

## ⚡ Quick Search & Discovery Cheat Sheet

| I Want To... | Check This Document | Shortcut / Query |
|--------------|---------------------|------------------|
| Run semantic search across workspace | [QUICK_START.md](Resources/copilot/search-router/QUICK_START.md) | `.venv/bin/python3 scripts/search_router/mcp_search_router.py --query "..."` (or `.venv\Scripts\python.exe` on Windows) |
| Create a new AI-searchable doc | [AI-SEARCHABLE-DOC-TEMPLATE.md](Resources/Templates/AI-SEARCHABLE-DOC-TEMPLATE.md) | Copy frontmatter and TL;DR boilerplate |
| Configure MCP tools | [MCP_SETUP.md](Resources/copilot/MCP_SETUP.md) | Setup mlaas-search and sequentialthinking |
| Look up vi / Vim editor commands | [vi-cheatsheet.md](Resources/vi-cheatsheet.md) | Terminal modal editing, navigation, write & quit |
| Find existing scripts & avoid dupes | [scripts/_INDEX.md](scripts/_INDEX.md) & [find-scripts SKILL](.github/skills/find-scripts/SKILL.md) | Audit 46 Python scripts across automation, indexing, search router, and tests |
