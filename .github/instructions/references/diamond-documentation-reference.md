---
title: "Diamond Documentation Standards — Full Reference"
description: "Reference specification for Diamond markdown documentation, 8-field frontmatter, Confluence sync rules, and migration procedures."
shield: "internal"
last_updated: "2026-10-23"
keywords: [documentation, diamond, markdown, frontmatter, confluence, facts-only]
---

# Diamond Documentation Standards — Full Reference

📄 **Instruction Hub:** `.github/instructions/diamond-documentation.instructions.md`  
**Source of Truth Template:** `Resources/copilot/AI-SEARCHABLE-DOC-TEMPLATE.md`

---

## 1. Complete YAML Frontmatter Specification

Every `.md` file must open with all 8 fields:

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
- **🟢🛡️ General:** Public information (public docs, filings, educational glossaries, OSS-scope files).
- **🔵🛡️ [client] Proprietary:** Internal use only (client-derived architecture, operational details). Private scope only (`Projects/Burstable MLaaS/**`, `Inbox/`). Fill `[client]` just in time; never guess or hardcode in OSS files.

---

## 2. Hard Gate: Facts Only (No Aspirational Claims)

**Every factual claim must have a verifiable source checked in the current turn:**
- **No invented counts:** Verify file or row counts live before writing.
- **No fabricated citations:** Ensure cited PRs, commits, and line numbers exist.
- **No unverified cost or ROI figures:** Cite official source documentation.
- **Permitted hedges:** If a count cannot be checked live, write `"see [file] for current count"` or mark as `"planned"`.

---

## 3. Confluence Sync & Structural Guidelines

- **Additive-Only Sync:** Never delete existing local definitions, acronyms, or local enrichments when syncing from external wikis. Keep `source_confluence_page_id:`.
- **Content Hierarchy:**
  - `# 📌 Title with Emoji`
  - `> **Brief context line**` + `**Status:** Active | Draft | Deprecated`
  - `## 🎯 TL;DR` (3-5 concise bullets + "Use this for:" line)
  - Clean H2/H3 hierarchy with workspace-relative links.
- **Move vs. Archive:**
  - Moving active files: update all living cross-references.
  - Archiving to `Archive/`: delete living links from active navigation; never leave links pointing into cold storage.
