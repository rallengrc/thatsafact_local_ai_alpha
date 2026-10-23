---
title: "MLaaS — Burstable Machine Learning Architecture & Search Router"
description: "Open-standards burstable ML compute orchestration (Flyte + Ray + Kubernetes + Karpenter) with local multi-index search intelligence."
keywords: [MLaaS, Flyte, Ray, Kubernetes, Karpenter, KubeRay, Tantivy, ChromaDB, Graphify, Search Router, Machine Learning, Distributed Compute]
category: reference
last_updated: '2026-10-18'
author: thatsafact
related:
  - Hello-MLaaS.md
  - CODE_REPOSITORIES.md
  - OLLAMA-SEARCH-LOCAL-AI.md
classification: 🟢🛡️ General
ai_search_aliases:
  - mlaas readme
  - repository overview
  - burstable mlaas architecture
  - search router overview
---

# 🚀 MLaaS — Burstable ML Architecture & Hybrid Search Router

> **TL;DR:** Open-standards machine learning engineering workspace uniting **Burstable Distributed Compute Orchestration** (Flyte macro-DAGs + Ray micro-distributed compute + Kubernetes/Karpenter autoscaling) with a **Local Multi-Index Hybrid Search Engine** (Tantivy + Graphify + ChromaDB + Ripgrep).
> **Status:** Active | **Classification:** 🟢🛡️ General (Open Platform Standards)

---

## 🏛️ System Architecture Overview

This repository is organized around two complementary, open-standards engineering systems:

```
┌──────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                       MLAAS WORKSPACE                                            │
├──────────────────────────────────────────────────┬───────────────────────────────────────────────┤
│ 1. BURSTABLE MLAAS COMPUTE ENGINE                │ 2. SEARCH ROUTER v2 HYBRID INTELLIGENCE       │
├──────────────────────────────────────────────────┼───────────────────────────────────────────────┤
│ • Macro Orchestration: Flyte (DAGs, Lineage)     │ • Tantivy: Sub-millisecond BM25 keyword search │
│ • Micro Compute: Ray (Distributed Actors, Plasma)│ • Graphify: Tree-sitter AST symbol graphs      │
│ • Infrastructure: Kubernetes + KubeRay Operator  │ • ChromaDB: Local semantic vector embeddings   │
│ • Autoscaling: Karpenter (Scale-to-Zero, Spot)   │ • Ripgrep: Live regex scanning across repos    │
│ • Tri-Environment: Local KinD, Cloud K8s, On-Prem│ • Local LLM: Ollama (Qwen 27B), no API spend   │
└──────────────────────────────────────────────────┴───────────────────────────────────────────────┘
```

---

## ⚡ System 1: Burstable MLaaS Orchestration

The compute architecture establishes a clean separation between **Macro-Orchestration** and **Micro-Compute**:

1. **Macro-Orchestration ([Flyte](https://flyte.org)):**
   - Manages top-level workflow directed acyclic graphs (DAGs).
   - Provides strict typed data contracts, artifact immutability, memoized execution caching, and automatic retry policies.
2. **Micro-Compute ([Ray](https://www.ray.io)):**
   - Executes fine-grained distributed training, surrogate physics simulations, and hyperparameter sweeps.
   - Employs zero-copy in-memory tensor sharing via the Plasma shared-memory object store.
   - Scales horizontally across multiple GPU ranks using NCCL Ring AllReduce over high-speed network fabrics.
3. **Dynamic Autoscaling ([Karpenter](https://karpenter.sh) + [KubeRay](https://github.com/ray-project/kuberay)):**
   - Replaces static server allocations with dynamic, just-in-time node provisioning.
   - Binds compute instances directly to active job pods and scales idle nodes back to zero in ~30 seconds.
   - Native integration with Spot interruption queues (2-minute warning) and Rebalance Recommendations for cost efficiency.
4. **The Tri-Environment Model:**
   - **Local Workstation:** 4-node simulated Kubernetes cluster via KinD on Apple Silicon Mac / Linux with Docker.
   - **Cloud Kubernetes:** Dynamic EKS/GKE clusters with accelerated GPU instances and cluster placement groups.
   - **Enterprise On-Premises:** Standardized containerized runners operating within enterprise firewall environments.

*For an architectural deep-dive and benchmark comparisons, see [Hello-MLaaS.md](Hello-MLaaS.md).*

---

## 🔍 System 2: Search Router v2 (Hybrid Search Engine)

The workspace includes a high-speed, local multi-index search subsystem designed to discover code, documentation, and prompt history with no workspace content leaving the machine:

| Search Engine | Mechanism | Ideal Query Intent | Typical Latency |
|---|---|---|:---:|
| **Tantivy** | Rust-based BM25 inverted index | Exact keywords, identifiers, error codes | **0.1 ms** |
| **Graphify** | Tree-sitter AST & dependency graphs | Classes, functions, call hierarchies | **0.26 ms** |
| **ChromaDB** | Local embeddings (all-MiniLM-L6-v2) | Conceptual, semantic, descriptive queries | **46 ms** |
| **Ripgrep** | PCRE2 live regex text scanner | Unindexed subrepos, live files, regex patterns | **9.6 ms** |

Results across engines are normalized and merged using **Reciprocal Rank Fusion (RRF)**. For local AI generation and document summarization, the system interfaces with local Ollama runtimes.

*For details on the local AI setup and model configurations, see [OLLAMA-SEARCH-LOCAL-AI.md](OLLAMA-SEARCH-LOCAL-AI.md).*

---

## 🛠️ Scripts & Workspace Automation

All automation in [scripts/](scripts) is built for cross-platform compatibility across **macOS, Linux, and Windows 11**, using [common_platform.py](scripts/common_platform.py) to guarantee UTF-8 encoding, POSIX path invariance, and dynamic virtual environment resolution.

The commands below use the macOS/Linux interpreter path `.venv/bin/python3`; on Windows substitute `.venv\Scripts\python.exe`.

```bash
# 1. Run the test suite
.venv/bin/python3 -m pytest scripts/tests/ -q

# 2. Benchmark search router engine latency
.venv/bin/python3 scripts/search_router/speed_test.py

# 3. Rebuild search indices
.venv/bin/python3 scripts/indexing/index_tantivy.py --clear
.venv/bin/python3 scripts/indexing/index_graphify.py --clear
.venv/bin/python3 scripts/indexing/index_workspace.py --clear --workspace . --provider chromadb --db-path .chroma

# 4. Sync team prompt telemetry and document citations
.venv/bin/python3 scripts/telemetry/sync_prompts_db.py

# 5. Export namespaced memory scopes to Markdown (namespace defaults to the current OS user; pass --user to override)
.venv/bin/python3 scripts/automation/export_memories.py
```

---

## 📂 Repository Layout

```
mlaas/
├── Hello-MLaaS.md               # Flagship architectural blueprint & empirical benchmark guide
├── OLLAMA-SEARCH-LOCAL-AI.md    # Local Ollama LLM setup, MCP server config & models guide
├── CODE_REPOSITORIES.md         # Directory of 34 cloned open-source sub-repositories in code/
├── scripts/                     # Cross-platform automation, indexers, search router & tests
│   ├── common_platform.py       # Cross-platform utilities (macOS, Linux, Windows 11)
│   ├── indexing/                # Tantivy, Graphify, and ChromaDB indexing engines
│   ├── search_router/           # Intent routing, RRF fusion, and speed benchmark harness
│   ├── automation/              # Document converters, memory exporters, index generators
│   ├── telemetry/               # SQLite FTS5 prompt database synchronization
│   └── tests/                   # Pytest test suite
├── Resources/                   # Technical references, guides, and AWS cloud documentation
│   └── third_party_docs/         # Local-only vendor docs (gitignored; not redistributed)
├── Projects/                    # Project implementation plans and runnable packages
│   └── hello-mlaas-burst/       # Runnable Flyte/Ray package & 4-node KinD test harness
├── memories/                    # Local-only prompt telemetry and session records (contents gitignored)
└── .github/                     # Copilot skills, instructions, and workspace configuration
```

---

## 🔒 Security & Standards Compliance

- **Classification:** 🟢🛡️ General. Contains open architectural blueprints, public cloud engineering patterns, and open-source tooling.
- **Local-First by Default:** Embeddings (Ollama at `localhost:11434`, or ChromaDB's bundled embedding model), AST indexing, BM25 search and prompt telemetry run on the local machine, and no workspace content is sent to a cloud LLM API. Expected outbound traffic is limited to one-time model downloads (Ollama model pulls; ChromaDB fetches its default embedding model on first run) and the explicit ingestion scripts under `scripts/automation/` that fetch public vendor documentation on request.
- **Open Platform Standards:** Standardizes on vendor-neutral, portable open-source components (Kubernetes, Ray, Flyte, Karpenter, Tantivy, ChromaDB).

---

## 📄 License

The **original work in this repository** (scripts, tests, architecture documents, skills, instructions and diagrams authored here) is dual-licensed under either the [Apache License, Version 2.0](LICENSE-APACHE) or the [MIT License](LICENSE-MIT), at your option. See [NOTICE](NOTICE) for the copyright statement and attributions.

**Third-party exceptions.** The dual license does not relicense material owned by others:

- `.github/skills/engineering-solution-pivot/` is MIT-licensed by its original author; see its own `LICENSE` file.
- Vendor documentation (AWS, Flyte, Ray, Docker/Kubernetes manuals) is **not published** in this repository. They live only in local, git-ignored directories and remain under their respective owners' terms.
- Upstream open-source projects referenced in [CODE_REPOSITORIES.md](CODE_REPOSITORIES.md) are cloned locally under the git-ignored `code/` directory and carry their own licenses.
- Quoted excerpts from published research or vendor documentation are attributed inline and remain the property of their authors.
