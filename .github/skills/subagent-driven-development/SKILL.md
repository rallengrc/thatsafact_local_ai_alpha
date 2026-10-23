---
name: subagent-driven-development
description: "Execute plans via fresh subagent per task with single combined task review (spec + quality), R=5 breaker trip, and continuous execution ledger."
---

# Subagent-Driven Development — Task Dispatch

**Triggers:** `subagent-driven`, `dispatch tasks`, `subagent execution`

**Upstream:** `writing-plans` creates the plan
**Downstream:** `finishing-a-development-branch` completes the work

---

## Core Principle (Superpowers v7.0.0)

Fresh subagent per task + single task review (spec + quality) + broad final review = high velocity, zero context pollution.

- **Rulings, not stalls:** Coordinator rules on conflicts and ambiguous edges; record decisions in `.ledger.md` as `Ruling: <decision> — <why> — <cost if wrong>` and keep executing.
- **Continuous execution:** Do not stop between tasks to ask "should I continue?". Run all plan tasks until complete, breaker trips, or irreversible action required.
- **Circuit breaker (`R = 5`):** If implementer cannot resolve review findings after 5 rounds, adjudicate open items, record in ledger, and proceed.

---

## When to Use

```
Have implementation plan? → Tasks mostly independent? → Stay in this session?
├── YES → YES → YES → subagent-driven-development (this skill)
├── YES → YES → NO → executing-plans (inline session execution)
└── NO or tightly coupled → brainstorm first or use executing-plans
```

---

## The Process

### Per Task Cycle:
1. **Dispatch implementer subagent:** Provide task text, files, and `Consumes`/`Produces` interface blocks.
2. **Implementer work:** Implementer writes failing test, implements minimal code, verifies all green, self-reviews, and commits.
3. **Dispatch task reviewer:** Single combined pass checking both spec compliance and code quality.
   - If ✅ approved: Append completion to `.ledger.md`, proceed to next task.
   - If findings conflict with plan: Rule on the conflict, ledger the ruling.
   - If fixes needed: Round 1-3 resume implementer; Round 4-5 dispatch fresh implementer on higher-capability model.
   - If Round 5 reached: Breaker trips. Adjudicate each finding, record rulings, and continue.

### After All Tasks:
- Dispatch final code reviewer for the whole branch diff.
- Complete work via `finishing-a-development-branch`.

---

## Model Selection

| Task Type | Model | Examples |
|-----------|-------|----------|
| Mechanical (1-2 files, clear spec) | Fast/cheap | Unit tests, CRUD, isolated functions |
| Integration (multi-file) | Standard | Search router engines, DAG pipelines |
| Architecture / Final Review | Most capable | Cross-system review, safety checks |

---

## References

- [Task Reviewer Prompt](references/task-reviewer-prompt.md) — Single combined spec + quality reviewer
- [Implementer Prompt](references/implementer-prompt.md) — Subagent implementer contract
- [Spec Reviewer Prompt (Legacy)](references/spec-reviewer-prompt.md)
- [Code Quality Reviewer Prompt (Legacy)](references/code-quality-reviewer-prompt.md)
- **Superpowers source:** `code/superpowers/skills/subagent-driven-development/SKILL.md` (Release v7.0.0)
