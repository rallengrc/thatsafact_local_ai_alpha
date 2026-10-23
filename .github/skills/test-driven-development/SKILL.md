---
name: test-driven-development
description: "Write the failing test first, watch it fail, then write minimal code to pass. Never write production code before a failing test exists."
---

# Test-Driven Development (TDD) — The Red-Green-Refactor Gate

**Triggers:** `tdd`, `test driven`, `write tests first`, `red green refactor`

**Upstream:** `writing-plans` or any bugfix/feature request
**Downstream:** Implementation code and `verification-before-completion`

---

## The Iron Law

```
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```

If you write code before the test, you must delete it and start over. Watching the test fail proves it tests the expected condition and is capable of failing.

---

## The Red-Green-Refactor Protocol

```
1. RED: Write one focused test for the next smallest unit of behavior.
2. VERIFY RED: Run test command. MUST fail with the expected failure (e.g. AssertionError, NameError).
   - If test passes immediately: The test is flawed or behavior already exists. Fix test.
3. GREEN: Write the minimal production code needed to pass the test.
4. VERIFY GREEN: Run test command. MUST pass (exit code 0).
5. REFACTOR: Clean up implementation without altering behavior. Verify all tests remain green.
```

---

## When TDD is Mandatory

- **New Features:** Define API contract and assertions before implementing logic.
- **Bug Fixes:** Write regression test demonstrating the bug before touching any fix.
- **Refactoring:** Ensure tests exist and pass before rewriting internal algorithms.

**Exceptions (Only with explicit user confirmation):**
- Throwaway one-liner exploratory CLI scripts.
- Pure declarative configuration files (JSON/YAML without embedded logic).

---

## References

- [TDD Cycle & Rationalization Prevention Table](references/tdd-cycle-and-rebuttals.md) — Common excuses and why order matters
- **Superpowers source:** `code/superpowers/skills/test-driven-development/SKILL.md` (Release v7.0.0)
