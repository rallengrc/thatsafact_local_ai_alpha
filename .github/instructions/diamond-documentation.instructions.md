---
description: 'Diamond markdown documentation standards. Frontmatter specification (8 required fields + shield), facts-only gate (no unverified claims), and Confluence additive-only sync rules.'
applyTo: 'Areas/**/*.md, Resources/**/*.md, Projects/**/*.md, *.md, *.MD'
---

# Diamond Documentation Standards (Auto-Apply)

> **Source of Truth Template:** `Resources/copilot/AI-SEARCHABLE-DOC-TEMPLATE.md`

1. **Mandatory 8-Field YAML Frontmatter:** Every `.md` file must open with `title`, `description`, `keywords`, `category`, `last_updated`, `author`, `related`, and `classification` (`🟢🛡️ General` or `🔵🛡️ [client] Proprietary`). Optional: `ai_search_aliases`.
2. **Hard Gate: Facts-Only (No Aspirational Claims):** Never invent metrics, line counts, or benchmarks. Verify counts live before output.
3. **Confluence Sync:** Local docs are additive-only; never delete local cross-references, search aliases, or local enrichments when syncing.
4. **Structure:** Title with emoji `# 📌 Title`, blockquote context + status, `## 🎯 TL;DR`, and clean H2/H3 hierarchy with workspace-relative links.
5. **Decouple on Archive:** When archiving to `Archive/`, sever living links from active navigation; never leave active docs pointing into cold storage.

📄 **See Also:** [diamond-documentation-reference.md](references/diamond-documentation-reference.md) for full frontmatter template, classification rules, and Confluence sync procedures.

