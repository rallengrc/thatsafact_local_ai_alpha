---
description: 'Prioritize ripgrep (rg) for deep, fast regex, session-log mining, gitignored subrepos, and workspace searches.'
applyTo: '**'
---

# Ripgrep (rg) First for Deep & Out-of-Workspace Search

> **Principle:** Prefer `rg` / ripgrep over plain `grep` whenever possible for maximum performance, PCRE2 support, and subrepo reach.

1. **Subrepos & Gitignored Paths:** Use `rg` to search `code/*` subrepos (which are gitignored at root and skipped by standard grep): `rg "class Foo" code/`.
2. **Session Logs & Telemetry:** Mine transcripts outside workspace: `rg "user_prompt" ~/.copilot/`.
3. **Advanced Patterns:** Use `rg --pcre2` for complex lookaheads/lookbehinds and type filters (`rg -t py`).
4. **Platform Resolution:** Call `find_executable("rg")` via `scripts/common_platform.py` on Windows (`rg.exe`) and macOS (`/opt/homebrew/bin/rg`).

📄 **See Also:** [ripgrep-scenarios-and-patterns.md](references/ripgrep-scenarios-and-patterns.md) for full scenario catalog and benchmarking.
