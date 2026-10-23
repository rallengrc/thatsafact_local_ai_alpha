---
name: executing-plans
description: "Execute implementation plans sequentially inline in the current session. TDD per-task gate, continuous execution without stalls, and append-only ledger."
---

# Executing Plans — Inline Plan Execution

**Triggers:** `executing-plans`, `execute plan`, `run plan inline`

**Upstream:** `writing-plans` produces the implementation plan
**Downstream:** `finishing-a-development-branch` or commit/PR

---

## Core Principles (Superpowers v7.0.0)

Inline execution executes tasks directly in the current session without spawning subagents. It pays for one context, maintaining state through a durable ledger.

1. **The Plan Did the Thinking:** Execute each task as specified. Do not redesign on the fly.
2. **Continuous Execution:** Do not stop between tasks to ask "should I continue?". Execute all tasks sequentially to completion.
3. **Rulings, Not Stalls:** When encountering minor ambiguities or edge cases, make an explicit ruling. Record in `.ledger.md` as `Ruling: <decision> — <why> — <cost if wrong>` and proceed.
4. **TDD is the Task Gate:** Write failing test first, make it pass, verify exit code 0, commit.

---

## When to Stop (The Four Hard Breakers)

Only four conditions permit stopping to prompt the user:
1. Irreversible or destructive operation (deleting branch, data loss).
2. Security-sensitive action (transmitting credentials, modifying permissions).
3. External side-effects outside repository (merging to shared remote, publishing packages).
4. Fatal plan defect where every forward path is pure guesswork.

---

## Execution Cycle per Task

```
1. READ: Load current task requirements, files, and Consumes/Produces interfaces.
2. RED: Write failing test, run test command, confirm it fails with expected message.
3. GREEN: Implement minimal code to satisfy test, run test command, confirm pass.
4. REFACTOR: Clean up syntax, remove debug output, verify all tests still pass.
5. COMMIT: Create git commit with conventional commit message.
6. LEDGER: Update plan checkbox (- [x]) and append completion entry to .ledger.md.
```

---

## References

- [Execution Ledger Protocol & Format](references/execution-ledger-protocol.md) — Durable tracking across turns
- **Superpowers source:** `code/superpowers/skills/executing-plans/SKILL.md` (Release v7.0.0)
