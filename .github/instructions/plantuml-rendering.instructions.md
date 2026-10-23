---
description: 'PlantUML and Mermaid diagram rendering to PNG. Dual-format convention, jar location, helper script, rendering commands.'
applyTo: '**/*.puml, **/*.mmd'
---

# PlantUML & Mermaid PNG Rendering (Auto-Apply)

## PlantUML JAR

**Location:** `reference/plantuml-mit-1.2026.2.jar` (MIT, 2026-02-27) | **Requires:** Java on PATH

## Quick Commands

```powershell
# Preferred: use JAVA_HOME explicitly
& "$env:JAVA_HOME\bin\java.exe" -jar reference\plantuml-mit-1.2026.2.jar path\to\file.puml
& "$env:JAVA_HOME\bin\java.exe" -jar reference\plantuml-mit-1.2026.2.jar path\to\file.puml -o "out\dir"
& "$env:JAVA_HOME\bin\java.exe" -jar reference\plantuml-mit-1.2026.2.jar "path\to\dir\*.puml"
.\99-System\scripts\plantuml\plantuml-render.ps1 path\to\file.puml output\dir         # Helper script (uses JAVA_HOME)
```

## Mermaid PNG

Use `renderMermaidDiagram` tool for inline chat rendering. To **save to disk**, use VS Code Markdown Preview or CLI — the tool does not write files.

## PlantUML Syntax — NOT Markdown!

**.puml files use PlantUML syntax, NOT Markdown.** Common AI mistakes:

| WRONG | RIGHT | Why |
|---|---|---|
| `**bold**` in attributes | `<b>bold</b>` or plain text | `**` = Creole bold, invalid in attributes |
| `// comment` on attribute line | `' comment` on own line | `//` = Creole italic, causes parse error |
| `★` or Unicode symbols | ASCII: `(PROTECTED)`, `[*]` | Encoding errors |
| `\n` in relationship labels | Omit or use note blocks | No escape support in labels |
| `.. Separator ..` in class body | `--` (thin) or `==` (double) | `..text..` is for package headers |
| Body text inside `component { }` | Empty component + `note` block | Components aren't classes — no body |
| Parens in labels: `"text (detail)"` | `text - detail` or backtick-quote | Parens confuse arrow parser |

### Two Root Causes (95% of PlantUML errors)

1. **Markdown in PlantUML:** AI uses `**bold**`, `//italic//`, `// comments` — PlantUML interprets as Creole markup. **Fix:** Plain text in attributes, `' comment` on separate lines, `<b>` only in notes.
2. **Body in components:** AI fills `component "X" { routes, fields }` like a class. Components don't support body content. **Fix:** Empty components + `note right of Alias` blocks.

### Quick Reference

```plantuml
' Formatting: <b>bold</b>, <i>italic</i>, ""monospace"", <color:red>text</color>
' Class separators: -- (thin) or == (double)
' Comments: ' single-line (ONLY way)
' Class attributes: plain text only — no **, //, or inline comments
' Components: empty body + note blocks for descriptions
```

## Diagram Convention (4-File Set)

Every diagram = `{name}.puml` + `{name}.mmd` + `{name}.png` + `{name}.md` (thin index) in `visualizations/`. Full convention: `03-Resources/copilot/diagram-convention.md`.

- **Dual-format:** Both `.puml` and `.mmd` for types supporting both (ERD, sequence, class, state, flowchart, component, mindmap, C4)
- **Render .puml only** → `.png` via jar. No Mermaid PNG rendering.
- **Single-format:** PlantUML-only (deployment, network, timing, wbs, usecase, object) or Mermaid-only (architecture, kanban, sankey, pie, quadrant, timeline, gantt, gitgraph)
- **.mmd format:** Raw Mermaid syntax, NO markdown fences

## Rules for AI

1. The jar is confirmed — **NEVER doubt** rendering capability
2. **ALWAYS** render with `& "$env:JAVA_HOME\bin\java.exe" -jar reference\plantuml-mit-1.2026.2.jar` (or use the helper script)
3. **NEVER use Markdown syntax in .puml files**
4. **ALWAYS test-render** after creating .puml — fix errors before moving on
5. For syntax questions, consult [Resources/visualization/PlantUML_Language_Reference_Guide.md](../../Resources/visualization/PlantUML_Language_Reference_Guide.md)
6. **ALWAYS create both .puml and .mmd** (dual-format types) + thin `.md` index
7. **NEVER embed inline Mermaid** in docs — embed `.png` from `.puml` instead
8. **NEVER brand diagrams.** No client, employer, site, vendor-product or internal-program names (client company or program names, research-campus or city names, internal registry brands, internal platform names, "Diamond") in titles, package/node labels, aliases, notes or filenames of `.puml`/`.mmd`/`.png`. Use generic labels ("On-Premises (Firewall VMs)", "Container Registry"). If branding is required, the user must ask for it explicitly. When editing a diagram, strip any branding found and re-render the `.png`. Never list the real names in this file; see the `client-neutral-content` skill.

## Diagram Pre-Flight — Required Before Any Diagram Task

**Before creating ANY diagram file:**
1. Read `plantuml-rendering.instructions.md` + `diagram-search.instructions.md` first — no exceptions
2. Plan `visualizations/` subdirectory structure — show to user and **wait for approval** before creating files
3. Every `.mmd` and `.puml` **MUST** have a `.png` rendered from it
4. Embed `.png` in the main doc — **NEVER embed inline Mermaid source**
5. Create `diagrams-index.md` in `visualizations/` cataloging all diagrams

**Post-completion checklist (before committing):**
- [ ] Main doc embeds PNG (not Mermaid source)?
- [ ] `visualizations/` subdirectory created?
- [ ] `diagrams-index.md` exists and catalogs all diagrams?

**Commit format:** `refactor(use case): restructure diagrams into visualizations/ with PNG renders and diagrams-index.md`

**Cost of skipping:** ~30 min user time + ~40k tokens per incident.
