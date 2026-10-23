---
name: systematic-debugging
description: "Discipline for isolating root cause before proposing fixes. Prevents guessing, thrashing, and symptom-only patches across complex distributed systems."
---

# Systematic Debugging — Root Cause Discipline

**Triggers:** `debug`, `test failing`, `unexpected behavior`, `investigate bug`, `root cause`

**Upstream:** Any failure, crash, test error, or unexpected latency
**Downstream:** `test-driven-development` (reproducing test) → surgical fix

---

## The Iron Law

```
NO CODE CHANGES WITHOUT ROOT CAUSE ISOLATION FIRST
```

If you have not identified the exact mechanism that causes the defect, proposing a patch is guessing. Symptom fixes are failure.

---

## The Four Phases

| Phase | Core Objective | Key Gate |
| :--- | :--- | :--- |
| **Phase 1: Root Cause Investigation** | Read full stack traces, reproduce consistently, trace data backwards | Explain *why* the bad value was generated |
| **Phase 2: Pattern Analysis** | Check recent diffs, component boundaries, and environment state | Pinpoint the exact layer failing |
| **Phase 3: Hypothesis Testing** | Form a falsifiable hypothesis and test assumptions minimally | Confirm hypothesis before editing production code |
| **Phase 4: Surgical Fix & Regression Test** | Write failing test first, apply minimal fix, verify no side-effects | Red-green cycle verified |

---

## When to Apply

- **Always** on any unexpected test failure, crash, or build error.
- **Especially** when under time pressure or when a "quick one-line fix" feels obvious.
- When working across multi-layer systems (e.g., Python → C/Rust FFI, KinD K8s → Docker, MCP stdio → LLM).

---

## Red Flags — Stop and Step Back

- ❌ Changing code to see "if this makes it work".
- ❌ Trying a second fix after the first failed without understanding why the first failed.
- ❌ Adding `try/except: pass` or default fallbacks that mask errors without logging.
- ❌ Skipping stack trace lines or assuming the top frame is the bug source.

---

## References

- [Root Cause Investigation & Call Stack Tracing](references/root-cause-investigation.md) — Multi-layer isolation techniques
- **Superpowers source:** `code/superpowers/skills/systematic-debugging/SKILL.md` (Release v7.0.0)
