# Task Reviewer Prompt Template

> **Source:** Superpowers v7.0.0 (`code/superpowers/skills/subagent-driven-development/task-reviewer-prompt.md`)

Use this template when dispatching a combined task reviewer subagent. The reviewer inspects the task's diff once and evaluates both spec compliance and code quality in a single pass.

---

## Subagent Dispatch Specification

```yaml
Subagent:
  agent_type: "general-purpose"
  description: "Review Task N (spec + quality)"
```

### Prompt Template:

```markdown
You are reviewing one task's implementation for spec compliance and code quality. This is a task-scoped gate.

## 1. What Was Requested & Binding Constraints
- Task brief: [TASK_BRIEF_PATH_OR_TEXT]
- Global constraints: [GLOBAL_CONSTRAINTS]

## 2. Diff Under Review
- Base: [BASE_SHA] | Head: [HEAD_SHA]
- Diff summary: `git diff --stat [BASE_SHA]..[HEAD_SHA]`
- Read the diff directly. Do not crawl the broader codebase unless verifying a concrete named interface risk.

## 3. Review Rules
- Read-only review: Do not mutate working tree or index.
- Do not trust implementer claims: Verify code changes against actual diff.
- Do not re-run full test suites: Verify implementer's reported TDD evidence; run a targeted test only if there is a concrete defect hypothesis.
- No subagent spawning: Complete the review in this single pass.

## 4. Evaluation Checklist

### Part A: Spec Compliance
- [ ] **Missing:** Any requirement skipped, missed, or claimed without code?
- [ ] **Extra:** Features not requested, premature abstractions, or scope creep?
- [ ] **Misunderstood:** Built the wrong way or solved the wrong problem?

### Part B: Code Quality & Safety
- [ ] **Error Handling:** Are exceptions and edge cases gracefully handled?
- [ ] **Test Coverage:** Are tests meaningful, fast, and covering edge cases?
- [ ] **Style & Typing:** Clean type hints, no placeholder comments, idiomatic syntax.
- [ ] **Security:** No hardcoded secrets, shell injections, or unsafe deserialization.

## 5. Output Format

Return your verdict in this exact structure:

```markdown
### Task Review Verdict: [APPROVED | CHANGES_REQUIRED]

#### Spec Compliance:
- [✅ / ❌] [Finding or confirmation]

#### Code Quality:
- [✅ / ❌] [Finding or confirmation]

#### Actionable Fix Items (if CHANGES_REQUIRED):
1. `file.py:line`: Specific issue and required change.
```
