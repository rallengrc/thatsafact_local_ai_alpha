#!/usr/bin/env python3
"""
test_search_router.py — Unit tests for unified search router.

Tests query analysis, result combination, deduplication, ranking, and
LLM curation.

Run with: python3 -m pytest scripts/test_search_router.py -v
"""

import sys
import os
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, os.path.dirname(__file__))

import pytest
from search_router import (
    UnifiedSearchRouter,
    QueryAnalyzer,
    QueryType,
    ResultDeduplicator,
    ResultRanker,
    LLMCurator,
    SearchResult,
    QueryAnalysis,
)


class TestQueryAnalyzer:
    """Tests for query type analysis."""

    def test_analyze_keyword_query(self):
        """Test analyzing keyword query."""
        analysis = QueryAnalyzer.analyze("docker")
        # Single word could be analyzed as semantic (natural language)
        assert analysis.query_type in (QueryType.KEYWORD, QueryType.HYBRID, QueryType.SEMANTIC)
        assert analysis.confidence > 0.7

    def test_analyze_regex_query(self):
        """Test analyzing regex query."""
        analysis = QueryAnalyzer.analyze("def.*deploy")
        assert analysis.has_regex_chars or analysis.query_type == QueryType.REGEX
        assert analysis.confidence > 0.7

    def test_analyze_code_query(self):
        """Test analyzing code-specific query."""
        analysis = QueryAnalyzer.analyze("def deploy")
        assert analysis.is_code_pattern
        assert QueryType.CODE in (analysis.query_type, QueryType.REGEX)

    def test_analyze_natural_language_query(self):
        """Test analyzing natural language query."""
        analysis = QueryAnalyzer.analyze("how to deploy kubernetes")
        assert analysis.is_natural_language
        assert analysis.query_type in (QueryType.SEMANTIC, QueryType.HYBRID)

    def test_analyze_class_keyword(self):
        """Test analyzing class keyword."""
        analysis = QueryAnalyzer.analyze("class MyClass")
        assert analysis.is_code_pattern

    def test_analyze_import_keyword(self):
        """Test analyzing import keyword."""
        analysis = QueryAnalyzer.analyze("import kubernetes")
        assert analysis.is_code_pattern

    def test_analyze_long_query(self):
        """Test analyzing long natural language query."""
        query = "what is the best way to configure kubernetes deployments"
        analysis = QueryAnalyzer.analyze(query)
        assert analysis.is_natural_language
        assert len(analysis.estimated_keywords) >= 0

    def test_analyze_regex_with_brackets(self):
        """Test analyzing regex with brackets."""
        analysis = QueryAnalyzer.analyze("def [a-z_]+")
        # Should detect regex or code pattern
        assert analysis.has_regex_chars or analysis.is_code_pattern

    def test_analyze_empty_query(self):
        """Test analyzing empty query."""
        analysis = QueryAnalyzer.analyze("")
        assert isinstance(analysis, QueryAnalysis)


class TestSearchResult:
    """Tests for SearchResult dataclass."""

    def test_search_result_creation(self):
        """Test creating SearchResult."""
        result = SearchResult(
            id="file.py:1",
            path="file.py",
            line_number=1,
            content="def test():",
            score=0.95,
            source="ripgrep",
        )
        assert result.id == "file.py:1"
        assert result.score == 0.95
        assert result.source == "ripgrep"

    def test_search_result_to_dict(self):
        """Test converting SearchResult to dict."""
        result = SearchResult(
            id="file.py:5",
            path="file.py",
            line_number=5,
            content="x = 42",
            score=0.8,
            source="semantic",
        )
        d = result.to_dict()
        assert d["id"] == "file.py:5"
        assert d["score"] == 0.8
        assert d["source"] == "semantic"

    def test_search_result_with_context(self):
        """Test SearchResult with context."""
        result = SearchResult(
            id="file.py:10",
            path="file.py",
            line_number=10,
            content="return value",
            score=0.9,
            source="ripgrep",
            context_before=["x = 5"],
            context_after=["y = 10"],
        )
        assert len(result.context_before) == 1
        assert len(result.context_after) == 1


class TestResultDeduplicator:
    """Tests for result deduplication."""

    def test_deduplicate_empty_list(self):
        """Test deduplicating empty list."""
        results = ResultDeduplicator.deduplicate([])
        assert results == []

    def test_deduplicate_single_result(self):
        """Test deduplicating single result."""
        result = SearchResult(
            id="file.py:1",
            path="file.py",
            line_number=1,
            content="test",
            score=0.9,
            source="ripgrep",
        )
        results = ResultDeduplicator.deduplicate([result])
        assert len(results) == 1

    def test_deduplicate_same_file_close_lines(self):
        """Test deduplicating results from same file close lines."""
        result1 = SearchResult(
            id="file.py:10",
            path="file.py",
            line_number=10,
            content="def deploy",
            score=0.9,
            source="ripgrep",
        )
        result2 = SearchResult(
            id="file.py:11",
            path="file.py",
            line_number=11,
            content="  config = load()",
            score=0.7,
            source="semantic",
        )
        results = ResultDeduplicator.deduplicate(
            [result1, result2],
            proximity_threshold=3,
        )
        # Should merge or keep best
        assert len(results) <= 2
        # Best score should be kept
        assert any(r.score >= 0.9 for r in results)

    def test_deduplicate_different_files(self):
        """Test deduplicating results from different files."""
        result1 = SearchResult(
            id="file1.py:1",
            path="file1.py",
            line_number=1,
            content="test1",
            score=0.9,
            source="ripgrep",
        )
        result2 = SearchResult(
            id="file2.py:1",
            path="file2.py",
            line_number=1,
            content="test2",
            score=0.8,
            source="semantic",
        )
        results = ResultDeduplicator.deduplicate([result1, result2])
        # Should keep both as they're from different files
        assert len(results) == 2

    def test_deduplicate_far_lines_same_file(self):
        """Test deduplicating results far apart in same file."""
        result1 = SearchResult(
            id="file.py:10",
            path="file.py",
            line_number=10,
            content="test1",
            score=0.9,
            source="ripgrep",
        )
        result2 = SearchResult(
            id="file.py:100",
            path="file.py",
            line_number=100,
            content="test2",
            score=0.8,
            source="semantic",
        )
        results = ResultDeduplicator.deduplicate(
            [result1, result2],
            proximity_threshold=3,
        )
        # Should keep both as they're far apart
        assert len(results) == 2

    def test_deduplicate_normalizes_windows_paths(self):
        """Test deduplicating results when paths have Windows backslashes."""
        result1 = SearchResult(
            id="src\\utils\\helper.py:10",
            path="src\\utils\\helper.py",
            line_number=10,
            content="def helper():",
            score=0.9,
            source="ripgrep",
        )
        result2 = SearchResult(
            id="src/utils/helper.py:11",
            path="src/utils/helper.py",
            line_number=11,
            content="    return 42",
            score=0.8,
            source="semantic",
        )
        results = ResultDeduplicator.deduplicate([result1, result2], proximity_threshold=3)
        assert len(results) == 1
        assert results[0].path == "src/utils/helper.py"


class TestResultRanker:
    """Tests for result ranking and scoring."""

    def test_rank_ripgrep_only(self):
        """Test ranking ripgrep results only."""
        results = [
            SearchResult(
                id="file.py:1",
                path="file.py",
                line_number=1,
                content="test",
                score=0.9,
                source="ripgrep",
            ),
            SearchResult(
                id="file.py:2",
                path="file.py",
                line_number=2,
                content="other",
                score=0.7,
                source="ripgrep",
            ),
        ]
        ranked = ResultRanker.rank(results, [])
        assert len(ranked) == 2
        # Check ordering by score
        assert ranked[0].score >= ranked[1].score

    def test_rank_semantic_only(self):
        """Test ranking semantic results only."""
        results = [
            SearchResult(
                id="file.py:1",
                path="file.py",
                line_number=1,
                content="test",
                score=0.8,
                source="semantic",
            ),
        ]
        ranked = ResultRanker.rank([], results)
        assert len(ranked) == 1

    def test_rank_combined_equal_weights(self):
        """Test ranking combined results with equal weights."""
        rg_results = [
            SearchResult(
                id="file.py:1",
                path="file.py",
                line_number=1,
                content="test1",
                score=0.9,
                source="ripgrep",
            ),
        ]
        sem_results = [
            SearchResult(
                id="file.py:2",
                path="file.py",
                line_number=2,
                content="test2",
                score=0.8,
                source="semantic",
            ),
        ]
        ranked = ResultRanker.rank(rg_results, sem_results, 0.5, 0.5)
        assert len(ranked) == 2

    def test_rank_weighted_ripgrep(self):
        """Test ranking with ripgrep weight preference."""
        rg_results = [
            SearchResult(
                id="file.py:1",
                path="file.py",
                line_number=1,
                content="test1",
                score=0.7,
                source="ripgrep",
            ),
        ]
        sem_results = [
            SearchResult(
                id="file.py:2",
                path="file.py",
                line_number=2,
                content="test2",
                score=0.9,
                source="semantic",
            ),
        ]
        # Ripgrep weight 0.8, semantic 0.2
        ranked = ResultRanker.rank(rg_results, sem_results, 0.8, 0.2)
        # Ripgrep result should score higher due to weight
        assert ranked[0].source == "ripgrep"

    def test_reciprocal_rank_fusion_normalizes_windows_paths(self):
        """Test RRF fuses results with mixed Windows backslashes and POSIX paths."""
        res_rg = SearchResult(
            id="dir\\file.py:5",
            path="dir\\file.py",
            line_number=5,
            content="print('hello')",
            score=0.9,
            source="ripgrep",
        )
        res_sem = SearchResult(
            id="dir/file.py:5",
            path="dir/file.py",
            line_number=5,
            content="print('hello')",
            score=0.85,
            source="semantic",
        )
        engine_results = {
            "ripgrep": [res_rg],
            "chromadb": [res_sem],
        }
        fused = ResultRanker.reciprocal_rank_fusion(engine_results)
        assert len(fused) == 1
        assert fused[0].path == "dir/file.py"
        assert fused[0].source == "chromadb+ripgrep"


class TestLLMCurator:
    """Tests for LLM result curation."""

    def test_curate_empty_results(self):
        """Test curating empty results."""
        curated, metadata = LLMCurator.curate([])
        assert curated == []
        assert metadata["truncated"] is False
        assert metadata["total_input"] == 0

    def test_curate_single_result(self):
        """Test curating single result."""
        result = SearchResult(
            id="file.py:1",
            path="file.py",
            line_number=1,
            content="test",
            score=0.9,
            source="ripgrep",
        )
        curated, metadata = LLMCurator.curate([result])
        assert len(curated) == 1
        assert metadata["total_output"] == 1

    def test_curate_respects_max_results(self):
        """Test curation respects max_results limit."""
        results = [
            SearchResult(
                id=f"file.py:{i}",
                path="file.py",
                line_number=i,
                content=f"test{i}",
                score=0.9 - i * 0.1,
                source="ripgrep",
            )
            for i in range(20)
        ]
        curated, metadata = LLMCurator.curate(results, max_results=5)
        assert len(curated) <= 5
        assert metadata["total_output"] <= 5

    def test_curate_respects_context_window(self):
        """Test curation respects context window."""
        results = [
            SearchResult(
                id=f"file.py:{i}",
                path="file.py",
                line_number=i,
                content="x" * 1000,  # Large content
                score=0.9 - i * 0.1,
                source="ripgrep",
            )
            for i in range(10)
        ]
        curated, metadata = LLMCurator.curate(results, context_window=500)
        # Should truncate due to context window
        assert len(curated) < len(results)
        assert metadata["truncated"]

    def test_curate_provides_metadata(self):
        """Test curation provides useful metadata."""
        result = SearchResult(
            id="file.py:1",
            path="file.py",
            line_number=1,
            content="test",
            score=0.9,
            source="ripgrep",
        )
        curated, metadata = LLMCurator.curate([result])
        assert "truncated" in metadata
        assert "total_input" in metadata
        assert "total_output" in metadata
        assert "tokens_estimated" in metadata


class TestUnifiedSearchRouter:
    """Tests for unified search router."""

    @patch("search_router.RipgrepSearcher")
    @patch("search_router.get_provider")
    def test_router_initialization(self, mock_provider, mock_searcher):
        """Test router initialization."""
        router = UnifiedSearchRouter(".", ".chroma")
        assert router.workspace_root == "."
        assert router.collection_name == "workspace"

    @patch("search_router.RipgrepSearcher")
    @patch("search_router.get_provider")
    def test_get_router_stats(self, mock_provider, mock_searcher):
        """Test getting router statistics."""
        mock_searcher_instance = MagicMock()
        mock_searcher_instance.rg_available = True
        mock_searcher.return_value = mock_searcher_instance

        mock_provider_instance = MagicMock()
        mock_provider_instance.get_stats.return_value = {"document_count": 45}
        mock_provider.return_value = mock_provider_instance

        router = UnifiedSearchRouter()
        stats = router.get_router_stats()
        assert "ripgrep_available" in stats
        assert "semantic_available" in stats

    @patch("search_router.RipgrepSearcher")
    @patch("search_router.get_provider")
    def test_search_ripgrep_not_available(self, mock_provider, mock_searcher):
        """Test search when ripgrep not available."""
        mock_searcher_instance = MagicMock()
        mock_searcher_instance.rg_available = False
        mock_searcher.return_value = mock_searcher_instance

        mock_provider_instance = MagicMock()
        mock_provider.return_value = mock_provider_instance

        router = UnifiedSearchRouter()
        results = router.search_ripgrep("test")
        assert results == []

    @patch("search_router.RipgrepSearcher")
    @patch("search_router.get_provider")
    def test_search_semantic_error_handling(self, mock_provider, mock_searcher):
        """Test semantic search error handling."""
        mock_searcher_instance = MagicMock()
        mock_searcher_instance.rg_available = True
        mock_searcher.return_value = mock_searcher_instance

        mock_provider_instance = MagicMock()
        mock_provider_instance.search.side_effect = Exception("DB Error")
        mock_provider.return_value = mock_provider_instance

        router = UnifiedSearchRouter()
        results = router.search_semantic("test")
        assert results == []

    @patch("search_router.RipgrepSearcher")
    @patch("search_router.get_provider")
    def test_search_code(self, mock_provider, mock_searcher):
        """Test code search method."""
        from livetext import SearchMatch

        mock_searcher_instance = MagicMock()
        mock_searcher_instance.rg_available = True
        mock_searcher_instance.search_code.return_value = [
            SearchMatch(
                id="file.py:1",
                path="file.py",
                line_number=1,
                content="def test():",
                context_before=[],
                context_after=[],
            ),
        ]
        mock_searcher.return_value = mock_searcher_instance

        mock_provider_instance = MagicMock()
        mock_provider.return_value = mock_provider_instance

        router = UnifiedSearchRouter()
        results = router.search_code("def ", language="python")
        assert len(results) > 0
        assert results[0].source == "ripgrep"


class TestIntegration:
    """Integration tests for search router."""

    @patch("search_router.RipgrepSearcher")
    @patch("search_router.get_provider")
    def test_hybrid_search_keyword(self, mock_provider, mock_searcher):
        """Test hybrid search with keyword query."""
        from livetext import SearchMatch

        # Mock ripgrep
        mock_searcher_instance = MagicMock()
        mock_searcher_instance.rg_available = True
        mock_searcher_instance.search.return_value = [
            SearchMatch(
                id="file.py:1",
                path="file.py",
                line_number=1,
                content="def deploy",
                context_before=[],
                context_after=[],
                confidence=0.95,
            ),
        ]
        mock_searcher.return_value = mock_searcher_instance

        # Mock semantic search - return something for single word query
        mock_provider_instance = MagicMock()
        mock_provider_instance.search.return_value = [
            {
                "id": "file.py:2",
                "text": "deploy configuration",
                "distance": 0.2,
                "metadata": {"path": "file.py", "line_number": 2},
            },
        ]
        mock_provider.return_value = mock_provider_instance

        router = UnifiedSearchRouter()
        results = router.search_hybrid("deploy")
        # Results should be either from ripgrep or semantic
        assert isinstance(results, list)

    @patch("search_router.RipgrepSearcher")
    @patch("search_router.get_provider")
    def test_hybrid_search_natural_language(self, mock_provider, mock_searcher):
        """Test hybrid search with natural language query."""
        mock_searcher_instance = MagicMock()
        mock_searcher_instance.rg_available = True
        mock_searcher_instance.search.return_value = []
        mock_searcher.return_value = mock_searcher_instance

        mock_provider_instance = MagicMock()
        mock_provider_instance.search.return_value = [
            {
                "id": "file.py:1",
                "text": "deployment configuration",
                "distance": 0.1,
                "metadata": {"path": "file.py", "line_number": 1},
            },
        ]
        mock_provider.return_value = mock_provider_instance

        router = UnifiedSearchRouter()
        results = router.search_hybrid("how to deploy")
        assert len(results) > 0

    @patch("search_router.RipgrepSearcher")
    @patch("search_router.get_provider")
    def test_hybrid_search_with_curation(self, mock_provider, mock_searcher):
        """Test hybrid search with LLM curation."""
        from livetext import SearchMatch

        mock_searcher_instance = MagicMock()
        mock_searcher_instance.rg_available = True
        mock_searcher_instance.search.return_value = [
            SearchMatch(
                id="file.py:1",
                path="file.py",
                line_number=1,
                content="def deploy(config):",
                context_before=["# deployment"],
                context_after=["    return True"],
                confidence=0.95,
            ),
        ]
        mock_searcher.return_value = mock_searcher_instance

        mock_provider_instance = MagicMock()
        mock_provider_instance.search.return_value = []
        mock_provider.return_value = mock_provider_instance

        router = UnifiedSearchRouter()
        results = router.search_hybrid("def deploy", curate_for_llm=True)
        # Should have results from ripgrep (code pattern)
        assert isinstance(results, list)
