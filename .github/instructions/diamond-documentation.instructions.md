---
description: 'Diamond markdown documentation standards. Frontmatter specification (8 required fields + shield), facts-only gate (no unverified claims), and Confluence additive-only sync rules.'
applyTo: 'Areas/**/*.md, Resources/**/*.md, Projects/**/*.md, *.md, *.MD'
---

# Diamond Documentation Standards (Auto-Apply for Markdown)

**Source of Truth Template:** `Resources/copilot/AI-SEARCHABLE-DOC-TEMPLATE.md`

Every markdown file created or updated in the Diamond knowledge base MUST comply with these standards.

---

## 1. Required YAML Frontmatter (All 8 Fields + Shield)

Every `.md` file must open with YAML frontmatter containing all 8 fields:

```yaml
---
title: "Document Title"
description: "50-100 character summary for semantic and keyword discovery."
keywords: [Domain, Acronyms, Keywords, CommaSeparated]
category: reference  # reference | planning | requirements | implementation | architecture | memory
last_updated: YYYY-MM-DD
author: Author Name
related:
  - # 1-3 related docs, or []
classification: 🔵🛡️ [client] Proprietary | 🟢🛡️ General
ai_search_aliases: [optional alternate search phrases]
---
```

### Security Classification Levels
- **🟢🛡️ General:** Public information (public docs, public filings, educational glossaries)
- **🔵🛡️ [client] Proprietary:** Internal use (client-derived architecture, Diamond infrastructure, operational details). Private scope only (`Projects/Burstable MLaaS/**`, `Inbox/`). Fill `[client]` just in time: user prompt, then the `client:` line in `Projects/Burstable MLaaS/.client-terms.txt`, then agreeing sibling docs; otherwise **ask, never guess**. Never copy a resolved name from a template or memory. See the `client-neutral-content` skill.

Only these two levels exist. Never add a third level.

---

## 2. Hard Gate: No Aspirational Claims (Facts Only)

> *"If we follow aspirations, the lights go out."* — thatsafact, 2026-05-03

**Every factual claim must have a verifiable source checked in this conversation turn:**
- **No invented counts:** Do NOT write `"40+ session analyses"`, `"20+ tables"`. Run the count in terminal/tool and cite the exact number.
- **No fabricated citations:** Do NOT invent PR or use cases (`"Used in PR 1205"`). Verify the artifact exists first. Cite line numbers.
- **No made-up percentages or estimates:** Do NOT write `"answers 80% of questions"` or `"takes ~5 minutes"`. Either measure it or omit it.
- **No unverified pricing/cost numbers:** Copilot/AI pricing or token ROI calculations must be sourced directly from official documentation.
- **Permitted hedges:** If a count or spec cannot be verified in this turn, omit it or write `"see [file] for current count"` or `"planned (not yet implemented)"`.

---

## 3. Confluence Sync Safety (Additive-Only)

When updating a local `.md` file with content from Confluence:
1. **Additive only:** NEVER delete existing definitions, acronyms, or local enrichments.
2. **Local enrichments are sacred:** Cross-references, search aliases, and code pointers exist only locally.
3. **Traceability:** Sourced files must track `source_confluence_page_id:` in frontmatter.

---

## 4. Required Content Structure

- `# 📌 Title with Emoji`
- `> **Brief context line**` + `**Status:** Active | Draft | Deprecated`
- `## 🎯 TL;DR` (3-5 concise bullet points + "Use this for:" line)
- Clean H2/H3 hierarchy with workspace-relative markdown links.

---

## 5. File Operations: Move vs. Archive (Decouple, Don't Redirect)

- **Moving an active file** (within `Projects/`, `Areas/`, `Resources/`, `scripts/`): UPDATE all cross-references and links to the new active path.
- **Archiving to `Archive/`:** DELETE / SEVER all cross-references, TOC entries, and search fallback index rows (`MASTER-TOC.md`, `_INDEX.md`) from living docs.
- ⛔ **NEVER DO THIS:** NEVER rewrite living links to point into `Archive/`. Cold storage must disappear from active navigation. Log the move in `Archive/_INDEX.md` only.

