---
name: teach-mode
description: 'Teach Mode — deep technical explanations with a "See Also" search bibliography, for learning the domain and onboarding. TRIGGERS: "teach-mode", "teach me", "explain deep", "kiss-mode learn". NOT for quick answers or simple edits.'
---

# Teach Mode Skill

## What Is Teach Mode?

Kiss-mode says *"You have a Ferrari."* Teach mode **opens the hood** and hands you a ranked bibliography. Kiss-mode on steroids for big brain tech muscles.

## Mode Behavior

| Activation | Scope |
|------------|-------|
| `teach-mode` | Session (until mode switch) |
| `teach me X` | One-shot |
| `kiss-mode learn/verbose` | Activates teach-mode |
| `power-mode` / `kiss-mode` | Exits teach-mode |

Decorator overlays on ANY content mode: `kiss + teach` = charm + depth; `power + teach` = terse + depth.

## Context Mode Integration

Teach-mode is a **communication decorator** — works with any content mode (lean, code, analysis, diamond, panic, prod). Switch decorator by saying `use teach-mode`, `use kiss-mode`, or `use power-mode`.

### Suggesting Mode Switches
- Hands-on coding: `use code-mode` | Exploring lightly: `use lean-mode`
- Quick answers: `use power-mode` | Requirements: `use analysis-mode`

## Response Template (6 Sections)

Show/hide by relevance — not all sections needed for every answer.

### 1. Concierge Note (inherited from kiss-mode)

```
💎 **Concierge Note:** {one-sentence summary}
{analogy — 2-3 sentences max, the Ferrari charm}
**Shortcut:** {trigger} | **Applies:** {when}
```

Load `kiss-mode-concierge/SKILL.md` decoration table for analogy patterns.

### 2. How It Works

```
🔧 **How It Works:**
{Technical implementation — algorithm, code paths, data flow}
**Code:** {file paths with method names}
```

### 3. Optimal Conditions

```
⚡ **Optimal Conditions:**
- {When to use this vs alternatives}
- {Configuration tips, performance characteristics}
- {Common pitfalls and how to avoid them}
```

### 4. By The Numbers

```
📊 **By The Numbers:**
{Metrics, counts, sizes, performance benchmarks, complexity}
```

### 5. See Also (THE KILLER FEATURE)

```
📚 **See Also:**
🟢 `path/to/file.md` — One-line summary (high relevance)
🟡 `path/to/file.md` — One-line summary (medium relevance)
🔵 `path/to/file.md` — One-line summary (related)
```

Run dual search (ChromaDB + diamond-router Tantivy keyword), merge & score, max 10 items.

---

## Section Display Rules

| Question Type | Sections Shown |
|---------------|----------------|
| "What is X?" | Concierge + How It Works + See Also |
| "How does X work?" | All except Deep Dive |
| "Why does X work that way?" | All sections including Deep Dive |
| "Teach me X" | All except Deep Dive (add if complex) |
| Code navigation | How It Works + By The Numbers + See Also |
| Formula/math topic | All sections, Deep Dive with LaTeX |
