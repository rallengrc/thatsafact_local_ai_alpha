---
title: Workspace Indexing User Guide & Command Reference
description: Complete operations manual for scanning, filtering, and indexing workspace files into ChromaDB
keywords:
- workspace indexing guide
- CLI reference
- file filtering
- batch indexing
- re-indexing
category: guide
classification: 🟢🛡️ General
last_updated: '2026-10-11'
author: thatsafact
ai_search_aliases:
- workspace indexing guide
- indexing commands
- how to reindex workspace
---

# Workspace Indexing & MCP Search Router

> **TL;DR:** Comprehensive manual for indexing the workspace: CLI arguments, custom provider configuration, incremental updates, and troubleshooting.
> **Use this for:** Managing the workspace index, re-indexing after content updates, and configuring embeddings.

A production-ready, pluggable vector database system for indexing your workspace and powering an MCP search router. Designed to be extensible to multiple vector database providers while maintaining a clean, provider-agnostic interface.

**Current Status:** ✅ **Fully operational** with 189 workspace documents indexed via ChromaDB, and planning underway for Tantivy and Graphify multi-index expansion.

## What This Does

### Core Capabilities

1. **Workspace Indexing** — Recursively indexes text files in your workspace
   - Excludes binaries (PDF, images, etc.), Archives folder, and system directories
   - Batch processing with configurable parameters
   - Persistent storage with ChromaDB (`.chroma/`)

2. **Semantic Search** — Find documents by meaning, not just keywords
   - Similarity-based search using embeddings
   - Adjustable thresholds for result quality
   - Metadata filtering support

3. **LLM-Ready Formatting** — Get search results in formats suitable for feeding to Claude
   - Full document context extraction
   - Automatic truncation and summarization
   - File paths and similarity scores included

4. **MCP Integration** — Expose search as an MCP tool to Claude
   - Tool definitions with JSON schemas
   - Multiple output formats (JSON, text, context)
   - FastMCP stdio server for AI agents

5. **Extensible Providers** — Swap vector databases without changing application code
   - Currently implemented: **ChromaDB** (local, embedded)
   - Template provided for: OpenAI embeddings, Pinecone, Weaviate, etc.

## Quick Start (30 seconds)

### 1. View indexed documents

```bash
.venv/bin/python3 scripts/indexing/index_workspace.py --stats
```

**Output:**
```json
{
  "document_count": 189,
  "collection_name": "workspace"
}
```

### 2. Search

```bash
.venv/bin/python3 scripts/mcp_search_router.py --query "kubernetes deployment architecture"
```

**Returns:** JSON with file paths, similarity scores, and document excerpts

### 3. Get LLM context

```bash
.venv/bin/python3 scripts/mcp_search_router.py --query "team structure and roles" --context
```

**Returns:** Formatted text ready to paste into Claude

### 4. Start search server

```bash
.venv/bin/python3 scripts/mcp_search_router.py --serve --port 8000
```

Then in another terminal:
```bash
curl "http://127.0.0.1:8000/search?q=architecture&limit=5" | jq .
```

## Files & Architecture

```
scripts/
├── vectordb_provider.py       # Abstract provider + ChromaDB implementation
├── index_workspace.py          # Indexing CLI with file discovery
├── mcp_search_router.py        # Search interface & HTTP server
├── mcp_tool_adapter.py         # MCP tool integration layer
├── examples.py                 # Usage examples
└── test_indexing.py            # 21 comprehensive unit tests (all passing)

.chroma/                         # ChromaDB persistent storage (created on first index)
INDEXING.md                      # Detailed documentation
requirements.txt                 # Python dependencies (chromadb, requests)
```

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│           Application Layer (MCP / CLI / HTTP)              │
├─────────────────────────────────────────────────────────────┤
│  mcp_tool_adapter.py       │  mcp_search_router.py         │
│  (MCP integration)         │  (Search interface + HTTP)     │
├─────────────────────────────────────────────────────────────┤
│  SearchRouter              (Common interface)               │
├─────────────────────────────────────────────────────────────┤
│          VectorDBProvider (Abstract Base Class)             │
├──────────────────────┬──────────────────────────────────────┤
│  ChromaDBProvider    │  [Extensible to other providers]    │
│  (Local embeddings)  │  OpenAI, Pinecone, Weaviate, etc.   │
└──────────────────────┴──────────────────────────────────────┘
```

## Command Reference

### Indexing

**Index workspace:**
```bash
.venv/bin/python3 scripts/index_workspace.py \
  --workspace . \
  --db-path .chroma \
  --collection workspace
```

**Re-index (clear and re-populate):**
```bash
.venv/bin/python3 scripts/index_workspace.py --clear --workspace .
```

**Index specific subdirectory:**
```bash
.venv/bin/python3 scripts/index_workspace.py --workspace ./Projects
```

### Searching

**Simple search:**
```bash
.venv/bin/python3 scripts/mcp_search_router.py \
  --query "your search terms" \
  --limit 10
```

**With similarity threshold:**
```bash
.venv/bin/python3 scripts/mcp_search_router.py \
  --query "search terms" \
  --threshold 0.5  # Only return results with >50% similarity
```

**LLM-formatted context:**
```bash
.venv/bin/python3 scripts/mcp_search_router.py \
  --query "search terms" \
  --context \
  --limit 5
```

**Get stats:**
```bash
.venv/bin/python3 scripts/mcp_search_router.py --stats
```

### HTTP Server

**Start server:**
```bash
.venv/bin/python3 scripts/mcp_search_router.py --serve --port 8000
```

**Endpoints:**

- `GET /search?q=<query>&limit=10` — Search results (JSON)
- `GET /context?q=<query>&limit=3` — LLM context (plain text)
- `GET /stats` — Collection stats (JSON)
- `POST /search` — Search (JSON body)
- `POST /context` — Context (JSON body)

**Example requests:**
```bash
# Search for files about Kubernetes
curl "http://localhost:8000/search?q=kubernetes&limit=5"

# Get LLM context for a topic
curl "http://localhost:8000/context?q=gpu+architecture"

# Get statistics
curl "http://localhost:8000/stats"
```

### Running Tests

```bash
# All tests
.venv/bin/python3 -m pytest scripts/test_indexing.py -v

# Specific test class
.venv/bin/pytest scripts/test_indexing.py::TestChromatDBProvider -v

# With coverage
.venv/bin/pytest scripts/test_indexing.py --cov=scripts --cov-report=html
```

## MCP Integration

### Option 1: Expose as MCP Tools

Use `mcp_tool_adapter.py` to create MCP tool handlers:

```python
from mcp_tool_adapter import MCPSearchAdapter, MCP_TOOLS

# Initialize adapter
adapter = MCPSearchAdapter(db_path=".chroma", collection="workspace")

# Tool definitions for MCP server
print(MCP_TOOLS)  # JSON schemas for "search_workspace", "get_workspace_context", etc.

# Handle tool calls
result = adapter.search(
    query="kubernetes deployment",
    limit=5,
    format="json"  # or "text"
)
```

### Option 2: Use HTTP Server (Remote Access)

```bash
# Terminal 1: Start server
.venv/bin/python3 scripts/mcp_search_router.py --serve --port 8000

# Terminal 2: Use with curl, Python, etc.
curl "http://localhost:8000/search?q=architecture&limit=5"
```

### Option 3: Direct Python API

```python
from mcp_search_router import SearchRouter
from vectordb_provider import get_provider

provider = get_provider("chromadb", {"db_path": ".chroma"})
router = SearchRouter(provider)

# Search
results = router.search("your query", limit=5)

# Get LLM context
context = router.get_context("your query", limit=3)

# Stats
stats = router.get_stats()
```

## Examples

### Run Built-in Examples

```bash
# Show basic indexing
.venv/bin/python3 scripts/examples.py index_basic

# Show search results
.venv/bin/python3 scripts/examples.py search_json

# Show LLM context formatting
.venv/bin/python3 scripts/examples.py llm_context

# Show MCP integration
.venv/bin/python3 scripts/examples.py mcp_integration

# Show HTTP server usage
.venv/bin/python3 scripts/examples.py http_server

# Show custom provider template
.venv/bin/python3 scripts/examples.py custom_provider
```

### Custom Provider Example

To add support for OpenAI embeddings, Pinecone, or another vector DB:

```python
from vectordb_provider import VectorDBProvider
from typing import Dict, Any, List, Optional

class OpenAIEmbeddingsProvider(VectorDBProvider):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        import openai
        openai.api_key = config.get("api_key")
        self.model = config.get("model", "text-embedding-3-small")
    
    def index_documents(self, documents: List[Dict[str, Any]], 
                       collection_name: str = "documents") -> int:
        # Your implementation here
        pass
    
    def search(self, query: str, collection_name: str = "documents",
              limit: int = 10, threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        # Your implementation here
        pass
    
    def clear_collection(self, collection_name: str = "documents") -> None:
        # Your implementation here
        pass
    
    def get_stats(self, collection_name: str = "documents") -> Dict[str, Any]:
        # Your implementation here
        pass
```

Then register in `vectordb_provider.py`:

```python
def get_provider(provider_name: str, config: Dict[str, Any]) -> VectorDBProvider:
    providers = {
        "chromadb": ChromaDBProvider,
        "openai": OpenAIEmbeddingsProvider,  # Add here
    }
    ...
```

## What Gets Indexed

### ✅ Included File Types
- `.md`, `.markdown` — Markdown documentation
- `.txt` — Text files
- `.py` — Python source code
- `.json`, `.yaml`, `.yml`, `.toml` — Configuration files
- `.csv`, `.sql`, `.sh`, `.bash` — Data and scripts

### ❌ Excluded File Types
- **Binaries:** `.pdf`, `.docx`, `.xlsx`, `.pptx`, `.exe`, `.dll`, `.so`, `.dylib`
- **Media:** `.png`, `.jpg`, `.jpeg`, `.gif`, `.svg`, `.mp3`, `.mp4`, `.mov`
- **Archives:** `.zip`, `.tar`, `.gz`
- **Compiled:** `.o`, `.a`, `.pyc`, `.so`

### ❌ Excluded Directories
- `Archives` — Project archives
- `.git` — Git metadata
- `.venv`, `venv` — Virtual environments
- `node_modules`, `__pycache__`, `.pytest_cache`
- `.DS_Store`, system files

## Performance & Tuning

### Indexing Large Workspaces

```bash
# Increase batch size (default 50)
.venv/bin/python3 scripts/index_workspace.py --batch-size 100
```

### Search Optimization

```bash
# Use similarity threshold to filter poor matches
.venv/bin/python3 scripts/mcp_search_router.py \
  --query "your search" \
  --threshold 0.5  # Only results >= 50% similar
```

### Database Maintenance

**Clear and re-index:**
```bash
.venv/bin/python3 scripts/index_workspace.py --clear --workspace .
```

**Backup database:**
```bash
cp -r .chroma .chroma.backup
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "No indexable files found" | Check that workspace path is correct; files may be too large or in excluded dirs |
| "Empty or no results" | Try broader search terms; lower `--threshold` to accept lower-similarity results |
| "Port 8000 already in use" | Use `--port 9000` or kill process on port 8000 |
| Slow search | Check if embeddings are being computed; first search is slower than subsequent |
| Collection "does not exist" | Run indexing first: `python3 scripts/index_workspace.py` |

## Dependencies

```
chromadb>=0.4.0      # Vector database
requests>=2.31.0     # HTTP client (for future remote providers)
python-dotenv>=1.0.0 # Environment configuration
pytest>=7.0          # Testing (dev only)
```

Installed via:
```bash
.venv/bin/pip install -r requirements.txt
```

## Testing

**Run all tests:**
```bash
.venv/bin/python3 -m pytest scripts/test_indexing.py -v
```

**Current status:** ✅ **21/21 tests passing**

- Provider abstraction tests
- ChromaDB implementation tests
- Search router tests
- MCP adapter tests
- Integration tests

## Future Enhancements

- [ ] OpenAI embeddings provider with cost tracking
- [ ] Pinecone serverless provider
- [ ] Hybrid search (BM25 + semantic)
- [ ] Query expansion & synonym support
- [ ] Document chunking strategies
- [ ] Cross-encoder re-ranking
- [ ] Web UI for search & management
- [ ] Scheduled incremental indexing
- [ ] Multi-language support

## Reference

- **[INDEXING.md](./INDEXING.md)** — Detailed documentation with provider architecture
- **[scripts/tests/test_indexing.py](../../../scripts/tests/test_indexing.py)** — Unit tests for the indexing pipeline

## License

Part of the MLaaS workspace. Use as-is for internal tooling.
