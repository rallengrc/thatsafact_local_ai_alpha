---
description: 'Use rg (ripgrep) for session-log mining, gitignored code/* subrepos, paths outside the workspace, and PCRE2 patterns that the built-in grep tool cannot reach. Load when searching transcripts, ~/.copilot, workspaceStorage, or code/.'
---

# ripgrep for Out-of-Workspace and Subrepo Search

Prefer the built-in grep tool for ordinary in-workspace search. Use `rg` (macOS/Linux) or `rg.exe` (Windows) in the terminal when the target is one of these:

- `code/*` subrepos (gitignored at the root, so the built-in grep skips them): `rg "class FooImpl" code/`
- Session logs and transcripts outside the workspace: `rg "user_prompt" ~/.copilot/`
- PCRE2 patterns: `rg --pcre2 "\bMLaaS\b"`
- Type-scoped search: `rg -t py "def test_" scripts/`

Full patterns: [ripgrep-scenarios-and-patterns.md](references/ripgrep-scenarios-and-patterns.md).
