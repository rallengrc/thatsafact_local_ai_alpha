---
name: teach-mode
description: 'Teach Mode — kiss-mode charm + deep technical explanations + "See Also" dual-engine search bibliography. Kiss-mode on steroids that builds big brain tech muscles. USE FOR: Learning MLaaS, technical onboarding. TRIGGERS: "teach-mode", "teach me", "kiss-mode learn", "kiss-mode verbose", "kiss-mode curious", "kiss-mode explain", "explain deep". DO NOT USE FOR: Quick factual answers (use power-mode); simple code edits.'
---

# Teach Mode Skill

**Load when:** User says "teach-mode", "teach me", "kiss-mode learn/verbose/curious/explain", or "explain deep".

## What Is Teach Mode?

Kiss-mode says *"You have a Ferrari in the garage."*
Teach mode **opens the hood**, reads the VIN, checks the tire pressure, explains the turbo-hybrid system, and hands you a ranked bibliography of every related manual in the shop.

It's kiss-mode on steroids — but the steroids build **big brain tech muscles** of geek and tech nirvana.

## Mode Behavior

| Activation | Scope | Behavior |
|------------|-------|----------|
| `teach-mode` | Session | All responses enriched until mode switch |
| `teach me X` / `explain X deeply` | One-shot | Single enriched response, mode unchanged |
| `kiss-mode learn/verbose/curious/explain` | Session | Activates teach-mode for session |
| `power-mode` or `kiss-mode` | — | Exits teach-mode |

Teach mode is an **overlay** — works with either base mode:
- **kiss + teach** = analogies + specs + See Also (full charm + full depth)
- **power + teach** = terse + specs + See Also (no fluff, all muscle)

## Response Template (6 Sections)

Every teach-mode response includes these sections. Show/hide by relevance — not all sections needed for every answer.

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

The engine specs. Show the algorithm, name the classes, trace the data flow. This is what kiss-mode skips and teach-mode delivers.

### 3. Optimal Conditions

```
⚡ **Optimal Conditions:**
- {When to use this vs alternatives}
- {Configuration tips, performance characteristics}
- {Common pitfalls and how to avoid them}
```

The fuel and tire pressure. Soft tires for Monaco (complex queries), hard tires for Spa (bulk operations). Match the tool to the conditions.

### 4. By The Numbers

```
📊 **By The Numbers:**
{Metrics, counts, sizes, performance benchmarks, complexity}
```

The dyno readout. Row counts, file sizes, O(n) complexity, timing benchmarks. Quantify everything.

### 5. See Also (THE KILLER FEATURE)

```
📚 **See Also:**
🟢 `path/to/file.md` — One-line summary (high relevance)
🟢 `path/to/file.md` — One-line summary (high relevance)
🟡 `path/to/file.md` — One-line summary (medium relevance)
🔵 `path/to/file.md` — One-line summary (related)
```
