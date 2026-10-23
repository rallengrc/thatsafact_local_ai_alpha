#!/usr/bin/env python3
"""
mcp_search_router.py — MCP-compatible search interface over indexed workspace.

Provides a simple HTTP/CLI interface to search the indexed workspace.
Can be extended to work as an MCP server tool.

Usage:
    python3 mcp_search_router.py --query "kubernetes deployment" --limit 5
    python3 mcp_search_router.py --serve  # Start HTTP server on port 8000
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_SCRIPTS_DIR = os.path.dirname(_CURRENT_DIR)
_INDEXING_DIR = os.path.join(_SCRIPTS_DIR, "indexing")
for _d in [_CURRENT_DIR, _INDEXING_DIR, _SCRIPTS_DIR]:
    if _d not in sys.path:
        sys.path.insert(0, _d)

from vectordb_provider import get_provider, VectorDBProvider

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


class SearchRouter:
    """Routes search queries to indexed workspace."""

    def __init__(self, provider: VectorDBProvider, collection_name: str = "workspace"):
        """
        Initialize search router.

        Args:
            provider: Vector database provider instance.
            collection_name: Name of the collection to search.
        """
        self.provider = provider
        self.collection_name = collection_name

    def search(
        self,
        query: str,
        limit: int = 10,
        threshold: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Search the indexed workspace.

        Args:
            query: Search query string.
            limit: Maximum number of results.
            threshold: Optional similarity threshold (0-1).

        Returns:
            Dictionary with search results and metadata.
        """
        if not query or not query.strip():
            return {
                "status": "error",
                "message": "Query cannot be empty",
                "results": [],
            }

        try:
            results = self.provider.search(
                query,
                collection_name=self.collection_name,
                limit=limit,
                threshold=threshold,
            )

            return {
                "status": "success",
                "query": query,
                "limit": limit,
                "threshold": threshold,
                "result_count": len(results),
                "results": results,
            }

        except Exception as e:
            logger.error(f"Search error: {e}")
            return {
                "status": "error",
                "message": str(e),
                "results": [],
            }

    def get_context(
        self,
        query: str,
        limit: int = 3,
        context_lines: int = 100,
    ) -> str:
        """
        Get formatted context for LLM based on search results.

        Args:
            query: Search query string.
            limit: Number of top results to include.
            context_lines: Lines of context per result.

        Returns:
            Formatted context string for LLM.
        """
        search_result = self.search(query, limit=limit)

        if search_result["status"] != "success" or not search_result["results"]:
            return f"No results found for query: {query}"

        context_parts = [f"Search Results for: {query}\n"]
        context_parts.append("=" * 60 + "\n")

        for i, result in enumerate(search_result["results"], 1):
            file_path = result["metadata"].get("path", "unknown")
            similarity = result.get("similarity", 0)

            context_parts.append(f"\n[{i}] {file_path} (similarity: {similarity:.3f})")
            context_parts.append("-" * 60)

            # Truncate content to context_lines
            lines = result["text"].split("\n")
            truncated = "\n".join(lines[:context_lines])
            if len(lines) > context_lines:
                truncated += f"\n... ({len(lines) - context_lines} more lines)"

            context_parts.append(truncated)

        return "\n".join(context_parts)

    def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics."""
        return self.provider.get_stats(self.collection_name)


class HTTPSearchServer:
    """Simple HTTP server for search interface."""

    def __init__(self, router: SearchRouter, host: str = "127.0.0.1", port: int = 8000):
        """
        Initialize HTTP server.

        Args:
            router: SearchRouter instance.
            host: Server host.
            port: Server port.
        """
        self.router = router
        self.host = host
        self.port = port

    def start(self):
        """Start HTTP server."""
        try:
            from http.server import HTTPServer, BaseHTTPRequestHandler
            import urllib.parse
        except ImportError:
            logger.error("HTTP server requires Python standard library (http.server)")
            return

        router = self.router

        class SearchHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                """Handle GET request."""
                parsed_path = urllib.parse.urlparse(self.path)
                query_params = urllib.parse.parse_qs(parsed_path.query)

                if parsed_path.path == "/search":
                    query = query_params.get("q", [""])[0]
                    limit = int(query_params.get("limit", [10])[0])
                    threshold = (
                        float(query_params.get("threshold", [None])[0])
                        if query_params.get("threshold", [None])[0]
                        else None
                    )

                    result = router.search(query, limit=limit, threshold=threshold)
                    self._send_json(result)

                elif parsed_path.path == "/context":
                    query = query_params.get("q", [""])[0]
                    limit = int(query_params.get("limit", [3])[0])
                    context = router.get_context(query, limit=limit)
                    self._send_json({"status": "success", "context": context})

                elif parsed_path.path == "/stats":
                    stats = router.get_stats()
                    self._send_json({"status": "success", "stats": stats})

                else:
                    self._send_json(
                        {
                            "status": "error",
                            "message": "Unknown endpoint",
                            "available": ["/search?q=...", "/context?q=...", "/stats"],
                        },
                        status=404,
                    )

            def do_POST(self):
                """Handle POST request."""
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length).decode("utf-8")

                try:
                    data = json.loads(body)
                except json.JSONDecodeError:
                    self._send_json(
                        {"status": "error", "message": "Invalid JSON"},
                        status=400,
                    )
                    return

                if self.path == "/search":
                    query = data.get("query", "")
                    limit = data.get("limit", 10)
                    threshold = data.get("threshold")
                    result = router.search(query, limit=limit, threshold=threshold)
                    self._send_json(result)

                elif self.path == "/context":
                    query = data.get("query", "")
                    limit = data.get("limit", 3)
                    context = router.get_context(query, limit=limit)
                    self._send_json({"status": "success", "context": context})

                else:
                    self._send_json(
                        {"status": "error", "message": "Unknown endpoint"},
                        status=404,
                    )

            def _send_json(self, data: Dict[str, Any], status: int = 200):
                """Send JSON response."""
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps(data, indent=2, default=str).encode())

            def log_message(self, format, *args):
                """Suppress default logging."""
                logger.debug(f"{self.address_string()} - {format % args}")

        try:
            server = HTTPServer((self.host, self.port), SearchHandler)
            logger.info(f"Search server running on http://{self.host}:{self.port}")
            logger.info("Endpoints: /search?q=... , /context?q=... , /stats")
            server.serve_forever()
        except KeyboardInterrupt:
            logger.info("Shutting down server")
        except OSError as e:
            logger.error(f"Failed to start server: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Search indexed workspace with optional HTTP server"
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=Path.cwd() / ".chroma",
        help="Database path (for chromadb)",
    )
    parser.add_argument(
        "--collection",
        type=str,
        default="workspace",
        help="Collection name",
    )
    parser.add_argument(
        "--query",
        type=str,
        help="Search query",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of results",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        help="Similarity threshold (0-1)",
    )
    parser.add_argument(
        "--context",
        action="store_true",
        help="Format results as LLM context",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Print collection stats",
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Start HTTP server",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="HTTP server host",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="HTTP server port",
    )

    args = parser.parse_args()

    # Initialize provider and router
    provider_config = {"db_path": str(args.db_path)}
    provider = get_provider("chromadb", provider_config)
    router = SearchRouter(provider, args.collection)

    # Handle stats mode
    if args.stats:
        stats = router.get_stats()
        print(json.dumps(stats, indent=2))
        return 0

    # Handle serve mode
    if args.serve:
        server = HTTPSearchServer(router, args.host, args.port)
        server.start()
        return 0

    # Handle query mode
    if args.query:
        if args.context:
            context = router.get_context(args.query, limit=args.limit)
            print(context)
        else:
            result = router.search(args.query, limit=args.limit, threshold=args.threshold)
            print(json.dumps(result, indent=2, default=str))
        return 0

    # Default: print help
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
