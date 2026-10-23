#!/usr/bin/env python3
"""
test_mcp_search_tools.py — Comprehensive tests for MCP search tools (Phase 3).

Tests cover:
- Hybrid search with intelligent routing
- Code search with language filtering
- Semantic search with similarity threshold
- Statistics and metadata
- Error handling and edge cases
"""

import unittest
from unittest.mock import MagicMock, patch, PropertyMock
import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from mcp_search_tools import MCPSearchTools, MCP_TOOLS, create_mcp_handlers
from livetext import SearchMatch


class TestMCPSearchToolsHybridSearch(unittest.TestCase):
    """Test hybrid search_workspace tool."""

    def setUp(self):
        """Set up test fixtures."""
        self.tools = MCPSearchTools()

    def test_hybrid_search_empty_query(self):
        """Test hybrid search with empty query."""
        result = self.tools.search_workspace("")
        assert result["status"] == "error"
        assert "empty" in result["message"].lower()

    def test_hybrid_search_none_query(self):
        """Test hybrid search with None query."""
        result = self.tools.search_workspace(None)
        assert result["status"] == "error"

    @patch("mcp_search_tools.UnifiedSearchRouter")
    def test_hybrid_search_success(self, mock_router_class):
        """Test successful hybrid search."""
        mock_router = MagicMock()
        mock_router_class.return_value = mock_router
        mock_router.search_hybrid.return_value = [
            {
                "file": "app.py",
                "line": 42,
                "content": "def deploy():",
                "confidence": 0.95,
            },
        ]
        mock_router.query_analyzer.analyze.return_value = MagicMock(
            query_type=MagicMock(value="code"),
            confidence=0.9,
        )

        tools = MCPSearchTools()
        result = tools.search_workspace("def deploy", limit=5)

        assert result["status"] == "success"
        assert result["query"] == "def deploy"
        assert result["result_count"] == 1

    @patch("mcp_search_tools.RipgrepSearcher")
    @patch("mcp_search_tools.UnifiedSearchRouter")
    def test_hybrid_search_with_language_filter(self, mock_router_class, mock_searcher_class):
        """Test hybrid search with language filter."""
        mock_searcher = MagicMock()
        mock_searcher.search.return_value = [
            SearchMatch(
                id="app.py:42",
                path="app.py",
                line_number=42,
                content="def deploy():",
                context_before=[],
                context_after=[],
                confidence=0.95,
            ),
        ]
        mock_searcher_class.return_value = mock_searcher

        mock_router = MagicMock()
        mock_router.query_analyzer.analyze.return_value = MagicMock(
            query_type=MagicMock(value="code"),
            confidence=0.9,
        )
        mock_router_class.return_value = mock_router

        tools = MCPSearchTools()
        tools.ripgrep = mock_searcher
        result = tools.search_workspace("deploy", language="python")

        assert result["status"] == "success"
        assert mock_searcher.search.called

    @patch("mcp_search_tools.UnifiedSearchRouter")
    def test_hybrid_search_with_llm_curation(self, mock_router_class):
        """Test hybrid search with LLM curation enabled."""
        from search_router import SearchResult

        mock_router = MagicMock()
        mock_router_class.return_value = mock_router
        # search_hybrid returns SearchResult objects
        mock_result = SearchResult(
            id="app.py:42",
            path="app.py",
            line_number=42,
            content="def deploy():",
            score=0.95,
            source="hybrid",
        )
        mock_router.search_hybrid.return_value = [mock_result]
        mock_router.query_analyzer.analyze.return_value = MagicMock(
            query_type=MagicMock(value="code"),
            confidence=0.9,
        )

        tools = MCPSearchTools()
        result = tools.search_workspace("deploy", curate_for_llm=True)

        assert result["status"] == "success"
        assert result["result_count"] == 1
        assert result["results"][0]["path"] == "app.py"

    @patch("mcp_search_tools.UnifiedSearchRouter")
    def test_hybrid_search_error_handling(self, mock_router_class):
        """Test hybrid search error handling."""
        mock_router = MagicMock()
        mock_router_class.return_value = mock_router
        mock_router.search_hybrid.side_effect = RuntimeError("Database error")
        mock_router.query_analyzer.analyze.side_effect = RuntimeError("Database error")

        tools = MCPSearchTools()
        result = tools.search_workspace("deploy")

        assert result["status"] == "error"
        assert "Database error" in result["message"]


class TestMCPSearchToolsCodeSearch(unittest.TestCase):
    """Test code search_code tool."""

    def setUp(self):
        """Set up test fixtures."""
        self.tools = MCPSearchTools()

    def test_code_search_empty_pattern(self):
        """Test code search with empty pattern."""
        result = self.tools.search_code("")
        assert result["status"] == "error"
        assert "empty" in result["message"].lower()

    def test_code_search_ripgrep_unavailable(self):
        """Test code search when ripgrep not available."""
        with patch.object(
            self.tools.ripgrep, "rg_available", False, create=True
        ):
            result = self.tools.search_code("def deploy")
            assert result["status"] == "error"
            assert "not available" in result["message"].lower()

    @patch("mcp_search_tools.RipgrepSearcher")
    def test_code_search_success(self, mock_searcher_class):
        """Test successful code search."""
        mock_searcher = MagicMock()
        mock_searcher.rg_available = True
        mock_searcher.search.return_value = [
            SearchMatch(
                id="app.py:42",
                path="app.py",
                line_number=42,
                content="def deploy(config):",
                context_before=["# deployment"],
                context_after=["    return True"],
                confidence=1.0,
            ),
            SearchMatch(
                id="utils.py:15",
                path="utils.py",
                line_number=15,
                content="def deploy_service():",
                context_before=[],
                context_after=["    pass"],
                confidence=1.0,
            ),
        ]
        mock_searcher_class.return_value = mock_searcher

        tools = MCPSearchTools()
        result = tools.search_code("def deploy", language="python", limit=20)

        assert result["status"] == "success"
        assert result["pattern"] == "def deploy"
        assert result["language"] == "python"
        assert result["result_count"] == 2
        assert result["results"][0]["file"] == "app.py"
        assert result["results"][0]["line"] == 42

    @patch("mcp_search_tools.RipgrepSearcher")
    def test_code_search_with_context(self, mock_searcher_class):
        """Test code search with context lines."""
        mock_searcher = MagicMock()
        mock_searcher.rg_available = True
        mock_searcher.search.return_value = [
            SearchMatch(
                id="app.py:42",
                path="app.py",
                line_number=42,
                content="def deploy(config):",
                context_before=["# deployment", "import kubernetes"],
                context_after=["    return True", "    log()"],
                confidence=1.0,
            ),
        ]
        mock_searcher_class.return_value = mock_searcher

        tools = MCPSearchTools()
        result = tools.search_code("deploy", context_lines=5)

        assert result["status"] == "success"
        assert len(result["results"][0]["context_before"]) > 0
        assert len(result["results"][0]["context_after"]) > 0

    @patch("mcp_search_tools.RipgrepSearcher")
    def test_code_search_error_handling(self, mock_searcher_class):
        """Test code search error handling."""
        mock_searcher = MagicMock()
        mock_searcher.rg_available = True
        mock_searcher.search.side_effect = Exception("Regex error")
        mock_searcher_class.return_value = mock_searcher

        tools = MCPSearchTools()
        result = tools.search_code("def [invalid")

        assert result["status"] == "error"
        assert "Regex error" in result["message"]


class TestMCPSearchToolsSemanticSearch(unittest.TestCase):
    """Test semantic search_semantic tool."""

    def setUp(self):
        """Set up test fixtures."""
        self.tools = MCPSearchTools()

    def test_semantic_search_empty_query(self):
        """Test semantic search with empty query."""
        result = self.tools.search_semantic("")
        assert result["status"] == "error"
        assert "empty" in result["message"].lower()

    @patch("mcp_search_tools.UnifiedSearchRouter")
    def test_semantic_search_success(self, mock_router_class):
        """Test successful semantic search."""
        mock_provider = MagicMock()
        mock_provider.search.return_value = [
            {
                "text": "def deploy kubernetes",
                "distance": 0.2,
                "metadata": {"path": "docs.md", "line_number": 10},
            },
            {
                "text": "deployment configuration",
                "distance": 0.3,
                "metadata": {"path": "config.yaml", "line_number": 25},
            },
        ]
        mock_router = MagicMock()
        mock_router.semantic_provider = mock_provider
        mock_router_class.return_value = mock_router

        tools = MCPSearchTools()
        result = tools.search_semantic("how to deploy", limit=5, threshold=0.5)

        assert result["status"] == "success"
        assert result["query"] == "how to deploy"
        assert result["result_count"] == 2
        assert result["threshold"] == 0.5

    @patch("mcp_search_tools.UnifiedSearchRouter")
    def test_semantic_search_similarity_score(self, mock_router_class):
        """Test semantic search converts distance to similarity."""
        mock_provider = MagicMock()
        mock_provider.search.return_value = [
            {
                "text": "deployment guide",
                "distance": 0.1,
                "metadata": {"path": "guide.md", "line_number": 5},
            },
        ]
        mock_router = MagicMock()
        mock_router.semantic_provider = mock_provider
        mock_router_class.return_value = mock_router

        tools = MCPSearchTools()
        result = tools.search_semantic("deployment")

        assert result["results"][0]["similarity"] == 0.9  # 1 - 0.1

    @patch("mcp_search_tools.UnifiedSearchRouter")
    def test_semantic_search_error_handling(self, mock_router_class):
        """Test semantic search error handling."""
        mock_provider = MagicMock()
        mock_provider.search.side_effect = ConnectionError("Database connection failed")
        mock_router = MagicMock()
        mock_router.semantic_provider = mock_provider
        mock_router_class.return_value = mock_router

        tools = MCPSearchTools()
        result = tools.search_semantic("query")

        assert result["status"] == "error"
        assert "connection" in result["message"].lower()


class TestMCPSearchToolsStats(unittest.TestCase):
    """Test statistics tool."""

    @patch("mcp_search_tools.UnifiedSearchRouter")
    def test_stats_success(self, mock_router_class):
        """Test stats retrieval."""
        mock_provider = MagicMock()
        mock_provider.get_stats.return_value = {
            "documents": 45,
            "collections": 1,
        }
        mock_router = MagicMock()
        mock_router.provider = mock_provider
        mock_router_class.return_value = mock_router

        tools = MCPSearchTools()
        stats = tools.stats()

        assert "tools" in stats
        assert "database" in stats
        assert stats["tools"]["ripgrep_available"] in (True, False)
        assert stats["database"]["provider"] == "chromadb"

    @patch("mcp_search_tools.UnifiedSearchRouter")
    def test_stats_provider_error(self, mock_router_class):
        """Test stats with provider error."""
        mock_provider = MagicMock()
        mock_provider.get_stats.side_effect = RuntimeError("Provider error")
        mock_router = MagicMock()
        mock_router.provider = mock_provider
        mock_router_class.return_value = mock_router

        tools = MCPSearchTools()
        stats = tools.stats()

        # Should still return stats structure even if provider fails
        assert "database" in stats
        assert "stats" in stats["database"]


class TestMCPToolsDefinitions(unittest.TestCase):
    """Test MCP tool definitions."""

    def test_mcp_tools_structure(self):
        """Test that MCP tools have correct structure."""
        assert len(MCP_TOOLS) >= 4

        tool_names = {tool["name"] for tool in MCP_TOOLS}
        assert "search_workspace" in tool_names
        assert "search_code" in tool_names
        assert "search_semantic" in tool_names
        assert "get_search_stats" in tool_names
        assert "search_symbols" in tool_names
        assert "search_everything" in tool_names

    def test_mcp_tools_have_descriptions(self):
        """Test all tools have descriptions."""
        for tool in MCP_TOOLS:
            assert "description" in tool
            assert len(tool["description"]) > 0

    def test_mcp_tools_have_schemas(self):
        """Test all tools have input schemas."""
        for tool in MCP_TOOLS:
            assert "inputSchema" in tool
            schema = tool["inputSchema"]
            assert schema["type"] == "object"
            assert "properties" in schema
            assert "required" in schema

    def test_search_workspace_schema(self):
        """Test search_workspace schema."""
        tool = next(t for t in MCP_TOOLS if t["name"] == "search_workspace")
        schema = tool["inputSchema"]

        assert "query" in schema["properties"]
        assert "query" in schema["required"]
        assert "limit" in schema["properties"]
        assert "curate_for_llm" in schema["properties"]
        assert "language" in schema["properties"]

    def test_search_code_schema(self):
        """Test search_code schema."""
        tool = next(t for t in MCP_TOOLS if t["name"] == "search_code")
        schema = tool["inputSchema"]

        assert "pattern" in schema["properties"]
        assert "pattern" in schema["required"]
        assert "language" in schema["properties"]
        assert "limit" in schema["properties"]

    def test_search_semantic_schema(self):
        """Test search_semantic schema."""
        tool = next(t for t in MCP_TOOLS if t["name"] == "search_semantic")
        schema = tool["inputSchema"]

        assert "query" in schema["properties"]
        assert "query" in schema["required"]
        assert "threshold" in schema["properties"]


class TestMCPHandlers(unittest.TestCase):
    """Test MCP handler creation and invocation."""

    @patch("mcp_search_tools.UnifiedSearchRouter")
    def test_create_handlers(self, mock_router_class):
        """Test creating MCP handlers."""
        tools = MCPSearchTools()
        handlers = create_mcp_handlers(tools)

        assert "search_workspace" in handlers
        assert "search_code" in handlers
        assert "search_semantic" in handlers
        assert "get_search_stats" in handlers

    @patch("mcp_search_tools.UnifiedSearchRouter")
    def test_handler_invocation(self, mock_router_class):
        """Test invoking handlers with arguments."""
        mock_router = MagicMock()
        mock_router.search_hybrid.return_value = []
        mock_router.query_analyzer.analyze.return_value = MagicMock(
            query_type=MagicMock(value="keyword"),
            confidence=0.8,
        )
        mock_router_class.return_value = mock_router

        tools = MCPSearchTools()
        handlers = create_mcp_handlers(tools)

        # Test search_workspace handler
        result = handlers["search_workspace"]({"query": "test", "limit": 5})
        assert "status" in result

    @patch("mcp_search_tools.RipgrepSearcher")
    @patch("mcp_search_tools.UnifiedSearchRouter")
    def test_handler_error_propagation(self, mock_router_class, mock_searcher_class):
        """Test that handler errors are caught and returned."""
        mock_searcher = MagicMock()
        mock_searcher.rg_available = True
        mock_searcher.search.side_effect = Exception("Search failed")
        mock_searcher_class.return_value = mock_searcher

        mock_router = MagicMock()
        mock_router_class.return_value = mock_router

        tools = MCPSearchTools()
        handlers = create_mcp_handlers(tools)

        result = handlers["search_code"]({"pattern": "test"})
        assert result["status"] == "error"


class TestMCPToolsIntegration(unittest.TestCase):
    """Integration tests for MCP tools."""

    @patch("mcp_search_tools.UnifiedSearchRouter")
    @patch("mcp_search_tools.RipgrepSearcher")
    def test_all_tools_initialize_cleanly(self, mock_searcher_class, mock_router_class):
        """Test that all tools initialize without errors."""
        mock_searcher = MagicMock()
        mock_searcher.rg_available = True
        mock_searcher_class.return_value = mock_searcher

        mock_router = MagicMock()
        mock_router_class.return_value = mock_router

        tools = MCPSearchTools(db_path=".chroma", collection="workspace")
        assert tools is not None
        assert tools.ripgrep is not None
        assert tools.router is not None

    @patch("mcp_search_tools.UnifiedSearchRouter")
    def test_result_formatting_consistency(self, mock_router_class):
        """Test that all search methods return consistent format."""
        mock_provider = MagicMock()
        mock_provider.search.return_value = []
        mock_router = MagicMock()
        mock_router.provider = mock_provider
        mock_router.search_hybrid.return_value = []
        mock_router.query_analyzer.analyze.return_value = MagicMock(
            query_type=MagicMock(value="semantic"),
            confidence=0.8,
        )
        mock_router_class.return_value = mock_router

        tools = MCPSearchTools()

        # All should return dicts with status, result_count, results
        hybrid = tools.search_workspace("test")
        semantic = tools.search_semantic("test")

        for result in [hybrid, semantic]:
            assert "status" in result
            assert "query" in result or "query" in result
            assert "result_count" in result
            assert "results" in result


if __name__ == "__main__":
    unittest.main()
