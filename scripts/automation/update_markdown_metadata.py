#!/usr/bin/env python3
"""
update_markdown_metadata.py

Enriches Markdown files across the MLaaS workspace with standardized YAML frontmatter
and TL;DR blocks per Resources/Templates/AI-SEARCHABLE-DOC-TEMPLATE.md.
"""

import os
from pathlib import Path
import re
import sys
import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from private_config import merged_doc_metadata

# Repo root, derived from this file so the script runs on any machine.
# Was hardcoded to a macOS path, which made it unrunnable elsewhere.
WORKSPACE = str(Path(__file__).resolve().parents[2])

# Curated metadata dictionary for workspace markdown files
DOC_METADATA = {
    # ---------------- ROOT ----------------
    "README.MD": {
        "title": "MLaaS — Machine Learning as a Service Workspace",
        "description": "Main landing guide covering workspace indexing, MCP hybrid search router, and local LLM setup",
        "keywords": ["MLaaS", "workspace", "indexing", "search router", "MCP", "Ollama", "qwen", "macOS"],
        "category": "index",
        "ai_search_aliases": ["mlaas readme", "workspace overview", "local llm setup", "start here mlaas"],
        "tldr": "Production-ready MLaaS workspace combining local LLM acceleration (Ollama + qwen3.8:27b on Apple Silicon) with a ChromaDB-powered MCP workspace search router and project delivery docs.",
        "use_for": "Getting started with the MLaaS repository, understanding project scope, and locating core systems."
    },
    "Resources/copilot/search-router/CHECKPOINT_SUMMARY.md": {
        "title": "Checkpoint Summary: Hybrid Search Router & Multi-Index Expansion",
        "description": "Milestone status summary documenting completed Phase 1–5 hybrid search router achievements and Phase 6 multi-index roadmap",
        "keywords": ["checkpoint", "summary", "indexing", "search router", "phase 1", "phase 5", "phase 6", "Tantivy", "Graphify", "ChromaDB", "ripgrep"],
        "category": "status",
        "ai_search_aliases": ["checkpoint summary", "indexing progress", "search router milestone", "search router checkpoint"],
        "tldr": "Comprehensive status checkpoint covering the fully delivered Phase 1–5 hybrid search router (ChromaDB + ripgrep) and architectural specification for Phase 6 multi-index expansion (Tantivy + Graphify AST).",
        "use_for": "Reviewing system development progress, verified test metrics, and architectural milestones."
    },
    "CODE_REPOSITORIES.md": {
        "title": "Sub-Repositories in code/ Index",
        "description": "Catalog of 25 cloned external open-source sub-repositories in code/ used for reference and indexing",
        "keywords": ["code repositories", "sub-repos", "Flyte", "Ray", "Tantivy", "MCP", "git clones", "reference"],
        "category": "index",
        "ai_search_aliases": ["code repos", "external repositories", "submodules", "cloned repos in code"],
        "tldr": "Comprehensive directory of 25 external reference repositories stored under `code/`, covering Flyte orchestration, Ray distributed compute, Tantivy search, and MCP implementations.",
        "use_for": "Discovering and locating cloned open-source reference codebases in the workspace."
    },
    ".instructions.md": {
        "title": "MLaaS Repository Agent Instructions",
        "description": "Operational guidelines, priorities, and workflow conventions for AI agents in the MLaaS repository",
        "keywords": ["agent instructions", "copilot", "guidelines", "search router", "indexing", "testing", "standards"],
        "category": "reference",
        "ai_search_aliases": ["agent instructions", "copilot instructions", "repository rules", "mlaas instructions"],
        "tldr": "Authoritative operating instructions and quality guidelines for AI agents working on the MLaaS indexing and search router systems.",
        "use_for": "Guiding AI agent sessions, code standards, test workflows, and architecture decisions."
    },

    # Entries for client documents live in the private config (see private_config.py).

    # ---------------- RESOURCES / TEMPLATES ----------------
    "Resources/Templates/Meeting Note.md": {
        "title": "Meeting Note Template",
        "description": "Obsidian/Markdown template for recording project meeting agendas, discussion notes, and action items",
        "keywords": ["template", "meeting note", "agenda", "action items", "smaas", "Burstable MLaaS"],
        "category": "template",
        "ai_search_aliases": ["meeting note template", "new meeting doc", "how to take meeting notes"],
        "tldr": "Standard Obsidian/Markdown template for capturing project meeting agendas, notes, action items, and SOW links.",
        "use_for": "Creating new meeting notes in the Projects/smaas/Meetings/ directory."
    },
    "Resources/Templates/Weekly Status Update.md": {
        "title": "Weekly Status Update Template",
        "description": "Structured template for weekly project reporting covering completed items, blockers, next steps, and hours",
        "keywords": ["template", "weekly status", "progress update", "blockers", "hours logged"],
        "category": "template",
        "ai_search_aliases": ["weekly status template", "weekly update format", "status report template"],
        "tldr": "Standard template for submitting weekly project status reports, tracking task progress, blockers, upcoming work, and resource hours.",
        "use_for": "Filing new weekly status updates in Projects/smaas/Status Updates/."
    },

    # ---------------- RESOURCES / AWS ----------------
    "Resources/third_party_docs/aws/AmazonBedrock_UserGuide.md": {
        "title": "Amazon Bedrock User Guide Reference",
        "description": "Extracted technical documentation reference for Amazon Bedrock foundation models and API capabilities",
        "keywords": ["Amazon Bedrock", "AWS", "foundation models", "LLM", "API reference", "generative AI"],
        "category": "reference",
        "ai_search_aliases": ["amazon bedrock guide", "bedrock documentation", "aws bedrock api"],
        "tldr": "Comprehensive reference guide covering Amazon Bedrock serverless foundation models, model invocation APIs, guardrails, and knowledge bases.",
        "use_for": "Architecting enterprise generative AI workflows using Amazon Bedrock foundation models."
    },
    "Resources/third_party_docs/aws/next-generation-sagemaker-ug.md": {
        "title": "Next-Generation Amazon SageMaker User Guide",
        "description": "Comprehensive reference guide for modern Amazon SageMaker features, distributed training, and HyperPod",
        "keywords": ["Amazon SageMaker", "SageMaker HyperPod", "AWS", "distributed training", "MLOps", "model serving"],
        "category": "reference",
        "ai_search_aliases": ["sagemaker user guide", "sagemaker hyperpod", "aws sagemaker reference"],
        "tldr": "Deep technical reference for next-generation SageMaker capabilities, including SageMaker HyperPod cluster orchestration, training jobs, and endpoint deployment.",
        "use_for": "Evaluating AWS-managed machine learning platform alternatives and distributed training clusters."
    },

    # ---------------- RESOURCES / COPILOT ROOT ----------------
    "Resources/copilot/MCP_SETUP.md": {
        "title": "MCP Setup, Verification & Troubleshooting",
        "description": "Complete setup and troubleshooting guide for running mlaas-search and sequentialthinking MCP servers",
        "keywords": ["MCP", "Model Context Protocol", "mlaas-search", "sequentialthinking", "troubleshooting", "config"],
        "category": "guide",
        "ai_search_aliases": ["mcp setup", "mcp config", "mcp troubleshooting", "configure mcp servers"],
        "tldr": "Step-by-step setup and verification instructions for running Model Context Protocol (MCP) servers across GitHub Copilot CLI and VS Code.",
        "use_for": "Configuring, verifying, or debugging MCP server connections and virtualenv Python interpreter settings."
    },
    "Resources/copilot/SEQUENTIAL_THINKING_INTEGRATION.md": {
        "title": "Sequential Thinking Integration Guide",
        "description": "Integration patterns and best practices for combining the sequential thinking MCP server with search tools",
        "keywords": ["sequential thinking", "reasoning", "MCP", "search router", "integration", "problem-solving"],
        "category": "guide",
        "ai_search_aliases": ["sequential thinking guide", "how to use seq-think", "sequential thinking mcp"],
        "tldr": "Guide explaining how the `sequentialthinking` MCP server structures complex problem-solving, architectural design, and debugging alongside search.",
        "use_for": "Structuring multi-step analysis, plan revisions, hypothesis testing, and deep-dive problem solving."
    },
    "Resources/copilot/lossless-compression.md": {
        "title": "Lossless Compression Patterns — Context Files",
        "description": "10-technique taxonomy for optimizing instruction and skill files to maximize AI context efficiency",
        "keywords": ["lossless compression", "context optimization", "prompts", "token efficiency", "lean context"],
        "category": "reference",
        "ai_search_aliases": ["lossless compression", "context compression", "token optimization", "compress prompts"],
        "tldr": "Actionable taxonomy of 10 lossless compression techniques to reduce token bloat in instructions and skill files without losing semantic precision.",
        "use_for": "Refactoring verbose instruction, memory, and skill files to conserve AI context tokens."
    },
    "Resources/copilot/vscode-terminal-bloat-bug.md": {
        "title": "VS Code Terminal Bloat Bug Analysis",
        "description": "Detailed defect report on VS Code GitHub Copilot Chat zombie terminal accumulation and token bloat",
        "keywords": ["VS Code bug", "terminal bloat", "zombie terminals", "context waste", "token bloat", "copilot chat"],
        "category": "bug-report",
        "ai_search_aliases": ["terminal bloat bug", "vscode zombie terminals", "terminal context bug"],
        "tldr": "Analysis of a bug where VS Code GitHub Copilot Chat fails to clean up terminal sessions, injecting dead terminal metadata that wastes AI context.",
        "use_for": "Understanding context bloat causes in VS Code chat sessions and applying workarounds."
    },

    # ---------------- RESOURCES / COPILOT / SEARCH-ROUTER ----------------
    "Resources/copilot/search-router/DEFECT_ANALYSIS.md": {
        "title": "mlaas-search — Defect Analysis",
        "description": "Root-cause defect analysis of the ripgrep wrapper, MCP server import bug, and context sizing in mlaas-search",
        "keywords": ["defect analysis", "mlaas-search", "ripgrep bug", "MCP bug", "search router defects"],
        "category": "architecture",
        "ai_search_aliases": ["search router defect analysis", "ripgrep bug analysis", "mlaas-search defects"],
        "tldr": "Exhaustive defect analysis identifying critical bugs in the search router: zero ripgrep results, missing server imports, and token sizing issues.",
        "use_for": "Remediating bugs in `livetext.py`, `search_router.py`, and `search_server.py`."
    },
    "Resources/copilot/search-router/DELIVERABLES.md": {
        "title": "Project Deliverables: Workspace Indexing & MCP Search Router",
        "description": "Executive summary and verification checklist of completed deliverables for the workspace indexing system",
        "keywords": ["deliverables", "workspace indexing", "MCP search router", "ChromaDB", "testing"],
        "category": "status",
        "ai_search_aliases": ["search router deliverables", "indexing deliverables", "project completion checklist"],
        "tldr": "Overview of Phase 1 deliverables: 45 indexed documents, 3 MCP tools, test suite, and quick-start docs.",
        "use_for": "Reviewing system completion criteria and operational readiness."
    },
    "Resources/copilot/search-router/IMPLEMENTATION_LOG.md": {
        "title": "Search Router Implementation Log & Progress Tracker",
        "description": "Checklists, phase tracking, and implementation history for the 5-phase hybrid search router roadmap",
        "keywords": ["implementation log", "progress tracker", "search router", "phases", "checklists"],
        "category": "planning",
        "ai_search_aliases": ["search router implementation log", "progress log", "search router checklist"],
        "tldr": "Comprehensive progress tracker and phase checklist detailing completed work and upcoming tasks for the hybrid search router.",
        "use_for": "Tracking ongoing development status and coordinating implementation across phases."
    },
    "Resources/copilot/search-router/INDEXING.md": {
        "title": "Technical Architecture: Workspace Indexing System",
        "description": "Technical specification of the document discovery, vector embedding, and ChromaDB indexing pipeline",
        "keywords": ["indexing architecture", "ChromaDB", "embeddings", "vector database", "batch processing"],
        "category": "architecture",
        "ai_search_aliases": ["indexing architecture", "chromadb architecture", "vector indexing system"],
        "tldr": "Deep dive into the workspace indexing pipeline: recursive file scanning, exclusion filtering, embedding generation, and ChromaDB persistence.",
        "use_for": "Understanding the document indexing internals and vector database provider interface."
    },
    "Resources/copilot/search-router/QUICK_START.md": {
        "title": "Quick Start: Workspace Indexing & MCP Search Router",
        "description": "5-minute setup and command reference for querying the workspace index and starting search services",
        "keywords": ["quick start", "CLI", "search queries", "HTTP server", "ChromaDB", "commands"],
        "category": "guide",
        "ai_search_aliases": ["quick start search", "search router commands", "how to search workspace"],
        "tldr": "5-minute quick-start guide providing standard commands for searching the workspace, formatting context for Claude, and running the HTTP server.",
        "use_for": "Running fast search queries and testing the search router CLI."
    },
    "Resources/copilot/search-router/README.md": {
        "title": "Search Router Subsystem Overview & Navigation Map",
        "description": "Subsystem overview and documentation index for the hybrid search router and vector index",
        "keywords": ["search router", "navigation map", "subsystem overview", "ChromaDB", "ripgrep"],
        "category": "index",
        "ai_search_aliases": ["search router readme", "search router overview", "search router documentation"],
        "tldr": "Subsystem README detailing the motivation, architecture, and navigation map for all search router and indexing documentation.",
        "use_for": "Orienting yourself within the search router documentation set."
    },
    "Resources/copilot/search-router/SEARCH_ROUTER_PLAN.md": {
        "title": "Unified Search Router: 5-Phase Implementation Roadmap",
        "description": "Comprehensive engineering roadmap for building a hybrid ripgrep + ChromaDB search router with LLM curation",
        "keywords": ["search router roadmap", "engineering plan", "hybrid search", "ripgrep", "ChromaDB", "MCP tools"],
        "category": "planning",
        "ai_search_aliases": ["search router plan", "hybrid search roadmap", "search router specification"],
        "tldr": "Authoritative 5-phase engineering roadmap for developing a unified hybrid search router combining keyword recall (ripgrep) and semantic precision (ChromaDB).",
        "use_for": "Guiding development across Phases 2 through 6 of the search router subsystem."
    },
    "Resources/copilot/search-router/START_HERE.md": {
        "title": "Workspace Indexing & MCP Search Router — START HERE",
        "description": "Immediate 2-minute onboarding guide to test and utilize the workspace semantic search system",
        "keywords": ["start here", "onboarding", "semantic search", "quick commands", "test queries"],
        "category": "guide",
        "ai_search_aliases": ["start here search router", "search router onboarding", "try search router"],
        "tldr": "Fast 2-minute onboarding guide to immediately run sample searches, extract LLM context, and verify the indexing test suite.",
        "use_for": "Verifying search functionality in under two minutes."
    },
    "Resources/copilot/search-router/SYSTEM_SUMMARY.md": {
        "title": "System Summary: Workspace Indexing Architecture",
        "description": "High-level summary of system layers, component interactions, and performance benchmarks for mlaas-search",
        "keywords": ["system summary", "architecture summary", "benchmarks", "components", "provider pattern"],
        "category": "architecture",
        "ai_search_aliases": ["system summary indexing", "indexing overview", "architecture summary search"],
        "tldr": "Architectural summary detailing the 4 system layers (MCP Tools, Search Router, VectorDB Provider, Storage) and performance benchmarks.",
        "use_for": "Quickly reviewing system design, technology choices, and component responsibilities."
    },
    "Resources/copilot/search-router/TOOLS_REFERENCE.md": {
        "title": "MCP Search Tools Reference",
        "description": "API schema and parameter reference for search_workspace, get_workspace_context, and get_workspace_stats",
        "keywords": ["tools reference", "MCP tools", "search_workspace", "tool schema", "API reference"],
        "category": "reference",
        "ai_search_aliases": ["mcp tools reference", "search tools api", "search tool schemas"],
        "tldr": "Detailed API reference defining input schemas, return types, and example payloads for all workspace MCP search tools.",
        "use_for": "Implementing or calling MCP search tools from AI agent harnesses."
    },
    "Resources/copilot/search-router/WORKSPACE_INDEXING.md": {
        "title": "Workspace Indexing User Guide & Command Reference",
        "description": "Complete operations manual for scanning, filtering, and indexing workspace files into ChromaDB",
        "keywords": ["workspace indexing guide", "CLI reference", "file filtering", "batch indexing", "re-indexing"],
        "category": "guide",
        "ai_search_aliases": ["workspace indexing guide", "indexing commands", "how to reindex workspace"],
        "tldr": "Comprehensive manual for indexing the workspace: CLI arguments, custom provider configuration, incremental updates, and troubleshooting.",
        "use_for": "Managing the workspace index, re-indexing after content updates, and configuring embeddings."
    },

    # ---------------- RESOURCES / FLYTE ----------------
    "Resources/third_party_docs/flyte/advanced-project.md": {
        "title": "Flyte 2 Advanced Project Structure Guide",
        "description": "Architecture patterns for structuring production-grade Flyte 2 repositories with multiple workflows and modules",
        "keywords": ["Flyte", "Flyte 2", "project structure", "modules", "best practices", "monorepo"],
        "category": "guide",
        "ai_search_aliases": ["flyte advanced project", "flyte repo structure", "organizing flyte projects"],
        "tldr": "Reference guide detailing best practices for structuring complex Flyte 2 projects across multiple packages, reusable tasks, and shared configurations.",
        "use_for": "Scaffolding and organizing production Flyte 2 repositories and task modules."
    },
    "Resources/third_party_docs/flyte/agents.md": {
        "title": "Flyte 2 AI Agents Guide",
        "description": "Guide to building, deploying, and orchestrating autonomous AI agents and tool-use workflows in Flyte 2",
        "keywords": ["Flyte", "Flyte 2", "agents", "AI agents", "tool use", "orchestration", "LLM workflows"],
        "category": "guide",
        "ai_search_aliases": ["flyte agents", "ai agents in flyte", "flyte llm orchestration"],
        "tldr": "Comprehensive overview of building durable, stateful AI agents and tool-calling execution loops using the Flyte 2 Python SDK.",
        "use_for": "Implementing autonomous AI agents and iterative LLM decision loops in Flyte."
    },
    "Resources/third_party_docs/flyte/apps.md": {
        "title": "Flyte 2 Interactive Apps Guide",
        "description": "Deploying long-running interactive applications, services, and web dashboards inside Flyte 2",
        "keywords": ["Flyte", "Flyte 2", "apps", "interactive services", "Streamlit", "Gradio", "long-running"],
        "category": "guide",
        "ai_search_aliases": ["flyte apps", "interactive apps flyte", "streamlit on flyte"],
        "tldr": "Guide to hosting interactive user interfaces (Streamlit, Gradio, custom web servers) directly within Flyte 2 workflows.",
        "use_for": "Exposing models and data workflows via interactive web applications on Flyte."
    },
    "Resources/third_party_docs/flyte/get-started.md": {
        "title": "Flyte 2 Get Started Guide",
        "description": "Foundational tutorial on Flyte 2 installation, pure Python syntax, local devbox, and first workflows",
        "keywords": ["Flyte", "Flyte 2", "get started", "tutorial", "Python SDK", "devbox", "tasks"],
        "category": "guide",
        "ai_search_aliases": ["flyte get started", "flyte tutorial", "learn flyte 2", "first flyte workflow"],
        "tldr": "Introductory guide to Flyte 2 covering installation, task definition, workflow composition, and local execution without DSL restrictions.",
        "use_for": "Onboarding to Flyte 2 SDK syntax and running initial ML pipelines."
    },
    "Resources/third_party_docs/flyte/scale-your-runs.md": {
        "title": "Flyte 2 Scaling Guide: Distributed Tasks & Resources",
        "description": "Configuring compute resources, GPU accelerators, container images, and cluster parallelism in Flyte 2",
        "keywords": ["Flyte", "scaling", "GPU allocation", "distributed compute", "resources", "concurrency"],
        "category": "guide",
        "ai_search_aliases": ["scale flyte runs", "flyte gpu configuration", "flyte resource requests"],
        "tldr": "Guide to scaling Flyte workloads by requesting CPU/memory, allocating GPUs, parallelizing map tasks, and optimizing container resource limits.",
        "use_for": "Configuring resource constraints, GPU requests, and horizontal task scaling in Flyte."
    },
    "Resources/third_party_docs/flyte/software-development-lifecycle.md": {
        "title": "Flyte 2 Software Development Lifecycle (SDLC)",
        "description": "CI/CD, environment promotion, testing, and version control patterns for Flyte 2 pipelines",
        "keywords": ["Flyte", "SDLC", "CI/CD", "testing", "staging to production", "versioning"],
        "category": "guide",
        "ai_search_aliases": ["flyte sdlc", "flyte ci cd", "deploying flyte pipelines"],
        "tldr": "Best practices for testing, building container images, automating CI/CD deployments, and managing multi-environment promotions for Flyte pipelines.",
        "use_for": "Setting up automated deployment pipelines and environment staging for Flyte."
    },
    "Resources/third_party_docs/flyte/system-one-types.md": {
        "title": "Flyte 2 System One Type System Reference",
        "description": "Deep dive into Flyte's type system, schema validation, data serialization, and type transformers",
        "keywords": ["Flyte", "type system", "schema", "serialization", "dataframes", "validation"],
        "category": "reference",
        "ai_search_aliases": ["flyte types", "flyte type system", "system one types flyte"],
        "tldr": "Reference document explaining Flyte's compile-time and runtime type system, covering primitive types, dataclasses, DataFrames, and file handles.",
        "use_for": "Ensuring strict type safety and optimizing data passing between Flyte tasks."
    },
    "Resources/third_party_docs/flyte/tasks.md": {
        "title": "Flyte 2 Tasks Reference",
        "description": "Detailed guide on task definitions, caching, retries, container customization, and async execution in Flyte 2",
        "keywords": ["Flyte", "tasks", "task caching", "retries", "decorators", "async tasks"],
        "category": "reference",
        "ai_search_aliases": ["flyte tasks", "flyte task guide", "task decorators flyte"],
        "tldr": "Exhaustive reference for authoring Flyte 2 tasks, configuring memoized caching, setting automated retries, and customizing task environments.",
        "use_for": "Designing robust, fault-tolerant, and cached tasks in Flyte workflows."
    },
    "Resources/third_party_docs/flyte/triggers.md": {
        "title": "Flyte 2 Triggers & Scheduling Guide",
        "description": "Automating workflow execution using cron schedules, webhook triggers, and event-driven signals in Flyte 2",
        "keywords": ["Flyte", "triggers", "schedules", "cron", "event-driven", "launch plans"],
        "category": "guide",
        "ai_search_aliases": ["flyte triggers", "flyte scheduling", "cron workflows flyte"],
        "tldr": "Guide on automating Flyte workflow executions via time-based cron schedules, external webhook events, and upstream data triggers.",
        "use_for": "Configuring automated scheduling and event-driven triggers for ML pipelines."
    },

    # ---------------- RESOURCES / RAY ----------------
    "Resources/third_party_docs/ray/Exoshuffle An Extensible Shuffle Architecture.md": {
        "title": "Exoshuffle: Large-Scale Shuffle Architecture in Ray",
        "description": "Architecture paper and analysis of Exoshuffle, Ray's extensible, high-performance distributed data shuffle engine",
        "keywords": ["Ray", "Exoshuffle", "distributed shuffle", "data processing", "Ray Data", "architecture"],
        "category": "architecture",
        "ai_search_aliases": ["exoshuffle ray", "ray shuffle architecture", "distributed shuffle ray"],
        "tldr": "Deep architectural analysis of Exoshuffle, Ray's distributed shuffle engine enabling fault-tolerant 100TB+ data shuffles without dedicated clusters.",
        "use_for": "Designing high-throughput distributed data preprocessing and shuffle pipelines."
    },
    "Resources/third_party_docs/ray/RayV2Architecture.md": {
        "title": "Ray v2 System Architecture Reference",
        "description": "Comprehensive whitepaper reference on Ray 2.0 distributed runtime, GCS, scheduling, and object store",
        "keywords": ["Ray", "Ray v2", "architecture", "distributed runtime", "GCS", "object store", "actors"],
        "category": "architecture",
        "ai_search_aliases": ["ray v2 architecture", "ray distributed system", "ray runtime internals"],
        "tldr": "Authoritative system architecture whitepaper detailing Ray 2.0's decentralized scheduler, Global Control Store (GCS), distributed plasma object store, and actor lifecycle.",
        "use_for": "Understanding the internal mechanics and operational characteristics of the Ray distributed runtime."
    },

    # ---------------- RESOURCES / VISUALIZATION & ROOT ----------------
    "Resources/visualization/Mermaid_Language_Reference_Guide.md": {
        "title": "Mermaid Language Reference Guide",
        "description": "Complete syntax reference and examples for flowcharts, sequence, class, state, ERD, and Gantt diagrams in Mermaid",
        "keywords": ["Mermaid", "diagrams", "syntax", "flowchart", "sequence", "ERD", "class diagram", "Gantt"],
        "category": "reference",
        "ai_search_aliases": ["mermaid syntax", "mermaid diagram reference", "how to write mermaid", "mermaid guide"],
        "tldr": "Complete syntax guide and example library covering every Mermaid diagram type (flowcharts, sequence diagrams, class diagrams, ERDs, mindmaps, and Gantt charts).",
        "use_for": "Authoring clean architectural and workflow diagrams in Markdown."
    },
    "Resources/visualization/PlantUML_Language_Reference_Guide.md": {
        "title": "PlantUML Language Reference Guide",
        "description": "Extracted reference manual for PlantUML diagram syntax including component, sequence, and deployment diagrams",
        "keywords": ["PlantUML", "UML", "diagrams", "sequence diagram", "component diagram", "architecture diagrams"],
        "category": "reference",
        "ai_search_aliases": ["plantuml syntax", "plantuml guide", "plantuml reference manual"],
        "tldr": "Extensive syntax reference for authoring UML sequence, class, component, and deployment diagrams using PlantUML.",
        "use_for": "Creating formal UML architectural diagrams and component models."
    },
    "Resources/self-referential.md": {
        "title": "Self-Referential — Accessing Prompt History, Token Usage & Memories",
        "description": "Guide to inspecting local VS Code session storage, token usage metrics, and persistent agent memories on macOS",
        "keywords": ["self-referential", "session storage", "prompts", "token usage", "memories", "SQLite", "Ollama", "telemetry"],
        "category": "guide",
        "ai_search_aliases": ["self-referential guide", "how to access prompt history", "where are vscode memories stored", "read token usage"],
        "tldr": "Technical guide explaining how to inspect your own prompt history, token consumption (IN/OUT), and agent memory stores from local VS Code SQLite databases and Ollama endpoints.",
        "use_for": "Auditing session history, inspecting prompt logs, tracking token metrics, and recovering conversation context."
    },

    # ---------------- MEMORIES ----------------
    "memories/user-memory.md": {
        "title": "User Memory — Global Cross-Workspace Profile",
        "description": "Persistent user preferences, pinned language models, extension configurations, and global chat session index",
        "keywords": ["user memory", "preferences", "pinned models", "VS Code state", "global memory"],
        "category": "memory",
        "ai_search_aliases": ["user memory", "global preferences", "pinned models list", "my user profile"],
        "tldr": "Global user memory extracted from VS Code state, detailing preferred LLM models, active extensions, and global chat history.",
        "use_for": "Retrieving user preferences and global environment configuration."
    },
    "memories/repo/repo-memory.md": {
        "title": "Repository Memory — MLaaS Workspace Profile",
        "description": "Workspace-specific session state, active chat modes, and recent interactive prompt turns in the MLaaS repository",
        "keywords": ["repo memory", "workspace memory", "prompt history", "chat modes", "checkpoints"],
        "category": "memory",
        "ai_search_aliases": ["repo memory", "workspace memory", "mlaas prompt history", "workspace state"],
        "tldr": "Workspace-scoped memory capturing recent interactive turns, registered chat modes, and checkpoint states in the MLaaS repo.",
        "use_for": "Understanding past interactive context and recent commands executed in this workspace."
    },
    "memories/session/session-memory.md": {
        "title": "Session Memory — Current Task Context & Token Telemetry",
        "description": "Active session metadata, task objectives, working directory context, and token usage telemetry",
        "keywords": ["session memory", "current task", "task context", "token usage", "session state"],
        "category": "memory",
        "ai_search_aliases": ["session memory", "current task context", "token usage telemetry"],
        "tldr": "Task-scoped session memory recording active task parameters, repository branches, and token metrics.",
        "use_for": "Tracking ongoing task goals and evaluating active session context."
    },
    "memories/sessions/index.md": {
        "title": "Chat Sessions Master Index",
        "description": "Catalog and navigation directory of all extracted chat sessions, prompt histories, and architectural checkpoints",
        "keywords": ["sessions index", "chat catalog", "checkpoints index", "session history", "master catalog"],
        "category": "index",
        "ai_search_aliases": ["sessions index", "chat history index", "all sessions catalog"],
        "tldr": "Master catalog indexing 7 historical development sessions, 49 prompts, and 9 architectural checkpoints.",
        "use_for": "Finding and navigating past AI conversations and development sessions."
    },
    "memories/sessions/all-prompts-history.md": {
        "title": "All Prompts History Transcript",
        "description": "Complete chronological transcript of every prompt submitted across all interactive chat turns and CLI sessions",
        "keywords": ["prompts history", "transcript", "prompts archive", "chat logs", "verbatim prompts"],
        "category": "memory",
        "ai_search_aliases": ["all prompts history", "verbatim prompt transcript", "prompt log archive"],
        "tldr": "Comprehensive transcript containing the verbatim text of all user prompts across 35 interactive chat turns and CLI sessions.",
        "use_for": "Reviewing exact user prompts and instructions across historical turns."
    },
    "memories/sessions/checkpoints-and-learnings.md": {
        "title": "Checkpoints & Architectural Learnings Archive",
        "description": "Consolidated record of 9 architectural checkpoints summarizing milestones, decisions, and lessons learned",
        "keywords": ["checkpoints", "learnings", "architectural decisions", "milestones", "handoff summaries"],
        "category": "memory",
        "ai_search_aliases": ["checkpoints and learnings", "architectural checkpoints", "session milestones log"],
        "tldr": "Consolidated archive of 9 architectural checkpoints recording milestone outcomes, implementation decisions, and key learnings.",
        "use_for": "Reviewing system architecture evolution and milestone handoff records."
    },
    "memories/sessions/session-1-local-qwen3-8-setup-and-pdf-converter.md": {
        "title": "Session Log 1: Local Qwen 3.8 Setup & PDF-to-Markdown Converter",
        "description": "Detailed log of session 1 implementing local Ollama qwen3.8:27b acceleration and the PyMuPDF converter",
        "keywords": ["session 1", "qwen", "Ollama", "pdf-to-md", "Apple Silicon", "MLX"],
        "category": "memory",
        "ai_search_aliases": ["session 1 log", "qwen setup session", "pdf converter session"],
        "tldr": "Session log documenting the initial installation of Ollama, configuration of qwen3.8:27b on Apple Silicon M5 Pro, and building the PyMuPDF converter.",
        "use_for": "Reviewing the local LLM setup history and PDF ingestion tool implementation."
    },
    "memories/sessions/session-2-chromadb-indexing-and-search-router.md": {
        "title": "Session Log 2: ChromaDB Indexing & MCP Search Router",
        "description": "Detailed log of session 2 building the ChromaDB workspace indexing pipeline, test suite, and search router",
        "keywords": ["session 2", "ChromaDB", "indexing", "search router", "pytest", "MCP tools"],
        "category": "memory",
        "ai_search_aliases": ["session 2 log", "chromadb indexing session", "search router build session"],
        "tldr": "Session log documenting the implementation of ChromaDB document indexing, provider abstraction, test suite, and search router CLI.",
        "use_for": "Reviewing the Phase 1 indexing system design and test validation history."
    },
    "memories/sessions/session-3-customizations-and-mcp-tools.md": {
        "title": "Session Log 3: Customizations & MCP Tool Integration",
        "description": "Log of session 3 configuring VS Code agent customizations, instructions, skills, and MCP tools",
        "keywords": ["session 3", "customizations", "MCP tools", "agent modes", "skills", "instructions"],
        "category": "memory",
        "ai_search_aliases": ["session 3 log", "customizations session", "mcp tool integration session"],
        "tldr": "Session log covering agent customization migration, custom prompt modes, and MCP server client connections.",
        "use_for": "Reviewing agent configuration and skill setup decisions."
    },
    "memories/sessions/session-4-mcp-cleanup-ray-docs-and-memories.md": {
        "title": "Session Log 4: MCP Cleanup, Ray Documentation & Memories Extraction",
        "description": "Log of session 4 troubleshooting MCP server lifecycles, ingesting Ray architecture docs, and building memories",
        "keywords": ["session 4", "MCP cleanup", "Ray docs", "memories extraction", "sequential thinking"],
        "category": "memory",
        "ai_search_aliases": ["session 4 log", "mcp cleanup session", "ray docs ingestion session"],
        "tldr": "Session log resolving MCP container issues, ingesting Ray v2 whitepapers, and extracting comprehensive session memory catalogs.",
        "use_for": "Examining MCP server troubleshooting and memory extraction history."
    },
    "memories/sessions/session-5-current-metadata-and-prompt-extraction.md": {
        "title": "Session Log 5: Metadata Extraction & Prompt Cataloging",
        "description": "Log of session 5 performing deep SQLite metadata mining and consolidating prompt histories",
        "keywords": ["session 5", "metadata extraction", "prompt history", "session mining", "telemetry"],
        "category": "memory",
        "ai_search_aliases": ["session 5 log", "metadata extraction session", "prompt cataloging session"],
        "tldr": "Session log detailing the extraction of raw metadata, prompt turns, and token metrics from VS Code state databases.",
        "use_for": "Understanding the session metadata extraction methodologies."
    },
    "memories/sessions/session-micro-gemini-confirmation.md": {
        "title": "Micro Session Log: Gemini Flash Confirmation",
        "description": "Brief session verification confirming active model identification for Gemini Flash 3.8",
        "keywords": ["micro session", "Gemini Flash", "model verification", "copilot"],
        "category": "memory",
        "ai_search_aliases": ["gemini confirmation session", "gemini micro session"],
        "tldr": "Quick micro-session log confirming that the selected model in the client host was Gemini Flash 3.8.",
        "use_for": "Verifying past model selection diagnostic steps."
    },
    "memories/sessions/session-micro-mcp-troubleshooting.md": {
        "title": "Micro Session Log: MCP Troubleshooting",
        "description": "Micro session log diagnosing tool execution failures and environment differences between CLI and VS Code",
        "keywords": ["micro session", "MCP troubleshooting", "tool errors", "CLI vs VS Code"],
        "category": "memory",
        "ai_search_aliases": ["mcp troubleshooting micro session", "tool failure diagnosis"],
        "tldr": "Diagnostic session investigating error states in MCP tool execution across CLI and VS Code harnesses.",
        "use_for": "Reviewing historical MCP server error diagnosis."
    }
}


def update_file(rel_path, meta):
    full_path = os.path.join(WORKSPACE, rel_path)
    if not os.path.exists(full_path):
        print(f"File not found: {rel_path}")
        return False

    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()

    # Extract existing frontmatter if any
    existing_fm_dict = {}
    remaining_content = content
    fm_match = re.match(r"^---\n(.*?)\n---\n?", content, re.DOTALL)
    if fm_match:
        fm_text = fm_match.group(1)
        remaining_content = content[fm_match.end():]
        try:
            parsed = yaml.safe_load(fm_text)
            if isinstance(parsed, dict):
                existing_fm_dict = parsed
        except Exception:
            # Fallback parse simple key-values
            for line in fm_text.splitlines():
                if ":" in line and not line.startswith(" ") and not line.startswith("-"):
                    k, v = line.split(":", 1)
                    existing_fm_dict[k.strip()] = v.strip()

    # Build standardized frontmatter
    # Preserve existing custom keys
    combined_fm = {}
    combined_fm["title"] = meta.get("title", existing_fm_dict.get("title", ""))
    combined_fm["description"] = meta.get("description", existing_fm_dict.get("description", ""))
    combined_fm["keywords"] = meta.get("keywords", existing_fm_dict.get("keywords", []))
    
    # If existing tags exist, preserve them
    if "tags" in existing_fm_dict:
        combined_fm["tags"] = existing_fm_dict["tags"]
    
    combined_fm["category"] = meta.get("category", existing_fm_dict.get("category", "reference"))
    combined_fm["classification"] = "🟢🛡️ General"
    combined_fm["last_updated"] = "2026-10-11"
    combined_fm["author"] = "thatsafact"
    combined_fm["ai_search_aliases"] = meta.get("ai_search_aliases", existing_fm_dict.get("ai_search_aliases", []))
    
    # Preserve other existing keys (e.g. engagement-title, effective-date, term-end, date, attendees, source, status, shield, version)
    for k, v in existing_fm_dict.items():
        if k not in combined_fm and k not in ("created", "last_updated", "author"):
            combined_fm[k] = v

    # Format YAML
    fm_yaml = yaml.dump(combined_fm, sort_keys=False, allow_unicode=True, width=1000).strip()
    new_frontmatter = f"---\n{fm_yaml}\n---\n\n"

    # Handle TL;DR and H1
    # Check if remaining_content starts with an H1
    h1_match = re.search(r"^(#\s+[^\n]+)", remaining_content, re.MULTILINE)
    
    tldr_block = f"> **TL;DR:** {meta['tldr']}\n> **Use this for:** {meta['use_for']}\n\n"
    
    if h1_match:
        h1_line = h1_match.group(1)
        h1_start = h1_match.start()
        h1_end = h1_match.end()
        
        post_h1 = remaining_content[h1_end:].lstrip("\n")
        
        # Check if post_h1 starts with an existing blockquote TL;DR or ## TL;DR
        # e.g., > **TL;DR:** ... or ## TL;DR\n...
        # We replace existing TL;DR if present right under H1
        existing_tldr_match = re.match(r"^(?:>\s*\*\*TL;DR:?[^\n]*\n(?:>[^\n]*\n)*|##\s+TL;DR[^\n]*\n(?:[^\n]+\n)*\n?)", post_h1, re.IGNORECASE)
        if existing_tldr_match:
            post_h1 = post_h1[existing_tldr_match.end():].lstrip("\n")
        
        # If there were preamble notes between beginning and H1, keep them or normalize
        pre_h1 = remaining_content[:h1_start].strip()
        if pre_h1:
            body = f"{pre_h1}\n\n{h1_line}\n\n{tldr_block}{post_h1}"
        else:
            body = f"{h1_line}\n\n{tldr_block}{post_h1}"
    else:
        # No H1 found; synthesize one from title
        title = meta.get("title", "Document")
        body = f"# {title}\n\n{tldr_block}{remaining_content.lstrip()}"

    final_content = new_frontmatter + body.lstrip("\n")
    
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(final_content)
    
    print(f"Updated: {rel_path}")
    return True


def main():
    # Client-document entries come from the private config when it exists.
    doc_metadata = merged_doc_metadata(DOC_METADATA, WORKSPACE)
    print(f"Starting update of {len(doc_metadata)} markdown files...")
    updated = 0
    for rel_path, meta in doc_metadata.items():
        if update_file(rel_path, meta):
            updated += 1
    print(f"Finished updating {updated} files.")

if __name__ == "__main__":
    main()
