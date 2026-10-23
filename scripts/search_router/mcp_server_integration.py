#!/usr/bin/env python3
"""
mcp_server_integration.py — Example MCP server integration with workspace search.

Shows how to integrate the workspace search system as MCP tools in a Claude MCP server.

This is a template/documentation file showing three integration patterns.
Copy the relevant pattern into your MCP server implementation.
"""

# ============================================================================
# PATTERN 1: Direct Python Integration (Recommended for Embedded Use)
# ============================================================================

def pattern_1_direct_integration():
    """
    Best for: Running directly in an MCP server process.
    - No network overhead
    - Low latency
    - Easy debugging
    """
    from mcp_tool_adapter import MCPSearchAdapter, MCP_TOOLS

    # Initialize once at server startup
    adapter = MCPSearchAdapter(
        db_path=".chroma",
        collection="workspace",
        provider_name="chromadb",
    )

    # Define MCP tools (copy MCP_TOOLS from mcp_tool_adapter.py)
    tools = MCP_TOOLS

    # Handle tool calls
    def handle_search_workspace(arguments: dict) -> str:
        """Handle search_workspace MCP tool call."""
        query = arguments.get("query", "")
        limit = arguments.get("limit", 5)
        threshold = arguments.get("threshold")
        output_format = arguments.get("format", "json")

        return adapter.search(
            query=query,
            limit=limit,
            threshold=threshold,
            format=output_format,
        )

    def handle_get_workspace_context(arguments: dict) -> str:
        """Handle get_workspace_context MCP tool call."""
        query = arguments.get("query", "")
        limit = arguments.get("limit", 3)
        context_lines = arguments.get("context_lines", 100)

        return adapter.context(
            query=query,
            limit=limit,
            context_lines=context_lines,
        )

    def handle_get_workspace_stats(arguments: dict) -> str:
        """Handle get_workspace_stats MCP tool call."""
        return adapter.stats()

    # Register handlers in your MCP server
    tool_handlers = {
        "search_workspace": handle_search_workspace,
        "get_workspace_context": handle_get_workspace_context,
        "get_workspace_stats": handle_get_workspace_stats,
    }

    return {
        "tools": tools,
        "handlers": tool_handlers,
    }


# ============================================================================
# PATTERN 2: HTTP Server Integration (Best for Loose Coupling)
# ============================================================================

def pattern_2_http_integration():
    """
    Best for: Remote deployment, multiple consumers.
    - Runs search server separately
    - Multiple services can query it
    - Scalable deployment
    """
    import requests
    import json

    class WorkspaceSearchClient:
        """HTTP client for workspace search."""

        def __init__(self, base_url: str = "http://127.0.0.1:8000"):
            self.base_url = base_url

        def search(self, query: str, limit: int = 5, threshold: float = None) -> dict:
            """Search workspace."""
            params = {
                "q": query,
                "limit": limit,
            }
            if threshold is not None:
                params["threshold"] = threshold

            response = requests.get(f"{self.base_url}/search", params=params)
            return response.json()

        def context(self, query: str, limit: int = 3, context_lines: int = 100) -> str:
            """Get LLM-formatted context."""
            params = {
                "q": query,
                "limit": limit,
                "context_lines": context_lines,
            }
            response = requests.get(f"{self.base_url}/context", params=params)
            return response.text

        def stats(self) -> dict:
            """Get collection stats."""
            response = requests.get(f"{self.base_url}/stats")
            return response.json()

    # Usage in MCP server
    client = WorkspaceSearchClient()

    def handle_search_workspace(arguments: dict) -> str:
        """Handle search_workspace MCP tool call."""
        result = client.search(
            query=arguments.get("query", ""),
            limit=arguments.get("limit", 5),
            threshold=arguments.get("threshold"),
        )
        return json.dumps(result)

    def handle_get_workspace_context(arguments: dict) -> str:
        """Handle get_workspace_context MCP tool call."""
        return client.context(
            query=arguments.get("query", ""),
            limit=arguments.get("limit", 3),
            context_lines=arguments.get("context_lines", 100),
        )

    def handle_get_workspace_stats(arguments: dict) -> str:
        """Handle get_workspace_stats MCP tool call."""
        return json.dumps(client.stats())

    return {
        "client": client,
        "handlers": {
            "search_workspace": handle_search_workspace,
            "get_workspace_context": handle_get_workspace_context,
            "get_workspace_stats": handle_get_workspace_stats,
        },
    }


# ============================================================================
# PATTERN 3: Subprocess Integration (For Isolation)
# ============================================================================

def pattern_3_subprocess_integration():
    """
    Best for: Complete isolation, external process management.
    - Search runs as separate process
    - Can restart without stopping MCP server
    - Good for resource constraints
    """
    import subprocess
    import json
    import sys

    class WorkspaceSearchSubprocess:
        """Subprocess-based workspace search."""

        def __init__(self, db_path: str = ".chroma"):
            self.db_path = db_path

        def search(self, query: str, limit: int = 5, threshold: float = None) -> dict:
            """Search workspace via subprocess."""
            cmd = [
                sys.executable,
                "scripts/mcp_search_router.py",
                "--query",
                query,
                "--limit",
                str(limit),
            ]
            if threshold is not None:
                cmd.extend(["--threshold", str(threshold)])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
            )

            # Parse JSON output (skip INFO lines)
            lines = [
                line
                for line in result.stdout.split("\n")
                if not line.startswith("INFO:")
            ]
            json_str = "\n".join(lines)
            return json.loads(json_str)

        def context(
            self, query: str, limit: int = 3, context_lines: int = 100
        ) -> str:
            """Get LLM context via subprocess."""
            cmd = [
                sys.executable,
                "scripts/mcp_search_router.py",
                "--query",
                query,
                "--context",
                "--limit",
                str(limit),
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
            )
            # Filter out INFO lines
            lines = [line for line in result.stdout.split("\n") if not line.startswith("INFO:")]
            return "\n".join(lines)

        def stats(self) -> dict:
            """Get stats via subprocess."""
            cmd = [sys.executable, "scripts/mcp_search_router.py", "--stats"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
            )

            # Parse JSON output (skip INFO lines)
            lines = [
                line for line in result.stdout.split("\n") if not line.startswith("INFO:")
            ]
            json_str = "\n".join(lines)
            return json.loads(json_str)

    # Usage in MCP server
    search = WorkspaceSearchSubprocess()

    def handle_search_workspace(arguments: dict) -> str:
        """Handle search_workspace MCP tool call."""
        result = search.search(
            query=arguments.get("query", ""),
            limit=arguments.get("limit", 5),
            threshold=arguments.get("threshold"),
        )
        return json.dumps(result)

    def handle_get_workspace_context(arguments: dict) -> str:
        """Handle get_workspace_context MCP tool call."""
        return search.context(
            query=arguments.get("query", ""),
            limit=arguments.get("limit", 3),
            context_lines=arguments.get("context_lines", 100),
        )

    def handle_get_workspace_stats(arguments: dict) -> str:
        """Handle get_workspace_stats MCP tool call."""
        return json.dumps(search.stats())

    return {
        "search": search,
        "handlers": {
            "search_workspace": handle_search_workspace,
            "get_workspace_context": handle_get_workspace_context,
            "get_workspace_stats": handle_get_workspace_stats,
        },
    }


# ============================================================================
# USAGE IN YOUR MCP SERVER
# ============================================================================

if __name__ == "__main__":
    print("MCP Server Integration Patterns")
    print("=" * 70)
    print()

    print("PATTERN 1: Direct Python Integration")
    print("-" * 70)
    print(
        """
    Best for: Embedded in MCP server
    
    1. Copy MCP_TOOLS from mcp_tool_adapter.py
    2. Import MCPSearchAdapter
    3. Create handlers that call adapter methods
    4. Register in your MCP server
    
    See pattern_1_direct_integration() for full code.
    """
    )
    print()

    print("PATTERN 2: HTTP Server Integration")
    print("-" * 70)
    print(
        """
    Best for: Loose coupling, multiple consumers
    
    1. Start search server: python3 scripts/mcp_search_router.py --serve
    2. Create HTTP client
    3. Make requests to http://localhost:8000/search, etc.
    
    See pattern_2_http_integration() for full code.
    """
    )
    print()

    print("PATTERN 3: Subprocess Integration")
    print("-" * 70)
    print(
        """
    Best for: Complete isolation, external management
    
    1. Create subprocess wrapper
    2. Call scripts/mcp_search_router.py via subprocess
    3. Parse JSON output
    
    See pattern_3_subprocess_integration() for full code.
    """
    )
    print()

    print("RECOMMENDATION:")
    print("-" * 70)
    print(
        """
    Use Pattern 1 (Direct Integration) for most MCP servers.
    
    It's:
    - Simplest to implement
    - No network/IPC overhead
    - Easy to debug
    - Single process = no extra management
    
    Patterns 2 & 3 are for special cases (remote deployment, isolation, etc).
    """
    )
