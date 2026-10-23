#!/usr/bin/env python3
"""
mcp_tool_adapter.py — Adapt search router to MCP tool interface.

Provides a simple bridge between the SearchRouter and MCP tool handlers.
Can be embedded in an MCP server or used standalone.

Example usage in an MCP server:
    from mcp_tool_adapter import MCPSearchAdapter
    
    adapter = MCPSearchAdapter(db_path=".chroma", collection="workspace")
    
    # In your MCP tool handler:
    result = adapter.search(query="kubernetes", limit=5, format="json")
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, Literal, List, Optional, Union

_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_SCRIPTS_DIR = os.path.dirname(_CURRENT_DIR)
_INDEXING_DIR = os.path.join(_SCRIPTS_DIR, "indexing")
for _d in [_CURRENT_DIR, _INDEXING_DIR, _SCRIPTS_DIR]:
    if _d not in sys.path:
        sys.path.insert(0, _d)

try:
    from .mcp_search_router import SearchRouter
except ImportError:
    from mcp_search_router import SearchRouter
from vectordb_provider import get_provider


class MCPSearchAdapter:
    """Adapter for using SearchRouter as an MCP tool."""

    def __init__(
        self,
        db_path: Union[str, Dict[str, Any]] = ".chroma",
        collection: str = "workspace",
        provider_name: str = "chromadb",
    ):
        """
        Initialize MCP search adapter.

        Args:
            db_path: Path to vector database (or config dict).
            collection: Collection name to search.
            provider_name: Vector database provider name.
        """
        if isinstance(db_path, dict):
            provider_config = db_path
            collection = db_path.get("collection_name", db_path.get("collection", collection))
            provider_name = db_path.get("provider_name", provider_name)
        else:
            provider_config = {"db_path": db_path}
        provider = get_provider(provider_name, provider_config)
        self.router = SearchRouter(provider, collection)

    def search(
        self,
        query: str,
        limit: int = 10,
        threshold: Optional[float] = None,
        format: Literal["json", "text"] = "json",
    ) -> str:
        """
        Search workspace and return formatted results.

        Args:
            query: Search query.
            limit: Maximum number of results.
            threshold: Optional similarity threshold.
            format: Output format ('json' or 'text').

        Returns:
            Formatted search results.
        """
        result = self.router.search(query, limit=limit, threshold=threshold)

        if format == "text":
            return self._format_text(result)
        else:
            return json.dumps(result, indent=2, default=str)

    def context(
        self,
        query: str,
        limit: int = 3,
        context_lines: int = 100,
    ) -> str:
        """
        Get LLM-formatted context for a query.

        Args:
            query: Search query.
            limit: Number of top results.
            context_lines: Lines of context per result.

        Returns:
            Formatted context string for LLM.
        """
        return self.router.get_context(query, limit=limit, context_lines=context_lines)

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific document by ID (if supported by provider).

        Args:
            doc_id: Document ID (typically file path).

        Returns:
            Document data or None if not found.
        """
        # This is provider-specific; ChromaDB doesn't expose raw get easily
        # For now, search for the doc_id as a query
        results = self.router.provider.search(
            doc_id,
            collection_name=self.router.collection_name,
            limit=1,
        )
        return results[0] if results else None

    def stats(self) -> str:
        """Get collection statistics as JSON."""
        stats = self.router.get_stats()
        return json.dumps(stats, indent=2, default=str)

    def _format_text(self, search_result: Dict[str, Any]) -> str:
        """Format search results as plain text."""
        if search_result["status"] != "success":
            return f"Error: {search_result.get('message', 'Unknown error')}"

        lines = [
            f"Search: {search_result['query']} ({search_result['result_count']} results)",
            "",
        ]

        for i, result in enumerate(search_result["results"], 1):
            file_path = result["metadata"].get("path", "unknown")
            similarity = result.get("similarity", 0)
            lines.append(f"{i}. {file_path} ({similarity:.1%})")

        return "\n".join(lines)


# MCP tool definitions for integration
MCP_TOOLS = [
    {
        "name": "search_workspace",
        "description": "Search indexed workspace documents by semantic similarity",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (e.g., 'kubernetes deployment' or 'project architecture')",
                },
                "limit": {
                    "type": "integer",
                    "default": 5,
                    "description": "Maximum number of results to return",
                },
                "threshold": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                    "description": "Similarity threshold (0-1). Lower = more results but lower quality.",
                },
                "format": {
                    "type": "string",
                    "enum": ["json", "text"],
                    "default": "json",
                    "description": "Output format",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_workspace_context",
        "description": "Get workspace context formatted for LLM use",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query to find relevant context",
                },
                "limit": {
                    "type": "integer",
                    "default": 3,
                    "description": "Number of top results to include",
                },
                "context_lines": {
                    "type": "integer",
                    "default": 100,
                    "description": "Lines of content per document",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_workspace_stats",
        "description": "Get statistics about the indexed workspace",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]


def create_mcp_tool_handlers(adapter: MCPSearchAdapter) -> Dict[str, callable]:
    """
    Create MCP tool handler functions.

    Args:
        adapter: MCPSearchAdapter instance.

    Returns:
        Dictionary mapping tool names to handler functions.
    """
    handlers = {
        "search_workspace": lambda args: adapter.search(
            query=args["query"],
            limit=args.get("limit", 5),
            threshold=args.get("threshold"),
            format=args.get("format", "json"),
        ),
        "get_workspace_context": lambda args: adapter.context(
            query=args["query"],
            limit=args.get("limit", 3),
            context_lines=args.get("context_lines", 100),
        ),
        "get_workspace_stats": lambda args: adapter.stats(),
    }
    return handlers


if __name__ == "__main__":
    # Demo usage
    import sys

    if len(sys.argv) < 2:
        print("Usage: mcp_tool_adapter.py <query> [--context] [--limit N]")
        print("Example: mcp_tool_adapter.py 'kubernetes architecture' --limit 3")
        sys.exit(1)

    query = sys.argv[1]
    context_mode = "--context" in sys.argv
    limit_idx = None
    try:
        limit_idx = sys.argv.index("--limit")
        limit = int(sys.argv[limit_idx + 1])
    except (ValueError, IndexError):
        limit = 5

    adapter = MCPSearchAdapter()

    if context_mode:
        result = adapter.context(query, limit=limit)
    else:
        result = adapter.search(query, limit=limit, format="json")

    print(result)
