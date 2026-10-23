---
name: using-git-worktrees
description: "Set up an isolated workspace for feature work or plan execution. Detect existing isolation, prefer native worktree tools, fall back to git worktree. Protects the current branch from changes."
---

# Using Git Worktrees — Isolated Workspace Setup

**Triggers:** `using-git-worktrees`, `isolated workspace`, `worktree`, `isolate feature work`

**Upstream:** `writing-plans` / `brainstorming` produce the work to isolate
**Downstream:** `executing-plans` or `subagent-driven-development` run inside the worktree

---

## Core Principle (Superpowers v7.0.0)

Detect existing isolation first. Then use native tools. Then fall back to git. **Never fight the harness.**

1. **Detect before creating:** You may already be in a linked worktree. Check first; never create a second one.
2. **Native tools win:** A harness worktree tool (e.g. `EnterWorktree`, `/worktree`, `--worktree`) owns placement, branching, and cleanup. Bypassing it creates phantom state the harness can't see.
3. **Git is the fallback:** Only when no native tool exists.
4. **Protect the branch:** Isolation keeps the current branch clean; a dirty baseline makes every later failure ambiguous.

---

## When to Use

```
Need isolation from current workspace?
├── YES → Already in a linked worktree? → YES → skip creation, go to setup
│        └── NO → Native worktree tool? → YES → use it
│                 └── NO → git worktree fallback
└── NO → work in place
```

---

## The Process (4 steps)

1. **Detect** — Already a linked worktree? (submodule guard included). Details: `references/worktree-protocol.md` §1.
2. **Create** — Native tool first; git fallback with directory selection + ignore-safety check. §2.
3. **Setup** — Auto-detect and install dependencies for the new workspace. §3.
4. **Baseline** — Run tests; a clean baseline is the gate before implementation. §4.

---

## Quick Reference

| Situation | Action |
|-----------|--------|
| Already in linked worktree | Skip creation (detect) |
| In a submodule | Treat as normal repo (guard) |
| Native worktree tool available | Use it |
| No native tool | Git worktree fallback |
| `.worktrees/` exists | Use it (verify ignored) |
| Neither exists | Check instructions, then default `.worktrees/` |
| Directory not ignored | Add to .gitignore + commit |
| Permission error on create | Sandbox fallback, work in place |
| Baseline tests fail | Report + ask |

---

## References

- [Worktree Protocol & Detection](references/worktree-protocol.md) — Detection, creation, setup, baseline, and rationalizations
- **Superpowers source:** `code/superpowers/skills/using-git-worktrees/SKILL.md` (Release v7.0.0)
