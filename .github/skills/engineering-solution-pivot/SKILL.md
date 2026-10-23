---
name: engineering-solution-pivot
description: "Deep-reasoning escalation for engineering dead ends, piling-up workarounds, or critical architectural decisions. TRIGGERS: 'solution-pivot', 'adversarial-review', 'stuck on design', 'workarounds piling up'. NOT for routine coding or single-file fixes."
---

# Engineering Solution Pivot

A deep-reasoning escalation method for technical problems where the obvious path is exhausted — blocked, failing, or suspiciously complex — or where an architectural or security decision warrants rigorous, skeptical analysis.

## Core Rules

1. **Optimize the objective, not the first implementation chosen:** The proposed implementation is only a hypothesis about how to reach an outcome.
2. **Transform constraints instead of accumulating workarounds:** Don't just ask *"How do we solve this within current limits?"* Ask *"Can we change the architecture, contract, layer, or data flow so the constraint no longer exists?"*
3. **Evidence labeling:** Explicitly label decision-critical claims: `[Verified]`, `[Inferred]`, `[Assumed]`, `[Unknown]`.
4. **Security controls are information, not obstacles:** Never disable or bypass security controls; find the path designers intended.
5. **Recommendation is not authorization:** Provide analysis and options; never execute high-impact mutations without explicit approval.

## The 11-Stage Gated Reasoning Workflow

When this skill is invoked, execute these steps using sequential thinking:

| # | Stage | Objective | Exit Condition |
|---|---|---|---|
| **0** | **Checkpoint** | Stop thrashing. Note prior attempts and the shared causal hypothesis. | Paused without repeating failed hypothesis. |
| **1** | **Frame Objective** | Separate the outcome from the implementation (success criteria). | 1–2 sentence outcome without implementation name. |
| **2** | **Establish Evidence** | Label claims `[Verified]`, `[Inferred]`, `[Assumed]`, `[Unknown]`. | Critical facts verified via direct observation/code. |
| **3** | **Diagnose** | Distinguish symptom from root cause; identify cheapest discriminating check. | Leading hypothesis supported by evidence. |
| **4** | **Classify Constraints** | Physical, security control, regulatory, preference, or design artifact. | Hard constraints separated from negotiable design artifacts. |
| **5** | **Transform or Work Around** | Apply 11 design transformation levers to remove the constraint entirely. | Candidate architectural transformations identified. |
| **6** | **Generate Options** | Propose materially different options labeled `[Verified|Plausible|Speculative]`. | 1–3 credible options with disqualifying evidence noted. |
| **7** | **Adversarial Review** | Attack the leading options (failure modes, race conditions, security, data loss). | Concrete risks and trade-offs documented. |
| **8** | **Decide** | Compare options against criteria (security, reliability, simplicity, reversibility). | Clear recommendation: *Keep / Investigate / Pivot / Escalate*. |
| **9** | **Validate Safely** | Define small, safe experiment: hypothesis, blast radius, signal, abort condition. | Verification test planned before broad changes. |
| **10**| **Stop** | Stop when evidence discriminates or pivot is thrashing. Report decision record. | Summary presented to user for direction. |

---

## Output Decision Record Template

```markdown
### 🧭 Engineering Solution Pivot
**Objective:** <Outcome independent of specific implementation>
**Success Criteria:** <Observable signals proving success>
**Evidence:** [Verified] ... | [Inferred] ... | [Assumed] ... | [Unknown] ...
**Diagnosis:** <Symptom> → <Leading root cause hypothesis> (<Confidence>)
**Constraints:** <Constraint description> — <Class: Hard/Security/Design Artifact> — <Owner>
**Options:**
- **Option A (Current / Workaround):** mechanism · why complex · disqualifier
- **Option B (Transformation Pivot):** mechanism · lever applied · why cleaner
**Adversarial Review:** [Confirmed|Risk|Hypothesis] <Key failure mode or security concern>
**Recommendation:** <Keep | Investigate | Pivot to X | Escalate> — <Rationale>
**Safe Validation:** Hypothesis · blast radius · abort condition · rollback path
```

---

## Progressive Disclosure References

- 📄 **11 Transformation Levers:** [.github/skills/engineering-solution-pivot/references/transformation-levers.md](references/transformation-levers.md) (Interface, protocol, abstraction layer, architecture, data flow, etc.)
- 📄 **Domain Lenses & Checklists:** [.github/skills/engineering-solution-pivot/references/domain-lenses.md](references/domain-lenses.md) (Distributed systems, DB, security, and SRE failure checklists)
