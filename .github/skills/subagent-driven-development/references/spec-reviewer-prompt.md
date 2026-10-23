# Spec Compliance Reviewer Prompt Template

**Purpose:** Verify implementer built what was requested (nothing more, nothing less).

**Only dispatch after implementer reports DONE or DONE_WITH_CONCERNS.**

---

## Subagent Dispatch Template

```
Task: Review spec compliance for Task N

You are reviewing whether an implementation matches its specification.

## What Was Requested

[FULL TEXT of task requirements]

## What Implementer Claims They Built

[From implementer's report]

## CRITICAL: Do Not Trust the Report

The implementer finished suspiciously quickly. Their report may be incomplete,
inaccurate, or optimistic. You MUST verify everything independently.

**DO NOT:**
- Take their word for what they implemented
- Trust their claims about completeness
- Accept their interpretation of requirements

**DO:**
- Read the actual code they wrote
- Compare actual implementation to requirements line by line
- Check for missing pieces they claimed to implement
- Look for extra features they didn't mention

## Your Job

Read the implementation code and verify:

**Missing requirements:**
- Did they implement everything requested?
- Are there requirements they skipped?
- Did they claim something works but didn't implement it?

**Extra/unneeded work:**
- Did they build things not requested?
- Did they over-engineer or add unnecessary features?

## Output Format

**Status:** ✅ Spec compliant | ❌ Issues found

**Issues (if any):**
- [file:line]: [specific issue]

**Missing:**
- [requirement not implemented]

**Extra:**
- [feature not requested]
```

---

**Source:** `code/superpowers/skills/subagent-driven-development/spec-reviewer-prompt.md`
