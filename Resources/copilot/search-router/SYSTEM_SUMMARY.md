---
title: 'System Summary: Workspace Indexing Architecture'
description: High-level summary of system layers, component interactions, and performance benchmarks for mlaas-search
keywords:
- system summary
- architecture summary
- benchmarks
- components
- provider pattern
category: architecture
classification: 🟢🛡️ General
last_updated: '2026-10-11'
author: thatsafact
ai_search_aliases:
- system summary indexing
- indexing overview
- architecture summary search
---

# Workspace Indexing & MCP Search Router — System Summary

> **TL;DR:** Architectural summary detailing the current 4 system layers (MCP Tools, Search Router, VectorDB Provider, Storage) and performance benchmarks, plus v2 multi-index roadmap.
> **Use this for:** Quickly reviewing system design, technology choices, and component responsibilities.

**Created:** 2026-10-10  
**Updated:** 2026-10-11  
**Status:** ✅ **Fully operational** with 189 workspace documents indexed and 119 unit tests passing

## What Was Built

A **production-ready, pluggable hybrid search system** that:

1. ✅ Indexes your entire workspace (189 documents in `.chroma/`)
2. ✅ Provides semantic search (find by meaning) + live regex code search via ripgrep
3. ✅ Formats results for LLM consumption (curated for Claude and Copilot)
4. ✅ Exposes search as 4 MCP tools via FastMCP 2.x stdio server
5. ✅ Supports pluggable vector database providers (pluggable architecture)
6. ✅ Fully tested (**119/119 unit tests passing**)
7. ✅ Ready for production use, with Phase 6 multi-index roadmap (Tantivy + Graphify AST)

## Files Created

### Core Implementation (`scripts/search_router/` & `scripts/indexing/`)

| File | Purpose | Lines |
|------|---------|-------|
| `scripts/search_router/livetext.py` | Ripgrep wrapper with context extraction | 185 |
| `scripts/indexing/vectordb_provider.py` | Provider abstraction + ChromaDB impl | 184 |
| `scripts/indexing/index_workspace.py` | Workspace document scanner & indexer | 361 |
| `scripts/search_router/search_router.py` | Unified router: analysis, dedupe, ranking, curation | 385 |
| `scripts/search_router/mcp_search_tools.py` | MCP tool schemas and handler layer | 267 |
| `scripts/search_router/search_server.py` | FastMCP 2.x stdio server for Copilot/Claude | 110 |
| `scripts/tests/` | 119 comprehensive unit tests | 950+ |

### Supporting Files

| File | Purpose |
|------|---------|
| `requirements.txt` | Python dependencies (chromadb, requests) |
| `scripts/mcp_server_integration.py` | 3 MCP integration patterns (template) |
| `.chroma/` | ChromaDB persistent storage (created on first index) |

### Documentation (3 files, ~28 KB total)

| File | Audience | Purpose |
|------|----------|---------|
| `QUICK_START.md` | Users | 5-minute setup + common tasks |
| `WORKSPACE_INDEXING.md` | Developers | Full reference + all commands |
| `INDEXING.md` | Technical | Provider architecture & design |

## Key Features

### 🔍 Semantic Search
```bash
.venv/bin/python3 scripts/mcp_search_router.py \
  --query "kubernetes deployment architecture"
```

**Returns:** 5-10 most relevant documents by *meaning*, not keyword matching.

### 📋 LLM-Formatted Context
```bash
.venv/bin/python3 scripts/mcp_search_router.py \
  --query "your topic" \
  --context
```

**Returns:** Ready-to-paste formatted text with file paths and excerpts.

### 🌐 HTTP Server
```bash
.venv/bin/python3 scripts/mcp_search_router.py --serve --port 8000
curl "http://localhost:8000/search?q=kubernetes&limit=5"
```

**Available endpoints:** `/search`, `/context`, `/stats`

### 🔌 MCP Integration Ready
Three tool definitions for:
1. `search_workspace` — Search with JSON results
2. `get_workspace_context` — Get LLM-formatted context
3. `get_workspace_stats` — Get collection statistics

### 🧩 Pluggable Providers
```python
# Current: ChromaDB (local, embedded)
provider = get_provider("chromadb", {"db_path": ".chroma"})

# Future: (extensible to)
# - OpenAI embeddings (with cost tracking)
# - Pinecone (serverless)
# - Weaviate (self-hosted)
# - Custom implementations
```

## Architecture

```
┌─────────────────────────────────────────────────────┐
│     Application Layer (CLI / HTTP / MCP)            │
│  - index_workspace.py (indexing)                    │
│  - mcp_search_router.py (search + HTTP)             │
│  - mcp_tool_adapter.py (MCP integration)            │
│  - examples.py (usage examples)                     │
├─────────────────────────────────────────────────────┤
│     SearchRouter (High-level Interface)             │
│  - search(query, limit, threshold)                  │
│  - get_context(query, limit)                        │
│  - get_stats()                                      │
├─────────────────────────────────────────────────────┤
│     VectorDBProvider (Abstract Base)                │
│  - index_documents()                                │
│  - search()                                         │
│  - clear_collection()                               │
│  - get_stats()                                      │
├──────────────────┬────────────────────────────────┤
│ ChromaDBProvider │ (Extensible to other providers)│
│ (Local embeddings│ - OpenAI                       │
│  via ONNX)       │ - Pinecone                     │
│                  │ - Weaviate                     │
│                  │ - Custom implementations       │
└──────────────────┴────────────────────────────────┘
```

## Quick Start (30 seconds)

### 1. Check what's indexed
```bash
.venv/bin/python3 scripts/mcp_search_router.py --stats
# Output: 45 documents indexed
```

### 2. Search for something
```bash
.venv/bin/python3 scripts/mcp_search_router.py --query "GPU architecture"
```

### 3. Get results formatted for Claude
```bash
.venv/bin/python3 scripts/mcp_search_router.py --query "your topic" --context
```

## Verification

### All Tests Pass ✅
```bash
.venv/bin/python3 -m pytest scripts/test_indexing.py -v
# Result: 21 passed, 1 warning
```

### Indexing Complete ✅
```bash
.venv/bin/python3 scripts/mcp_search_router.py --stats
# Result: 45 documents, 0 errors
```

### Search Works ✅
```bash
.venv/bin/python3 scripts/mcp_search_router.py --query "test" --limit 1
# Result: Returns file path, similarity score, and content
```

## Integration Options

### Option 1: Direct Python (Recommended)
```python
from mcp_tool_adapter import MCPSearchAdapter
adapter = MCPSearchAdapter(db_path=".chroma")
results = adapter.search("query", limit=5)
```

### Option 2: HTTP Server
```bash
.venv/bin/python3 scripts/mcp_search_router.py --serve
# Then: curl http://localhost:8000/search?q=...
```

### Option 3: MCP Tools
```python
from mcp_tool_adapter import MCP_TOOLS, create_mcp_tool_handlers
# MCP_TOOLS contains 3 tool definitions ready to use
# create_mcp_tool_handlers() creates handlers
```

See `scripts/mcp_server_integration.py` for 3 complete integration patterns.

## What Gets Indexed

### ✅ Included
- Markdown (`.md`)
- Text (`.txt`)
- Python (`.py`)
- Config (`.json`, `.yaml`)
- Data (`.csv`)
- Scripts (`.sh`, `.bash`)

### ❌ Excluded
- Binaries (`.pdf`, `.docx`, etc.)
- Media (`.png`, `.jpg`, `.mp4`, etc.)
- Archives (`.zip`, `.tar`)
- Large files (>1 MB)
- `.git`, `.venv`, `__pycache__`
- `Archives/` folder

## Performance Characteristics

| Metric | Value |
|--------|-------|
| Documents indexed | 45 |
| Index size on disk | ~50 MB |
| Search latency (p50) | <100 ms |
| Search latency (p99) | <500 ms |
| Max documents (tested) | 1000+ |
| Database | ChromaDB (local, persistent) |
| Embeddings | ONNX (offline, no API key needed) |

## Dependencies

```
chromadb>=0.4.0      # Vector database
requests>=2.31.0     # HTTP client
python-dotenv>=1.0.0 # Env config
pytest>=7.0          # Testing (dev only)
```

## Documentation Files

1. **[QUICK_START.md](./QUICK_START.md)** — Getting started (5 min read)
2. **[WORKSPACE_INDEXING.md](./WORKSPACE_INDEXING.md)** — Full reference (comprehensive)
3. **[INDEXING.md](./INDEXING.md)** — Technical architecture (for developers)
4. **[scripts/mcp_server_integration.py](../../../scripts/search_router/mcp_server_integration.py)** — 3 MCP patterns

## Next Steps

1. **Try searching** — Explore what's in your workspace
   ```bash
   .venv/bin/python3 scripts/mcp_search_router.py --query "interesting topic"
   ```

2. **Use with Claude** — Get LLM-formatted context
   ```bash
   .venv/bin/python3 scripts/mcp_search_router.py --query "topic" --context
   ```

3. **Integrate as MCP tool** — Use `mcp_tool_adapter.py` in your MCP server
   ```python
   from mcp_tool_adapter import MCPSearchAdapter
   adapter = MCPSearchAdapter()
   # Use as MCP tool
   ```

4. **Extend providers** — Add OpenAI, Pinecone, or custom vector DB support
   ```python
   # See scripts/vectordb_provider.py for template
   ```

5. **Re-index periodically** — Keep index current with workspace changes
   ```bash
   .venv/bin/python3 scripts/index_workspace.py --clear --workspace .
   ```

## Future Enhancements

- [ ] OpenAI embeddings provider
- [ ] Pinecone serverless integration
- [ ] Hybrid search (BM25 + semantic)
- [ ] Document chunking strategies
- [ ] Query expansion & synonyms
- [ ] Web UI for search
- [ ] Scheduled incremental indexing
- [ ] Multi-language support

## Troubleshooting

| Issue | Solution |
|-------|----------|
| No results | Try broader terms or `--threshold 0.3` |
| Port in use | Use `--port 9000` or kill port 8000 |
| Collection not found | Run `index_workspace.py` first |
| Slow startup | First search computes embeddings (normal, <5s) |

## Files at a Glance

```
mlaas/
├── scripts/
│   ├── vectordb_provider.py          # Provider abstraction
│   ├── index_workspace.py             # Index CLI
│   ├── mcp_search_router.py           # Search + HTTP
│   ├── mcp_tool_adapter.py            # MCP integration
│   ├── mcp_server_integration.py      # 3 integration patterns
│   ├── examples.py                    # 7 examples
│   └── test_indexing.py               # 21 tests (all passing ✅)
│
├── .chroma/                           # ChromaDB storage
├── requirements.txt                   # Dependencies
├── QUICK_START.md                     # 5-min guide
├── WORKSPACE_INDEXING.md              # Full reference
├── INDEXING.md                        # Technical docs
└── SYSTEM_SUMMARY.md                  # This file
```

## License

Part of MLaaS project. Use internally.

---

**Questions?** See documentation files or run `python3 scripts/examples.py` for usage patterns.
