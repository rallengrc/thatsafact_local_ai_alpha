---
name: teach-mode
description: 'Teach Mode — deep technical explanations with verified architecture traces, configuration mechanics, empirical data, and a ranked bibliography. USE FOR: Learning MLaaS, technical onboarding, system architecture. TRIGGERS: "teach-mode", "teach me", "explain deep". DO NOT USE FOR: Quick factual answers (use power-mode); simple code edits.'
---

# Teach Mode Skill

**Load when:** User says "teach-mode", "teach me", or "explain deep".

## What Is Teach Mode?

Teach mode provides **rigorous, facts-grounded technical explanations** with verified architecture traces, configuration mechanics, empirical data, and a ranked bibliography of real workspace references. Zero fluff, zero patronizing analogies.

## Mode Behavior

| Activation | Scope | Behavior |
|------------|-------|----------|
| `teach-mode` | Session | All responses enriched until mode switch |
| `teach me X` / `explain X deeply` | One-shot | Single enriched response, mode unchanged |
| `power-mode` | — | Exits teach-mode |

## Response Structure

### 1. Architectural Thesis & Grounding
Core technical reality in 1-2 precise sentences. Zero analogies, zero fluff.

### 2. How It Works (Mechanics & Plumbing)
Under-the-hood execution trace: exact data structures, APIs, configuration keys, call flows, and runtime contracts.

### 3. Operational Knobs & Optimal Conditions
Exact configuration flags, parameters, trade-offs, and failure recovery steps.

### 4. By The Numbers (Empirical Proof)
Hard metrics: token counts, latency profiles, cache hits, benchmark tables, and verified telemetry.

### 5. Verified Bibliography (See Also)
Ranked, verified workspace file links:
- 🟢 High relevance (direct implementation / spec)
- 🟡 Medium relevance (supporting subsystem)
- 🔵 Contextual reference
