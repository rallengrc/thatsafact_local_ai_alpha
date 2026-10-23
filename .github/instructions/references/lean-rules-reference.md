---
title: "Lean Rules Reference — Full Examples + Templates"
description: "Detailed examples, code templates, and dispatch patterns for .github training file lean rules. See github-content-lean-rules.instructions.md for the enforcement summary."
shield: "internal"
last_updated: "2026-04-30"
---

# Lean Rules Reference — Full Examples + Templates

📄 **Enforcement summary:** `.github/instructions/github-authoring.instructions.md`

![Lean Context Engineering Pattern](../../../Resources/visualization/lean-context-engineering.png)

---

## Content Distribution Patterns

### Pattern 1: Orchestrator → Sub-Skills
- `SKILL.md` (≤100L): Dispatch table, triggers, and `📄 See Also` pointers only.
- `references/dispatch-protocol.md` (≤150L): Detailed step-by-step algorithms, rationale, and edge cases.
- **Result:** Orchestrator remains discoverable without bloating context.

### Pattern 2: Orchestrator → Methodology Reference
- `SKILL.md` (≤100L): High-level table and quick triggers.
- `references/methodology.md` (≤150L): In-depth domain guardrails and discovery protocols.

### Pattern 3: Feature Documentation → Deep Architecture
- `SKILL.md` (≤60L): Quick purpose + trigger aliases.
- Deep architecture lives in `Resources/copilot/` or `Projects/`.

---

## Examples: Inline vs. Extracted

- **❌ DON'T:** Inline 100-line test classes or multi-page JSON payloads directly in `SKILL.md`.
- **✅ DO:** Extract to `references/examples.md` and link via `📄 See Also: references/examples.md`.

---

## When to Create vs. Enhance

| Action | When |
|--------|------|
| ✅ CREATE new SKILL.md | New domain, new orchestrator, triggers + dispatch pattern established |
| ✅ ENHANCE existing SKILL.md | New trigger phrases, new sub-skill in dispatch table, small additions (<5L) |
| ❌ DON'T create for feature docs | Use `Resources/copilot/` or add to dispatch table |
| ❌ DON'T mix methodology + orchestrator | Methodology → `references/methodology.md`; SKILL.md = dispatch hub only |

---

## Frontmatter Template

```yaml
---
name: [skill-name or file-type]
description: '[1-line summary] USE FOR: [...]. TRIGGERS: [...]. DO NOT USE FOR: [...]'
applyTo: '**/.github/**' (or specific pattern)
last_updated: 'YYYY-MM-DD'
---
```

**Example:**

```yaml
---
name: result-deduplication
description: 'QW #2 — Deduplicate results from parallel search engines (ChromaDB + search-router Tantivy keyword). USE FOR: Cleaning noise from search results. TRIGGERS: deduplicate results, QW #2, search noise. DO NOT USE FOR: Modifying ranking or search algorithm.'
last_updated: '2026-04-30'
---
```

---

## Quick Reference: File Structure Templates

### For New SKILL.md (Orchestrator)

```markdown
---
name: [skill-name]
description: '[one sentence] USE FOR: [...]. TRIGGERS: [...]. DO NOT USE FOR: [...]'
---

# [Skill Name] — Orchestrator

> **Purpose:** [one-line purpose]

## Triggers
- "trigger 1"
- "trigger 2"

## Quick Summary
[2-3 sentences]

## Sub-Skills / References
| # | Name | Purpose |
|---|------|---------|
| 1 | sub-1 | Purpose 1 |

📄 **See Also:**
- `.github/skills/[skill]/references/methodology.md` — Detailed protocols
```

### For New Reference File

```markdown
---
title: "[Skill] — [Topic]"
description: "[detailed purpose]"
last_updated: "YYYY-MM-DD"
---

# [Skill]: [Topic]

## Section 1: Core Concept
[Detailed explanation]

## Section 2: Protocol
[Step-by-step]

## Section 3: Advanced
[Edge cases, tuning, gotchas]
```

---

## Review Process

**When PR adds/edits `.github/` files:**

1. **Auto-check:** Line count tool flags SKILL.md >100 or reference >150
2. **Manual review:** Verify orchestrator + dispatch + reference pattern followed
3. **Frontmatter check:** description + triggers + applyTo present
4. **Link check:** SKILL.md includes "See Also" pointers to reference files
5. **Feedback:** If bloat detected, request splits before merge

**Merge criteria:**
- ✅ SKILL.md ≤100 lines (orchestrator) OR ≤120 (workflow)
- ✅ Reference files ≤150 lines each
- ✅ Orchestrator + dispatch + reference pattern followed
- ✅ Frontmatter complete
- ✅ "See Also" pointers included
