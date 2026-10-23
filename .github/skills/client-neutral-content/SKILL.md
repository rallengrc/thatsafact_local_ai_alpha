---
name: client-neutral-content
description: "Keep client, site, internal-system and people commentary out of OSS-scope files; route client notes to Projects/Burstable MLaaS/; resolve the [client] classification label or ASK. TRIGGERS: 'client neutral', 'oss hygiene', 'scrub client', 'de-brand', 'classification label', 'who is the client'."
last_updated: "2026-10-19"
---

# 🧼 Client-Neutral Content — Keep Client Commentary Out of OSS

> **Purpose:** OSS-scope files (design patterns, ML technical docs, scripts, search-index config, `.github/` AI training, diagrams) describe the technique, never the customer. Client-specific material has exactly one home: `Projects/Burstable MLaaS/`.

## Triggers
- `client neutral` / `oss hygiene` / `scrub client` / `de-brand` / `no client names`
- `classification label` / `who is the client`
- **Auto:** any write or edit to a file outside the private project directory.

---

## The Iron Law

```
NEVER WRITE CLIENT, SITE, INTERNAL-SYSTEM, PEOPLE OR ENGAGEMENT NAMES INTO OSS-SCOPE FILES
```

This covers file content, diagrams, test fixtures, examples, commit messages, PR text and search-index config. The AI writes what the prompt contained; this rule is what stops that.

## Scope

| Path | Rule |
|------|------|
| `Projects/Burstable MLaaS/**`, `Inbox/` | **Private.** Client detail allowed |
| `Projects/hello-mlaas-burst/` (after the planned move), `Areas/`, `Resources/**`, `scripts/**`, `.github/**`, root docs | **OSS scope.** Must be clean |
| `memories/**`, `Archives/` | Undecided. Do not add client commentary |

## Workflow

1. **Classify the target path** with the table above before writing.
2. **Split the content.** The technique (topology, air-gapped or proxy-restricted environments, registry mirroring, surrogate ML) goes in the OSS file in generic words. The attribution (who, where, SOW, schedule, internal systems) goes in a note under `Projects/Burstable MLaaS/`.
3. **Use neutral words.** See [neutral-vocabulary.md](references/neutral-vocabulary.md) for replacements.
4. **Run the scanner** on the paths you touched, before and after:
   ```bash
   .venv/bin/python3 scripts/automation/client_term_scan.py --paths <path> [<path> ...]
   ```
   Exit 1 means hits. The scanner prints class and location, **never the matched term**. Do not paste the term into chat or commits when fixing a hit.
5. **Fix, then re-run** until it exits 0.

## Dynamic classification label: `🔵🛡️ [client] Proprietary`

Private documents carry this label. `[client]` is filled **just in time**, when you write the frontmatter, never copied from a template, memory file or earlier output.

| Step | Source | Use when |
|------|--------|----------|
| 1 | The user's current prompt | Names the client explicitly |
| 2 | `client:` line in `Projects/Burstable MLaaS/.client-terms.txt` | Exactly one value |
| 3 | `classification:` of sibling docs in the same private project, read live | All agree |
| 4 | **ASK** with `ask_user` | Zero candidates, more than one, or any disagreement |

**If unsure who the client is, ASK. Never guess** from a path, a vendor name or a previous session. After the answer, offer to record it in the private config.

Rules: 🔵 is valid only in private scope. A resolved 🔵 label in OSS scope is a defect; genericise the content and label it 🟢 General, or move it to the private project. Public templates and rule files carry only the placeholder.

## Search / AI framework rule
Metadata dicts, aliases, keywords, index text and generators read client-specific values from the private config. No client literals in code, tests, fixtures or `ai_search_aliases`. Test fixtures use a made-up name.

## Dogfood
This skill, its instruction and the `copilot-instructions.md` gate must themselves pass the scanner. The real term list lives only in the private file; never write it into any `.github/` file.

## 📄 See Also
- [neutral-vocabulary.md](references/neutral-vocabulary.md) — term classes, replacements, term-file format
- [client-neutral-content.instructions.md](../../instructions/client-neutral-content.instructions.md) — always-on rule
- [diamond-documentation.instructions.md](../../instructions/diamond-documentation.instructions.md) — classification levels
- [plantuml-rendering.instructions.md](../../instructions/plantuml-rendering.instructions.md) — Rule 8, no branded diagrams
