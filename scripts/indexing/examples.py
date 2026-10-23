#!/usr/bin/env python3
"""
examples.py — Example usage patterns for the workspace indexing system.

Run individual examples to understand the API:
    python3 examples.py index_basic
    python3 examples.py search_json
    python3 examples.py llm_context
    python3 examples.py mcp_integration
"""

import sys
import os
from pathlib import Path
from pprint import pprint

_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_SCRIPTS_DIR = os.path.dirname(_CURRENT_DIR)
_SEARCH_DIR = os.path.join(_SCRIPTS_DIR, "search_router")
for _d in [_CURRENT_DIR, _SEARCH_DIR, _SCRIPTS_DIR]:
    if _d not in sys.path:
        sys.path.insert(0, _d)

from vectordb_provider import get_provider, ChromaDBProvider
from mcp_search_router import SearchRouter
from mcp_tool_adapter import MCPSearchAdapter


def example_index_basic():
    """Basic indexing example."""
    print("=" * 70)
    print("EXAMPLE 1: Basic Indexing")
    print("=" * 70)
    print()

    # Create a provider
    provider = ChromaDBProvider({"db_path": ".chroma"})

    # Create sample documents
    documents = [
        {
            "id": "doc1",
            "text": "Kubernetes is a container orchestration platform",
            "metadata": {"source": "example", "type": "technology"},
        },
        {
            "id": "doc2",
            "text": "Docker containers package applications for deployment",
            "metadata": {"source": "example", "type": "technology"},
        },
        {
            "id": "doc3",
            "text": "GPU clusters accelerate machine learning workloads",
            "metadata": {"source": "example", "type": "ml-infrastructure"},
        },
    ]

    # Index documents
    count = provider.index_documents(documents, collection_name="examples")
    print(f"✓ Indexed {count} documents into 'examples' collection")
    print()

    # Get stats
    stats = provider.get_stats("examples")
    print(f"✓ Collection stats: {stats}")
    print()


def example_search_json():
    """Search and return JSON results."""
    print("=" * 70)
    print("EXAMPLE 2: Search with JSON Results")
    print("=" * 70)
    print()

    provider = get_provider("chromadb", {"db_path": ".chroma"})
    router = SearchRouter(provider, collection_name="examples")

    # Search
    query = "container orchestration kubernetes"
    results = router.search(query, limit=3)

    print(f"Query: {query}")
    print()
    for i, result in enumerate(results, 1):
        print(f"  [{i}] {result['id']}")
        print(f"      Similarity: {result['similarity']:.3f}")
        print(f"      Text: {result['text'][:60]}...")
        print()


def example_llm_context():
    """Format results as LLM context."""
    print("=" * 70)
    print("EXAMPLE 3: LLM-Formatted Context")
    print("=" * 70)
    print()

    provider = get_provider("chromadb", {"db_path": ".chroma"})
    router = SearchRouter(provider, collection_name="examples")

    query = "machine learning GPU acceleration"
    context = router.get_context(query, limit=2)

    print(context)
    print()


def example_mcp_integration():
    """MCP tool adapter usage."""
    print("=" * 70)
    print("EXAMPLE 4: MCP Tool Adapter")
    print("=" * 70)
    print()

    adapter = MCPSearchAdapter(db_path=".chroma", collection="examples")

    # Example 1: Simple search
    print("4a. Simple search (JSON format):")
    result = adapter.search("kubernetes deployment", limit=2, format="json")
    print(result)
    print()

    # Example 2: Text format
    print("4b. Search (text format):")
    result = adapter.search("kubernetes deployment", limit=2, format="text")
    print(result)
    print()

    # Example 3: LLM context
    print("4c. LLM context:")
    result = adapter.context("machine learning", limit=2)
    print(result)
    print()

    # Example 4: Stats
    print("4d. Collection stats:")
    result = adapter.stats()
    print(result)
    print()


def example_mcp_tool_definitions():
    """Show MCP tool definitions for integration."""
    print("=" * 70)
    print("EXAMPLE 5: MCP Tool Definitions")
    print("=" * 70)
    print()

    from mcp_tool_adapter import MCP_TOOLS
    import json

    print("Available tools for MCP server:")
    print(json.dumps(MCP_TOOLS, indent=2))
    print()


def example_custom_provider():
    """Show how to create a custom provider."""
    print("=" * 70)
    print("EXAMPLE 6: Custom Vector DB Provider")
    print("=" * 70)
    print()

    code = '''
from vectordb_provider import VectorDBProvider
from typing import Dict, Any, List, Optional

class MyCustomProvider(VectorDBProvider):
    """Example custom vector database provider."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        # Initialize your custom vector DB client here
        self.documents = {}
    
    def index_documents(self, documents: List[Dict[str, Any]], 
                       collection_name: str = "documents") -> int:
        """Index documents (could call your custom DB API)."""
        for doc in documents:
            self.documents[doc["id"]] = doc
        return len(documents)
    
    def search(self, query: str, collection_name: str = "documents",
              limit: int = 10, threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """Search documents (could use your custom similarity function)."""
        # Implement your search logic here
        return list(self.documents.values())[:limit]
    
    def clear_collection(self, collection_name: str = "documents") -> None:
        """Clear all documents from collection."""
        self.documents.clear()
    
    def get_stats(self, collection_name: str = "documents") -> Dict[str, Any]:
        """Get collection statistics."""
        return {"document_count": len(self.documents)}

# Register in get_provider():
# In vectordb_provider.py, add to providers dict:
# "my-custom": MyCustomProvider,
'''

    print("Template for a custom provider:")
    print(code)
    print()


def example_http_server():
    """Show how to run HTTP server."""
    print("=" * 70)
    print("EXAMPLE 7: HTTP Server Integration")
    print("=" * 70)
    print()

    print("To start the HTTP server, run:")
    print()
    print("  .venv/bin/python3 scripts/mcp_search_router.py --serve --port 8000")
    print()
    print("Then use curl to test endpoints:")
    print()
    print("  # Search")
    print("  curl 'http://127.0.0.1:8000/search?q=kubernetes&limit=5'")
    print()
    print("  # Context for LLM")
    print("  curl 'http://127.0.0.1:8000/context?q=architecture&limit=3'")
    print()
    print("  # Stats")
    print("  curl 'http://127.0.0.1:8000/stats'")
    print()
    print("  # POST request (search with threshold)")
    print("  curl -X POST http://127.0.0.1:8000/search \\")
    print('    -H "Content-Type: application/json" \\')
    print('    -d \'{"query": "kubernetes", "limit": 5, "threshold": 0.3}\'')
    print()


def main():
    """Run examples."""
    if len(sys.argv) < 2:
        print("Usage: python3 examples.py <example_name>")
        print()
        print("Available examples:")
        print("  index_basic           — Basic document indexing")
        print("  search_json          — Search with JSON results")
        print("  llm_context          — Format results for LLM")
        print("  mcp_integration      — Use MCP tool adapter")
        print("  mcp_tool_definitions — Show MCP tool schemas")
        print("  custom_provider      — Create custom provider")
        print("  http_server          — HTTP server usage")
        print()
        print("Example: python3 examples.py search_json")
        sys.exit(1)

    example_name = sys.argv[1]

    examples = {
        "index_basic": example_index_basic,
        "search_json": example_search_json,
        "llm_context": example_llm_context,
        "mcp_integration": example_mcp_integration,
        "mcp_tool_definitions": example_mcp_tool_definitions,
        "custom_provider": example_custom_provider,
        "http_server": example_http_server,
    }

    if example_name not in examples:
        print(f"Unknown example: {example_name}")
        print(f"Available: {', '.join(examples.keys())}")
        sys.exit(1)

    examples[example_name]()


if __name__ == "__main__":
    main()
