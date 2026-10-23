---
title: 'Quick Start: Workspace Indexing & MCP Search Router'
description: 5-minute setup and command reference for querying the workspace index and starting search services
keywords:
- quick start
- CLI
- search queries
- HTTP server
- ChromaDB
- commands
category: guide
classification: 🟢🛡️ General
last_updated: '2026-10-11'
author: thatsafact
ai_search_aliases:
- quick start search
- search router commands
- how to search workspace
---

# Quick Start: Workspace Indexing & MCP Search Router

> **TL;DR:** 5-minute quick-start guide providing standard commands for searching the workspace, formatting context for Claude, and running the HTTP server.
> **Use this for:** Running fast search queries and testing the search router CLI.

**Status:** ✅ All 189 workspace documents indexed and ready to search.

## 5-Minute Setup

### 1. Verify Installation (already done)

The workspace is already indexed. Check:

```bash
.venv/bin/python3 scripts/indexing/index_workspace.py --stats
```

Should show:
```json
{
  "document_count": 189,
  "collection_name": "workspace"
}
```

### 2. Try a Hybrid Search (Ripgrep + ChromaDB)

```bash
.venv/bin/python3 scripts/search_router/mcp_search_router.py --query "kubernetes GPU architecture" --limit 5
```

Returns JSON with file paths, similarity scores, and content excerpts.

### 3. Get LLM Context (easiest for Claude & Copilot)

```bash
.venv/bin/python3 scripts/search_router/mcp_search_router.py --query "surrogate model accelerator" --context --limit 3
```

Copy-paste the output into Claude or Copilot.

### 4. Run the Full Test Suite (119 Passing Tests)

```bash
.venv/bin/python3 -m pytest scripts/tests/ -v
```

### 5. Launch the MCP Stdio Server

```bash
.venv/bin/python3 scripts/search_router/search_server.py
```

## Common Tasks

### Search for something

```bash
.venv/bin/python3 scripts/mcp_search_router.py \
  --query "what you're looking for" \
  --limit 5
```

### Get results in plain text

```bash
.venv/bin/python3 scripts/mcp_search_router.py \
  --query "your query" \
  --context \
  --limit 3
```

### Re-index workspace

New files added? Re-index:

```bash
.venv/bin/python3 scripts/index_workspace.py --clear --workspace .
```

### Start HTTP server (for integration)

```bash
.venv/bin/python3 scripts/mcp_search_router.py --serve --port 8000
```

Then in another terminal:

```bash
curl "http://localhost:8000/search?q=kubernetes&limit=5"
```

### Run tests

```bash
.venv/bin/python3 -m pytest scripts/test_indexing.py -v
```

All 21 tests should pass ✅

## Integration with MCP

### Option A: Use as HTTP Server

```python
# Start the server once
.venv/bin/python3 scripts/mcp_search_router.py --serve

# Then in your MCP server, make HTTP requests
import requests
response = requests.get("http://localhost:8000/search", params={
    "q": "kubernetes",
    "limit": 5
})
results = response.json()
```

### Option B: Direct Python Import

```python
from mcp_tool_adapter import MCPSearchAdapter

adapter = MCPSearchAdapter(db_path=".chroma", collection="workspace")

# Search
results = adapter.search("your query", limit=5, format="json")

# Get LLM context
context = adapter.context("your query", limit=3)

# Stats
stats = adapter.stats()
```

### Option C: MCP Tool Definitions

```python
from mcp_tool_adapter import MCP_TOOLS, create_mcp_tool_handlers, MCPSearchAdapter

# Get tool definitions for your MCP server
tools = MCP_TOOLS

# Create handlers
adapter = MCPSearchAdapter()
handlers = create_mcp_tool_handlers(adapter)

# In your tool handler:
result = handlers["search_workspace"]({"query": "kubernetes", "limit": 5})
```

## What's Indexed

✅ **Included:**
- Markdown files (`.md`)
- Text files (`.txt`)
- Code (`.py`)
- Config (`.json`, `.yaml`, `.yml`)
- Data (`.csv`)

❌ **Excluded:**
- Binary/media (`.pdf`, `.png`, `.mp4`, etc.)
- Archives (`.zip`, `.tar`)
- System dirs (`.git`, `.venv`, `__pycache__`)
- `Archives/` folder
- Large files (>1 MB)

## Performance

- **Search latency:** <100ms (after warmup)
- **Index size:** ~50 MB for 45 documents
- **Supported:** Hundreds of documents easily, thousands with tuning
- **Search quality:** Semantic (meaning-based), not keyword matching

## Troubleshooting

| Problem | Fix |
|---------|-----|
| "No results" | Try broader terms or lower `--threshold 0.3` |
| "Port already in use" | Use `--port 9000` or kill process on 8000 |
| "Collection doesn't exist" | Run: `python3 scripts/index_workspace.py` |
| Slow search | First search is slower (embeddings computed); subsequent are fast |

## Docs

- **[WORKSPACE_INDEXING.md](./WORKSPACE_INDEXING.md)** — Full reference with all commands
- **[INDEXING.md](./INDEXING.md)** — Technical details & provider architecture
- **[scripts/examples.py](../../../scripts/indexing/examples.py)** — 7 runnable examples

## Key Files

| File | Purpose |
|------|---------|
| `scripts/vectordb_provider.py` | Abstract provider + ChromaDB implementation |
| `scripts/index_workspace.py` | Index workspace files |
| `scripts/mcp_search_router.py` | Search interface + HTTP server |
| `scripts/mcp_tool_adapter.py` | MCP tool integration |
| `scripts/test_indexing.py` | 21 unit tests (all passing) |
| `.chroma/` | ChromaDB database (persistent) |

## Next Steps

1. **Try searches** to understand what's in your workspace
2. **Use `--context` mode** when feeding results to Claude
3. **Integrate into MCP** using `mcp_tool_adapter.py`
4. **Customize** by adding new providers or adjusting index parameters

---

**Questions?** See [WORKSPACE_INDEXING.md](./WORKSPACE_INDEXING.md) for comprehensive documentation.
