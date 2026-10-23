# Code Quality Reviewer Prompt Template

**Purpose:** Verify implementation is well-built (clean, tested, maintainable).

**Only dispatch after spec compliance review passes.**

---

## Subagent Dispatch Template

```
Task: Review code quality for Task N

You are reviewing code quality for an implementation that passed spec compliance.

## What Was Implemented

[From implementer's report]

## Git Diff Context

BASE_SHA: [commit before task]
HEAD_SHA: [current commit]

## Your Job

Review the code for quality concerns:

**Structure:**
- Does each file have one clear responsibility?
- Are units decomposed for independent testing?
- Is the implementation following the file structure from the plan?

**Quality:**
- Is the code clean and readable?
- Are tests comprehensive and meaningful?
- Is error handling appropriate?

**Growth concerns:**
- Did this change create new files that are already large?
- Did it significantly grow existing files?
- (Don't flag pre-existing file sizes)

## Output Format

**Strengths:**
- [what was done well]

**Issues:**
- **Critical:** [must fix before merge]
- **Important:** [should fix]
- **Minor:** [nice to have]

**Assessment:** ✅ Approved | ❌ Needs fixes
```

---

**Source:** `code/superpowers/skills/subagent-driven-development/code-quality-reviewer-prompt.md`
