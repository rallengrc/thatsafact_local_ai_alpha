# ripgrep (rg / rg.exe) Scenarios, Commands & Reference Guide

**Related Instruction:** `.github/instructions/cli-ripgrep-defaults.instructions.md`  
**Purpose:** Comprehensive reference for ripgrep syntax, search patterns, cross-peer forensics, and session mining on macOS and Windows.

---

## 1. Scenario Routing Table

| Scenario | Tool / Command | Example |
|---|---|---|
| **Session transcripts** (COB xref, session mining) | Terminal `rg` | macOS: `rg "user_prompt" "$HOME/Library/Application Support/Code/User/workspaceStorage/<hash>/GitHub.copilot-chat/transcripts"`<br>Windows: `rg "user_prompt" "%APPDATA%\Code\User\workspaceStorage\<hash>\GitHub.copilot-chat\transcripts"` |
| **Code symbols in `code/*` repos** (gitignored at root) | Terminal `rg` | `rg "class FooImpl" "code/Repository/src"` |
| **PCRE2 regex patterns** (`\b`, `\d`, lookaheads) | Terminal `rg` | `rg "\b@Jira\b" "code/Repository/src"` |
| **File-type scoped** (Python, Java only) | Terminal `rg -t <type>` | `rg -t py "def train_" "Projects/"` |
| **Workspace-external paths** (session-store, absolute) | Terminal `rg` | macOS: `~/.copilot/` or `/Library/...`<br>Windows: `%APPDATA%` |
| **Semantic concept search** (fallback if rg empty) | `search_workspace` | Concept or business logic questions |

---

## 2. Common Patterns & Cheat Sheet

### Symbol & Function Search
```bash
# macOS / Linux (bash/zsh)
rg -t py "def train_surrogate" Projects/
rg -l "class RayJob" Projects/
rg -i "getsupply" code/

# Windows (PowerShell)
rg.exe -t py "def train_surrogate" Projects/
```

### Regex & Word-Boundary Search
```bash
# Exact word boundary (prevents partial matches)
rg "\bMLaaS\b" "Areas/"

# Search for numeric patterns Ray-1234
rg "Ray-\d{4}" "Projects/"
```

### Session Mining & Transcript Recovery
```bash
# macOS: Search transcripts with 3 lines of context
rg -C 3 "surrogate" "$HOME/Library/Application Support/Code/User/workspaceStorage/" -g "*.jsonl"

# macOS / Linux: Search cross-session store JSONL events
rg "user.message" "$HOME/.copilot/session-state/" -g "events.jsonl"

# Windows: Search transcripts
rg -C 3 "keyword" "$env:APPDATA\Code\User\workspaceStorage\<hash>\GitHub.copilot-chat\transcripts"
```

---

## 3. Why `rg` Outperforms Built-in Tools

| Capability | Terminal `rg` (macOS/Win) | Built-in UI Search |
|---|---|---|
| **Speed** | 10–50x faster (Rust multi-threaded) | Slow / times out on large repos |
| **Workspace-External Paths** | Full access across filesystem | **Fails silently / returns 0 results** |
| **Gitignored `code/*` subrepos** | Searches with `--no-ignore` or direct path | Often excluded by `.gitignore` |
| **PCRE2 Regex Support** | Full support (`\b`, lookarounds, etc.) | Limited JavaScript regex |
| **Cross-Peer Support** | Works identically on VS Code and CLI | **Does not exist on CLI peer** |
