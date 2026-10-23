---
title: Duplicate Prevention & Script Reuse Protocol
description: Step-by-step procedure to audit existing scripts and skills before authoring new tooling in MLaaS
keywords: [duplicate prevention, script reuse, lean ai, tooling audit, anti-duplication, skill audit]
category: reference
classification: 🟢🛡️ General
last_updated: '2026-10-12'
author: thatsafact
ai_search_aliases: [avoid dupe scripts, script audit protocol, prevent duplicate code, dupe skill check]
---

# Duplicate Prevention & Script Reuse Protocol

> **TL;DR:** Strict 4-step audit protocol to prevent duplicate scripts or duplicate skills from being created in MLaaS.
> **Use this for:** Guiding AI agents and developers through tool discovery before any new script or skill file is authored.

---

## 1. The Duplicate Hazard & Root Causes

A duplicate script occurs when:
1. An agent checks only `scripts/` root instead of subsystem subdirectories (`automation/`, `indexing/`, `search_router/`).
2. An agent assumes a missing utility without grepping the codebase or checking `_INDEX.md`.
3. An agent creates a duplicate skill in `.github/skills/` without inspecting `.github/skills/` or `available_skills`.

### Case Study: The `pdf_to_md.py` Duplication
In October 2026, an agent created `scripts/pdf_to_md.py` unaware that a battle-tested `scripts/automation/pdf_to_md.py` already existed. The duplicate had to be deleted, the real script relocated, and documents reprocessed.
**Lesson:** Subsystem indices must be checked first, not just top-level directory listings.

---

## 2. Mandatory Pre-Authoring Checklist

Before creating ANY new `.py` file or `.github/skills/<name>` directory, execute this checklist:

```bash
# Step 1: Scan master script index
view path="scripts/_INDEX.md"

# Step 2: Search for relevant keywords in all script indices
grep -n "keyword" scripts/**/_INDEX.md

# Step 3: Check if a similar file name exists anywhere under scripts/
glob pattern="**/*keyword*.py" paths=["scripts"]

# Step 4: Check if a skill for this domain already exists
glob pattern="*" paths=[".github/skills"]
```

---

## 3. Decision Matrix: Reuse vs. Extend vs. Create

| Situation | Action to Take |
|---|---|
| Script exists and does what is needed | **Execute existing script** directly with appropriate flags. |
| Script exists but needs an additional flag or optimization | **Extend existing script in-place**; do NOT create a separate wrapper. |
| Functionality belongs to an existing subsystem (`automation`, `indexing`, `search_router`) | Create the file **inside that subsystem folder**, never in root `scripts/`. |
| Genuinely new subsystem required | Discuss with user first, create subfolder, add `_INDEX.md`, register in `scripts/_INDEX.md`. |
| Skill exists in `.github/skills/` covering the domain | **Extend existing skill** or its `references/` instead of creating a dupe skill. |

---

## 4. Post-Creation Registration Requirements

If a new script or skill MUST be created:
1. **Never dump in `scripts/` root:** Place it in `scripts/automation/`, `scripts/indexing/`, or `scripts/search_router/`.
2. **Update Subsystem Index:** Add row to `scripts/<subsystem>/_INDEX.md`.
3. **Update Master TOC:** If user-facing, update `MASTER_TOC.md`.
4. **Re-index:** Run `.venv/bin/python scripts/indexing/index_workspace.py` and `index_tantivy.py`.
5. **Verify Tests:** Ensure `.venv/bin/python -m pytest scripts/` passes.
