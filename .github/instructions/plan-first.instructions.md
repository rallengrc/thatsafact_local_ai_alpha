---
description: 'Plan-first workflow. When user says "plan-first" or request touches 5+ files, present numbered plan and WAIT for approval before executing.'
applyTo: '**'
---

# Plan-First Workflow (Auto-Apply)

> **Trigger:** User says "plan-first" OR request involves: deleting files, ≥5 file changes, branch operations, or "convert"/"migrate"/"refactor".

1. **Context First (Silent):** Read files and inspect scope. Do NOT modify code.
2. **Present Plan:**
   - Table: `| # | Action | File | Rationale |`
   - Include: **Risks** (destructive/irreversible flags) and **Build/Verification** commands.
3. **WAIT for Approval:**
   - Print: `"Plan ready. Say 'do it' to execute, or adjust."`
   - Proceed only after affirmative signal ("do it", "go", "execute", "approved", "continue").
4. **Execute & Track:** Execute sequentially and maintain an append-only todo ledger.
5. **Skip When:** User gave exact step-by-step instructions, single-file edits, or says "just do it".
