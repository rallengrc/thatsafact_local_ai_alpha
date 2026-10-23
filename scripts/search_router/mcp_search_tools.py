#!/usr/bin/env python3
"""
mcp_search_tools.py — Phase 3: MCP search tools exposing hybrid ripgrep + ChromaDB search.

Implements three MCP tools:
1. search_workspace — Hybrid search (ripgrep + semantic) with intelligent routing
2. search_code — Fast ripgrep-based code search with language filtering
3. search_semantic — Pure semantic search via ChromaDB

Replaces VS Code's broken semantic search with a unified hybrid approach.
"""

import json
import logging
import sys
import os
from typing import Dict, List, Any, Optional, Literal

_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_SCRIPTS_DIR = os.path.dirname(_CURRENT_DIR)
_INDEXING_DIR = os.path.join(_SCRIPTS_DIR, "indexing")
for _d in [_CURRENT_DIR, _INDEXING_DIR, _SCRIPTS_DIR]:
    if _d not in sys.path:
        sys.path.insert(0, _d)

try:
    from .search_router import UnifiedSearchRouter, QueryType
    from .livetext import RipgrepSearcher, SearchMatch
except ImportError:
    from search_router import UnifiedSearchRouter, QueryType
    from livetext import RipgrepSearcher, SearchMatch

from vectordb_provider import get_provider

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


class MCPSearchTools:
    """MCP-compatible search tools using hybrid ripgrep + semantic search."""

    def __init__(
        self,
        db_path: Any = ".chroma",
        collection: str = "workspace",
        provider_name: str = "chromadb",
        workspace_root: Optional[str] = None,
    ):
        """
        Initialize MCP search tools.

        Args:
            db_path: Path to vector database (or config dict).
            collection: Collection name to search.
            provider_name: Vector database provider name.
            workspace_root: Root directory for ripgrep searches (defaults to current dir).
        """
        if isinstance(db_path, dict):
            collection = db_path.get("collection_name", db_path.get("collection", collection))
            provider_name = db_path.get("provider_name", provider_name)
            db_path = db_path.get("db_path", ".chroma")

        self.db_path = db_path
        self.collection = collection
        self.provider_name = provider_name
        self.workspace_root = workspace_root or "."

        # Initialize components
        self.ripgrep = RipgrepSearcher(self.workspace_root)
        
        # UnifiedSearchRouter handles its own provider initialization
        self.router = UnifiedSearchRouter(
            workspace_root=self.workspace_root,
            chroma_db_path=self.db_path,
            collection_name=collection,
        )

        logger.info(
            f"MCPSearchTools initialized: ripgrep={self.ripgrep.rg_available}, "
            f"chromadb={provider_name}, workspace={self.workspace_root}"
        )

    def search_workspace(
        self,
        query: str,
        limit: int = 10,
        curate_for_llm: bool = True,
        language: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Hybrid search combining ripgrep + semantic search.

        This is the primary search tool that intelligently routes queries to the best
        search method(s). Replaces VS Code's semantic search which has known issues
        in large workspaces.

        Args:
            query: Search query (supports keywords, regexes, code patterns, natural language)
            limit: Maximum results to return
            curate_for_llm: Whether to optimize results for LLM context (default True)
            language: Optional language filter (python, javascript, rust, etc.)

        Returns:
            Dictionary with:
                - status: 'success' or 'error'
                - query: Original query
                - query_type: Detected type (KEYWORD, CODE, REGEX, SEMANTIC, HYBRID)
                - result_count: Number of results
                - results: List of search results
                - metadata: Curation info if curate_for_llm=True
        """
        try:
            if not query or not query.strip():
                return {
                    "status": "error",
                    "message": "Query cannot be empty",
                    "results": [],
                }

            # Analyze query to determine search strategy
            analysis = self.router.query_analyzer.analyze(query)
            logger.info(
                f"Query analysis: type={analysis.query_type}, "
                f"confidence={analysis.confidence:.2f}"
            )

            # If language specified, use ripgrep with language filter
            if language:
                file_types = self._get_file_types_for_language(language)
                results = self.ripgrep.search(
                    query, file_types=file_types, limit=limit
                )
                results = [self._search_match_to_dict(r) for r in results]
            else:
                # Use unified router for intelligent hybrid search
                results = self.router.search_hybrid(
                    query, limit=limit, curate_for_llm=curate_for_llm
                )
                # Convert SearchResult objects to dicts
                results = [r.to_dict() if hasattr(r, 'to_dict') else r for r in results]

            metadata = {}

            return {
                "status": "success",
                "query": query,
                "query_type": str(analysis.query_type.value),
                "routing_confidence": analysis.confidence,
                "result_count": len(results),
                "results": results,
                "metadata": metadata,
            }

        except Exception as e:
            logger.error(f"Hybrid search error: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "results": [],
            }

    def search_code(
        self,
        pattern: str,
        language: Optional[str] = None,
        limit: int = 20,
        context_lines: int = 3,
    ) -> Dict[str, Any]:
        """
        Fast ripgrep-based code search with language filtering.

        Optimized for finding code patterns, definitions, imports, and function calls.
        Use this when you need fast exact/regex matching without semantic analysis.

        Args:
            pattern: Search pattern (supports regex)
            language: Optional language filter (python, javascript, typescript, rust, go, etc.)
            limit: Maximum results
            context_lines: Lines of context before/after match

        Returns:
            Dictionary with:
                - status: 'success' or 'error'
                - pattern: Original pattern
                - language: Language filter used
                - result_count: Number of matches
                - results: List of matches with context
        """
        try:
            if not pattern or not pattern.strip():
                return {
                    "status": "error",
                    "message": "Pattern cannot be empty",
                    "results": [],
                }

            if not self.ripgrep.rg_available:
                return {
                    "status": "error",
                    "message": "ripgrep not available",
                    "results": [],
                }

            logger.info(
                f"Code search: pattern={pattern}, language={language}, limit={limit}"
            )

            file_types = None
            if language:
                file_types = self._get_file_types_for_language(language)

            results = self.ripgrep.search(
                pattern, file_types=file_types, limit=limit, context_lines=context_lines
            )

            return {
                "status": "success",
                "pattern": pattern,
                "language": language,
                "result_count": len(results),
                "results": [self._search_match_to_dict(r) for r in results],
            }

        except Exception as e:
            logger.error(f"Code search error: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "results": [],
            }

    def search_semantic(
        self,
        query: str,
        limit: int = 10,
        threshold: Optional[float] = 0.3,
    ) -> Dict[str, Any]:
        """
        Pure semantic search via ChromaDB.

        Use this for natural language queries where you want similarity-based matching
        without ripgrep's exact matching. Less effective in large workspaces than hybrid.

        Args:
            query: Natural language query
            limit: Maximum results
            threshold: Similarity threshold (0-1). Lower = more results but lower quality.

        Returns:
            Dictionary with:
                - status: 'success' or 'error'
                - query: Original query
                - result_count: Number of results
                - results: List of results with similarity scores
        """
        try:
            if not query or not query.strip():
                return {
                    "status": "error",
                    "message": "Query cannot be empty",
                    "results": [],
                }

            logger.info(f"Semantic search: query={query}, limit={limit}")

            results = self.router.semantic_provider.search(
                query,
                collection_name=self.collection,
                limit=limit,
                threshold=threshold,
            )

            # Normalize results format
            normalized = [
                {
                    "file": r.get("metadata", {}).get("path", "unknown"),
                    "line": r.get("metadata", {}).get("line_number", 0),
                    "content": r.get("text", ""),
                    "similarity": 1 - r.get("distance", 1),
                    "metadata": r.get("metadata", {}),
                }
                for r in results
            ]

            return {
                "status": "success",
                "query": query,
                "threshold": threshold,
                "result_count": len(normalized),
                "results": normalized,
            }

        except Exception as e:
            logger.error(f"Semantic search error: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "results": [],
            }

    def search_symbols(
        self,
        query: str,
        limit: int = 15,
        kind: Optional[str] = None,
        file_filter: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Search code symbols (classes, methods, functions) via Graphify AST."""
        try:
            if not query or not query.strip():
                return {"status": "error", "message": "Query cannot be empty", "results": []}

            logger.info(f"Symbol search: query={query}, kind={kind}, limit={limit}")
            results = self.router.search_symbols(
                query=query, limit=limit, kind=kind, file_filter=file_filter
            )
            return {
                "status": "success",
                "query": query,
                "kind": kind,
                "result_count": len(results),
                "results": [r.to_dict() for r in results],
            }
        except Exception as e:
            logger.error(f"Symbol search error: {e}", exc_info=True)
            return {"status": "error", "message": str(e), "results": []}

    def search_everything(
        self,
        query: str,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """Broad full-text search across all workspace files using Tantivy BM25."""
        try:
            if not query or not query.strip():
                return {"status": "error", "message": "Query cannot be empty", "results": []}

            logger.info(f"Broad everything search: query={query}, limit={limit}")
            results = self.router.search_everything(query=query, limit=limit)
            return {
                "status": "success",
                "query": query,
                "result_count": len(results),
                "results": [r.to_dict() for r in results],
            }
        except Exception as e:
            logger.error(f"Broad search error: {e}", exc_info=True)
            return {"status": "error", "message": str(e), "results": []}

    def _search_match_to_dict(self, match: SearchMatch) -> Dict[str, Any]:
        """Convert SearchMatch to dictionary format."""
        return {
            "file": match.path,
            "line": match.line_number,
            "content": match.content,
            "context_before": match.context_before,
            "context_after": match.context_after,
            "confidence": match.confidence,
            "type": match.match_type,
        }

    def _get_file_types_for_language(self, language: str) -> List[str]:
        """Convert language name to ripgrep file types."""
        language = language.lower().strip()
        language_map = {
            "python": ["py"],
            "javascript": ["js"],
            "typescript": ["ts", "tsx"],
            "rust": ["rs"],
            "go": ["go"],
            "c": ["c"],
            "cpp": ["cpp", "cc", "cxx", "h", "hpp"],
            "java": ["java"],
            "yaml": ["yaml", "yml"],
            "json": ["json"],
            "markdown": ["md", "markdown"],
            "shell": ["sh", "bash"],
        }
        return language_map.get(language, [language])

    def stats(self) -> Dict[str, Any]:
        """Get statistics about indexed workspace and search tools."""
        router_stats = self.router.get_router_stats()
        stats = {
            "tools": {
                "ripgrep_available": self.ripgrep.rg_available,
                "chromadb_available": True,
                "tantivy_available": router_stats.get("tantivy_available", False),
                "graphify_available": router_stats.get("graphify_available", False),
            },
            "database": {
                "path": self.db_path,
                "collection": self.collection,
                "provider": self.provider_name,
            },
        }

        try:
            provider_stats = self.router.semantic_provider.get_stats(self.collection)
            stats["database"]["stats"] = provider_stats
        except Exception as e:
            logger.warning(f"Could not get provider stats: {e}")
            stats["database"]["stats"] = {"error": str(e)}

        if "tantivy_stats" in router_stats:
            stats["tantivy"] = router_stats["tantivy_stats"]
        if "graphify_stats" in router_stats:
            stats["graphify"] = router_stats["graphify_stats"]

        return stats

        return stats


# MCP tool definitions
MCP_TOOLS = [
    {
        "name": "search_workspace",
        "description": (
            "Hybrid search using ripgrep + semantic search. Intelligently routes queries "
            "to the best search method(s). Replaces VS Code's broken semantic search. "
            "Supports keywords, regexes, code patterns, and natural language queries."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Search query. Can be: natural language (e.g., 'kubernetes setup'), "
                        "code pattern (e.g., 'def deploy'), regex (e.g., 'class.*Base'), "
                        "or keyword (e.g., 'docker')"
                    ),
                },
                "limit": {
                    "type": "integer",
                    "default": 10,
                    "description": "Maximum number of results to return",
                },
                "curate_for_llm": {
                    "type": "boolean",
                    "default": True,
                    "description": "Optimize results for LLM context window (deduplicate, rank, trim)",
                },
                "language": {
                    "type": "string",
                    "description": (
                        "Optional language filter: python, javascript, typescript, "
                        "rust, go, c, java, yaml, json, markdown, shell"
                    ),
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "search_code",
        "description": (
            "Fast ripgrep-based code search. Use for regex patterns, definitions, imports, "
            "and function calls. Returns exact matches with code context."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": (
                        "Search pattern (supports regex). Examples: "
                        "'def deploy', 'class.*Handler', 'import.*kubernetes'"
                    ),
                },
                "language": {
                    "type": "string",
                    "description": (
                        "Optional language filter: python, javascript, typescript, "
                        "rust, go, c, java, yaml, json, markdown, shell"
                    ),
                },
                "limit": {
                    "type": "integer",
                    "default": 20,
                    "description": "Maximum number of matches to return",
                },
                "context_lines": {
                    "type": "integer",
                    "default": 3,
                    "description": "Lines of context before/after each match",
                },
            },
            "required": ["pattern"],
        },
    },
    {
        "name": "search_semantic",
        "description": (
            "Pure semantic search using ChromaDB. Best for natural language similarity queries. "
            "Less effective in large workspaces than hybrid search."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language query (e.g., 'how to deploy to kubernetes')",
                },
                "limit": {
                    "type": "integer",
                    "default": 10,
                    "description": "Maximum number of results",
                },
                "threshold": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                    "default": 0.3,
                    "description": (
                        "Similarity threshold (0-1). Lower values return more results but "
                        "with lower quality matches."
                    ),
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "search_symbols",
        "description": (
            "AST-aware code symbol search powered by Graphify Tree-sitter parsers. "
            "Locates class, function, and method definitions with exact line coordinates and hierarchy."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Symbol name or pattern (e.g. 'UnifiedSearchRouter', 'parse_query')",
                },
                "kind": {
                    "type": "string",
                    "description": "Optional symbol kind: 'class', 'function', 'method'",
                },
                "limit": {
                    "type": "integer",
                    "default": 15,
                    "description": "Maximum number of symbols to return",
                },
                "file_filter": {
                    "type": "string",
                    "description": "Optional substring filter on file path",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "search_everything",
        "description": (
            "Broad full-text and boolean search across all workspace files, documents, and code "
            "using the Rust-powered Tantivy BM25 inverted index."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Full-text keywords or boolean expression across all files",
                },
                "limit": {
                    "type": "integer",
                    "default": 10,
                    "description": "Maximum number of results to return",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_search_stats",
        "description": "Get statistics about indexed workspace and available search tools",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]


def create_mcp_handlers(tools: MCPSearchTools) -> Dict[str, callable]:
    """Create MCP tool handler functions."""
    return {
        "search_workspace": lambda args: tools.search_workspace(
            query=args["query"],
            limit=args.get("limit", 10),
            curate_for_llm=args.get("curate_for_llm", True),
            language=args.get("language"),
        ),
        "search_code": lambda args: tools.search_code(
            pattern=args["pattern"],
            language=args.get("language"),
            limit=args.get("limit", 20),
            context_lines=args.get("context_lines", 3),
        ),
        "search_semantic": lambda args: tools.search_semantic(
            query=args["query"],
            limit=args.get("limit", 10),
            threshold=args.get("threshold", 0.3),
        ),
        "search_symbols": lambda args: tools.search_symbols(
            query=args["query"],
            limit=args.get("limit", 15),
            kind=args.get("kind"),
            file_filter=args.get("file_filter"),
        ),
        "search_everything": lambda args: tools.search_everything(
            query=args["query"],
            limit=args.get("limit", 10),
        ),
        "get_search_stats": lambda args: tools.stats(),
    }


if __name__ == "__main__":
    # Demo usage
    import argparse

    parser = argparse.ArgumentParser(description="MCP Search Tools Demo")
    parser.add_argument("--hybrid", type=str, help="Hybrid search query")
    parser.add_argument("--code", type=str, help="Code search pattern")
    parser.add_argument("--semantic", type=str, help="Semantic search query")
    parser.add_argument("--stats", action="store_true", help="Show stats")
    parser.add_argument("--language", type=str, help="Language filter")
    parser.add_argument("--limit", type=int, default=5, help="Result limit")

    args = parser.parse_args()

    tools = MCPSearchTools()

    if args.hybrid:
        result = tools.search_workspace(
            args.hybrid, limit=args.limit, language=args.language
        )
        print(json.dumps(result, indent=2, default=str))

    elif args.code:
        result = tools.search_code(
            args.code, language=args.language, limit=args.limit
        )
        print(json.dumps(result, indent=2, default=str))

    elif args.semantic:
        result = tools.search_semantic(args.semantic, limit=args.limit)
        print(json.dumps(result, indent=2, default=str))

    elif args.stats:
        result = tools.stats()
        print(json.dumps(result, indent=2, default=str))

    else:
        parser.print_help()
