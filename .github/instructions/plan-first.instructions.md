---
description: 'Plan-first workflow. When user says "plan-first" or request is bulk (5+ files, convert, migrate, refactor, delete), present numbered plan and WAIT for approval before executing.'
applyTo: '**'
---

# Plan-First Workflow (Auto-Apply)

## Trigger: `plan-first` or Bulk Operations

Activate when user says "plan-first" OR request involves: deleting files, 5+ file changes, branch operations, "convert"/"migrate"/"refactor", "plan and then..."

## Workflow

### 1. Gather Context (Silent)
Read files, search codebase, understand scope. Do NOT implement.

### 2. Present Plan

| # | Action | File | Rationale |
|---|--------|------|-----------|
| 1 | Create | path/to/file | ... |

Include: **Risks** (destructive/irreversible flags) and **Build verification** command.

### 3. WAIT
Print: **"Plan ready. Say 'do it' to execute, or adjust."**

Approval signals: "do it", "go", "execute", "approved", "continue", "looks good", "lgtm", any affirmative.

### 4. Execute
Implement in order. Track progress with todo list.

## Skip Plan-First When
- User gave step-by-step instructions already
- Single-file, single-change operations
- "just do it" or "skip plan"
- Continuation of already-approved work
