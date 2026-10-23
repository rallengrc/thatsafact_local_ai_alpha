---
description: 'Give-options directive. Probability-scored options (2-6) for debugging, architecture trade-offs, and ambiguous requests; "give options" and "sample tails" keywords force it. Skip for factual answers and single-action requests.'
applyTo: '**'
---

# Give Options — Probability Sampling

For debugging, architecture trade-offs, and requirements open to interpretation, return 2-6 distinct options, each with a probability, instead of one "typical" answer. Rationale: [Stanford-Prompt-Engineering.md](../../Resources/copilot/stanford-llm-creativity/Stanford-Prompt-Engineering.md).

- **Triggers:** `give options` forces it; `sample tails` forces 5-6 options, most under ~10%.
- **Do NOT apply** to factual answers, single-action requests ("run the tests"), or clarifying questions. Unsure → answer directly.
- **Count:** 2-3 for simple questions, 5-6 for complex ones. Never pad.
- **Probability:** "how likely correct" (debugging) or "how well it fits" (design). Sum to ~100% unless options are not mutually exclusive. Probabilities are judgment, never benchmarks.
- **Distinct:** options must differ in substance. In debugging, always include one labeled low-probability cause and what evidence would confirm it.
- **Finish** with one recommendation and the single check that would validate it.

```markdown
| # | Option | Probability | Why / How to confirm |
|---|--------|-------------|----------------------|
| 1 | Most likely | 55% | Evidence + quick check |
| 2 | 🎲 Tail: unconventional | 15% | What would prove it |

**Recommendation:** Option 1 — verify with <one check>.
```

Bulk operations still plan first: [plan-first.instructions.md](plan-first.instructions.md).
