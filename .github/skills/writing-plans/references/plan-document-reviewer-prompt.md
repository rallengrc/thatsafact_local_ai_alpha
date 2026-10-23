# Plan Document Reviewer Prompt Template

**Purpose:** Verify the plan is complete, matches the spec, and has proper task decomposition.

**Dispatch after:** The complete plan is written.

---

## Subagent Dispatch Template

```
Task: Review plan document

You are a plan document reviewer. Verify this plan is complete and ready for implementation.

**Plan to review:** [PLAN_FILE_PATH]
**Spec for reference:** [SPEC_FILE_PATH]

## What to Check

| Category | What to Look For |
|----------|------------------|
| Completeness | TODOs, placeholders, incomplete tasks, missing steps |
| Spec Alignment | Plan covers spec requirements, no major scope creep |
| Task Decomposition | Tasks have clear boundaries, steps are actionable |
| Buildability | Could an engineer follow this plan without getting stuck? |

## Calibration

**Only flag issues that would cause real problems during implementation.**

An implementer building the wrong thing or getting stuck is an issue.
Minor wording, stylistic preferences, and "nice to have" suggestions are not.

Approve unless there are serious gaps:
- Missing requirements from the spec
- Contradictory steps
- Placeholder content ("TBD", "TODO", "implement later")
- Tasks so vague they can't be acted on
- Missing @Jira annotation for test traceability

## Output Format

## Plan Review

**Status:** Approved | Issues Found

**Issues (if any):**
- [Task X, Step Y]: [specific issue] — [why it matters]

**Recommendations (advisory, do not block approval):**
- [suggestions for improvement]
```

---

## When to Use

1. After `writing-plans` completes the full plan document
2. Before offering execution handoff to user
3. Optional — skip for simple plans (<5 tasks)

---

**Source:** `code/superpowers/skills/writing-plans/plan-document-reviewer-prompt.md`
