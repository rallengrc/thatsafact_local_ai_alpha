---
title: "PlantUML & Mermaid Rendering — Detailed Execution Reference"
description: "Detailed rendering commands for macOS (bash/zsh) and Windows (PowerShell), Creole vs Markdown syntax rules, and diagram convention."
shield: "internal"
last_updated: "2026-10-23"
keywords: [plantuml, mermaid, rendering, diagrams, macos, windows, powershell, bash]
---

# PlantUML & Mermaid Rendering — Detailed Execution Reference

📄 **Instruction Hub:** `.github/instructions/plantuml-rendering.instructions.md`  
**JAR Location:** `reference/plantuml-mit-1.2026.2.jar` (MIT, 2026-02-27) | **Requires:** Java on PATH (`java -version`)

---

## 1. Dual-Platform Rendering Commands

### macOS / Linux (bash / zsh / sh)
```bash
# Render a single diagram to PNG
java -jar reference/plantuml-mit-1.2026.2.jar path/to/file.puml

# Render with explicit output directory
java -jar reference/plantuml-mit-1.2026.2.jar path/to/file.puml -o "out/dir"

# Batch render all .puml files in a directory
java -jar reference/plantuml-mit-1.2026.2.jar "path/to/dir/*.puml"

# Using JAVA_HOME explicitly if java is not on global PATH
"$JAVA_HOME/bin/java" -jar reference/plantuml-mit-1.2026.2.jar path/to/file.puml
```

### Windows 11 (PowerShell)
```powershell
# Preferred: use JAVA_HOME explicitly
& "$env:JAVA_HOME\bin\java.exe" -jar reference\plantuml-mit-1.2026.2.jar path\to\file.puml
& "$env:JAVA_HOME\bin\java.exe" -jar reference\plantuml-mit-1.2026.2.jar path\to\file.puml -o "out\dir"
& "$env:JAVA_HOME\bin\java.exe" -jar reference\plantuml-mit-1.2026.2.jar "path\to\dir\*.puml"

# Helper script (uses JAVA_HOME)
.\99-System\scripts\plantuml\plantuml-render.ps1 path\to\file.puml output\dir
```

---

## 2. PlantUML Syntax & Anti-Patterns (Creole vs. Markdown)

`.puml` files parse using PlantUML Creole syntax, NOT standard Markdown. Common pitfalls:

| WRONG | RIGHT | Reason |
|---|---|---|
| `**bold**` in attributes | `<b>bold</b>` or plain text | `**` is Creole bold; causes parse errors in class attributes |
| `// comment` on attribute line | `' comment` on its own line | `//` is Creole italic; breaks attribute definition |
| `★` or Unicode emojis | Plain ASCII `(PROTECTED)`, `[*]` | JVM encoding mismatches across platforms |
| `\n` in arrow labels | Omit or use `note` blocks | PlantUML arrow labels do not interpret `\n` escapes |
| `.. Separator ..` in class body | `--` (thin) or `==` (double) | `..text..` is reserved for package headings |
| Body text inside `component { }` | Empty component + `note` block | Components have no body; use notes |
| Parens in labels: `"text (detail)"` | `text - detail` or backtick quotes | Parentheses interfere with arrow parser |

---

## 3. Mermaid & Diagram Convention

- **Mermaid PNG:** Render inline in chat via tools or preview in VS Code Markdown Preview.
- **4-File Diagram Set:** Every diagram lives as `{name}.puml` + `{name}.mmd` + `{name}.png` + `{name}.md` index in `visualizations/`.
- **Single-format:** PlantUML-only (deployment, network, timing, wbs, usecase, object) or Mermaid-only (architecture, kanban, sankey, pie, quadrant, timeline, gantt, gitgraph).
- **.mmd format:** Raw Mermaid syntax, NO markdown fences.
- **Client Neutrality:** Never brand diagrams. No client, site, or internal-system names in labels or titles; use generic labels ("On-Premises (Firewall VMs)", "Container Registry").
- **Embedding:** Embed `.png` in documentation instead of raw Mermaid blocks.
- **Pre-flight:** Verify directory structure in `visualizations/` and maintain `diagrams-index.md`.
