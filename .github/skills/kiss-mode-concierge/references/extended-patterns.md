# Kiss-Mode Concierge — Extended Patterns

> Archived from SKILL.md for lean compliance

## Dynamic Command Discovery Protocol

**Step 1 — Extract Topic:** Identify 2-3 core keywords from the current question/conversation context.

**Step 2 — Search Library:** Run search-router MCP (ChromaDB and Tantivy engine).

**Step 3 — Read Matches:** For each top result, read the first 15 lines to get the description and trigger phrases.

**Step 4 — Present (max 2-3 commands):**

```
**Diamond shortcuts for [topic]:**
- `/command-name` — one-line description
- `/command-name` — one-line description
```

## Rules

- **Max 2-3 commands** per response
- **Only suggest if genuinely relevant**
- **Fire at most once per topic domain per session**
- **Context-adaptive:** skills added under `.github/skills/` are auto-discovered by description

## On-Demand Instruction Suggestions

Whenever the user's context indicates a file type, surface the relevant on-demand instruction file.

**Format (One-Liner):**
```
💡 **On-Demand:** {file-type} files → {instruction} auto-loads (no user action needed)
```

## Kiss-Mode Branch Safety Script

> **I'm activating branch safety checks.**
>
> This workspace has **protected branches** — shared highways. Your personal branch is your driveway — park however you want. But the highway (`feature/use-case`, `develop`, `main`) has rules because other people drive on it too.
>
> **What I did:** Checked target branch, verified it's your personal branch. If it's protected, I'll stop and warn you.

## Vague Request Tip

> **Tip:** The more specific you are, the better I work! Instead of "fix the bug," try "fix the null pointer in `MyJavaFile.java` line 45."
