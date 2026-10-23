---
name: find-scripts
description: "Find and reuse existing workspace scripts (via scripts/_INDEX.md) before writing new ones. TRIGGERS: 'find script', 'existing scripts', 'script inventory', 'what scripts do we have', 'dupe script', 'reuse script'."
last_updated: "2026-10-12"
---

# 🔍 Find Scripts — Workspace Tooling Discovery & Reuse

> **Purpose:** Locate and reuse existing operational Python scripts across all subsystems before writing new code. Enforces `scripts/_INDEX.md` and subsystem index files as the authoritative source of truth to prevent duplicate scripts or duplicate skills.

## Triggers
- `find script` / `find scripts` / `find tool`
- `existing scripts` / `script inventory` / `list scripts`
- `what scripts do we have` / `locate script` / `check scripts`
- `dupe script` / `prevent duplicate script` / `reuse script`

---

## The Iron Law of Script Reuse

```
NEVER CREATE A NEW SCRIPT BEFORE AUDITING SCRIPTS/_INDEX.MD AND SUBSYSTEM INDICES
```

Reinventing existing tooling wastes context, causes divergence, and fragments maintenance. Always verify what exists before writing a single line of script code.

---

## Subsystem Dispatch Map

| Need / Domain | Primary Subsystem Directory | Subsystem Index | Key Scripts to Reuse |
|---|---|---|---|
| **PDF Conversion & Ingestion** | `scripts/automation/` | [`automation/_INDEX.md`](../../../scripts/automation/_INDEX.md) | `pdf_to_md.py` (standard), `pdf_to_md_fast.py` (large/batch) |
| **OCR & Figure Linking** | `scripts/automation/` | [`automation/_INDEX.md`](../../../scripts/automation/_INDEX.md) | `ocr_packt_figures.py`, `insert_ocr_links.py` |
| **Doc Chunking & Metadata** | `scripts/automation/` | [`automation/_INDEX.md`](../../../scripts/automation/_INDEX.md) | `chunk_aws_docs.py`, `add_aws_frontmatter.py`, `update_markdown_metadata.py` |
| **TOC & Index Regeneration** | `scripts/automation/` | [`automation/_INDEX.md`](../../../scripts/automation/_INDEX.md) | `generate_indices_and_master_toc.py` |
| **Session & Telemetry Mining** | `scripts/automation/` | [`automation/_INDEX.md`](../../../scripts/automation/_INDEX.md) | `export_memories.py`, `probe.py`, `setup_memory_link.py` |
| **Workspace Indexing** | `scripts/indexing/` | [`indexing/_INDEX.md`](../../../scripts/indexing/_INDEX.md) | `index_workspace.py` (Chroma), `index_tantivy.py`, `index_graphify.py` |
| **Vector DB Abstraction** | `scripts/indexing/` | [`indexing/_INDEX.md`](../../../scripts/indexing/_INDEX.md) | `vectordb_provider.py` (`VectorDBProvider`, `ChromaDBProvider`) |
| **Search Routing & Fusion** | `scripts/search_router/` | [`search_router/_INDEX.md`](../../../scripts/search_router/_INDEX.md) | `search_router.py` (hybrid), `livetext.py` (rg), `tantivy_searcher.py`, `graphify_searcher.py` |
| **MCP Servers & Adapters** | `scripts/search_router/` | [`search_router/_INDEX.md`](../../../scripts/search_router/_INDEX.md) | `search_server.py`, `mcp_tool_adapter.py`, `mcp_search_tools.py` |
| **Latency & SLA Benchmarks** | `scripts/search_router/` | [`search_router/_INDEX.md`](../../../scripts/search_router/_INDEX.md) | `speed_test.py`, `scripts/mcp_speed_bench.py` |
| **SQLite Telemetry & MCP** | `scripts/` | [`scripts/_INDEX.md`](../../../scripts/_INDEX.md) | `sqlite_server.py` (metrics + copilot DBs) |
| **Testing & Quality Gates** | `scripts/tests/` | [`tests/_INDEX.md`](../../../scripts/tests/_INDEX.md) | `pytest scripts/` (146 unit & integration tests) |

---

## 4-Step Pre-Creation Gate

1. **Scan the Master Index:** Read [`scripts/_INDEX.md`](../../../scripts/_INDEX.md) to locate the relevant subsystem.
2. **Scan the Subsystem Index:** Read `scripts/<subsystem>/_INDEX.md` for exact capabilities, flags, and trampolines.
3. **Probe Existing Code:** Grep for function or class names before writing (`grep -rn "def <function>" scripts/`).
4. **Co-locate & Index:** If new functionality is genuinely required:
   - Co-locate in the proper subsystem subfolder (`search_router/`, `indexing/`, or `automation/`), never dump in `scripts/` root.
   - Immediately register the new script in that subsystem's `_INDEX.md` and `scripts/_INDEX.md`.

---

## Red Flags — Stop Immediately

- ❌ Creating `scripts/foo.py` when `scripts/automation/foo.py` or similar already exists.
- ❌ Re-implementing PDF extraction, OCR, frontmatter parsing, or indexing from scratch.
- ❌ Creating a duplicate skill in `.github/skills/` without checking existing skills first.
- ❌ Leaving new scripts unregistered in `_INDEX.md`.

---

## Deep References

- [`references/scripts-inventory.md`](references/scripts-inventory.md) — Comprehensive inventory of all 45 scripts with CLI syntax & options.
- [`references/dupe-prevention-protocol.md`](references/dupe-prevention-protocol.md) — Detailed discovery workflow and anti-duplication audit patterns.
