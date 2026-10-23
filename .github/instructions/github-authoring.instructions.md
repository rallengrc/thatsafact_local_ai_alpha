---
description: 'GitHub .github file authoring rules. No-hooks hard gate, orchestrator pattern, line limits, seq-think + plan-first discipline. Merged from github-file-authoring-rules + github-content-lean-rules.'
applyTo: '**/.github/**.*'
---

# GitHub File Authoring Rules (Auto-Apply to `.github/` Files)

## 🚨 RULE 1: NO HOOKS — EVER

**Hard Gate:** `preExecutionHook`, `postExecutionHook`, event handlers, lifecycle hooks — **ALL FAIL SILENTLY.**

**Why:** VS Code Copilot ignores hook keys silently. April 2026 data: 47/52 turns abandoned hook logic.

**What to use instead:** seq-think, plan-first, mechanical rules, or AI-triggered scripts on demand.

---

## ✅ RULE 2: ORCHESTRATOR PATTERN + LINE LIMITS

**Pattern:** `SKILL.md` = dispatcher only → details go in `references/` files.

| File Type | Max Lines | Role |
|-----------|-----------|------|
| `SKILL.md` orchestrator | **≤100** | Dispatch table + triggers + `📄 See Also` pointers |
| `SKILL.md` workflow | **≤120** | Steps with minimal inline examples |
| `references/*.md` | **≤150** | Methodology, algorithms, detailed logic |
| `references/examples.md` | **≤200** | Code walkthroughs |
| `*.prompt.md` | **≤180** | Prompt logic + examples |
| `*.agent.md` | **≤180** | Agent dispatch logic |
| `.instructions.md` | **≤180** | Rules + examples (≤200 for critical safety) |

**When SKILL.md exceeds limit:**
1. Extract examples → `references/examples/`
2. Extract methodology → `references/methodology.md`
3. Keep SKILL.md as pure orchestrator (triggers + dispatch + `📄 See Also`)

---

## ✅ RULE 3: SEQ-THINK BEFORE MAJOR EDITS

**Trigger when:** Multi-file edits to same pattern, new trigger definitions, complex reference extraction, or ambiguous requirement needing multi-angle analysis.

**Workflow:** seq-think FIRST (before reading files) → identify extraction targets + what breaks → execute → verify line counts.

---

## ✅ RULE 4: PLAN-FIRST BEFORE NEW PATTERNS

**Trigger when:** Creating a new SKILL.md, defining new `applyTo` pattern, bulk refactoring >5 `.github/` files, or adding new reference-tier files to an existing skill.

---

## Anti-Patterns

| Anti-Pattern | Fix |
|--------------|-----|
| SKILL.md >100L | Extract to `references/` |
| `references/*.md` >150L | Split or archive |
| New `.instructions.md` without `applyTo` | Always set `applyTo` |
| Inline examples >20 lines in SKILL.md | Extract to `references/examples.md` |
| No `📄 See Also` pointers | Add `📄 **See Also:**` links from SKILL.md to references |
| Edit `.github/` without seq-think | Use seq-think → plan-first |

---

## Enforcement Checklist (Before Committing)

- [ ] SKILL.md: orchestrator ≤100L? workflow ≤120L?
- [ ] `references/` files: each ≤150L?
- [ ] Frontmatter: `name` + `description` + `applyTo` present?
- [ ] `📄 See Also` links from SKILL.md to reference files?
- [ ] No hooks added?
- [ ] New instruction file has `applyTo` set?

**AI enforcement:** On any `.github/` edit — flag hooks, verify line counts, warn on missing `applyTo`, suggest orchestrator pattern for SKILL.md, suggest seq-think/plan-first for multi-file changes.

---

## Exceptions

- **Critical safety rules** (ps1-safety, branch protection) → allow ≤200L with justification in commit
- **Orchestrator dispatch tables** → allow ~118L if formatting requires it
