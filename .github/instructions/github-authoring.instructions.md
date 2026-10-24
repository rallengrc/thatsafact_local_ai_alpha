---
description: 'GitHub .github file authoring rules. Hard no-hooks gate, orchestrator pattern, line limits, and reference tier discipline.'
applyTo: '**/.github/**.*'
---

# GitHub Authoring Standards (Auto-Apply)

> **Core Principle:** Lean context engineering. Keep orchestrators and instructions tight; dispatch depth to `references/`.

1. **🚨 Hard Gate: NO HOOKS & NO PROMPTS EVER:**
   - `preExecutionHook`, `postExecutionHook`, event handlers, or lifecycle hooks fail silently in VS Code Copilot. Never use them.
   - Never create, recommend, or optimize into `.github/prompts/*.prompt.md` files. Prompt files are deprecated and will stop working. Use standard skills or manual-invocation skills (`disable-model-invocation: true`).
2. **Line Limits & Roles:**
   - `.instructions.md`: **≤30 lines** (hub with scoped `applyTo` + `📄 See Also`).
   - `SKILL.md` orchestrators: **≤100 lines** (dispatch matrix + triggers + pointers).
   - `references/*.md`: **≤150 lines** (methodology, templates, deep specs).
   - `.agent.md`: **≤180 lines**. (Do NOT use `.prompt.md`).
3. **Mandatory Scoped `applyTo`:** Never use broad `applyTo: '**'` unless universally applicable (e.g. security/client gates). Always scope to file types (`**/*.py`, `**/*.puml`, `**/*.yaml`).
4. **Seq-Think & Plan-First:** Use sequential thinking before multi-file `.github/` refactors, and plan-first for changes touching ≥5 files or new skills.

📄 **See Also:** [lean-rules-reference.md](references/lean-rules-reference.md) for full anti-patterns, review checklists, and file structure templates.
