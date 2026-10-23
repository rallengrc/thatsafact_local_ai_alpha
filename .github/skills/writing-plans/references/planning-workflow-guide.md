# Planning Workflow — Best Leverage Guide

> **Source:** Superpowers project (`code/superpowers/skills/`)

---

## The Complete Workflow

```
┌─────────────────────────┐
│ analyze-and-brainstorm  │  ← JIRA ticket → design spec
└───────────┬─────────────┘
            │ (produces approved spec)
            ▼
┌─────────────────────────┐
│    writing-plans        │  ← spec → implementation plan
└───────────┬─────────────┘
            │ (produces bite-sized tasks)
            ▼
     ┌──────┴──────┐
     ▼             ▼
┌──────────┐  ┌──────────────────────────┐
│executing │  │ subagent-driven-         │
│-plans    │  │ development              │
└────┬─────┘  └────────────┬─────────────┘
     │                     │
     │ (inline execution)  │ (fresh subagent per task)
     └──────────┬──────────┘
                ▼
┌─────────────────────────────────┐
│ finishing-a-development-branch  │  ← verify tests → PR/merge
└─────────────────────────────────┘
```

**Supporting skill:** `using-git-worktrees` (isolate work in clean worktree)

---

## When to Use Each Skill

| Situation | Skill | Why |
|-----------|-------|-----|
| Use case exists, need design | `analyze-and-brainstorm` | Produces spec with diagrams |
| Have spec, need tasks | `writing-plans` | TDD-oriented task breakdown |
| Small task list (<5) | `executing-plans` | Inline checkpoints, fast |
| Large or complex tasks (5+) | `subagent-driven-development` | Fresh context per task |
| Work done, need merge | `finishing-a-development-branch` | Tests → PR → cleanup |
| Need isolated environment | `using-git-worktrees` | Clean git state per feature |

---

## Best Practices for Maximum Leverage

### 1. Start with analyze-and-brainstorm for any use case
```
/analyze implement-ray-enhancement.md
```
- Gets context automatically
- Produces design spec with options matrix
- Generates diagrams for complex flows
- **Output:** Detailed spec ready for implementation

### 2. Generate plan BEFORE touching code
```
/write-plan ray-enhancemnt-spec.md
```
- Breaks spec into TDD tasks
- Each task is independently testable
- Include constraints (cloud, local, security)
- **Output:** Plan document with numbered tasks ray-enhancement-plam.md

### 3. Choose execution strategy based on complexity

**For 1-4 simple tasks → `executing-plans`:**
- Inline execution with checkpoints
- Git commits after each task
- Fast, no subagent overhead

**For 5+ tasks OR complex work → `subagent-driven-development`:**
- Fresh subagent per task (clean context)
- Two-stage review (spec compliance + code quality)
- Parallel-safe

### 4. Always finish branches properly
```
/finish-branch
```
- Verifies all tests pass
- Presents merge options (squash vs merge commit)
- Cleans up worktree if used
- **Output:** PR link or merge confirmation

### 5. Use worktrees for risky work
```
/worktree feature/My-ML-Experiment
```
- Isolated environment
- Can't accidentally commit to wrong branch
- Easy cleanup on failure

---

## Cross-Skill Integration Points

### analyze-and-brainstorm → writing-plans
- `analyze-and-brainstorm` produces `## Approved Spec` section
- `writing-plans` consumes that as input

### writing-plans → execution
- `writing-plans` produces numbered task list
- `executing-plans` runs them inline (small)
- `subagent-driven-development` dispatches parallel (large)

### godfather-mode → subagent-driven-development
- `godfather-mode` produces decisive recommendation
- Complex execution chains to `subagent-driven-development`

---

## Shared References (Reuse These)

| Template | Location | Used By |
|----------|----------|---------|
| Implementer prompt | `.github/skills/subagent-driven-development/references/implementer-prompt.md` | subagent-driven-development, godfather-mode |
| Spec reviewer | `.github/skills/subagent-driven-development/references/spec-reviewer-prompt.md` | subagent-driven-development |
| Code quality reviewer | `.github/skills/subagent-driven-development/references/code-quality-reviewer-prompt.md` | subagent-driven-development |
| Plan reviewer | `.github/skills/writing-plans/references/plan-document-reviewer-prompt.md` | writing-plans |

---

## Common Mistakes & Quick Commands

- **Skip brainstorm:** Leads to design rework — always start with a spec.
- **Giant task list:** Causes context overflow — use subagents for >5 tasks.
- **Work on main:** Risk to codebase — always use feature worktrees.

```bash
/analyze Epic Use Case       # Start with Epic
/write-plan                  # Generate implementation plan
/execute-plan                # Inline execution (small)
/subagent Use Case in Epic   # Parallel execution (large)
/finish-branch               # Tests → PR → cleanup
```

---

*Created: 2026-09-25 | Source: code/superpowers/skills/*
