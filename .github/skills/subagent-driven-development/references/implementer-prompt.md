# Implementer Subagent Prompt Template

**Purpose:** Dispatch a subagent to implement a single task from the plan.

---

## Subagent Dispatch Template

```
Task: Implement Task N: [task name]

You are implementing Task N: [task name]

## Task Description

[FULL TEXT of task from plan — paste it here, don't make subagent read file]

## Context

[Scene-setting: where this fits, dependencies, architectural context]

## Before You Begin

If you have questions about:
- Requirements or acceptance criteria
- Approach or implementation strategy
- Dependencies or assumptions
- Anything unclear

**Ask them now.** Raise concerns before starting work.

## Your Job

Once clear on requirements:
1. Implement exactly what the task specifies
2. Write tests (TDD if task says to)
3. Verify implementation works
4. Commit your work with @Jira annotation if test file
5. Self-review
6. Report back

Work from: [directory]

**While you work:** If you encounter something unexpected, **ask questions**.
Don't guess or make assumptions.

## Status Codes

Report one of:
- **DONE** — Task complete, ready for review
- **DONE_WITH_CONCERNS** — Complete but flagging doubts
- **NEEDS_CONTEXT** — Need more information
- **BLOCKED** — Cannot complete, explain why
```

---

**Source:** `code/superpowers/skills/subagent-driven-development/implementer-prompt.md`
