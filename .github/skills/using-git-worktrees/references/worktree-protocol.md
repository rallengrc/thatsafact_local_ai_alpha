# Worktree Protocol — Detection, Creation, Setup, Baseline

> **Source:** Superpowers v7.0.0 (`code/superpowers/skills/using-git-worktrees/SKILL.md`)

Detailed steps for the `using-git-worktrees` orchestrator. Announce at start: "I'm using the using-git-worktrees skill to set up an isolated workspace."

---

## 1. Detect Existing Isolation

Before creating anything, check if you are already in an isolated workspace.

```bash
GIT_DIR=$(cd "$(git rev-parse --git-dir)" 2>/dev/null && pwd -P)
GIT_COMMON=$(cd "$(git rev-parse --git-common-dir)" 2>/dev/null && pwd -P)
BRANCH=$(git branch --show-current)
```

**Submodule guard:** `GIT_DIR != GIT_COMMON` is also true inside git submodules. Before concluding "already in a worktree," verify you are not in a submodule:

```bash
# If this returns a path, you're in a submodule, not a worktree — treat as normal repo
git rev-parse --show-superproject-working-tree 2>/dev/null
```

- **`GIT_DIR != GIT_COMMON` (and not a submodule):** Already in a linked worktree. Skip to §3. Do NOT create another.
  - On a branch: "Already in isolated workspace at `<path>` on branch `<name>`."
  - Detached HEAD: "Already in isolated workspace at `<path>` (detached HEAD, externally managed). Branch creation needed at finish time."
- **`GIT_DIR == GIT_COMMON` (or in a submodule):** Normal repo checkout. Has the user declared a worktree preference in instructions? If not, ask consent: "Would you like me to set up an isolated worktree? It protects your current branch from changes." Honor any declared preference without asking. If declined, work in place and skip to §3.

---

## 2. Create Isolated Workspace

Two mechanisms, in this order.

### 2a. Native Worktree Tools (preferred)

Do you have a way to create a worktree? A tool named like `EnterWorktree`, `WorktreeCreate`, a `/worktree` command, or a `--worktree` flag. If so, use it and skip to §3. Native tools handle placement, branching, and cleanup automatically. Using `git worktree add` when a native tool exists creates phantom state the harness can't see or manage.

### 2b. Git Worktree Fallback

Only if 2a does not apply.

**Directory selection (priority order; explicit user preference always beats observed state):**
1. Declared worktree directory in instructions — use it without asking.
2. Existing project-local directory:
   ```bash
   ls -d .worktrees 2>/dev/null     # Preferred (hidden)
   ls -d worktrees 2>/dev/null      # Alternative
   ```
   If found, use it. If both exist, `.worktrees` wins.
3. No other guidance → default to `.worktrees/` at the project root.

**Safety verification (project-local directories only) — MUST verify ignored before creating:**
```bash
git check-ignore -q .worktrees 2>/dev/null || git check-ignore -q worktrees 2>/dev/null
```
If NOT ignored: add to `.gitignore`, commit the change, then proceed. Why critical: prevents accidentally committing worktree contents into the repository.

**Create:**
```bash
path="$LOCATION/$BRANCH_NAME"
git worktree add "$path" -b "$BRANCH_NAME"
cd "$path"
```

**Sandbox fallback:** If `git worktree add` fails with a permission error, tell the user the sandbox blocked worktree creation and you're working in the current directory instead. Then run setup and baseline tests in place.

---

## 3. Project Setup

Auto-detect and run appropriate setup:
```bash
[ -f package.json ] && npm install
[ -f Cargo.toml ] && cargo build
[ -f requirements.txt ] && pip install -r requirements.txt
[ -f pyproject.toml ] && poetry install
[ -f go.mod ] && go mod download
```

---

## 4. Verify Clean Baseline

Run tests to ensure the workspace starts clean:
```bash
npm test / cargo test / pytest / go test ./...
```
- **Tests fail:** Report failures, ask whether to proceed or investigate.
- **Tests pass:** Report ready.

**Report:**
```
Worktree ready at <full-path>
Tests passing (<N> tests, 0 failures)
Ready to implement <feature-name>
```

---

## Common Rationalizations

| Excuse | Reality |
|--------|---------|
| "I'm obviously not in a worktree — no need to check" | Run §1. Harness-created isolation and submodules both fool eyeballing; the detection commands settle it. |
| "`git worktree add` is quicker than hunting for a native tool" | A native tool owns placement, branching, and cleanup. Bypassing it is the #1 mistake — it creates phantom state the harness can't see. |
| "The worktree directory is surely ignored already" | Run `git check-ignore`. An unignored worktree directory commits the whole tree into the repo. |
| "Any directory name works" | Explicit instructions beat an existing project-local directory, which beats the `.worktrees/` default. |
| "The workspace is fresh — baseline tests can wait" | A dirty baseline makes every later failure ambiguous. Run the tests now; proceeding past failures is the user's call. |
