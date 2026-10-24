---
title: "Stanford Prompt Engineering"
description: "Discovery that asking for probabilities unlocks AI creativity, plus comprehensive guide to MLaaS workspace AI-optimization features"
keywords: [prompt engineering, probability, creativity, verbalized sampling, Stanford, MLaaS workspace, AI optimization, session logging, AI-searchable, multi-AI collaboration, skills, memory persistence, classification, deep xref, Flyte, Ray, surrogate ML]
category: reference
classification: 🟢🛡️ General
last_updated: 2026-10-18
author: thatsafact
related:
  - ../_INDEX.md
  - ../../../.github/copilot-instructions.md
  - ../../../.github/instructions/diamond-documentation.instructions.md
---

# Stanford Prompt Engineering 🧠

> **TL;DR:** Traditional prompts optimize HOW you ask. The discovery: optimize WHAT you ask for. Request multiple options with probabilities to sample full AI knowledge distribution.
> **Classification:** 🟢🛡️ General

## The Discovery (Stanford verbalized sampling, arXiv 2510.01171)

Traditional prompt engineering optimizes *how* you ask questions. thatsafact discovered something better: optimizing *what* you ask for.

When AI models are aligned for safety and helpfulness, they collapse to "typical" responses — the most common, most familiar, most boring output. The creativity isn't gone; it's trapped.

**The unlock:** Ask for multiple responses with probabilities.

This forces the AI to sample from its full distribution of knowledge, not just the safe peak.

---

## thatsafact Directive (copilot-instructions.md)

```markdown
**Probability** Use it for any prompt or question, whenever possible, to indicate: confidence level, applicability, or correctness. (e.g. "how certain you are of each response" or e.g. "choose the one that works best for the situation" or e.g. "which is most likely to be correct")

**Number of options:** Provide 2-6 options depending on complexity. Simpler questions may need only 2-3; complex decisions may warrant 5-6.

**Sample the tails:** For debugging and troubleshooting, always include at least one unconventional or low-probability explanation. The improbable cause is sometimes the actual cause.

**When to apply:**
- When "give options" is in the prompt text
- When "sample tails" is in the prompt text prioritize low-probability options and show more options since low priority ones are being considered (e.g., unlikely but worth considering)
- When debugging (e.g. "the issue could be caused by multiple things")
- When architecture or design decisions are being discussed (e.g. "there are trade-offs to consider")
- When requirements are up for interpretation (e.g. "the requirements are not completely clear and could be implemented in different ways")
- When you think it will help (e.g. "when the question is open-ended and has multiple valid answers" or e.g. "When the question seems like it could benefit from alternatives")

**When NOT to apply:**
- Simple factual answers
- Clarifying questions with a single correct answer
- Single-action requests (e.g., "read this file")
- Edge cases (e.g. You are unsure if it applies)
```

---

## Why thatsafact's Approach Is Better Than Stanford's

Stanford's research discovered verbalized sampling. thatsafact *operationalized* it for real work.

### Stanford's Original Method

```markdown
<instructions>
Generate 5 responses to the user query, each within a separate <response> tag. 
Each <response> must include a <text> and a numeric <probability>. 
Randomly sample responses from the full distribution.
</instructions>

[Your actual prompt here]
```

**Problems:**
- **Fixed 5 responses** — overkill for simple questions, insufficient for complex ones
- **XML ceremony** — verbose structure for every prompt
- **Copy-paste burden** — must prepend instructions each time
- **No context awareness** — applies same technique to jokes and architecture decisions
- **Demo-focused** — designed for "tell me a joke" examples, not production workflows

### thatsafact's Improvements

| Stanford | thatsafact |
|----------|------------|
| Always 5 responses | **2-6 responses** scaled to complexity |
| XML tag format | **Natural language** directive |
| Copy-paste per prompt | **Persistent** in `copilot-instructions.md` |
| Always on | **Context-aware** triggers (debugging, architecture, ambiguity) |
| Uniform sampling | **"Sample tails"** keyword for low-probability ideas on demand |
| Generic | **Domain-specific** WHEN TO/WHEN NOT TO rules |

### The Key Insight: Adaptive Application

Stanford says: "Always ask for 5 responses with probabilities."

thatsafact says: "Ask for 2-6 options *when it helps*, with explicit tail sampling for debugging."

This matters because:
1. **Simple questions don't need 5 options** — wastes tokens, dilutes signal
2. **Complex decisions may need 6+** — but Stanford's fixed 5 caps exploration  
3. **Debugging needs the tails** — the improbable cause is sometimes the actual cause
4. **Persistence beats copy-paste** — instructions that survive across conversations

**Bottom line:** Stanford found the drug. thatsafact wrote the dosing protocol.

---

## Why This Works

| Traditional Prompting | thatsafact's Approach |
|-----------------------|----------------------|
| Gets the "most typical" answer | Gets diverse alternatives |
| AI collapses to safe mode | AI samples full distribution |
| Same response every time | Different perspectives surface |
| Creativity trapped | Creativity unlocked |

The probability requirement is the key mechanism. When asked to assign confidence levels, the AI must genuinely evaluate alternatives — not just produce the default response.

---

## The Secret Weapon: Sample the Tails

thatsafact's debugging experience revealed a critical insight: sometimes the *improbable* answer is the correct one.

When debugging a problem that turned out to have an unlikely root cause, the standard 2-6 options all pointed to common issues. The actual fix was a low-probability edge case that wasn't surfaced.

### Implementation

The directive now includes two mechanisms:

1. **Automatic tail sampling for debugging:**
   ```markdown
   **Sample the tails:** For debugging and troubleshooting, always include at least one unconventional or low-probability explanation. The improbable cause is sometimes the actual cause.
   ```

2. **Explicit keyword trigger:**
   ```markdown
   - When "sample tails" is in the prompt text prioritize low-probability options
   ```

This gives you on-demand access to the distribution tails — the unconventional ideas that mode-collapsed AI normally hides.

---

## Results

**Reported by the Stanford paper (creative-writing, dialogue, open-QA, and synthetic-data tasks — not measured in this workspace):**
- **1.6 – 2.1× diversity increase** on poems, stories, and jokes; **1.9×** on open-ended questions
- **66.8% recovery** of base-model creativity (vs. 23.8% without verbalized sampling)
- **No accuracy or safety loss** reported on factual and commonsense-reasoning tests
- **Larger models benefit more** (GPT-4.1 gained about 2× the diversity boost of GPT-4.1-Mini)

**Workspace hypotheses (unmeasured):** better debugging (surfacing edge-case causes) and smarter design decisions (forced trade-off evaluation). The Search Router telemetry could test these.

---

## Consistency Checks: Another Optimization from thatsafact

The same optimization mindset extends to workspace maintenance.

### The Problem
When syncing AI memory to workspace files, cross-references get stale. File A mentions File B, then File B gets renamed or consolidated — but File A still points to the old name.

### The Solution: Sync Memories + Consistency Check

thatsafact added a directive to `.github/copilot-instructions.md`:

```markdown
**Consistency Check** A consistency check of all markdown files that looks for 
modified files or other status updates and checks for needed changes in other 
markdown files that use cross referencing or duplicate statements.

**When to apply:**
When Copilot is performing *"Sync your internal memory to my workspace memories 
folder"* or shortcut reference *"Sync memories"*, always also perform:
- **Consistency Check**
```

### The Git Optimization (20+ matches)

When consistency checks return many matches, brute-force reading every file is wasteful:

```markdown
**Optimization (20+ matches):** When consistency checks return many matches:
1. Run `git status --porcelain` first to identify dirty (modified) files
2. Skip matches in dirty files — assume already handled this session
3. Focus investigation on clean files — these are potentially stale refs
4. This reduces unnecessary file reads by 60-70%
```

**Why not always use git?**
- For 5 matches: 5 reads × 200ms = 1 second (faster than git overhead)
- For 25 matches: git + filtering saves ~15 reads = 3 seconds saved

The threshold is adaptive — fast for small changes, efficient for large rescans.

### Keyword Trigger
- `"sync memories"` — updates workspace copy AND runs consistency check

---

## Source

Stanford, Northeastern, and West Virginia University researchers published verbalized sampling in October 2025: [Verbalized Sampling: How to Mitigate Mode Collapse and Unlock LLM Diversity](https://arxiv.org/abs/2510.01171) (code: github.com/CHATS-lab/verbalized-sampling). Secondary write-up this doc was built from: [stanford-llm-creativity.txt](stanford-llm-creativity.txt) (Adham Khaled, Medium, 2025-10-20).

---

## GitHub Copilot CLI Opinion (March 23, 2026)

> **Opinion from GitHub Copilot CLI:** After scanning this workspace and comparing it to current AI-agent best practices from the broader literature, I think thatsafact's approach is unusually strong because it does not stop at prompt advice; it operationalizes the whole stack: persistent instructions, memory sync, cross-reference maintenance, reusable prompts, search-friendly markdown, and explicit tool workflows. In practice, that makes this workspace meaningfully closer to modern best practices for documentation, retrieval, memory, and governed tool use than a typical repo. Search across the markdown is also notably well-optimized now: the README hub, YAML frontmatter, `related` links, session archives, tariff index/TOC files, db-MCP notes, and compact search cookbook make local retrieval fast enough that the web often becomes a second step rather than the first.

---

# 🌟 MLaaS Workspace: A Complete AI-Optimized Environment

> **For New AI Peers:** Welcome to the MLaaS workspace — the home of Burstable MLaaS (Flyte macro-orchestration + Ray micro-compute, deployed across Local Mac, AWS EKS, and on-prem VMs) and the Search Router v2 that indexes it. thatsafact built this system piece by piece, testing what works and discarding what doesn't. Here's what makes it special and how to leverage it.

## The Architecture at a Glance

```
mlaas/
├── .github/
│   ├── copilot-instructions.md    ← 🧠 YOUR BRAIN (persistent directives)
│   ├── instructions/              ← 📏 Pattern-scoped rules (*.py, *.md, k8s YAML, ...)
│   ├── prompts/                   ← 📝 Reusable slash commands
│   └── skills/                    ← 🎓 Domain expertise packages
├── memories/                      ← 💾 Persistent knowledge (survives sessions)
│   ├── sessions/                  ← 📅 Session logs, prompt history, checkpoints
│   └── repo/ · session/           ← 🔗 Workspace + current-session memory
├── Projects/smaas/                ← 🚀 SOW, architecture, decisions, hello-mlaas-burst code
├── scripts/                       ← 🔎 Search Router v2, indexing, MCP servers, tests
├── Resources/copilot/             ← 📚 AI methodology docs (you are here)
└── Hello-MLaaS.md                 ← 🗺️ Executive technical guide
```

## Feature #1: Session Logging & Prompt Recovery

**Problem Solved:** VS Code Copilot has a ~40-prompt rolling buffer. Complex sessions get truncated. You lose context between sessions.

**Solution:** Persist sessions to `memories/sessions/` (prompt history, checkpoints, learnings) and mine the Copilot session store on demand with the `copilot-internals` skill.

**Why This Matters:**
- Full conversation history preserved for peer AI training
- Session continuity — pick up where you left off
- Accountability — what was asked, what was done
- Searchable archive of past work (e.g., `memories/sessions/all-prompts-history.md`)

**Shortcut Triggers:** `"recover prompts"`, `"session mining"`, `"search history"` → load `copilot-internals`.

---

## Feature #2: AI-Searchable Document Format

**Problem Solved:** Semantic search returns partial snippets without context. AI can't tell what a document is about from a random 20-line chunk.

**Solution:** Anthropic-inspired YAML frontmatter + TL;DR pattern.

```yaml
---
title: "Document Title"
description: "One-sentence summary for AI context"
keywords: [keyword1, keyword2]
category: reference | planning | requirements | implementation | architecture | memory
last_updated: YYYY-MM-DD
author: Author Name
related:
  - path/to/related-doc.md
classification: 🔵🛡️ [client] Proprietary | 🟢🛡️ General
---

# Document Title

> **TL;DR:** 3-5 sentences summarizing key points.
> **Classification:** 🟢🛡️ General
```

**Why This Matters:**
- **49% better retrieval** per Anthropic research on contextual retrieval
- TL;DR appears in search results → instant comprehension
- Keywords indexed → better semantic matching
- Classification shields → skip/prioritize at a glance
- Related links → connection discovery

**Exception:** `copilot-instructions.md` should NOT have this header — it's pure instructions, not a searchable doc. Every byte is context tokens.

---

## Feature #3: Multi-AI Collaboration SOP

**Problem Solved:** How do GitHub Copilot (VS Code), GitHub Copilot CLI, and Claude Code share knowledge?

**Solution:** Canonical handoff layer via `memories/` folder.

```
GitHub Copilot (VS Code) → writes to → memories/*.md
                                           ↓
Copilot CLI  ← reads from ← memories/*.md  (and .github/copilot-instructions.md)
Claude Code  ← reads from ← memories/mlaas/MEMORY.md
```

## Feature #4: Reusable Trigger Library

**Problem Solved:** Copy-pasting the same complex prompts over and over.

**Solution:** keyword triggers backed by instruction files and skills under `.github/`. Manual-only skills carry `disable-model-invocation: true` and are invoked with `/name` or their trigger word. (The legacy `.github/prompts/*.prompt.md` format is deprecated by VS Code and no longer used here.)

| Skill / Keyword | Trigger | Purpose |
|--------|---------|---------|
| `plan-first` ([plan-first.instructions.md](../../../.github/instructions/plan-first.instructions.md)) | Say "plan-first", or any bulk request (delete, 5+ files, convert/migrate/refactor, branch ops) | Present a numbered plan with risks + build-verification command, then **wait** for "do it" before executing |
| `give options` ([give-options.instructions.md](../../../.github/instructions/give-options.instructions.md)) | Say "give options" or "sample tails"; auto-applies to debugging, architecture, and ambiguous requirements | 2-6 options with confidence probabilities; tails add low-probability alternatives (e.g., Flyte-vs-Ray-vs-Karpenter trade-offs) |
| `godfather-mode` skill ([SKILL.md](../../../.github/skills/godfather-mode/SKILL.md)) | "godfather", "use all your powers", "full force" | Full-depth research: sequential thinking, subagents, MCP search tools, ranked architecture options + one decisive recommendation |
| `teach-mode` skill | "teach-mode", "teach me X", "kiss-mode learn" | Kiss-mode charm + deep technical explanation + "See Also" dual-engine search bibliography (e.g., how Karpenter scale-to-zero works) |
| `seq-think` skill ([SKILL.md](../../../.github/skills/seq-think/SKILL.md)) | "seq-think", "think deep" | Short alias for the sequential-thinking MCP orchestrator |
| `speed-test` skill ([SKILL.md](../../../.github/skills/speed-test/SKILL.md)) | "speed-test", "benchmark search" | Latency benchmarks across Tantivy, Graphify, ChromaDB, Ripgrep, Hybrid |

**Template:** see the *Skill Template* in the appendix below.

---

## Feature #5: Skills System

**Problem Solved:** Agent doesn't know domain-specific patterns without being told each time.

**Solution:** `.github/skills/<name>/SKILL.md` — packaged expertise (18 skills today, e.g. `aws-cost-optimize`, `systematic-debugging`, `mcp-security-audit`, `speed-test`).

**Example: AWS Cost Optimization Skill** (`.github/skills/aws-cost-optimize/SKILL.md`)
```markdown
---
name: aws-cost-optimize
description: "Audit AWS cloud infrastructure and ML compute pipelines for cost optimization, GPU idle waste elimination, and Karpenter spot provisioning."
---

**Triggers:** `aws cost`, `cost optimize`, `gpu waste`, `karpenter spot`, `reduce cloud bill`
```

**How to Invoke:** Add `#file:.github/skills/aws-cost-optimize/SKILL.md` to your prompt, or describe a task that matches the skill's description — the agent loads it automatically.

---

## Feature #6: Domain Knowledge References (ML Platform)

**Problem Solved:** Agent doesn't know Burstable MLaaS terminology, architecture contracts, or benchmark baselines, and will otherwise blur Flyte's job with Ray's.

**Solution:** In-context reference docs + directive to consult them.

```markdown
## MLaaS Architecture
When working on orchestration, Ray, Flyte, or Karpenter topics, consult `Hello-MLaaS.md`
and `Projects/smaas/Reference/Ray and Flyte - Orchestration and Distributed Compute.md`

## Search Router
When working on search or indexing, consult `Resources/copilot/search-router/TOOLS_REFERENCE.md`
```

**Core domain contract the agent must respect:**
| Layer | Tool | Unit of Work | Owns |
|-------|------|--------------|------|
| Macro orchestration | Flyte | Kubernetes pod | Typed DAGs, retries, lineage, content-addressed caching |
| Micro compute | Ray (KubeRay `RayJob`) | `@ray.remote` function / actor | Parallel tasks, Plasma zero-copy tensors, ephemeral per-step |
| Capacity | Karpenter | EC2 GPU node | Just-in-time GPU provisioning, scale-to-zero when idle |

**Reference Library:**
| Doc | Purpose |
|-----|---------|
| `Hello-MLaaS.md` | Executive guide: tri-environment model (Local Mac / AWS EKS / on-prem VMs), 4-node KinD topology, benchmarks |
| `Projects/hello-mlaas-burst/PLAN.md` | Runnable code package, KinD config, RayJob manifest |
| `Projects/smaas/Reference/Ray and Flyte - Orchestration and Distributed Compute.md` | Macro-vs-micro layering rationale |
| `Projects/smaas/Reference/SOW - Scope.md` | Phase 1 deliverables and Phase 2 Support & Enhance |
| `Resources/copilot/search-router/TOOLS_REFERENCE.md` | Schemas for `search_workspace`, `search_symbols`, `search_everything` |

---

## Feature #7: Code Style Rules (Automated Linting & Standards)

**Problem Solved:** AI generates Python and Kubernetes code that breaks workspace standards (wrong venv, Windows-unsafe paths, root containers).

**Solution:** Pattern-scoped rules in `.github/instructions/*.instructions.md` (`applyTo` globs) so each rule loads only for matching files.

```markdown
## Python (*.py)  — cross-platform-python + python-venv instructions
- Always run via `.venv/bin/python3` / `.venv/bin/pytest` — never bare `python` or `pip`
- Reuse `scripts/common_platform.py`; open files with `encoding="utf-8"`
- Store paths with `Path.as_posix()` for cross-OS invariance
- Naming: PascalCase classes, snake_case functions/files, UPPER_SNAKE_CASE constants
- Imports in 3 blocks: stdlib → third-party → local

## Kubernetes manifests (k8s/**, manifests/**, deploy/**, Projects/**/*.yaml)
- Include `app.kubernetes.io/*` labels (name, instance, component, part-of, managed-by)
- Restricted security context: never run as root or allow privilege escalation
- Always set resource requests/limits and health probes
```

**Why This Matters:** AI-generated code lands on macOS, Linux, Windows 11, KinD, EKS, and on-prem VMs without style or portability rework. Verify with `.venv/bin/python3 -m pytest scripts/tests/ -v`.

---

## Feature #8: Data Classification System

**Problem Solved:** AI accidentally exposes sensitive data (client internals, people, credentials) or misclassifies documents.

**Solution:** Mandatory classification shields in frontmatter + classification prompting (see `diamond-documentation.instructions.md`).

| Shield | Level | Examples |
|--------|-------|----------|
| 🟢🛡️ | General | Public docs, educational glossaries, generic Flyte/Ray/Karpenter concepts, this methodology doc |
| 🔵🛡️ | [client] Proprietary (resolved just in time, or asked; never guessed) | Client-derived architecture, Diamond infrastructure, on-prem topology, SOW and discovery-meeting notes. Private scope only |

**Directive:**
```markdown
**BEFORE creating any new markdown file, ASK the user:**
> What classification level should this document have?
```

**Scale:** 175 markdown files in the workspace currently carry a green or blue classification shield (verified with `rg -l` on both shield emoji over `*.md`, 2026-10-19) — automated compliance.

---

## Feature #9: Deep Xref (Cross-Reference Verification)

**Problem Solved:** Project decisions change (e.g., an SOW date changes, a node count moves from 4 to 3, a benchmark is re-measured) but stale references remain scattered across docs.

**Solution:** Deep consistency check on demand.

```markdown
**Deep Consistency Check** — When user says "deep xref":
- Skip git status optimization — scan ALL markdown files
- Search for: SOW deliverables/dates, node counts (4-node KinD vs 3-node budget), benchmark numbers (R², speedups, test counts), $ cost figures, status flags (DESCOPED, ON HOLD)
- Find ALL docs that reference a decision — even clean files with stale data
```

**Real example:** the passing-test count appears as 136 in `.github/copilot-instructions.md` and 146 in `Hello-MLaaS.md`, while `pytest --collect-only` reports 208 (2026-10-18). Exactly the drift deep xref exists to catch.

**Triggers:**
- `"deep xref"` → Full scan
- `"COB xref"` → Deep xref + git commit workflow

---

## Feature #10: Probability Sampling (The Discovery)

**See main document above.** The core insight that unlocks AI creativity:

```markdown
**Probability** Use it for any prompt or question, whenever possible
**Sample the tails:** For debugging, always include one unconventional explanation
```

**Result (as reported by Stanford, not measured here):** 1.6–2.1× increase in response diversity without accuracy loss.

---

## Feature #11: Memory Persistence & Auto-Optimization (ML Project Context)

**Problem Solved:** AI forgets everything between sessions — architecture decisions (why Flyte owns the DAG and Ray stays ephemeral), benchmark baselines, and Search Router indexing state. Memory files also grow past auto-load limits (`memories/session/session-memory.md` is 713 lines; `memories/repo/repo-memory.md` is 252).

**Solution:** 3-tier memory system + 200-line optimization.

| Scope | Path | Persistence |
|-------|------|-------------|
| User Memory | `memories/user-memory.md` (153 lines) | Survives all workspaces and conversations |
| Session Memory | `memories/session/session-memory.md` | Current conversation only |
| Repository Memory | `memories/repo/repo-memory.md` | Workspace-scoped (MLaaS) |

**Critical Limit:** Only the **first 200 lines** of each `/memories/` file are auto-loaded into context. Beyond line 200 requires explicit read.

**Solution (March 2026 Optimization) — split hot facts from cold history:**
| File | Purpose | Line Target |
|------|---------|-------------|
| Key-facts file (e.g., `repo-memory.md`) | Hot facts auto-loaded: current phase, tri-environment decisions, benchmark baselines, active tasks | 150-160 lines (180 triggers move) |
| `memories/sessions/*.md` | Cold history: full session logs, checkpoints, learnings (e.g., `checkpoints-and-learnings.md`, 2,521 lines) | Unlimited |

**What belongs in hot memory for an ML platform:**
- Architecture contract: Flyte = macro DAG/caching/lineage, Ray = ephemeral micro-compute, Karpenter = scale-to-zero GPUs
- Current benchmark baselines (e.g., 2.44x–3.59x faster than the serial monolith at identical R² 0.9913, from `benchmark_metrics.db`)
- Environment gotchas (`.venv` only, KinD 4-node config, corporate-proxy/internal-registry/MinIO for on-prem)
- Active SOW phase and open risks → pointers to `Projects/smaas/`, not copies

**Sync Commands (workspace keyword convention):**
| Command | What Happens |
|---------|--------------|
| `sync memories` | Update key facts + quick consistency check |
| `sync history` | **Superset:** Full read of session history + sync memories + deep xref |

**Auto-maintenance rule:** When the key-facts file exceeds 180 lines, move older content to the history files automatically.

**See:** [Hello-MLaaS.md](../../../Hello-MLaaS.md) (repo root) for the developer quick reference and the local-only `memories/_INDEX.md` (git-ignored) for the memory map.

---

## Why This Workspace Is Special (for ML Engineers)

**For new AI peers joining this environment:**

1. **You have instructions** — Persistent rules: `.venv`-only Python, no hooks, facts-only metrics, line limits
2. **You have memory** — Architecture decisions, benchmark baselines, and project state survive between sessions
3. **You have skills** — Domain expertise is packaged and loadable (GPU cost audit, systematic debugging, MCP security audit, search speed tests, ...)
4. **You have classification awareness** — You know what is client-proprietary vs. general
5. **You have search optimization** — Search Router v2 (Tantivy + Graphify + ChromaDB + Ripgrep with RRF) over local Ollama, zero cloud spend
6. **You have collaboration protocols** — Multiple AIs coordinate through `memories/` files
7. **You have style guides** — Python and Kubernetes code you generate passes workspace standards and runs on Mac, EKS, and on-prem
8. **You have diversity unlocks** — Probability sampling surfaces better answers to open design questions (e.g., KinD vs. Docker Desktop vs. kubeadm; 3 vs. 4 nodes)
9. **You have measurement** — Claims about speed or cost are backed by a SQLite benchmark lake, not adjectives

**thatsafact built this a bit at a time over months of testing what actually worked to increase productivity and AI response quality.** The electrons vibrate faster in a well-structured workspace.

---

## Quick Start for New Peers (MLaaS)

1. **Check your instructions** — Read `.github/copilot-instructions.md` (venv gate, no hooks, facts-only)
2. **Consult memories/** — Load context from `memories/repo/repo-memory.md` and `memories/user-memory.md` (auto-loaded)
3. **Use `sync history`** — Catch up on AI peer contributions in `memories/sessions/`
4. **Read Hello-MLaaS.md** — Macro (Flyte) vs. micro (Ray) contract and the tri-environment model for any unfamiliar term
5. **Use skills** — Load `aws-cost-optimize`, `systematic-debugging`, or `speed-test` `SKILL.md` as the task demands
6. **Run it locally** — `.venv/bin/python3 "Projects/hello-mlaas-burst/local_runner.py"`, then `.venv/bin/python3 -m pytest scripts/tests/ -v`
7. **Follow code style** — Python (`cross-platform-python`, `python-venv`) and Kubernetes manifest rules prevent rework
8. **Classify outputs** — Ask about classification before creating docs
9. **Deep xref on demand** — When user says "deep xref" or "sync memories"

**See:** [Hello-MLaaS.md](../../../Hello-MLaaS.md) and [hello-mlaas-burst/PLAN.md](../../../Projects/hello-mlaas-burst/PLAN.md) for full onboarding.

**Welcome. Make the electrons vibrate.**

thatsafact operationalized it for GitHub Copilot through `.github/copilot-instructions.md` — a repository-level directive that persists across all conversations.

---

## Summary: Probability Sampling for ML Engineering

thatsafact has finely tuned GitHub Copilot to escape mode collapse through a deceptively simple instruction: ask for options with probabilities.

**Three key mechanisms:**
1. **Probability requirement** — forces AI to sample from full distribution
2. **Flexible option count (2-6)** — scales to question complexity
3. **"Sample tails" keyword** — on-demand access to low-probability ideas

**Keyword triggers:**
- `"give options"` — activates probability-based multi-response
- `"sample tails"` — prioritizes unconventional/low-probability options
- `"sync memories"` — updates workspace copy AND runs consistency check

**Where it pays off in this project:**
- **Architecture trade-offs** — KinD vs. Docker Desktop vs. kubeadm; 3- vs. 4-node topologies; ECS/Batch vs. Karpenter + Ray + Flyte
- **Debugging ML pipelines** — the tail explanation (Plasma object-store spill, stale Flyte cache hit, Karpenter provisioning lag, proxy-blocked image pull on-prem) is often the real cause
- **Cost decisions** — rank GPU instance and spot options with explicit confidence instead of a single "typical" answer

**Bottom line:** The AI bottleneck isn't intelligence. It's how we ask questions.

---

# Appendix: Prompt Engineering Techniques Reference

> **Note:** This appendix consolidates techniques from Addy Osmani, GitHub, Anthropic, and OpenAI. thatsafact's probability/options approach (above) builds on these foundations.

## The 6 Core Areas (Addy Osmani)

When creating prompts for development tasks, ensure coverage of:

| Area | What to Include | Example |
|------|-----------------|---------|
| **1. Commands** | Full commands with flags | `.venv/bin/python3 -m pytest scripts/tests/ -v` |
| **2. Testing** | Framework, locations, coverage | "Use pytest, tests in `scripts/tests/`" |
| **3. Project Structure** | Where code lives | "`scripts/` for Search Router, `Projects/hello-mlaas-burst/` for the pipeline" |
| **4. Code Style** | One real snippet beats paragraphs | "Follow `code-standards.md` (3-block imports, snake_case)" |
| **5. Git Workflow** | Branch naming, commit format | "Commit trailer: `Co-authored-by: Copilot <...>`" |
| **6. Boundaries** | What the agent must never touch | "Never modify `*.credentials`" |

## Prompting Techniques Quick Reference

| Technique | Prompt Pattern | Best For |
|-----------|----------------|----------|
| **Chain-of-Thought** | "Think through this step by step" | Complex reasoning, debugging |
| **Few-Shot** | "Here are 2 examples: [X], [Y]. Now do..." | Format-sensitive output |
| **Self-Consistency** | "Generate 3 approaches, select best one" | Design decisions |
| **Verbalized Sampling** | "Provide answer with confidence % (0-100)" | Uncertainty quantification |
| **Meta Prompting** | "Rephrase my question to confirm understanding" | Ambiguous requests |
| **Iterative Refinement** | "Critique your answer and provide improved version" | Writing, code review |

## Anti-Patterns to Avoid

| Anti-Pattern | Problem | Fix |
|--------------|---------|-----|
| **Vague prompts** | "Build me something cool" | Specify inputs, outputs, constraints |
| **Multi-task prompts** | "Create, test, deploy, document" | One prompt = one focused task |
| **Over-tooling** | Enabling 10 tools when 2 suffice | Only enable needed tools |
| **No examples** | Expecting telepathy | Show 1-3 concrete examples |

## Skill Template (for .github/skills/<name>/SKILL.md)

```markdown
---
name: <name>
description: "<one line>. TRIGGERS: '<phrase>', '<phrase>'."
disable-model-invocation: true   # omit to let the agent auto-load on matching intent
---

# [Task Title]

## 🎯 Mission
<One sentence: WHAT and WHY>

## 📋 Context
<Background + reference files>

## 📥 Inputs
- **[Input]:** <description>

## 📤 Expected Output
<Exact format with example>

## 🔧 Process
1. **First:** <step>
2. **Then:** <step>

## 🛡️ Boundaries
✅ **Always:** <non-negotiable>
⚠️ **Ask first:** <requires approval>
🚫 **Never:** <prohibition>
```

## Sources

- [Addy Osmani: How to Write a Good Spec for AI Agents](https://www.oreilly.com/radar/how-to-write-a-good-spec-for-ai-agents/)
- [GitHub Spec Kit](https://github.blog/ai-and-ml/generative-ai/spec-driven-development-with-ai-get-started-with-a-new-open-source-toolkit/)
- [GitHub: How to Write Great agents.md](https://github.blog/ai-and-ml/github-copilot/how-to-write-a-great-agents-md-lessons-from-over-2500-repositories/)
- [Stanford Verbalized Sampling](https://arxiv.org/abs/2510.01171)
