---
name: verification-before-completion
description: "Require fresh command execution evidence before claiming tasks are complete, fixed, or passing. Never assume or extrapolate success without proof."
---

# Verification Before Completion — Evidence Before Claims

**Triggers:** `verify before complete`, `confirm fix`, `evidence gate`, `pre-commit verification`

**Upstream:** Any task execution or bugfix
**Downstream:** Commit, PR creation, or task close

---

## The Iron Law

```
NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
```

If you have not executed the verification command in the current turn and inspected the exit code and output, you cannot claim it passes.

---

## The Verification Gate

```
BEFORE claiming any status or completion:
1. IDENTIFY: What specific command proves this claim?
2. RUN: Execute the FULL command (fresh, complete, targeted).
3. READ: Full output, check exit code (0), count failures (0).
4. VERIFY: Does the evidence substantiate the claim?
   - If NO: State actual status with exact error/failure output.
   - If YES: State claim WITH evidence.
5. ONLY THEN: Make the completion claim.
```

---

## Required Proof per Claim Type

| Claim Type | Required Evidence | Unacceptable Substitute |
| :--- | :--- | :--- |
| **Tests Pass** | Live test command output showing 0 failures | Previous turn output, "should pass" |
| **Linter Clean** | Linter output showing 0 errors | Code inspection, "looks clean" |
| **Build / Compile** | Build command exit code 0 | Linter passing (linter != compiler) |
| **Bug Fixed** | Test reproducing original symptom now passes | Code changed, assumption of fix |
| **Pod / Service Healthy** | `kubectl get pods`, HTTP curl status 200 | Deployment created, manifest applied |
| **Benchmark Claim** | SQLite metrics row with latency/speedup | Mathematical estimation or projection |

---

## Red Flags & Rationalization Prevention

- ❌ "Should work now" / "Looks correct" → **Run the verification.**
- ❌ "Tests pass, phase complete" → **Verify against the requirements checklist.**
- ❌ "Agent reported success" → **Inspect the git diff directly.**
- ❌ Expressing satisfaction ("Great!", "Done!") before tool verification output is visible.

---

## References

- [Verification Patterns & Edge Cases](references/verification-patterns.md) — Command patterns for tests, builds, and k8s
- **Superpowers source:** `code/superpowers/skills/verification-before-completion/SKILL.md` (Release v7.0.0)
