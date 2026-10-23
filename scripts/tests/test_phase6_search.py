#!/usr/bin/env python3
"""
test_phase6_search.py — Unit and integration tests for Phase 6 Multi-Index Expansion.

Tests cover:
- Tantivy BM25 inverted index searcher & indexer
- Graphify Tree-sitter AST symbol searcher & knowledge graph
- Local Ollama LLM enforcement (zero cloud spend)
- QueryIntentClassifier & Preprocessing
- Reciprocal Rank Fusion (RRF) & AST span deduplication
- UnifiedSearchRouter 4-engine integration
"""

import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_SCRIPTS_DIR = os.path.dirname(_CURRENT_DIR)
_ROUTER_DIR = os.path.join(_SCRIPTS_DIR, "search_router")
_INDEXING_DIR = os.path.join(_SCRIPTS_DIR, "indexing")
_REPO_ROOT = os.path.dirname(_SCRIPTS_DIR)
_GRAPHIFY_DIR = os.path.join(_REPO_ROOT, "code", "graphify")

for _d in [_CURRENT_DIR, _ROUTER_DIR, _INDEXING_DIR, _SCRIPTS_DIR, _GRAPHIFY_DIR]:
    if _d not in sys.path and os.path.exists(_d):
        sys.path.insert(0, _d)

from search_router import (
    UnifiedSearchRouter,
    QueryAnalyzer,
    QueryType,
    ResultDeduplicator,
    ResultRanker,
    SearchResult,
)
from tantivy_searcher import TantivySearcher, get_tantivy_schema, TANTIVY_AVAILABLE
from graphify_searcher import GraphifySearcher, GRAPHIFY_AVAILABLE
from index_tantivy import TantivyIndexer
from index_graphify import GraphifyIndexer


class TestTantivySearcher:
    """Tests for Tantivy BM25 inverted index searcher."""

    def test_schema_creation(self):
        """Test Tantivy schema creation."""
        if not TANTIVY_AVAILABLE:
            pytest.skip("Tantivy not available")
        schema = get_tantivy_schema()
        assert schema is not None

    def test_searcher_uninitialized_index(self):
        """Test searcher behavior when index directory does not exist."""
        searcher = TantivySearcher(str(Path(tempfile.gettempdir()) / "nonexistent_tantivy_index_path"))
        assert not searcher.has_index
        results = searcher.search("query")
        assert results == []
        stats = searcher.get_stats()
        assert stats["available"] is True
        assert stats["indexed"] is False

    def test_indexing_and_search_in_temp_dir(self):
        """Test creating a temporary index, indexing documents, and querying."""
        if not TANTIVY_AVAILABLE:
            pytest.skip("Tantivy not available")

        temp_dir = tempfile.mkdtemp()
        temp_workspace = tempfile.mkdtemp()
        try:
            # Create a sample document
            doc_file = Path(temp_workspace) / "sample.md"
            with open(doc_file, "w", encoding="utf-8") as f:
                f.write("# Distributed Training on Ray\nRay clusters provide burstable GPU execution.")

            indexer = TantivyIndexer(workspace_root=temp_workspace, index_path=temp_dir, include_code=False)
            res = indexer.index()
            assert res["indexed_count"] == 1

            searcher = TantivySearcher(temp_dir)
            assert searcher.has_index

            hits = searcher.search("burstable GPU", limit=5)
            assert len(hits) == 1
            assert "sample.md" in hits[0]["path"]
            assert hits[0]["score"] > 0
            assert hits[0]["source"] == "tantivy"

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
            shutil.rmtree(temp_workspace, ignore_errors=True)


class TestGraphifySearcher:
    """Tests for Graphify AST code intelligence searcher."""

    def test_graphify_searcher_initialization(self):
        """Test GraphifySearcher initialization and availability."""
        searcher = GraphifySearcher(workspace_root=".", graph_path=".graphify/graph.json")
        assert searcher.is_available is True
        stats = searcher.get_stats()
        assert stats["available"] is True
        assert "nodes" in stats
        assert "local_llm_model" in stats
        assert stats["local_llm_model"] == "qwen3.8:27b"

    def test_search_symbols_finds_classes(self):
        """Test searching symbols in AST graph."""
        searcher = GraphifySearcher(workspace_root=".", graph_path=".graphify/graph.json")
        hits = searcher.search_symbols("UnifiedSearchRouter", limit=5)
        assert len(hits) > 0
        top = hits[0]
        assert top["source"] == "graphify"
        assert top["metadata"]["symbol"] == "UnifiedSearchRouter"
        assert top["metadata"]["kind"] == "class"
        assert top["line_number"] > 0

    def test_search_symbols_kind_filter(self):
        """Test filtering symbols by kind."""
        searcher = GraphifySearcher(workspace_root=".", graph_path=".graphify/graph.json")
        class_hits = searcher.search_symbols("QueryAnalyzer", kind="class", limit=5)
        assert all(h["metadata"]["kind"] == "class" for h in class_hits)

    def test_graph_neighbors(self):
        """Test retrieving callers/callees in graph."""
        searcher = GraphifySearcher(workspace_root=".", graph_path=".graphify/graph.json")
        neighbors = searcher.get_neighbors("UnifiedSearchRouter")
        assert "callers" in neighbors
        assert "callees" in neighbors

    def test_search_symbols_finds_markdown_sections(self):
        """Test searching markdown sections and documents in the AST graph."""
        searcher = GraphifySearcher(workspace_root=".", graph_path=".graphify/graph.json")
        hits = searcher.search_symbols("Macro vs. Micro", kind="section", limit=5)
        assert len(hits) > 0
        top = hits[0]
        assert top["source"] == "graphify"
        assert top["metadata"]["kind"] == "section"
        assert "PLAN.md" in top["path"]

    def test_indexer_safely_skips_missing_subrepos(self, tmp_path):
        """Test GraphifyIndexer safely skips nonexistent directories without crashing."""
        temp_graph = tmp_path / "temp_graph.json"
        indexer = GraphifyIndexer(
            workspace_root=".",
            graph_path=str(temp_graph),
            target_dirs=["nonexistent_dir_12345", "another_missing_repo"],
        )
        discovered = indexer.discover_files()
        assert discovered == []
        res = indexer.index(clear_first=False)
        assert res["files_parsed"] == 0
        assert res["errors"] == 0

    @patch("urllib.request.urlopen")
    def test_local_ollama_call_mocked(self, mock_urlopen):
        """Test ask_local_llm calls local Ollama endpoint without cloud egress."""
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({"response": "Abstract Syntax Tree"}).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        searcher = GraphifySearcher(workspace_root=".", graph_path=".graphify/graph.json")
        reply = searcher.ask_local_llm("What is AST?")
        assert reply == "Abstract Syntax Tree"


class TestQueryIntentAndFusion:
    """Tests for query intent classification and Reciprocal Rank Fusion."""

    def test_code_intent_detection(self):
        """Test detecting code patterns and symbols."""
        analysis = QueryAnalyzer.analyze("def search_symbols")
        assert analysis.is_code_pattern is True
        assert analysis.query_type in (QueryType.CODE, QueryType.REGEX)

    def test_reciprocal_rank_fusion(self):
        """Test blending multi-engine results with RRF."""
        res1 = SearchResult(id="f1:10", path="f1.py", line_number=10, content="code1", score=10.0, source="tantivy")
        res2 = SearchResult(id="f2:20", path="f2.py", line_number=20, content="code2", score=5.0, source="tantivy")
        res3 = SearchResult(id="f1:10", path="f1.py", line_number=10, content="code1 ast", score=1.0, source="graphify")

        engine_results = {
            "tantivy": [res1, res2],
            "graphify": [res3],
        }

        fused = ResultRanker.reciprocal_rank_fusion(engine_results, k=60)
        assert len(fused) == 2
        # f1:10 should rank #1 because it has matches in both Tantivy and Graphify
        assert fused[0].path == "f1.py"
        assert "graphify" in fused[0].source
        assert "tantivy" in fused[0].source

    def test_ast_span_deduplication(self):
        """Test merging raw grep hits into AST symbol ranges."""
        ast_symbol = SearchResult(
            id="search_router.py:40",
            path="scripts/search_router/search_router.py",
            line_number=40,
            content="class QueryAnalyzer:",
            score=1.0,
            source="graphify",
            metadata={"kind": "class", "symbol": "QueryAnalyzer"},
        )
        grep_hit = SearchResult(
            id="search_router.py:45",
            path="scripts/search_router/search_router.py",
            line_number=45,
            content="    REGEX_CHARS = ...",
            score=0.8,
            source="ripgrep",
        )

        deduped = ResultDeduplicator.deduplicate([ast_symbol, grep_hit], proximity_threshold=3)
        # Grep hit at line 45 is within 5 lines of AST symbol at line 40, so they merge
        assert len(deduped) == 1
        assert "graphify" in deduped[0].source
        assert "ripgrep" in deduped[0].source


class TestUnifiedSearchRouterPhase6:
    """Tests for 4-engine unified router methods."""

    def test_search_everything_method(self):
        """Test search_everything delegates to Tantivy."""
        router = UnifiedSearchRouter(workspace_root=".", chroma_db_path=".chroma")
        results = router.search_everything("burstable", limit=5)
        # Should return results from existing .tantivy index
        assert isinstance(results, list)

    def test_search_symbols_method(self):
        """Test search_symbols returns AST entities."""
        router = UnifiedSearchRouter(workspace_root=".", chroma_db_path=".chroma")
        results = router.search_symbols("UnifiedSearchRouter", limit=3)
        assert len(results) > 0
        assert results[0].source == "graphify"

    def test_get_router_stats_includes_all_four_engines(self):
        """Test stats return data for ripgrep, semantic, tantivy, and graphify."""
        router = UnifiedSearchRouter(workspace_root=".", chroma_db_path=".chroma")
        stats = router.get_router_stats()
        assert "ripgrep_available" in stats
        assert "semantic_available" in stats
        assert "tantivy_available" in stats
        assert "graphify_available" in stats
        assert stats["tantivy_available"] is True
        assert stats["graphify_available"] is True
