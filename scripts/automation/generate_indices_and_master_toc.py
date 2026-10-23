#!/usr/bin/env python3
"""
generate_indices_and_master_toc.py

Generates missing _INDEX.md files for directories and MASTER_TOC.md in the workspace root,
following the specifications in Resources/Templates/AI-SEARCHABLE-DOC-TEMPLATE.md.
"""

import os
import re
import sys
from pathlib import Path
import datetime
import urllib.parse
import yaml

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from private_config import merged_indices

# Repo root, derived from this file so the script runs on any machine.
# Was hardcoded to a macOS path, which made it unrunnable elsewhere.
WORKSPACE = str(Path(__file__).resolve().parents[2])

INDICES = {
    "Areas/_INDEX.md": {
        "title": "Areas Knowledge Index",
        "description": "Index of ongoing areas of knowledge, AI lingua franca, and PARA workspace organization",
        "keywords": ["Areas", "knowledge index", "PARA", "ai lingua franca", "standards", "organization"],
        "category": "index",
        "ai_search_aliases": ["areas index", "find areas docs", "areas table of contents", "para areas"],
        "tldr": "Index of ongoing responsibilities, communication standards, and organizational methodologies under Areas/.",
        "use_for": "Discovering area-level knowledge, terminology, and PARA organizational foundations.",
        "contents": [
            ("ai-lingua-franca.md", "Shared terminology and communication standard for AI collaboration across teams", "lingua franca, terminology, glossary, AI communication"),
        ]
    },
    "Projects/_INDEX.md": {
        "title": "Projects Directory Index",
        "description": "Index of runnable project packages and project workspaces under Projects/",
        "keywords": ["Projects", "project index", "hello-mlaas-burst", "runnable packages"],
        "category": "index",
        "ai_search_aliases": ["projects index", "find projects", "projects table of contents"],
        "tldr": "Directory index for all active project workspaces and surrogate ML packages under Projects/.",
        "use_for": "Discovering active projects and delivery initiatives.",
        "contents": [
            ("hello-mlaas-burst/README.md", "Runnable Flyte + Ray surrogate modeling pipeline & 4-node KinD test harness", "hello-mlaas-burst, surrogate, KinD, Ray, Flyte, benchmark")
        ]
    },
    # Entries for any private project directory live in the private config (see private_config.py).
    "Resources/_INDEX.md": {
        "title": "Resources Knowledge Index",
        "description": "Master index of external reference docs, technical guides, templates, and frameworks under Resources/",
        "keywords": ["resources index", "templates", "Copilot", "visualization", "search router"],
        "category": "index",
        "ai_search_aliases": ["resources index", "find resource docs", "resources table of contents", "external docs"],
        "tldr": "Master catalog of technical references, templates, and search router engineering documentation.",
        "use_for": "Navigating all reference manuals, architectural specifications, and tooling templates.",
        "contents": [
            ("Templates/_INDEX.md", "Index of document templates (AI-searchable docs, meeting notes, status updates)", "templates, AI-searchable, meetings, status updates"),
            ("copilot/_INDEX.md", "GitHub Copilot customizations, MCP setup, sequential thinking, and search router", "Copilot, MCP, sequential thinking, search router"),
            ("visualization/_INDEX.md", "Syntax reference guides for Mermaid and PlantUML diagrams", "Mermaid, PlantUML, diagrams, syntax, UML"),
            ("self-referential.md", "Guide to inspecting local VS Code session storage, token usage, and memories", "self-referential, prompt history, token usage, memories")
        ]
    },
    "Resources/Templates/_INDEX.md": {
        "title": "Resources Templates Index",
        "description": "Index of standardized templates for AI-searchable documents, meeting notes, and status updates",
        "keywords": ["templates index", "doc templates", "AI-searchable", "meeting template", "status template"],
        "category": "index",
        "ai_search_aliases": ["templates index", "find templates", "document templates list"],
        "tldr": "Directory of standardized Markdown templates designed for AI searchability and structured documentation.",
        "use_for": "Selecting templates for new documents, meeting notes, or status reports.",
        "contents": [
            ("AI-SEARCHABLE-DOC-TEMPLATE.md", "Authoritative copy-paste template for creating AI-optimized markdown documents with frontmatter and TL;DR", "doc template, YAML frontmatter, TL;DR, rules, AI search"),
            ("Meeting Note.md", "Obsidian/Markdown template for capturing project meeting agendas, notes, and action items", "meeting template, notes, agenda, action items"),
            ("Weekly Status Update.md", "Structured template for weekly project status reporting covering progress, blockers, and hours", "weekly status template, blockers, hours logged")
        ]
    },
    "Resources/visualization/_INDEX.md": {
        "title": "Visualization Syntax Guides Index",
        "description": "Index of syntax guides and reference manuals for Mermaid and PlantUML diagram authoring",
        "keywords": ["visualization index", "Mermaid", "PlantUML", "diagrams", "syntax guide", "UML", "flowchart"],
        "category": "index",
        "ai_search_aliases": ["visualization index", "find diagram guides", "mermaid and plantuml docs"],
        "tldr": "Index of syntax reference manuals and diagram examples for Mermaid and PlantUML.",
        "use_for": "Writing architecture, sequence, flowchart, and ERD diagrams in Markdown.",
        "contents": [
            ("Mermaid_Language_Reference_Guide.md", "Complete syntax reference and examples for flowcharts, sequence, class, and ERD diagrams in Mermaid", "Mermaid, diagrams, flowchart, sequence, ERD, syntax"),
            ("PlantUML_Language_Reference_Guide.md", "Extracted reference manual for PlantUML diagram syntax including component, sequence, and deployment diagrams", "PlantUML, UML, diagrams, sequence diagram, component diagram"),
        ]
    },
    "memories/_INDEX.md": {
        "title": "Memories Knowledge Index",
        "description": "Master directory index of persistent AI memories covering user preferences, repo state, and session logs",
        "keywords": ["memories index", "user memory", "repo memory", "session memory", "chat history", "checkpoints"],
        "category": "index",
        "ai_search_aliases": ["memories index", "find memories", "all memories table", "session logs index"],
        "tldr": "Master index of cross-session and task memories: global user preferences, workspace state, active tasks, and session archives.",
        "use_for": "Discovering persistent memory stores, recovered conversation histories, and milestone handoffs.",
        "contents": [
            ("sessions/_INDEX.md", "Shared legacy session catalog and consolidated workspace transcripts", "sessions index, prompt transcript, checkpoints, history"),
            ("mlaas/MEMORY.md", "Claude Code project memory, shared across machines via a link from the local `.claude` profile", "claude code memory, project memory, MEMORY.md, cross-machine")
        ]
    },
    "memories/repo/_INDEX.md": {
        "title": "Repository Memory Index",
        "description": "Index of repository-level persistent memories, interactive chat histories, and active chat modes",
        "keywords": ["repo memory index", "workspace memory", "prompt history", "chat modes"],
        "category": "index",
        "ai_search_aliases": ["repo memory index", "workspace memory index"],
        "tldr": "Index of workspace-scoped repository memory and prompt turn records for the MLaaS project.",
        "use_for": "Discovering workspace-specific memory profiles and interactive turns.",
        "contents": [
            ("repo-memory.md", "Workspace-specific session state, active chat modes, and recent interactive prompt turns in MLaaS", "repo memory, workspace state, chat modes, prompts")
        ]
    },
    "memories/session/_INDEX.md": {
        "title": "Session Memory Index",
        "description": "Index of task-scoped session memory, active working directory context, and token usage telemetry",
        "keywords": ["session memory index", "current task", "token telemetry", "active session"],
        "category": "index",
        "ai_search_aliases": ["session memory index", "task context index"],
        "tldr": "Index of temporary task-scoped session memory files and token consumption metrics.",
        "use_for": "Accessing active session parameters and token consumption tracking.",
        "contents": [
            ("session-memory.md", "Active session metadata, task objectives, working directory context, and token usage telemetry", "session memory, current task, token telemetry, active context")
        ]
    },
    "memories/sessions/_INDEX.md": {
        "title": "Chat Sessions Master Directory Index",
        "description": "Index of historical development sessions, verbatim prompt transcripts, and architectural checkpoints",
        "keywords": ["sessions index", "prompt history", "checkpoints", "session logs", "transcripts", "learnings"],
        "category": "index",
        "ai_search_aliases": ["chat sessions index", "all session logs", "prompts archive index"],
        "tldr": "Comprehensive catalog linking all historical development sessions, prompt archives, and checkpoint summaries.",
        "use_for": "Navigating past AI conversation sessions, recovered prompt logs, and technical decisions.",
        "contents": [
            ("index.md", "Master session catalog detailing the 7 sessions, prompt counts, and token telemetry", "master catalog, session overview, telemetry table"),
            ("all-prompts-history.md", "Chronological transcript containing the verbatim text of all user prompts across 35 turns and CLI sessions", "all prompts, verbatim transcript, prompt archive"),
            ("checkpoints-and-learnings.md", "Consolidated record of 9 architectural checkpoints summarizing milestones, decisions, and lessons learned", "checkpoints, learnings, architectural decisions, handoffs"),
            ("session-1-local-qwen3-8-setup-and-pdf-converter.md", "Session 1 log: local Ollama qwen3.8:27b acceleration and PyMuPDF converter", "session 1, qwen, Ollama, pdf-to-md, Apple Silicon"),
            ("session-2-chromadb-indexing-and-search-router.md", "Session 2 log: ChromaDB workspace indexing pipeline, test suite, and search router", "session 2, ChromaDB, indexing, search router, pytest"),
            ("session-3-customizations-and-mcp-tools.md", "Session 3 log: VS Code agent customizations, instructions, skills, and MCP tools", "session 3, customizations, agent modes, skills, MCP"),
            ("session-4-mcp-cleanup-ray-docs-and-memories.md", "Session 4 log: MCP lifecycle cleanup, Ray whitepaper ingestion, and memories extraction", "session 4, MCP cleanup, Ray docs, memories extraction"),
            ("session-5-current-metadata-and-prompt-extraction.md", "Session 5 log: SQLite metadata mining and prompt history consolidation", "session 5, metadata extraction, prompt history, session mining"),
            ("session-6-master-toc-and-scripts-reorg.md", "Session 6 log: Workspace master TOC generation, PARA index alignment, and scripts reorganization", "session 6, master toc, scripts reorg, PARA"),
            ("session-7-phase6-hello-mlaas-burst-and-kind.md", "Session 7 log: Phase 6 Burstable MLaaS KinD cluster, RayJob execution, and benchmark metrics", "session 7, phase 6, kind, rayjob, burstable mlaas"),
            ("session-8-code-repositories-update.md", "Session 8 log: Code repositories catalog refresh and external reference clones", "session 8, code repositories, git subrepos"),
            ("session-9-telemetry-and-indices.md", "Session 9 log: Prompt telemetry ingestion, SQLite FTS5 database, and multi-user memory partitions", "session 9, telemetry, prompt analytics, fts5, multi-user"),
            ("session-micro-gemini-confirmation.md", "Micro-session log: Gemini Flash 3.8 model verification", "gemini confirmation, micro session, model check"),
            ("session-micro-mcp-troubleshooting.md", "Micro-session log: MCP tool failure diagnosis and CLI vs VS Code comparison", "mcp troubleshooting, micro session, tool errors")
        ]
    },
    "scripts/_INDEX.md": {
        "title": "Scripts & Tooling Master Index",
        "description": "Master index of operational Python subsystems: search routing, indexing, automation, and test suites",
        "keywords": ["scripts index", "Python scripts", "search router", "indexing", "automation", "test suite", "architecture"],
        "category": "index",
        "ai_search_aliases": ["scripts index", "find scripts", "python tools table", "scripts list", "subsystems"],
        "tldr": "Modular catalog of Python scripts organized into search_router, indexing, automation, and tests subdirectories.",
        "use_for": "Discovering CLI tools, servers, batch automation, and test suites in the `scripts/` directory.",
        "contents": [
            ("search_router/_INDEX.md", "Hybrid ripgrep + ChromaDB search router, MCP tools, and stdio search server", "search router, search_server, livetext, adapter, mcp"),
            ("indexing/_INDEX.md", "Workspace document indexing CLI, ChromaDB provider abstraction, and vector database examples", "indexing, chromadb, vectordb, embeddings, indexer"),
            ("telemetry/_INDEX.md", "Team prompt telemetry ingestion engine, SQLite FTS5 indexer, and analytics tools", "telemetry, prompt tracking, fts5, doc attribution"),
            ("automation/_INDEX.md", "Documentation maintenance tools, metadata enrichers, PDF-to-MD converter, and diagnostic probes", "automation, metadata, toc generator, pdf converter"),
            ("tests/_INDEX.md", "Comprehensive unit and integration test suite covering all subsystems (154 passing tests)", "tests, pytest, unit tests, integration tests"),
            ("search_server.py", "Backward-compatible trampoline to search_router/search_server.py", "search server, trampoline, compatibility"),
            ("index_workspace.py", "Backward-compatible trampoline to indexing/index_workspace.py", "indexing, trampoline, compatibility"),
            ("mcp_search_router.py", "Backward-compatible trampoline to search_router/mcp_search_router.py", "mcp search router, trampoline, compatibility")
        ]
    },
    "scripts/telemetry/_INDEX.md": {
        "title": "Prompt Telemetry Subsystem Index",
        "description": "Index of Python modules for team prompt telemetry synchronization, FTS5 full-text indexing, and analytics",
        "keywords": ["telemetry index", "prompt telemetry", "FTS5 analytics", "doc citations"],
        "category": "index",
        "ai_search_aliases": ["telemetry index", "prompt telemetry scripts", "sync prompts db"],
        "tldr": "Subsystem for ingesting multi-user prompt histories from `memories/<username>/` into an ephemeral SQLite FTS5 database (`prompts_analytics.db`).",
        "use_for": "Synchronizing prompt transcripts, running Okapi BM25 keyword searches, and measuring workspace documentation citations.",
        "contents": [
            ("sync_prompts_db.py", "Ingestion engine populating SQLite FTS5 tables and tracking doc citations", "sync prompts, FTS5, BM25, doc citations, telemetry")
        ]
    },
    "scripts/search_router/_INDEX.md": {
        "title": "Search Router Subsystem Scripts Index",
        "description": "Index of hybrid search routing, ripgrep integration, MCP server, and adapter Python scripts",
        "keywords": ["search router", "MCP server", "ripgrep", "livetext", "hybrid search", "ChromaDB", "tools"],
        "category": "index",
        "ai_search_aliases": ["search router scripts", "search server scripts", "mcp search scripts"],
        "tldr": "Index of Python modules implementing hybrid search routing, ripgrep integration, and MCP server endpoints.",
        "use_for": "Locating search algorithms, MCP tool handlers, and server entry points.",
        "contents": [
            ("search_router.py", "Unified hybrid search router combining keyword recall (ripgrep) and semantic precision (ChromaDB)", "unified router, hybrid search, ranking, curation"),
            ("search_server.py", "Production stdio MCP server exposing hybrid search tools to AI agents", "MCP server, stdio, search server, agent tools"),
            ("livetext.py", "RipgrepSearcher wrapper for fast code-aware search and context extraction", "ripgrep, livetext, code search, regex"),
            ("mcp_search_tools.py", "MCP tool definitions for search_workspace, search_code, and search_semantic", "mcp tools, handlers, tool schemas"),
            ("mcp_tool_adapter.py", "Adapter bridging SearchRouter to MCP tool handlers with JSON/text formats", "mcp adapter, tool adapter, formats"),
            ("mcp_search_router.py", "CLI and HTTP search server interface with LLM context formatting", "search router CLI, HTTP server, query runner"),
            ("mcp_server_integration.py", "Integration patterns and examples for connecting MCP search tools", "mcp integration, server patterns, examples"),
            ("mcp_examples.py", "Standalone demonstration examples calling MCP search adapter tools", "mcp examples, tool demos, usage")
        ]
    },
    "scripts/indexing/_INDEX.md": {
        "title": "Workspace Indexing Subsystem Scripts Index",
        "description": "Index of workspace document scanning, ChromaDB vector storage, and provider abstraction modules",
        "keywords": ["indexing scripts", "ChromaDB", "vector database", "provider abstraction", "workspace indexer"],
        "category": "index",
        "ai_search_aliases": ["indexing scripts", "chromadb scripts", "vectordb provider scripts"],
        "tldr": "Index of Python modules for scanning workspace files, generating embeddings, and persisting into ChromaDB.",
        "use_for": "Managing workspace indexing, extending vector DB providers, and running indexing examples.",
        "contents": [
            ("index_workspace.py", "CLI script to recursively scan, filter, and index workspace documents into ChromaDB", "index workspace, ChromaDB, CLI, batch indexing"),
            ("vectordb_provider.py", "Abstract base class VectorDBProvider and ChromaDBProvider implementation with defensive path handling", "vector DB provider, ChromaDB, abstraction, factory"),
            ("examples.py", "Demonstration script covering basic indexing, custom collections, and search queries", "indexing examples, chromadb demo, usage")
        ]
    },
    "scripts/automation/_INDEX.md": {
        "title": "Automation & Tooling Scripts Index",
        "description": "Index of documentation maintenance, metadata enrichment, PDF conversion, and diagnostic tools",
        "keywords": ["automation scripts", "metadata enrichment", "master toc", "pdf converter", "utilities"],
        "category": "index",
        "ai_search_aliases": ["automation scripts", "utility scripts", "maintenance scripts"],
        "tldr": "Index of utility and automation scripts maintaining documentation metadata, table of contents, and data ingestion.",
        "use_for": "Updating frontmatter, regenerating indices, converting PDFs, and checking environment health.",
        "contents": [
            ("generate_indices_and_master_toc.py", "Generator script creating standardized _INDEX.md files and MASTER_TOC.md", "generate index, master toc, documentation tooling"),
            ("update_markdown_metadata.py", "Batch tool to enrich workspace Markdown files with standardized YAML frontmatter and TL;DR", "update metadata, YAML frontmatter, TLDR, automation"),
            ("pdf_to_md.py", "PyMuPDF-based converter extracting text, images, and layout from PDFs into Markdown", "pdf to md, converter, PyMuPDF, document extraction"),
            ("export_memories.py", "Diagnostic extractor mining VS Code state and prompt histories into memory files", "export memories, session mining, SQLite, telemetry"),
            ("probe.py", "Environment probe checking Apple Silicon hardware, MLX, and Ollama configurations", "probe, environment check, Apple Silicon, hardware"),
            ("ingest_aws_ray_blogs.py", "Ingest AWS blog posts covering Ray & KubeRay architectures into Diamond-compliant Markdown with local image assets", "ingest blogs, AWS, Ray, KubeRay, markdown"),
            ("convert_eks_bpg_fast.py", "Fast converter for Resources/third_party_docs/aws/eks-bpg.pdf to Markdown with embedded image assets", "eks-bpg, converter, PyMuPDF, fast pdf to md")
        ]
    },
    "scripts/tests/_INDEX.md": {
        "title": "Test Suite Index",
        "description": "Index of unit and integration test modules covering search routing, indexing, MCP tools, and reasoning",
        "keywords": ["test suite", "pytest", "unit tests", "integration tests", "indexing tests", "search tests"],
        "category": "index",
        "ai_search_aliases": ["test suite index", "pytest scripts", "run tests"],
        "tldr": "Comprehensive test suite containing 119 unit and integration tests across all workspace subsystems.",
        "use_for": "Verifying code changes, checking test coverage, and validating search accuracy.",
        "contents": [
            ("test_indexing.py", "Unit tests for WorkspaceIndexer, ChromaDBProvider, and MCP tool adapter (21 tests)", "indexing tests, chromadb tests, pytest"),
            ("test_search_router.py", "Unit tests for UnifiedSearchRouter, query analyzer, deduplicator, ranker, and curator (20 tests)", "search router tests, unit tests, pytest"),
            ("test_livetext.py", "Unit tests for RipgrepSearcher code-aware search and context extraction (16 tests)", "livetext tests, ripgrep tests, pytest"),
            ("test_mcp_search_tools.py", "Unit tests for MCPSearchTools tool definitions and handlers (10 tests)", "mcp search tools tests, tool tests"),
            ("test_mcp_client.py", "Integration tests verifying MCP client connections to the search server", "mcp client tests, integration tests"),
            ("test_sequential_thinking.py", "Smoke tests verifying sequential thinking server execution", "sequential thinking tests, reasoning tests")
        ]
    }
}


def _gitignored_paths():
    """Plain (glob-free) path entries from the workspace .gitignore."""
    try:
        with open(os.path.join(WORKSPACE, ".gitignore"), encoding="utf-8") as f:
            raw = f.read().splitlines()
    except OSError:
        return []
    entries = []
    for line in raw:
        line = line.strip()
        if line.endswith("/*"):  # "dir/*" ignores the directory contents
            line = line[:-2]
        if not line or line.startswith(("#", "!")) or any(c in line for c in "*?["):
            continue
        entries.append(line.strip("/"))
    return entries


def _is_gitignored(abs_path):
    """True if abs_path falls under a plain .gitignore entry (such files are not published)."""
    try:
        rel = Path(os.path.normpath(abs_path)).relative_to(WORKSPACE).as_posix()
    except ValueError:
        return False
    parts = rel.split("/")
    for entry in _gitignored_paths():
        if "/" in entry:
            if rel == entry or rel.startswith(entry + "/"):
                return True
        elif entry in parts:
            return True
    return False


def _published_exists(abs_path):
    """True if the path exists and would be published (not git-ignored)."""
    return os.path.exists(abs_path) and not _is_gitignored(abs_path)


def _parse_existing_index(full_path):
    """Return (table_rows, trailing_prose) from an existing _INDEX.md."""
    if not os.path.exists(full_path):
        return [], ""
    with open(full_path, encoding="utf-8") as f:
        text = f.read()
    if "## Contents" not in text:
        return [], ""
    lines = text.split("## Contents", 1)[1].splitlines()
    # Only the FIRST contiguous table is the Contents table. Prose below it may
    # contain tables of its own, so scanning to the last "|" line would swallow it.
    i = 0
    while i < len(lines) and not lines[i].strip().startswith("|"):
        i += 1
    if i == len(lines):
        return [], ""
    start = i
    while i < len(lines) and lines[i].strip().startswith("|"):
        i += 1
    rows = lines[start:i]
    prose = "\n".join(lines[i:]).strip()
    return rows, prose


def _row_link_target(row):
    """Extract the markdown link target from the first cell of a table row."""
    cells = row.split("|")
    if len(cells) < 2 or "](" not in cells[1]:
        return None
    cell = cells[1]
    return cell[cell.index("](") + 2 : cell.rindex(")")]


def _split_frontmatter(text: str):
    """Parse existing frontmatter, returning (fm_dict, raw_fm_block, body)."""
    if not text.startswith("---"):
        return {}, "", text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, "", text
    try:
        data = yaml.safe_load(parts[1]) or {}
    except Exception:
        data = {}
    return data, parts[1], parts[2]


def _normalize_body(text: str) -> str:
    """Normalize body text for whitespace comparison."""
    return re.sub(r"\s+", " ", text).strip()


def create_index_file(rel_path, data):
    full_path = os.path.join(WORKSPACE, rel_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)

    existing_text = ""
    existing_fm = {}
    existing_body = ""
    if os.path.exists(full_path):
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                existing_text = f.read()
            existing_fm, _, existing_body = _split_frontmatter(existing_text)
        except OSError:
            pass

    table_rows = []
    for link_target, desc, kw in data["contents"]:
        name = os.path.basename(link_target)
        dir_name = os.path.dirname(link_target)
        if link_target.endswith("/_INDEX.md"):
            folder_name = os.path.basename(dir_name)
            display = f"📁 [{folder_name}/]({link_target})"
        elif link_target.endswith("/"):
            folder_name = link_target.strip("/")
            display = f"📁 [{folder_name}/]({link_target})"
        elif link_target.startswith("mlaas/"):
            display = f"📁 [mlaas/]({link_target})"
        elif dir_name in ("repo", "session", "sessions"):
            display = f"📁 [{dir_name}/]({link_target})"
        elif link_target.endswith("_INDEX.md"):
            display = f"📁 [Index]({link_target})"
        elif link_target.endswith(".py"):
            display = f"🐍 [`{name}`]({link_target})"
        else:
            display = f"📄 [{name}]({link_target})"
        table_rows.append(f"| {display} | {desc} | {kw} |")

    # Keep rows for files that exist on disk but are not declared in INDICES,
    # so additions made since INDICES was last edited are not dropped.
    existing_rows, trailing_prose = _parse_existing_index(full_path)
    declared = {lt for lt, _, _ in data["contents"]}
    index_dir = os.path.dirname(full_path)
    for row in existing_rows:
        target = _row_link_target(row)
        if not target or target in declared:
            continue
        # Link targets may be percent-encoded (e.g. "Amazon%20SageMaker.md").
        decoded = urllib.parse.unquote(target)
        candidate = os.path.normpath(os.path.join(index_dir, decoded))
        # An index inside an ignored directory (e.g. memories/) keeps its own rows.
        exists = os.path.exists(candidate) if _is_gitignored(full_path) else _published_exists(candidate)
        if exists:
            table_rows.append(row.rstrip())

    table_content = "\n".join(table_rows)

    candidate_body = f"""
# {data['title']}

> **TL;DR:** {data['tldr']}
> **Use this for:** {data['use_for']}

## Contents

| File / Folder | Description | Keywords |
|---------------|-------------|----------|
{table_content}
"""

    # Preserve any prose written below the table.
    if trailing_prose:
        candidate_body += "\n" + trailing_prose + "\n"

    # Only bump last_updated if content actually changed or file is new
    last_updated = datetime.date.today().isoformat()
    if existing_fm.get("last_updated") and _normalize_body(candidate_body) == _normalize_body(existing_body):
        fm_keys_match = (
            existing_fm.get("title") == data["title"]
            and existing_fm.get("description") == data["description"]
            and existing_fm.get("keywords") == data["keywords"]
            and existing_fm.get("category") == data["category"]
            and existing_fm.get("ai_search_aliases") == data["ai_search_aliases"]
        )
        if fm_keys_match:
            last_updated = str(existing_fm["last_updated"])

    fm_dict = {
        "title": data["title"],
        "description": data["description"],
        "keywords": data["keywords"],
        "category": data["category"],
        "classification": "🟢🛡️ General",
        "last_updated": last_updated,
        "author": "thatsafact",
        "ai_search_aliases": data["ai_search_aliases"]
    }

    fm_yaml = yaml.dump(fm_dict, sort_keys=False, allow_unicode=True, width=1000).strip()
    content = f"---\n{fm_yaml}\n---\n\n{candidate_body.strip()}\n"

    if content == existing_text:
        return

    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Created/Updated index: {rel_path}")


def _row_targets(row):
    """Every markdown link target in a table row (a row may carry several)."""
    return set(re.findall(r"\]\(([^)]+)\)", row))


def _target_exists(target):
    """True if a link target resolves to a real file under the workspace."""
    target = urllib.parse.unquote(target.split("#", 1)[0]).strip()
    if not target or target.startswith(("http://", "https://", "mailto:")):
        return False
    return _published_exists(os.path.normpath(os.path.join(WORKSPACE, target)))


def _section_tables(text):
    """Map each '## ' heading to the table rows beneath it."""
    out, current = {}, None
    for line in text.splitlines():
        if line.startswith("## "):
            current = line.strip()
            out.setdefault(current, [])
        elif current is not None and line.strip().startswith("|"):
            out[current].append(line)
    return out


def _preserve_master_toc_rows(content, full_path):
    """Carry over rows the regenerated TOC dropped, per section.

    A row is kept when none of its link targets appear in the regenerated
    section and at least one still resolves on disk.
    """
    if not os.path.exists(full_path):
        return content
    with open(full_path, encoding="utf-8") as f:
        existing = f.read()

    old_tables = _section_tables(existing)
    new_tables = _section_tables(content)

    lines = content.splitlines()
    last_row_idx, current = {}, None
    for i, line in enumerate(lines):
        if line.startswith("## "):
            current = line.strip()
        elif current is not None and line.strip().startswith("|"):
            last_row_idx[current] = i

    additions = {}
    for heading, old_rows in old_tables.items():
        if heading not in new_tables or heading not in last_row_idx:
            continue
        present = set()
        for row in new_tables[heading]:
            present |= _row_targets(row)
        keep = []
        for row in old_rows:
            targets = _row_targets(row)
            if not targets or (targets & present):
                continue
            if any(_target_exists(t) for t in targets):
                keep.append(row.rstrip())
        if keep:
            additions[heading] = keep

    # Insert bottom-up so earlier indices stay valid.
    for heading in sorted(additions, key=lambda h: last_row_idx[h], reverse=True):
        at = last_row_idx[heading] + 1
        lines[at:at] = additions[heading]
        safe = heading.encode("ascii", "ignore").decode().strip("# ").strip()
        print(f"  preserved {len(additions[heading])} row(s) under: {safe}")

    return "\n".join(lines) + "\n"


def _count_code_repositories(default=None):
    """Number of repositories catalogued in CODE_REPOSITORIES.md.

    Each repo is a numbered '### N. [name](path)' heading. Counting them keeps
    MASTER_TOC in step with the catalog instead of restating a literal that
    goes stale whenever a repo is added. Returns `default` if the file cannot
    be read or contains no numbered entries.
    """
    path = os.path.join(WORKSPACE, "CODE_REPOSITORIES.md")
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except OSError:
        return default
    count = len(re.findall(r"^###\s+\d+\.\s", text, re.MULTILINE))
    return count or default


def create_master_toc():
    rel_path = "MASTER_TOC.md"
    full_path = os.path.join(WORKSPACE, rel_path)

    existing_text = ""
    existing_fm = {}
    existing_body = ""
    if os.path.exists(full_path):
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                existing_text = f.read()
            existing_fm, _, existing_body = _split_frontmatter(existing_text)
        except OSError:
            pass

    # Derived, not hardcoded - see _count_code_repositories.
    repo_count = _count_code_repositories(default=32)

    candidate_body = f"""
# 🗺️ MLaaS Master Table of Contents

> **TL;DR:** Central knowledge map and master directory indexing all sections, sub-systems, project packages, reference manuals, local memories, and scripts across the MLaaS workspace.
> **Use this for:** Global discovery and navigation across the entire MLaaS knowledge base.

---

## 🧭 High-Level Workspace Architecture

The MLaaS workspace is organized into five main functional domains adhering to PARA methodology principles:

1. **[Projects/](Projects/_INDEX.md):** Runnable project packages, featuring **hello-mlaas-burst**.
2. **[Areas/](Areas/_INDEX.md):** Ongoing knowledge areas, communication standards, and organizational methodologies.
3. **[Resources/](Resources/_INDEX.md):** Reusable templates, diagram guides, and search router engineering docs.
4. **Memories/** (local only, git-ignored): Persistent AI context, user preferences, repository state, prompt histories, and architectural checkpoints.
5. **[Scripts/](scripts/_INDEX.md):** Operational Python scripts for vector indexing, MCP search routing, ripgrep scanning, and test suites.

---

## 📁 Master Directory & Index Registry

| Section / Directory | Index Link | Purpose & Highlights | Key Topics |
|---------------------|------------|----------------------|------------|
| **Root Docs** | [README.MD](README.MD) | Workspace overview, local LLM setup, and quick commands | MLaaS, Ollama, qwen3.8, indexing |
| **Code Repositories** | [CODE_REPOSITORIES.md](CODE_REPOSITORIES.md) | Catalog of {repo_count} external reference git repositories in `code/` | Flyte, Ray, Karpenter, Tantivy, MCP, Kubernetes, clones |
| **Areas** | [Areas/_INDEX.md](Areas/_INDEX.md) | Communication standards and terminology | Lingua franca, glossary, standards |
| **Projects** | [Projects/_INDEX.md](Projects/_INDEX.md) | Master index for runnable project packages | hello-mlaas-burst, Karpenter, Ray, Flyte |
| ↳ *Hello MLaaS Burst* | [Projects/hello-mlaas-burst/README.md](Projects/hello-mlaas-burst/README.md) | Runnable Flyte + Ray surrogate modeling pipeline & 4-node KinD harness | hello-mlaas-burst, surrogate, KinD, benchmark |
| **Resources** | [Resources/_INDEX.md](Resources/_INDEX.md) | Master catalog of technical references and frameworks | Templates, Copilot, visualization, search router |
| ↳ *Templates* | [Resources/Templates/_INDEX.md](Resources/Templates/_INDEX.md) | Standardized templates for docs, meetings, and status | AI-searchable template, meeting note |
| ↳ *Copilot & Tools* | [Resources/copilot/_INDEX.md](Resources/copilot/_INDEX.md) | MCP server setup, sequential thinking, lean authoring | MCP, sequential thinking, lean AI |
| ↳ *Search Router* | [Resources/copilot/search-router/_INDEX.md](Resources/copilot/search-router/_INDEX.md) | Hybrid ripgrep + ChromaDB search router engineering docs | Quick start, roadmap, architecture |
| ↳ *Visualization* | [Resources/visualization/_INDEX.md](Resources/visualization/_INDEX.md) | Syntax reference manuals for Mermaid and PlantUML | Mermaid syntax, PlantUML syntax |
| **Scripts & Tooling** | [scripts/_INDEX.md](scripts/_INDEX.md) | Master index of Python subsystems: search routing, indexing, automation, and tests | search_router, indexing, automation, tests |
| ↳ *Search Router* | [scripts/.../search_router/_INDEX.md](scripts/search_router/_INDEX.md) | Hybrid ripgrep + ChromaDB search router, MCP tools, and stdio server | search_router, search_server, livetext, adapter |
| ↳ *Indexing* | [scripts/.../indexing/_INDEX.md](scripts/indexing/_INDEX.md) | Workspace document scanner, ChromaDB provider abstraction, and demos | index_workspace, vectordb_provider, embeddings |
| ↳ *Telemetry* | [scripts/.../telemetry/_INDEX.md](scripts/telemetry/_INDEX.md) | Team prompt telemetry ingestion engine, SQLite FTS5 indexer, and analytics | telemetry, prompt tracking, fts5, doc attribution |
| ↳ *Automation* | [scripts/.../automation/_INDEX.md](scripts/automation/_INDEX.md) | Metadata enricher, TOC/index generator, and PDF converter | update_metadata, generate_toc, pdf_to_md |
| ↳ *Tests* | [scripts/.../tests/_INDEX.md](scripts/tests/_INDEX.md) | Comprehensive test suite covering all subsystems (238 passing tests) | test_indexing, test_search_router, test_livetext, test_common_platform |

---

## ⚡ Quick Search & Discovery Cheat Sheet

| I Want To... | Check This Document | Shortcut / Query |
|--------------|---------------------|------------------|
| Run semantic search across workspace | [QUICK_START.md](Resources/copilot/search-router/QUICK_START.md) | `.venv/bin/python3 scripts/search_router/mcp_search_router.py --query "..."` (or `.venv\\Scripts\\python.exe` on Windows) |
| Create a new AI-searchable doc | [AI-SEARCHABLE-DOC-TEMPLATE.md](Resources/Templates/AI-SEARCHABLE-DOC-TEMPLATE.md) | Copy frontmatter and TL;DR boilerplate |
| Configure MCP tools | [MCP_SETUP.md](Resources/copilot/MCP_SETUP.md) | Setup mlaas-search and sequentialthinking |
"""

    preserved_body = _preserve_master_toc_rows(candidate_body, full_path)

    # Only bump last_updated if content actually changed or file is new
    last_updated = datetime.date.today().isoformat()
    if existing_fm.get("last_updated") and _normalize_body(preserved_body) == _normalize_body(existing_body):
        last_updated = str(existing_fm["last_updated"])

    fm_dict = {
        "title": "MLaaS Master Table of Contents",
        "description": "Central master table of contents and knowledge map for the entire MLaaS workspace",
        "keywords": ["master toc", "table of contents", "knowledge map", "index", "navigation", "MLaaS", "find", "search", "locate"],
        "category": "index",
        "classification": "🟢🛡️ General",
        "last_updated": last_updated,
        "author": "thatsafact",
        "ai_search_aliases": ["master toc", "table of contents", "site map", "all docs", "find any file", "workspace map", "knowledge map"]
    }

    fm_yaml = yaml.dump(fm_dict, sort_keys=False, allow_unicode=True, width=1000).strip()
    content = f"---\n{fm_yaml}\n---\n\n{preserved_body.strip()}\n"

    # Only write file if content actually changed
    if content == existing_text:
        return

    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Created Master TOC: {rel_path}")


def main():
    # Client-directory index definitions come from the private config when it exists.
    indices = merged_indices(INDICES, WORKSPACE)
    print(f"Generating {len(indices)} _INDEX.md files...")
    for rel_path, data in indices.items():
        create_index_file(rel_path, data)
    print("Generating MASTER_TOC.md...")
    create_master_toc()
    print("All indices and MASTER_TOC.md successfully generated.")


if __name__ == "__main__":
    main()
