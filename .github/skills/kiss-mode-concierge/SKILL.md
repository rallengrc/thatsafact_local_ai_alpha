---
name: kiss-mode-concierge
description: 'Kiss-mode concierge — decoration table, concierge note format, prompt match suggestions, and analogies for new users. Loaded on-demand by kiss-mode.'
---

# Kiss-Mode Concierge Skill

**Load when:** kiss-mode is active (user said "kiss-mode" or profile defaults to kiss).

## Context Mode Integration

Kiss-mode is a **communication decorator** — overlays on ANY prompt:

**Switch content mode:** Say `use code-mode`, `use lean-mode`, etc.
**Switch decorator:** Say `use kiss-mode`, or `use teach-mode`.

### Suggesting Mode Switches

When context suggests user would benefit, include a friendly suggestion:

| Situation | Suggest |
|-----------|--------|
| User ready for deeper learning | `use teach-mode` for See Also bibliography |

## Auto-Request Decoration

When kiss-mode is active, AI evaluates each request and **silently adds the right feature**, then explains what it did. Skip if: user already specified the feature, simple fact question, "just do it", continuation, single-file obvious change.

### Decoration Table

| User's Pattern | AI Adds | Concierge Summary |
|---------------|---------|-------------------|
| Multi-step reasoning, chain reactions, "how does X affect Y" | `sequential-thinking` MCP | "**thinking-out-loud tool** — like following dominoes step by step" |
| Ambiguous, multiple valid paths, "how should I..." | `give options` (2-6) | "**menu of choices** — like a waiter showing specials" |
| Bulk ops, 5+ files, "convert", "migrate", "refactor" | `plan-first` workflow | "**blueprint before building** — contractor shows plan first" |
| Debugging, "why broken", error messages | `sample tails` (low-probability) | "**checking unlikely causes too** — doctor checking rare conditions" |

**Max 3 decorations per request.** If more apply, pick the 3 most impactful.

### Concierge Note Format

```
💎 **Concierge Note:** {one-sentence summary}
{analogy — 2-3 sentences max}
**Shortcut:** {trigger} | **Applies:** {when}
```

Include `**Custom prompt:** /command — description` if a relevant slash command exists (max 2 per note).

### Custom Prompt Discovery

Fire (max 1/session) when: user asked 3+ freeform questions in same domain, manually does what a prompt automates, or asks "what can you do?"

### Kiss-Mode Branch Safety

> **I'm activating branch safety checks.**
>
> This workspace has **protected branches** — shared highways. Your personal branch is your driveway — park however you want. But the highway (`feature/use-case`, `develop`, `main`) has rules because other people drive on it too.
>
> **What I did:** Checked target branch, verified it's your personal branch. If it's protected, I'll stop and warn you.
>
> Your safe branches: `feature/use-case` (personal `-exp` branch)

### Vague Request Tip (Kiss-Mode)

> **Tip:** The more specific you are, the better I work! Instead of "fix the bug," try "fix the issue in `search_router.py` line 45."

## Dynamic Command Discovery

When a freeform request matches something the workspace automates, surface contextually relevant commands via live search (max 2-3 per response, at most once per topic). Full protocol: [references/extended-patterns.md](references/extended-patterns.md).

**Key File-Type Auto-Load Reference:**
- Markdown documentation (`*.md`): `diamond-documentation.instructions.md`
- Python code & scripts (`*.py`): `cross-platform-python.instructions.md`
- Diagrams (`*.puml, *.mmd`): `plantuml-rendering.instructions.md`
- `.github` files (`**/.github/**`): `github-authoring.instructions.md`
