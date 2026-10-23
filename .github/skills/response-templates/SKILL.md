---
name: response-templates
description: "Enforce consistent response structure based on question type. Maps question patterns to response formats."
---

# Response Templates — Format Enforcement

**Auto-invoked:** Every response. Classifies question → applies template.

---

## Question Classification → Template

| Pattern | Template | Example |
|---------|----------|---------|
| "what is X" | Definition | Definition → Context → See Also |
| "how to X" | Procedure | Steps → Prerequisites → Gotchas |
| "why does X" | Explanation | Cause → Effect → Evidence |
| "find X" | Search Result | Results Table → Source → Confidence |
| "fix X" | Solution | Problem → Fix → Verification |
| "compare X vs Y" | Comparison | Table → Recommendation → Trade-offs |
| "create X" | Creation | Plan → Execution → Verification |
| Complex/multi-part | Godfather | Full discovery → Options → Recommendation |

---

## Template Structures

### Definition Template
```markdown
**{Term}:** {one-line definition}

**Context:** {when/where this applies}

**See Also:** {related terms or files}
```

### Procedure Template
```markdown
## Steps
1. {step}
2. {step}

## Prerequisites
- {requirement}

## Gotchas
- {common mistake}
```

### Search Result Template
```markdown
| File | Match | Confidence |
|------|-------|------------|
| path | excerpt | HIGH/MED/LOW |

**Source:** {engine used}
```

---

## Mode Overrides

| Mode | Template Behavior |
|------|-------------------|
| teach-mode | Expand all sections + analogies |
| kiss-mode | Add Concierge Note + charm |

---

## Skip Conditions

- User says "just answer" or "skip format"
- Response is single-word acknowledgment
- Error/exception response
- Terminal notification
