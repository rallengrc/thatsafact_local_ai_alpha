# Copilot Instructions — MLaaS Workspace (Orchestrator)

> **TL;DR:** Lean technical instructions for GitHub Copilot in the MLaaS workspace. Governs code execution, search tools, and burstable ML workloads across Mac, AWS, and on-premises firewall VMs.
> **Architecture Overview:** System 1 is **Search Router v2** (Tantivy + Graphify + ChromaDB + Ripgrep); System 2 is **Burstable MLaaS** (Flyte macro DAG + Ray micro distributed compute).

---

## 🎯 System Quick Reference

1. **Search Router v2 (Multi-Index Search Engine):**
   - Coordinates 4 complementary search engines with intelligent intent pre-routing and Reciprocal Rank Fusion (RRF).
   - Backed by **local Ollama LLM** (`qwen3.8:27b` on MLX) for zero cloud spend.
   - Unit-tested in `scripts/tests/` (run the suite for the live count).
2. **Burstable MLaaS (Surrogate ML Acceleration):**
   - Implements a "surrogate in a box" for aerodynamic turbine & physics simulations.
   - Separates **Macro-Orchestration** (Flyte DAGs, caching, lineage) from **Micro-Compute** (Ray distributed actors, in-memory shared-memory tensors).
   - Designed for the **Tri-Environment Model**: Local Mac (Apple Silicon 4-node KinD cluster), AWS EKS (burstable GPU nodes via Karpenter and KubeRay), and On-Premises Firewall VMs.

---

## ⚡ Essential Commands (Virtualenv Enforced)

All Python executions **must** use `.venv/bin/python3` or `.venv/bin/pytest`:

```bash
# Test execution
.venv/bin/python3 -m pytest scripts/tests/ -v

# Speed & SLA benchmark suite (p50: Tantivy 0.1ms, Graphify 0.26ms, Ripgrep 9.6ms, Chroma 46ms)
.venv/bin/python3 scripts/search_router/speed_test.py

# Multi-index re-indexing
.venv/bin/python3 scripts/indexing/index_tantivy.py --clear
.venv/bin/python3 scripts/indexing/index_graphify.py --clear
.venv/bin/python3 scripts/indexing/index_workspace.py --clear --workspace . --provider chromadb --db-path .chroma

# Local surrogate pipeline run (<2s on Mac)
.venv/bin/python3 "Projects/hello-mlaas-burst/local_runner.py"
```

---

## 📋 Modular Reference Dispatch

| Category | Reference Document | Purpose |
|---|---|---|
| **Workflows & Operations** | 📄 [agent-workflows.md](instructions/references/agent-workflows.md) | Full pytest, indexing, benchmarking, and troubleshooting commands |
| **Code Conventions & Standards** | 📄 [code-standards.md](instructions/references/code-standards.md) | Python typing, import structure, error handling, design patterns |
| **Search Router v2 Roadmap** | 📄 [SEARCH_ROUTER_PLAN.md](../Resources/copilot/search-router/SEARCH_ROUTER_PLAN.md) | Multi-index design, query intent classification, RRF fusion |
| **Search Tools Schemas** | 📄 [TOOLS_REFERENCE.md](../Resources/copilot/search-router/TOOLS_REFERENCE.md) | Schemas for `search_workspace`, `search_symbols`, `search_everything`, etc. |
| **Hello MLaaS Architecture** | 📄 [Hello-MLaaS.md](../Hello-MLaaS.md) | Executive technical guide, 4-node KinD topology, ROI metrics |
| **Hello MLaaS Code Package** | 📄 [hello-mlaas-burst/PLAN.md](../Projects/hello-mlaas-burst/PLAN.md) | Runnable code files, 4-node KinD config, RayJob manifest |
| **Lean AI Content Discipline** | 📄 [lean-rules-reference.md](instructions/references/lean-rules-reference.md) | Authoritative rules for skill and instruction files |
| **Client-Neutral Content** | 📄 [client-neutral-content skill](skills/client-neutral-content/SKILL.md) | Keeps client commentary out of OSS-scope files; dynamic `[client]` label |
| **Token Budgeting** | 📄 [token-budgeting-and-pruning.md](instructions/references/token-budgeting-and-pruning.md) | Multi-turn compaction, Ollama local context limits |
| **ripgrep Patterns** | 📄 [ripgrep-scenarios-and-patterns.md](instructions/references/ripgrep-scenarios-and-patterns.md) | `rg` for session logs, `code/*` subrepos, PCRE2 (the built-in grep misses these) |

---

## 🚨 Hard Operational Gates

1. **Always Use `.venv`:** Never call `python` or `pip` directly.
2. **No Hooks & No Prompts:** Never use `preExecutionHook` or lifecycle hooks (they fail silently). Never create or suggest `.github/prompts/*.prompt.md` files (deprecated format that stops working; use skills with `disable-model-invocation: true` instead).
3. **Line Limits:** `SKILL.md` ≤100L, references ≤150L, instructions ≤180L. (`.prompt.md` is strictly forbidden).
4. **Facts-Only:** Never invent metrics or citations. Verify all counts live before output.
5. **Client-Neutral Content:** No client, site, internal-system or engagement names outside `Projects/Burstable MLaaS/`; unsure who the client is → **ask, never guess**. Rules and scanner command: [client-neutral-content.instructions.md](instructions/client-neutral-content.instructions.md).
6. **Direct Execution Default & Subagent Routing:**
   - **Default (~80% of tasks):** Run directly in the primary session with Gemini 3.8 Flash (zero subagents).
   - **`seq-think` keyword:** Decompose problem via sequential thinking into discrete subtasks, then execute each task with a subagent passing `model: "gemini-3.8-flash"`.
   - **`subagent-flow` keyword:** Fast subagent dispatch without prior sequential thinking planning; all child tasks explicitly pass `model: "gemini-3.8-flash"`.
   - **Auto-trigger:** Disparate multi-directory searches or parallel verification builds automatically trigger subagent flow (locked to Gemini 3.8 Flash). Never leave `model` empty to prevent fallback to `gpt-5.6-luna`.
7. **Sticky Search Modes (`internal-first` / `external-first`):**
   - **`internal-first` (Sticky):** Persists across turns once activated. Pre-routes queries through local Search Router v2 (Tantivy + Graphify + Ripgrep + ChromaDB via RRF) and injects bounded top results (≤1,500 tokens) before tool calling.
   - **`external-first` (Sticky):** Deactivates local RRF pre-injection; returns to default direct on-demand tool execution.
