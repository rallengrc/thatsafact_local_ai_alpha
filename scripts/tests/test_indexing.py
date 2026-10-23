#!/usr/bin/env python3
"""
test_indexing.py — Unit tests for workspace indexing system.

Run with: python3 -m pytest scripts/test_indexing.py -v
Or: .venv/bin/python3 -m pytest scripts/test_indexing.py -v
"""

import sys
import os
import shutil
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, os.path.dirname(__file__))

_SCRIPTS_DIR = Path(__file__).resolve().parents[1]
_INDEXING_DIR = _SCRIPTS_DIR / "indexing"
for _p in [str(_SCRIPTS_DIR), str(_INDEXING_DIR)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import pytest
from vectordb_provider import ChromaDBProvider, VectorDBProvider, get_provider
from mcp_search_router import SearchRouter
from mcp_tool_adapter import MCPSearchAdapter, create_mcp_tool_handlers
from index_workspace import WorkspaceIndexer


class TestVectorDBProvider:
    """Tests for VectorDBProvider abstraction."""

    def test_get_provider_chromadb(self):
        """Test getting ChromaDB provider."""
        with tempfile.TemporaryDirectory() as tmpdir:
            provider = get_provider("chromadb", {"db_path": tmpdir})
            assert isinstance(provider, ChromaDBProvider)

    def test_get_provider_unknown(self):
        """Test getting unknown provider raises error."""
        with pytest.raises(ValueError, match="Unknown provider"):
            get_provider("unknown-db", {})


class TestChromatDBProvider:
    """Tests for ChromaDB provider implementation."""

    @pytest.fixture
    def provider(self):
        """Create temporary ChromaDB provider."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield ChromaDBProvider({"db_path": tmpdir})

    def test_index_documents(self, provider):
        """Test indexing documents."""
        docs = [
            {
                "id": "doc1",
                "text": "This is a test document",
                "metadata": {"source": "test"},
            },
            {
                "id": "doc2",
                "text": "Another test document",
                "metadata": {"source": "test"},
            },
        ]

        count = provider.index_documents(docs, "test-collection")
        assert count == 2

    def test_index_empty_list(self, provider):
        """Test indexing empty list."""
        count = provider.index_documents([], "test-collection")
        assert count == 0

    def test_search(self, provider):
        """Test searching documents."""
        docs = [
            {
                "id": "doc1",
                "text": "Kubernetes is a container orchestration platform",
                "metadata": {},
            },
            {
                "id": "doc2",
                "text": "Docker is a containerization platform",
                "metadata": {},
            },
        ]

        provider.index_documents(docs, "test-collection")

        results = provider.search(
            "kubernetes containers",
            collection_name="test-collection",
            limit=2,
        )

        assert len(results) > 0
        assert "id" in results[0]
        assert "text" in results[0]
        assert "similarity" in results[0]
        assert "metadata" in results[0]

    def test_search_with_threshold(self, provider):
        """Test searching with similarity threshold."""
        docs = [
            {
                "id": "doc1",
                "text": "Kubernetes is a container orchestration platform",
                "metadata": {},
            },
        ]

        provider.index_documents(docs, "test-collection")

        # High threshold should filter results
        results_high = provider.search(
            "unrelated query about pizza",
            collection_name="test-collection",
            limit=10,
            threshold=0.9,
        )

        # Low threshold should return results
        results_low = provider.search(
            "unrelated query about pizza",
            collection_name="test-collection",
            limit=10,
            threshold=0.1,
        )

        assert len(results_high) <= len(results_low)

    def test_clear_collection(self, provider):
        """Test clearing collection."""
        docs = [
            {"id": "doc1", "text": "Test", "metadata": {}},
        ]

        provider.index_documents(docs, "test-collection")
        stats_before = provider.get_stats("test-collection")
        assert stats_before["document_count"] == 1

        provider.clear_collection("test-collection")
        stats_after = provider.get_stats("test-collection")
        assert stats_after["document_count"] == 0

    def test_get_stats(self, provider):
        """Test getting collection statistics."""
        docs = [
            {"id": f"doc{i}", "text": f"Document {i}", "metadata": {}}
            for i in range(5)
        ]

        provider.index_documents(docs, "test-collection")
        stats = provider.get_stats("test-collection")

        assert "document_count" in stats
        assert stats["document_count"] == 5
        assert stats["collection_name"] == "test-collection"


class TestSearchRouter:
    """Tests for SearchRouter."""

    @pytest.fixture
    def router(self):
        """Create router with sample documents."""
        with tempfile.TemporaryDirectory() as tmpdir:
            provider = ChromaDBProvider({"db_path": tmpdir})

            docs = [
                {
                    "id": "doc1",
                    "text": "Kubernetes is a container orchestration platform",
                    "metadata": {"file_type": ".md", "path": "k8s.md"},
                },
                {
                    "id": "doc2",
                    "text": "Docker is a containerization platform",
                    "metadata": {"file_type": ".md", "path": "docker.md"},
                },
                {
                    "id": "doc3",
                    "text": "Python is a programming language",
                    "metadata": {"file_type": ".py", "path": "code.py"},
                },
            ]

            provider.index_documents(docs, "test-collection")
            yield SearchRouter(provider, "test-collection")

    def test_search(self, router):
        """Test search functionality."""
        result = router.search("kubernetes containers", limit=2)

        assert result["status"] == "success"
        assert result["query"] == "kubernetes containers"
        assert result["result_count"] >= 1

    def test_search_empty_query(self, router):
        """Test search with empty query."""
        result = router.search("", limit=2)
        assert result["status"] == "error"
        assert result["results"] == []

    def test_get_context(self, router):
        """Test context formatting for LLM."""
        context = router.get_context("kubernetes", limit=2, context_lines=10)

        assert isinstance(context, str)
        assert "kubernetes" in context.lower()

    def test_get_stats(self, router):
        """Test getting stats."""
        stats = router.get_stats()
        assert "document_count" in stats
        assert stats["document_count"] == 3


class TestMCPToolAdapter:
    """Tests for MCP tool adapter."""

    @pytest.fixture
    def adapter(self):
        """Create adapter with sample documents."""
        with tempfile.TemporaryDirectory() as tmpdir:
            provider = ChromaDBProvider({"db_path": tmpdir})

            docs = [
                {
                    "id": "doc1",
                    "text": "Kubernetes deployment on AWS",
                    "metadata": {"source": "test"},
                },
                {
                    "id": "doc2",
                    "text": "GPU clusters for machine learning",
                    "metadata": {"source": "test"},
                },
            ]

            provider.index_documents(docs, "test-collection")
            adapter = MCPSearchAdapter(
                db_path=tmpdir,
                collection="test-collection",
            )
            yield adapter

    def test_search_json(self, adapter):
        """Test search with JSON output."""
        result = adapter.search("kubernetes", limit=2, format="json")
        parsed = json.loads(result)

        assert parsed["status"] == "success"
        assert "results" in parsed

    def test_search_text(self, adapter):
        """Test search with text output."""
        result = adapter.search("kubernetes", limit=2, format="text")
        assert isinstance(result, str)
        assert "kubernetes" in result.lower() or "Search" in result

    def test_context(self, adapter):
        """Test context formatting."""
        context = adapter.context("kubernetes", limit=2)
        assert isinstance(context, str)
        assert len(context) > 0

    def test_stats(self, adapter):
        """Test stats output."""
        stats_str = adapter.stats()
        stats = json.loads(stats_str)

        assert "document_count" in stats
        assert stats["document_count"] == 2


class TestMCPToolDefinitions:
    """Tests for MCP tool definitions."""

    def test_tool_definitions_exist(self):
        """Test that MCP tool definitions are valid."""
        from mcp_tool_adapter import MCP_TOOLS

        assert isinstance(MCP_TOOLS, list)
        assert len(MCP_TOOLS) >= 3

    def test_tool_definitions_schema(self):
        """Test that each tool has required fields."""
        from mcp_tool_adapter import MCP_TOOLS

        required_fields = {"name", "description", "inputSchema"}

        for tool in MCP_TOOLS:
            for field in required_fields:
                assert field in tool, f"Missing field '{field}' in tool"


class TestMCPToolHandlers:
    """Tests for MCP tool handler creation."""

    def test_create_handlers(self):
        """Test creating MCP tool handlers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            provider = ChromaDBProvider({"db_path": tmpdir})
            adapter = MCPSearchAdapter(db_path=tmpdir)

            handlers = create_mcp_tool_handlers(adapter)

            assert "search_workspace" in handlers
            assert "get_workspace_context" in handlers
            assert "get_workspace_stats" in handlers

    def test_handler_callable(self):
        """Test that handlers are callable."""
        with tempfile.TemporaryDirectory() as tmpdir:
            adapter = MCPSearchAdapter(db_path=tmpdir)
            handlers = create_mcp_tool_handlers(adapter)

            # All handlers should be callable
            for handler in handlers.values():
                assert callable(handler)


class TestIntegration:
    """Integration tests."""

    def test_end_to_end_workflow(self):
        """Test complete indexing and search workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Step 1: Create provider
            provider = get_provider("chromadb", {"db_path": tmpdir})

            # Step 2: Index documents
            docs = [
                {
                    "id": "guide1",
                    "text": "Kubernetes beginner guide for cloud deployment",
                    "metadata": {"type": "tutorial"},
                },
                {
                    "id": "guide2",
                    "text": "Advanced GPU cluster optimization techniques",
                    "metadata": {"type": "tutorial"},
                },
                {
                    "id": "guide3",
                    "text": "Python programming best practices",
                    "metadata": {"type": "tutorial"},
                },
            ]

            count = provider.index_documents(docs, "guides")
            assert count == 3

            # Step 3: Search
            router = SearchRouter(provider, "guides")
            results = router.search("kubernetes cloud", limit=2)

            assert results["status"] == "success"
            assert len(results["results"]) > 0

            # Step 4: Get context
            context = router.get_context("kubernetes", limit=1)
            assert "kubernetes" in context.lower()

            # Step 5: Get stats
            stats = router.get_stats()
            assert stats["document_count"] == 3


class TestPosixPathInvariance:
    """Tests for POSIX path invariance across indexing components."""

    def test_workspace_indexer_collect_files_posix(self):
        """Test that WorkspaceIndexer produces POSIX-style relative paths."""
        scratch = Path("./.scratch_test_indexing")
        try:
            test_file = scratch / "nested" / "subfolder" / "doc.md"
            test_file.parent.mkdir(parents=True, exist_ok=True)
            test_file.write_text("# Hello POSIX\n", encoding="utf-8")

            indexer = WorkspaceIndexer(workspace_root=scratch, provider=MagicMock())
            files = indexer.collect_files()

            assert len(files) == 1
            assert files[0].relative_path == "nested/subfolder/doc.md"
            assert "\\" not in files[0].relative_path
        finally:
            if scratch.exists():
                shutil.rmtree(scratch, ignore_errors=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
