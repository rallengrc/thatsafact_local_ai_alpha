---
description: 'Client-neutral content gate. Never write client, site, internal-system, people or engagement names into OSS-scope files, diagrams, scripts, search-index config, commit messages or test fixtures. Client notes go only under Projects/Burstable MLaaS/. Dynamic [client] label: resolve just in time or ASK.'
applyTo: '**'
---

# Client-Neutral Content

The technique goes in OSS-scope files; the customer's name, sites, internal systems, people and deal details go only under `Projects/Burstable MLaaS/`. Full workflow: [client-neutral-content skill](../skills/client-neutral-content/SKILL.md).

| Path | Rule |
|------|------|
| `Projects/Burstable MLaaS/**`, `Inbox/` | Private. Client detail allowed here only |
| `memories/**`, `Archives/` | Undecided. Do not add client commentary |
| Everything else | OSS scope. Must be clean |

1. Describe the technique generically ("on-premises VMs behind a corporate proxy"); vocabulary: [neutral-vocabulary.md](../skills/client-neutral-content/references/neutral-vocabulary.md).
2. Client detail in a prompt: write the generic content in the OSS file, put the client note under `Projects/Burstable MLaaS/`.
3. This covers diagrams, fixtures, examples, `ai_search_aliases`, index text, commit messages and PR text. Fixtures use a made-up name.
4. Never write the real term list into an OSS-scope file; it lives only in `Projects/Burstable MLaaS/.client-terms.txt`.
5. Before finishing: `.venv/bin/python3 scripts/automation/client_term_scan.py --paths <touched paths>`. Exit 1 = fix and re-run. Never copy a matched term into chat or commits.

**`[client]` label** (`🔵🛡️ [client] Proprietary`): fill from the user's prompt, else the `client:` line in `.client-terms.txt`, else agreeing sibling docs, else **ASK**. Never guess or copy a name from a template or memory. 🔵 is valid only in private scope; OSS scope uses 🟢 General.
