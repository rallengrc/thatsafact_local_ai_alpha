---
title: VS Code Terminal Bloat Bug Analysis
description: Detailed defect report on VS Code GitHub Copilot Chat zombie terminal accumulation and token bloat
keywords:
- VS Code bug
- terminal bloat
- zombie terminals
- context waste
- token bloat
- copilot chat
category: bug-report
classification: 🟢🛡️ General
last_updated: '2026-10-11'
author: thatsafact
ai_search_aliases:
- terminal bloat bug
- vscode zombie terminals
- terminal context bug
---

﻿---
title: "VS Code Terminal Bloat Bug"
description: "VS Code creates zombie terminals for every run_in_terminal call, injecting them into AI context"
keywords: [vscode, terminal, bloat, context, bug, zombie]
category: bug-report
classification: 🟢🛡️ Public / Community
created: 2026-04-22
author: thatsafact
status: OPEN — not yet filed upstream
---

# VS Code Terminal Bloat Bug

> **TL;DR:** Analysis of a bug where VS Code GitHub Copilot Chat fails to clean up terminal sessions, injecting dead terminal metadata that wastes AI context.
> **Use this for:** Understanding context bloat causes in VS Code chat sessions and applying workarounds.

## Summary

VS Code's GitHub Copilot Chat creates a new terminal session for every `run_in_terminal` tool call and **never cleans them up**. Each zombie terminal adds ~500 characters to the `<context>` block injected into every subsequent AI prompt, wasting context window tokens on dead terminal metadata.

## Impact

| Terminals | Wasted Context | Wasted Tokens (est) |
|-----------|---------------|---------------------|
| 10 | 5k chars | ~1.3k |
| 40 | 20k chars | ~5k |
| 80 | 40k chars | ~10k |
| 120+ | 60k chars | ~15k |

In a typical session with 15+ prompts that use terminal commands, 80+ zombie terminals accumulate. This wastes ~10k tokens (10-15% of the context window) on identical `Activate.ps1` entries.

## Reproduction

1. Open VS Code with Copilot Chat
2. Send 20+ prompts that trigger `run_in_terminal`
3. Observe the `<context>` block injected into each prompt
4. Count terminal entries — they only grow, never shrink
5. User sees ~2 terminal tabs; AI context has 80+ entries

## Root Cause

- `run_in_terminal` creates a new terminal for each invocation
- Completed terminals (Exit Code: 0) remain in VS Code's terminal session registry
- The `<context>` block serializes ALL registered terminal sessions into every prompt
- No automatic pruning of completed terminal sessions
- No user-visible UI shows the full list of ghost terminals

## User Impact

- **User cannot see zombie terminals** — they see 2-3 tabs in the Terminal panel
- **User cannot clean up** — no bulk close UI for ghost sessions
- **AI told user to "close terminals"** — user CANNOT because they're invisible
- **Context budget silently consumed** — no warning when terminals eat 40k of context

## Workaround (AI-side)

Added to `.github/instructions/ai-session-management.instructions.md`:

### Primary: Kill-After-Use (Tier 1)
1. Use `mode=async` for `run_in_terminal` — returns both output AND a UUID
2. **Immediately** after reading the output, call `kill_terminal(UUID)` — one command, one kill
3. No UUID tracking needed across the turn — each command is self-contained
4. Exception: intentionally persistent terminals (dev servers) — keep alive
5. Never kill user-created terminals (no UUID = not AI-created)
6. **Why this replaced "track UUIDs":** The old approach required remembering UUIDs across the entire turn, which got lost after conversation summary. Kill-after-use needs zero memory.

### Fallback: Nuclear Option (Tier 2)
7. If `terms > 5` in context block and no UUIDs available (used `mode=sync`), use `workbench.action.terminal.killAll` via `run_vscode_command` — this is destructive (kills user's terminal too; reactivate venv afterward)
8. Terminal cleanup is part of COB/EOD xref workflow (Tier 3 = always nuke at end of day)
9. AI never tells user to close terminals (they can't see them)

## Proposed Fix (for VS Code team)

1. **Auto-prune completed terminals** from context injection after N minutes or next prompt
2. **Limit terminal context injection** to the 5 most recent active terminals
3. **Add terminal count to context metadata** so AI can see the budget impact
4. **Provide user-facing terminal session manager** showing all ghost sessions
5. **Reuse terminal sessions** for sequential sync commands instead of creating new ones
6. **Expose selective terminal kill** — `kill_terminal` requires the exact UUID returned by `run_in_terminal` at creation time. After a context rollover (conversation summary), those UUIDs are lost and the AI has no way to kill individual zombie terminals. The only available command is `workbench.action.terminal.killAll` which is destructive — it kills the user's active terminal too. VS Code should expose a `workbench.action.terminal.kill` command that accepts a terminal label, index, or the `Last Command` metadata visible in the `<context>` block, allowing the AI to surgically remove dead terminals without nuking the user's live session.

## Automation (Hook-Based)

### preToolUse Hook: `terminal-hygiene.ps1`
Registered in `.github/hooks/session-log.json`. Fires before every `run_in_terminal` call. If `mode=sync` (or no mode specified), emits a warning nudging the AI to use `mode=async` + `kill_terminal(UUID)`. Rate-limited to warn on 1st call, then every 3rd to reduce noise.

### Why This Works
Instructions alone failed — the AI naturally defaults to `mode=sync` because it's simpler. The hook provides a behavioral nudge at the moment of decision, not a rule buried in an instruction file. The warning text is injected into the AI's context, making Tier 1 the path of least resistance.

## Evidence

Session `f9a0829c-838e-49c9-984a-2d390365ea0a` on April 22, 2026:
- 80+ terminal entries in `<context>` block
- All showing identical `Activate.ps1` last command
- All with `Exit Code: 0` (completed)
- User reported seeing only 2 terminals
- ~40k chars / ~10k tokens wasted per prompt

## Filing

- **Repo:** https://github.com/microsoft/vscode-copilot-release/issues
- **Labels:** bug, copilot-chat, terminal, context-window
- **Status:** Documented locally, awaiting upstream filing

## Meta Note

The AI that discovered this bug also wrote its own fix — instruction-based behavioral rules that program the AI to use `mode=async` (to capture UUIDs), track them during each turn, and batch-kill them at the end. The AI wrote the rules, tested them, and updated this bug report — all in the same session. The bug report itself was created by the system it documents. The fix was designed by the agent it constrains.
