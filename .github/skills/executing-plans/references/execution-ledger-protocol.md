# Execution Ledger Protocol & Template

> **Source:** Superpowers v7.0.0 (`code/superpowers/skills/executing-plans/references/`)

The execution ledger (`.ledger.md`) maintains durable state across turns and context compressions without bloating parent context.

---

## 1. Ledger File Location & Header

File path: `.ledger.md` (or co-located with plan in `Projects/.../.ledger.md`).

```markdown
# Execution Ledger

**Plan:** [PATH_TO_PLAN]
**Started:** [TIMESTAMP]
**Strategy:** Inline Execution / Subagent-Driven

---

## Log
```

---

## 2. Entry Types

### Task Completion Entry:
```markdown
### [TIMESTAMP] Task N: [Task Name] Complete
- **Status:** APPROVED
- **Verification:** `.venv/bin/pytest tests/test_feature.py` (3 passed in 0.12s)
- **Commit:** `abc1234` "feat: add feature endpoint"
```

### Ruling Entry (Rulings, Not Stalls):
```markdown
### [TIMESTAMP] Ruling on Task N
- **Issue:** Specification was silent on handling empty JSON list input.
- **Decision:** Return empty list `[]` with HTTP 200 instead of HTTP 400.
- **Rationale:** Aligns with REST idempotency and existing search router pattern.
- **Cost if Wrong:** Low — caller expects list type; easy one-line validator update if strictness needed.
```

### Circuit Breaker Trip:
```markdown
### [TIMESTAMP] Circuit Breaker Tripped (Task N)
- **Rounds Exceeded:** 5 rounds attempted.
- **Open Finding:** Third-party dependency version mismatch on Python 3.14.
- **Resolution:** Pinned compatible pre-release wheel in requirements.txt.
```
