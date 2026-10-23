---
name: writing-plans
description: "Write comprehensive implementation plans from specs/designs. DRY, YAGNI, TDD, frequent commits. Creates bite-sized tasks an engineer can execute without guessing."
---

# Writing Plans — Spec → Implementation Plan

**Triggers:** `writing-plans`, `write plan`, `create implementation plan`, `plan this design`

**Upstream:** `analyze-and-brainstorm` hands off here after spec approval
**Downstream:** `executing-plans` or `subagent-driven-development` executes the plan

## Dependencies

| Skill | Required? | Purpose |
|-------|-----------|---------|
| `executing-plans` | One of these | Inline execution with checkpoints |
| `subagent-driven-development` | One of these | Subagent per task (recommended) |

---

## Output Contract

Every plan MUST include:

```markdown
# [Feature Name] Implementation Plan

> **Execution:** Use `subagent-driven-development` (recommended) or `executing-plans`

**Goal:** [One sentence]
**Architecture:** [2-3 sentences]
**Tech Stack:** [Key technologies]

## Global Constraints & Review Focus
- [Global constraints copied verbatim from spec]
- [Top 5 implied edge cases / failure modes to pin with tests]

---

### Task N: [Component Name]

**Files:**
- Create: `exact/path/to/file`
- Modify: `exact/path/to/existing:123-145`
- Test: `tests/exact/path/test.py`

**Interfaces:**
- Consumes: [Exact function signatures, types from earlier tasks]
- Produces: [Exact function names, parameters, return types for later tasks]

- [ ] **Step 1:** [Write failing test + exact command]
- [ ] **Step 2:** [Minimal implementation + run test to pass]
- [ ] **Step 3:** [Commit message]
```

---

## Core Principles (Superpowers v7.0.0)

1. **Bite-sized steps** — 2-5 min steps (test-first, run fail, minimal code, run pass, commit).
2. **Task right-sizing** — Smallest unit carrying its own test cycle for meaningful approval.
3. **Explicit interfaces** — Consumes/Produces blocks prevent subagent signature guessing.
4. **No placeholders** — Every step has runnable code, exact paths, exact commands.
5. **Frequent commits** — One commit per task minimum.

---

## Process

1. **Load spec** — Extract requirements, constraints, and platform limits.
2. **Scope check** — Break independent subsystems into distinct sub-plans.
3. **Map file structure** — One clear responsibility per file; design focused interfaces.
4. **Write tasks** — Bite-sized steps with explicit `Consumes` / `Produces` interfaces.
5. **Self-review** — Check against Review Focus failure modes; verify no placeholders.
6. **Save plan** — `Projects/.../<feature>/PLAN.md` or `Resources/copilot/plans/<feature>.md`.
7. **Offer execution** — Subagent-driven (recommended) or inline execution.

---

## Execution Handoff

```markdown
Plan saved to `<plan_path>`.
**Execution options:**
1. **Subagent-Driven** (recommended) — Fresh agent per task, task review gate.
2. **Inline Execution** — Execute sequentially in current session with ledger.
```

---

## References

- [Planning Workflow Guide](references/planning-workflow-guide.md) — Detailed decomposition & interface rules
- [Plan Document Reviewer](references/plan-document-reviewer-prompt.md) — Subagent template for plan review
- **Superpowers source:** `code/superpowers/skills/writing-plans/SKILL.md` (Release v7.0.0)
