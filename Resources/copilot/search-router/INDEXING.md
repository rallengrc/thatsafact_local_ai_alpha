---
title: 'Technical Architecture: Workspace Indexing System'
description: Technical specification of the document discovery, vector embedding, and ChromaDB indexing pipeline
keywords:
- indexing architecture
- ChromaDB
- embeddings
- vector database
- batch processing
category: architecture
classification: 🟢🛡️ General
last_updated: '2026-10-11'
author: thatsafact
ai_search_aliases:
- indexing architecture
- chromadb architecture
- vector indexing system
---

# Workspace Indexing & MCP Search Router

> **TL;DR:** Deep dive into the workspace indexing pipeline: recursive file scanning, exclusion filtering, embedding generation, and ChromaDB persistence.
> **Use this for:** Understanding the document indexing internals and vector database provider interface.

A pluggable vector database indexing system for your workspace, designed to seed an MCP search router. Supports multiple vector database providers (chromadb by default, extensible to OpenAI embeddings, Pinecone, etc.).

## Overview

This system provides:

1. **`vectordb_provider.py`** — Abstract base class for vector database providers
   - Currently implements: `ChromaDBProvider` (local, persistent embeddings)
   - Extensible for: OpenAI embeddings, Pinecone, Weaviate, etc.

2. **`index_workspace.py`** — Workspace indexing script
   - Recursively indexes text files (excludes Archives, binaries, large files)
   - Batch processing with configurable collection names
   - CLI with stats, clear, and test-search options

3. **`mcp_search_router.py`** — Search interface & HTTP server
   - Query the indexed workspace
   - Format results as LLM context
   - Optional HTTP server for integration with MCP servers
   - Pluggable into Claude MCP tools

## Quick Start

### 1. Install Dependencies

```bash
.venv/bin/pip install -r requirements.txt
```

### 2. Index Your Workspace

```bash
.venv/bin/python3 scripts/index_workspace.py \
  --workspace . \
  --db-path .chroma \
  --collection workspace
```

**Output:**
```
INFO: Found 45 files to index
INFO: Indexed 45 documents into 'workspace'
{
  "status": "success",
  "indexed": 45,
  "skipped": 0,
  "errors": 0,
  "stats": {
    "document_count": 45,
    "collection_name": "workspace"
  }
}
```

### 3. Search the Index

**Simple search:**
```bash
.venv/bin/python3 scripts/mcp_search_router.py \
  --query "kubernetes deployment GPU" \
  --limit 5
```

**LLM-formatted context:**
```bash
.venv/bin/python3 scripts/mcp_search_router.py \
  --query "kubernetes deployment GPU" \
  --limit 3 \
  --context
```

**View collection stats:**
```bash
.venv/bin/python3 scripts/mcp_search_router.py --stats
```

### 4. Start HTTP Server (Optional)

```bash
.venv/bin/python3 scripts/mcp_search_router.py --serve --port 8000
```

**Available endpoints:**
- `GET /search?q=<query>&limit=10` — Search results as JSON
- `GET /context?q=<query>&limit=3` — Formatted LLM context
- `GET /stats` — Collection statistics
- `POST /search` / `POST /context` — JSON request body

**Example:**
```bash
curl "http://127.0.0.1:8000/search?q=architecture&limit=3" | jq '.results[] | {id, similarity}'
```

## Indexing Configuration

### What Gets Indexed

**Included file types:**
- `.md`, `.markdown` — Markdown documentation
- `.txt` — Text files
- `.py` — Python code
- `.json`, `.yaml`, `.yml`, `.toml` — Configuration files
- `.csv`, `.sql`, `.sh`, `.bash` — Data & scripts

**Excluded file types:**
- Binary/media: `.pdf`, `.docx`, `.xlsx`, `.png`, `.jpg`, `.mp4`, etc.
- Archives: `.zip`, `.tar`, `.gz`
- Compiled: `.exe`, `.dll`, `.so`, `.dylib`

**Excluded directories:**
- `Archives` — Project archives
- `.git` — Git metadata
- `.venv` / `venv` — Virtual environments
- `node_modules`, `__pycache__`, `.pytest_cache`
- `.DS_Store` — macOS system files

### Custom Indexing

**Re-index with a different collection:**
```bash
.venv/bin/python3 scripts/index_workspace.py \
  --collection my-docs \
  --batch-size 100
```

**Clear and re-index:**
```bash
.venv/bin/python3 scripts/index_workspace.py \
  --clear \
  --workspace .
```

**Index specific subdirectory:**
```bash
.venv/bin/python3 scripts/index_workspace.py \
  --workspace ./Projects/Burstable\ MLaaS
```

## Provider Architecture

### Adding a New Vector Database Provider

Extend `VectorDBProvider` and implement these methods:

```python
from vectordb_provider import VectorDBProvider

class MyVectorDBProvider(VectorDBProvider):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        # Initialize your vector DB client
    
    def index_documents(self, documents: List[Dict[str, Any]], 
                       collection_name: str = "documents") -> int:
        # Add documents to the index
        pass
    
    def search(self, query: str, collection_name: str = "documents",
              limit: int = 10, threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        # Return list of {id, text, similarity, distance, metadata}
        pass
    
    def clear_collection(self, collection_name: str = "documents") -> None:
        # Remove all documents from collection
        pass
    
    def get_stats(self, collection_name: str = "documents") -> Dict[str, Any]:
        # Return {document_count, ...}
        pass
```

Register in `get_provider()` factory:

```python
def get_provider(provider_name: str, config: Dict[str, Any]) -> VectorDBProvider:
    providers = {
        "chromadb": ChromaDBProvider,
        "my-vectordb": MyVectorDBProvider,  # Add here
    }
    ...
```

### Example: OpenAI Embeddings Provider

```python
class OpenAIEmbeddingsProvider(VectorDBProvider):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        import openai
        openai.api_key = config.get("api_key")
        self.model = config.get("model", "text-embedding-3-small")
        self.documents = {}  # In-memory store
    
    def index_documents(self, documents, collection_name="documents"):
        import openai
        for doc in documents:
            embedding = openai.Embedding.create(
                input=doc["text"],
                model=self.model
            )["data"][0]["embedding"]
            self.documents[doc["id"]] = {
                "text": doc["text"],
                "embedding": embedding,
                "metadata": doc.get("metadata", {})
            }
        return len(documents)
    
    def search(self, query, collection_name="documents", limit=10, threshold=None):
        import openai
        from scipy.spatial.distance import cosine
        
        query_embedding = openai.Embedding.create(
            input=query,
            model=self.model
        )["data"][0]["embedding"]
        
        results = []
        for doc_id, doc_data in self.documents.items():
            similarity = 1 - cosine(query_embedding, doc_data["embedding"])
            if threshold is None or similarity >= threshold:
                results.append({
                    "id": doc_id,
                    "text": doc_data["text"],
                    "similarity": similarity,
                    "metadata": doc_data["metadata"]
                })
        
        return sorted(results, key=lambda x: x["similarity"], reverse=True)[:limit]
```

## MCP Integration

### Using as an MCP Tool

Create an MCP tool definition to expose search to Claude:

```json
{
  "name": "search_workspace",
  "description": "Search indexed workspace documents",
  "inputSchema": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "Search query"
      },
      "limit": {
        "type": "integer",
        "default": 5,
        "description": "Max results"
      },
      "context": {
        "type": "boolean",
        "default": false,
        "description": "Format as LLM context"
      }
    },
    "required": ["query"]
  }
}
```

**Handler:**
```python
from mcp_search_router import SearchRouter
from vectordb_provider import get_provider

provider = get_provider("chromadb", {"db_path": ".chroma"})
router = SearchRouter(provider)

def handle_search_workspace(query: str, limit: int = 5, context: bool = False):
    if context:
        return router.get_context(query, limit=limit)
    else:
        return router.search(query, limit=limit)
```

## Performance Tuning

### Indexing Large Workspaces

- **Batch size:** Increase `--batch-size` for faster indexing (default 50)
- **Max file size:** Edit `_read_file_safely()` to increase limit (default 1 MB)
- **Skip large files:** Use glob patterns or modify `SKIP_DIRECTORIES`

### Search Optimization

- **Similarity threshold:** Use `--threshold 0.5` to filter poor matches
- **Collection names:** Separate concerns with multiple collections (e.g., `workspace`, `docs`, `code`)
- **Result limit:** Lower `--limit` for faster responses (default 10)

### Database Maintenance

**Re-index periodically:**
```bash
.venv/bin/python3 scripts/index_workspace.py --clear --workspace .
```

**Backup ChromaDB:**
```bash
cp -r .chroma .chroma.backup
```

## Troubleshooting

### "Collection does not exist"
Your workspace hasn't been indexed yet. Run:
```bash
.venv/bin/python3 scripts/index_workspace.py
```

### "Empty or no results"
- Check query for typos
- Try broader search terms
- Verify files were indexed with `--stats`
- Lower `--threshold` to accept lower-similarity results

### Slow indexing
- Increase `--batch-size` (e.g., 100)
- Exclude more directories
- Check disk I/O and free space

### HTTP server won't start
- Port 8000 already in use: use `--port 9000`
- Host binding issue: try `--host 0.0.0.0` (if on trusted network)

## Files

- **`vectordb_provider.py`** — Provider abstraction & ChromaDB implementation
- **`index_workspace.py`** — Workspace indexing CLI
- **`mcp_search_router.py`** — Search router & HTTP server
- **`.chroma/`** — ChromaDB persistent storage (created on first run)
- **`requirements.txt`** — Python dependencies

## Future Enhancements

- [ ] Support for OpenAI embeddings (with cost tracking)
- [ ] Pinecone provider (serverless vector DB)
- [ ] Weaviate provider (self-hosted)
- [ ] Hybrid search (BM25 + semantic)
- [ ] Query expansion & synonyms
- [ ] Document chunking strategies (currently full-text)
- [ ] Re-ranking with cross-encoders
- [ ] Web UI for search & management
- [ ] Scheduled incremental indexing
- [ ] Multi-language support

## License

Part of the MLaaS workspace. Use as-is for internal tooling.
