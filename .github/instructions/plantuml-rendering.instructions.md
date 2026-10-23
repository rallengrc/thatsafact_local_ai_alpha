---
description: 'PlantUML and Mermaid diagram rendering standards. Dual-format convention, JAR runner, syntax guardrails.'
applyTo: '**/*.puml, **/*.mmd'
---

# PlantUML & Mermaid Rendering Standards

> **Execution:** Run via `java -jar reference/plantuml-mit-1.2026.2.jar <file.puml>` (Java required on PATH).

1. **PlantUML Syntax Guardrail (NOT Markdown):**
   - **Comments:** Use single quote `' comment` on its own line. Never use `//`.
   - **Attributes:** Plain ASCII text only. Never use `**bold**`, `//italic//`, or emojis.
   - **Components:** Components must have empty bodies `{}`; place descriptions in `note right of Alias` blocks.
   - **Labels:** Never use raw parens `()` or `\n` inside relationship arrows.
2. **Dual-Format Convention:** Maintain both `{name}.puml` and `{name}.mmd` for all architecture diagrams.
3. **PNG Rendering:** Always render `.puml` → `.png` using the JAR runner.
4. **Mermaid Display:** Use Mermaid for in-chat visualization and markdown previews.

📄 **See Also:** [plantuml-rendering-reference.md](references/plantuml-rendering-reference.md) for macOS bash & Windows PowerShell commands, full syntax matrix, and diagram conventions.
