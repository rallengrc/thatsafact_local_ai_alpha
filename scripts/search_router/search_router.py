#!/usr/bin/env python3
"""
search_router.py — Unified search router combining ripgrep + ChromaDB.

Provides intelligent query routing, result deduplication, ranking, and
LLM-optimized curation. Routes queries to ripgrep (keyword/regex), semantic
search (ChromaDB), or both based on query analysis.

Usage:
    from search_router import UnifiedSearchRouter
    router = UnifiedSearchRouter(".", ".chroma")
    
    # Hybrid search
    results = router.search_hybrid("kubernetes deployment", curate_for_llm=True)
    
    # Single source
    results = router.search_ripgrep("def deploy")
    results = router.search_semantic("how to deploy")
"""

import logging
import re
import sys
import os
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_SCRIPTS_DIR = os.path.dirname(_CURRENT_DIR)
_INDEXING_DIR = os.path.join(_SCRIPTS_DIR, "indexing")
for _d in [_CURRENT_DIR, _INDEXING_DIR, _SCRIPTS_DIR]:
    if _d not in sys.path:
        sys.path.insert(0, _d)

from common_platform import normalize_posix_path

try:
    from .livetext import RipgrepSearcher, SearchMatch
except ImportError:
    from livetext import RipgrepSearcher, SearchMatch
from vectordb_provider import get_provider, VectorDBProvider

try:
    from .tantivy_searcher import TantivySearcher
except ImportError:
    try:
        from tantivy_searcher import TantivySearcher
    except ImportError:
        TantivySearcher = None

try:
    from .graphify_searcher import GraphifySearcher
except ImportError:
    try:
        from graphify_searcher import GraphifySearcher
    except ImportError:
        GraphifySearcher = None

try:
    from .passport import PassportResolver, Passport
except ImportError:
    try:
        from passport import PassportResolver, Passport
    except ImportError:
        PassportResolver = None
        Passport = None

logger = logging.getLogger(__name__)


class QueryType(Enum):
    """Query type detected by router."""

    KEYWORD = "keyword"  # Exact or simple pattern match
    REGEX = "regex"  # Regex with special characters
    CODE = "code"  # Code-specific keywords
    SEMANTIC = "semantic"  # Natural language
    SYMBOL = "symbol"  # Code symbol definitions (AST)
    BROAD = "broad"  # Broad workspace-wide search (Tantivy BM25)
    HYBRID = "hybrid"  # Ambiguous, use both



@dataclass
class SearchResult:
    """Unified search result from hybrid search."""

    id: str
    path: str
    line_number: int
    content: str
    score: float
    source: str  # "ripgrep" or "semantic" or "hybrid"
    metadata: Dict[str, Any] = field(default_factory=dict)
    context_before: List[str] = field(default_factory=list)
    context_after: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "id": self.id,
            "path": self.path,
            "line_number": self.line_number,
            "content": self.content,
            "score": self.score,
            "source": self.source,
            "metadata": self.metadata,
            "context_before": self.context_before,
            "context_after": self.context_after,
        }


@dataclass
class QueryAnalysis:
    """Result of query analysis."""

    query_type: QueryType
    estimated_keywords: List[str]
    has_regex_chars: bool
    is_code_pattern: bool
    is_natural_language: bool
    confidence: float


class QueryAnalyzer:
    """Analyzes queries to determine search type."""

    # Regex special characters
    REGEX_CHARS = set(r".*+?{}[]()|\^$")

    # Common code keywords
    CODE_KEYWORDS = {
        "def",
        "class",
        "function",
        "import",
        "return",
        "async",
        "await",
        "try",
        "except",
        "if",
        "for",
        "while",
        "lambda",
        "yield",
        "const",
        "let",
        "var",
        "int",
        "float",
        "bool",
        "string",
        "void",
        "public",
        "private",
        "protected",
        "struct",
        "enum",
        "interface",
    }

    @classmethod
    def analyze(cls, query: str) -> QueryAnalysis:
        """Analyze query to determine type.

        Args:
            query: Search query string

        Returns:
            QueryAnalysis with detected type and confidence
        """
        query_lower = query.lower()
        tokens = query_lower.split()

        # Check for regex patterns
        has_regex = any(c in query for c in cls.REGEX_CHARS if c not in "()")
        is_regex = has_regex or query.count(".*") > 0

        # Check for code keywords
        code_keywords = [t for t in tokens if t in cls.CODE_KEYWORDS]
        is_code = len(code_keywords) > 0 or query.startswith("def ") or query.startswith("class ")

        # Natural language characteristics
        is_natural = (
            len(tokens) > 3  # Longer queries
            or any(word in query_lower for word in ["how", "what", "why", "when", "where"])
            or not is_regex
        )

        # Determine type
        if is_regex and not is_natural:
            query_type = QueryType.REGEX
        elif is_code:
            query_type = QueryType.CODE
        elif is_natural and not is_code:
            query_type = QueryType.SEMANTIC
        else:
            query_type = QueryType.HYBRID

        confidence = 0.8
        if is_regex or is_code:
            confidence = 0.95
        elif is_natural:
            confidence = 0.85

        return QueryAnalysis(
            query_type=query_type,
            estimated_keywords=code_keywords,
            has_regex_chars=has_regex,
            is_code_pattern=is_code,
            is_natural_language=is_natural,
            confidence=confidence,
        )


class ResultDeduplicator:
    """Deduplicates and merges overlapping search results."""

    @staticmethod
    def deduplicate(
        results: List[SearchResult],
        proximity_threshold: int = 3,
    ) -> List[SearchResult]:
        """Deduplicate results from multiple sources.

        Merges results from same file within proximity_threshold lines,
        keeping highest scoring result.

        Args:
            results: List of search results
            proximity_threshold: Lines within which to consider results same

        Returns:
            Deduplicated list of results
        """
        if not results:
            return []

        # Group by file
        by_file: Dict[str, List[SearchResult]] = {}
        for result in results:
            result.path = normalize_posix_path(result.path)
            if result.path not in by_file:
                by_file[result.path] = []
            by_file[result.path].append(result)

        # Deduplicate within each file
        deduped = []
        for path, file_results in by_file.items():
            # Sort by line number
            file_results.sort(key=lambda r: r.line_number)

            merged_groups = []
            current_group = [file_results[0]]

            for result in file_results[1:]:
                last_result = current_group[-1]
                # If either result is an AST symbol (from graphify), allow wider span merging (e.g. 10 lines)
                threshold = proximity_threshold
                if any(r.source == "graphify" for r in current_group) or result.source == "graphify":
                    threshold = max(proximity_threshold, 10)

                if abs(result.line_number - last_result.line_number) <= threshold:
                    current_group.append(result)
                else:
                    merged_groups.append(current_group)
                    current_group = [result]

            merged_groups.append(current_group)

            # Keep best result from each group, merging sources if distinct engines matched
            for group in merged_groups:
                best = max(group, key=lambda r: r.score)
                sources = set(r.source for r in group)
                if len(sources) > 1:
                    graphify_item = next((r for r in group if r.source == "graphify"), None)
                    if graphify_item:
                        best = graphify_item
                    best.source = "+".join(sorted(sources))
                deduped.append(best)

        return deduped


class ResultRanker:
    """Ranks and scores combined search results."""

    @staticmethod
    def rank(
        ripgrep_results: List[SearchResult],
        semantic_results: List[SearchResult],
        ripgrep_weight: float = 0.5,
        semantic_weight: float = 0.5,
    ) -> List[SearchResult]:
        """Rank combined results by weighted score.

        Args:
            ripgrep_results: Results from ripgrep
            semantic_results: Results from semantic search
            ripgrep_weight: Weight for ripgrep results (0-1)
            semantic_weight: Weight for semantic results (0-1)

        Returns:
            Ranked list of results
        """
        # Normalize weights
        total_weight = ripgrep_weight + semantic_weight
        rg_norm = ripgrep_weight / total_weight if total_weight > 0 else 0.5
        sem_norm = semantic_weight / total_weight if total_weight > 0 else 0.5

        # Combine results
        combined = []
        for result in ripgrep_results:
            result.score = result.score * rg_norm
            combined.append(result)
        for result in semantic_results:
            result.score = result.score * sem_norm
            combined.append(result)

        # Sort by score
        combined.sort(key=lambda r: r.score, reverse=True)

        return combined

    @staticmethod
    def reciprocal_rank_fusion(
        engine_results: Dict[str, List[SearchResult]],
        k: int = 60,
        weights: Optional[Dict[str, float]] = None,
    ) -> List[SearchResult]:
        """Combine results from multiple search engines using Reciprocal Rank Fusion (RRF).

        Formula: RRF_score(d) = sum_{engine} (weight_engine / (k + rank_engine(d)))

        Args:
            engine_results: Mapping of engine_name -> list of SearchResults
            k: Smoothing constant (default 60)
            weights: Optional dict mapping engine_name -> float weight

        Returns:
            Combined, reranked list of SearchResult objects
        """
        weights = weights or {}
        scores: Dict[str, float] = {}
        merged_results: Dict[str, SearchResult] = {}
        contributing_engines: Dict[str, set] = {}

        for engine, results in engine_results.items():
            w = weights.get(engine, 1.0)
            for rank, res in enumerate(results, start=1):
                norm_path = normalize_posix_path(res.path)
                res.path = norm_path
                key = f"{norm_path}:{res.line_number}"
                rrf_increment = w / (k + rank)
                scores[key] = scores.get(key, 0.0) + rrf_increment

                if key not in merged_results:
                    merged_results[key] = res
                    contributing_engines[key] = {engine}
                else:
                    contributing_engines[key].add(engine)
                    # If this engine has rich AST metadata, prioritize it
                    if res.source == "graphify":
                        merged_results[key] = res

        fused = []
        for key, res in merged_results.items():
            sources = contributing_engines.get(key, {res.source})
            res.score = scores[key]
            res.source = "+".join(sorted(sources))
            fused.append(res)

        fused.sort(key=lambda r: r.score, reverse=True)
        return fused



class LLMCurator:
    """Curates results for LLM consumption."""

    MAX_CONTEXT_WINDOW = 4000

    @staticmethod
    def curate(
        results: List[SearchResult],
        context_window: int = MAX_CONTEXT_WINDOW,
        max_results: int = 10,
    ) -> Tuple[List[SearchResult], Dict[str, Any]]:
        """Curate results for LLM context.

        Formats results to fit context window, preserving highest
        relevance results. Adds metadata about curation.

        Args:
            results: List of search results
            context_window: Available context window in tokens (rough estimate)
            max_results: Maximum number of results to return

        Returns:
            (curated_results, curation_metadata)
        """
        if not results:
            return [], {
                "truncated": False,
                "total_input": 0,
                "total_output": 0,
                "curation_reason": "no results",
            }

        # Estimate tokens per text snippet (rough: 1 char ≈ 0.25 tokens)
        def estimate_tokens(text: str) -> int:
            return max(1, int(len(text) * 0.25))

        curated = []
        total_tokens = 0
        tokens_used = 0
        truncated = False
        curation_reason = None
        MAX_SNIPPET_CHARS = 2000

        # Add results up to limits
        for result in results:
            if len(curated) >= max_results:
                truncated = True
                curation_reason = "max_results_limit"
                break

            content = result.content
            if len(content) > MAX_SNIPPET_CHARS:
                content = content[:MAX_SNIPPET_CHARS] + "\n... [truncated]"

            result_tokens = estimate_tokens(
                f"{result.path}:{result.line_number}\n{content}\n"
                + "\n".join(result.context_before)
                + "\n"
                + "\n".join(result.context_after)
            )

            if total_tokens + result_tokens > context_window:
                # If we have no results yet, include at least the first one truncated to remaining window
                if not curated:
                    avail_chars = max(200, int((context_window - total_tokens) / 0.25))
                    curated_content = result.content[:avail_chars] + "\n... [truncated]"
                    curated_result = SearchResult(
                        id=result.id,
                        path=result.path,
                        line_number=result.line_number,
                        content=curated_content,
                        score=result.score,
                        source=result.source,
                        metadata=result.metadata,
                        context_before=result.context_before,
                        context_after=result.context_after,
                    )
                    curated.append(curated_result)
                    tokens_used += estimate_tokens(curated_content)
                truncated = True
                curation_reason = "context_window_limit"
                break

            curated_result = SearchResult(
                id=result.id,
                path=result.path,
                line_number=result.line_number,
                content=content,
                score=result.score,
                source=result.source,
                metadata=result.metadata,
                context_before=result.context_before,
                context_after=result.context_after,
            )
            curated.append(curated_result)
            total_tokens += result_tokens
            tokens_used += result_tokens

        metadata = {
            "truncated": truncated,
            "total_input": len(results),
            "total_output": len(curated),
            "curation_reason": curation_reason,
            "tokens_estimated": tokens_used,
            "context_window": context_window,
        }

        return curated, metadata


class UnifiedSearchRouter:
    """Unified search router combining ripgrep, ChromaDB, Tantivy, and Graphify AST."""

    def __init__(
        self,
        workspace_root: str = ".",
        chroma_db_path: Any = ".chroma",
        collection_name: str = "workspace",
        tantivy_index_path: str = ".tantivy",
        graph_path: str = ".graphify/graph.json",
    ):
        """Initialize unified search router.

        Args:
            workspace_root: Root directory for ripgrep and graphify searches
            chroma_db_path: Path to ChromaDB storage (or config dict)
            collection_name: ChromaDB collection name
            tantivy_index_path: Path to Tantivy BM25 inverted index
            graph_path: Path to Graphify AST knowledge graph JSON
        """
        if isinstance(chroma_db_path, dict):
            collection_name = chroma_db_path.get("collection_name", collection_name)
            chroma_db_path = chroma_db_path.get("db_path", ".chroma")

        self.workspace_root = workspace_root
        rs = getattr(sys.modules.get("search_router"), "RipgrepSearcher", RipgrepSearcher)
        gp = getattr(sys.modules.get("search_router"), "get_provider", get_provider)
        self.rg_searcher = rs(workspace_root)
        self.semantic_provider = gp("chromadb", {"db_path": chroma_db_path})
        self.collection_name = collection_name
        self.query_analyzer = QueryAnalyzer()
        self.deduplicator = ResultDeduplicator()
        self.ranker = ResultRanker()
        self.curator = LLMCurator()

        # Phase 6 Multi-Index engines
        ws_path = Path(workspace_root).resolve()
        abs_tantivy_path = str(ws_path / tantivy_index_path) if not os.path.isabs(tantivy_index_path) else tantivy_index_path
        abs_graph_path = str(ws_path / graph_path) if not os.path.isabs(graph_path) else graph_path

        ts = getattr(sys.modules.get("search_router"), "TantivySearcher", TantivySearcher)
        gs = getattr(sys.modules.get("search_router"), "GraphifySearcher", GraphifySearcher)
        self.tantivy_searcher = ts(abs_tantivy_path) if ts else None
        self.graphify_searcher = gs(workspace_root, abs_graph_path) if gs else None

    def search_hybrid(
        self,
        query: str,
        limit: int = 10,
        ripgrep_weight: float = 0.5,
        semantic_weight: float = 0.5,
        curate_for_llm: bool = False,
        passport: Optional[str] = None,
    ) -> List[SearchResult]:
        """Hybrid search combining ripgrep + semantic (+ tantivy/graphify when appropriate).

        Args:
            query: Search query
            limit: Maximum results to return
            ripgrep_weight: Weight for ripgrep results (0-1)
            semantic_weight: Weight for semantic results (0-1)
            curate_for_llm: Curate results for LLM consumption

        Returns:
            List of SearchResult objects
        """
        # Analyze query
        analysis = self.query_analyzer.analyze(query)
        logger.debug(f"Query analysis: {analysis.query_type.value}, confidence: {analysis.confidence}")

        # Check if query is code symbol lookup
        graphify_results = []
        if analysis.query_type in (QueryType.CODE, QueryType.SYMBOL) and self.graphify_searcher:
            graphify_results = self.search_symbols(query, limit=limit)

        # Get results from ripgrep (if keyword/regex/code)
        ripgrep_results = []
        if analysis.query_type in (QueryType.KEYWORD, QueryType.REGEX, QueryType.CODE, QueryType.HYBRID):
            ripgrep_results = self.search_ripgrep(query, limit=limit)

        # Get results from semantic search (if semantic/natural language/hybrid)
        semantic_results = []
        if analysis.query_type in (QueryType.SEMANTIC, QueryType.HYBRID):
            semantic_results = self.search_semantic(query, limit=limit)

        # Get results from Tantivy (if broad/keyword/hybrid and index ready)
        tantivy_results = []
        if (
            analysis.query_type in (QueryType.KEYWORD, QueryType.BROAD, QueryType.HYBRID)
            and self.tantivy_searcher
            and getattr(self.tantivy_searcher, "has_index", False)
        ):
            tantivy_results = self.search_tantivy(query, limit=limit)

        # Multi-engine fusion
        if tantivy_results or graphify_results:
            engine_map = {}
            if ripgrep_results:
                engine_map["ripgrep"] = ripgrep_results
            if semantic_results:
                engine_map["semantic"] = semantic_results
            if tantivy_results:
                engine_map["tantivy"] = tantivy_results
            if graphify_results:
                engine_map["graphify"] = graphify_results

            weights = {
                "ripgrep": ripgrep_weight,
                "semantic": semantic_weight,
                "tantivy": 0.6,
                "graphify": 0.8,
            }
            combined = self.ranker.reciprocal_rank_fusion(engine_map, weights=weights)
        else:
            # Fallback to standard 2-engine ranking for backwards compatibility
            combined = self.ranker.rank(
                ripgrep_results,
                semantic_results,
                ripgrep_weight=ripgrep_weight,
                semantic_weight=semantic_weight,
            )

        # Deduplicate
        deduped = self.deduplicator.deduplicate(combined)

        # Limit results
        limited = deduped[:limit]

        # Curate for LLM if requested
        if curate_for_llm:
            limited, _ = self.curator.curate(limited)

        if passport and PassportResolver:
            limited = PassportResolver.filter_results(limited, passport)

        return limited

    def search_ripgrep(
        self,
        pattern: str,
        limit: int = 20,
        context_lines: int = 2,
    ) -> List[SearchResult]:
        """Search using ripgrep only.

        Args:
            pattern: Regex or keyword pattern
            limit: Maximum results
            context_lines: Lines of context to include

        Returns:
            List of SearchResult objects from ripgrep
        """
        if not self.rg_searcher.rg_available:
            logger.warning("ripgrep not available, returning empty results")
            return []

        matches = self.rg_searcher.search(
            pattern=pattern,
            limit=limit,
            context_lines=context_lines,
        )

        results = []
        for match in matches:
            result = SearchResult(
                id=match.id,
                path=match.path,
                line_number=match.line_number,
                content=match.content,
                score=match.confidence,  # Ripgrep gives confidence
                source="ripgrep",
                context_before=match.context_before,
                context_after=match.context_after,
            )
            results.append(result)

        return results

    def search_semantic(
        self,
        query: str,
        limit: int = 10,
        threshold: Optional[float] = None,
    ) -> List[SearchResult]:
        """Search using semantic search (ChromaDB) only.

        Args:
            query: Natural language query
            limit: Maximum results
            threshold: Minimum similarity threshold

        Returns:
            List of SearchResult objects from ChromaDB
        """
        try:
            matches = self.semantic_provider.search(
                query=query,
                collection_name=self.collection_name,
                limit=limit,
                threshold=threshold,
            )
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []

        results = []
        for match in matches:
            # ChromaDB results have: id, distance, metadata, text
            metadata = match.get("metadata", {})
            path = metadata.get("path", match.get("id", "unknown"))
            line_num = metadata.get("line_number", 0)

            result = SearchResult(
                id=match.get("id", f"{path}:{line_num}"),
                path=path,
                line_number=line_num,
                content=match.get("text", ""),
                score=1.0 - match.get("distance", 0.5),  # Convert distance to similarity
                source="semantic",
                metadata=metadata,
                context_before=metadata.get("context_before", []),
                context_after=metadata.get("context_after", []),
            )
            results.append(result)

        return results

    def search_code(
        self,
        pattern: str,
        language: Optional[str] = None,
        limit: int = 20,
    ) -> List[SearchResult]:
        """Code-specific search using ripgrep.

        Args:
            pattern: Code pattern (regex or keyword)
            language: Programming language filter
            limit: Maximum results

        Returns:
            List of SearchResult objects
        """
        if not self.rg_searcher.rg_available:
            logger.warning("ripgrep not available for code search")
            return []

        matches = self.rg_searcher.search_code(
            pattern=pattern,
            language=language,
            context_lines=3,
        )

        results = []
        for match in matches:
            result = SearchResult(
                id=match.id,
                path=match.path,
                line_number=match.line_number,
                content=match.content,
                score=match.confidence,
                source="ripgrep",
                context_before=match.context_before,
                context_after=match.context_after,
            )
            results.append(result)

        return results

    def search_tantivy(
        self,
        query: str,
        limit: int = 10,
        fields: Optional[List[str]] = None,
    ) -> List[SearchResult]:
        """Search using Tantivy BM25 inverted index.

        Args:
            query: Keyword query string
            limit: Maximum results
            fields: Target fields to search

        Returns:
            List of SearchResult objects
        """
        if not self.tantivy_searcher or not getattr(self.tantivy_searcher, "is_available", False):
            logger.debug("Tantivy searcher not available")
            return []

        raw_hits = self.tantivy_searcher.search(query=query, limit=limit, fields=fields)
        results = []
        for hit in raw_hits:
            results.append(
                SearchResult(
                    id=hit["id"],
                    path=hit["path"],
                    line_number=hit["line_number"],
                    content=hit["content"],
                    score=hit["score"],
                    source="tantivy",
                    metadata=hit.get("metadata", {}),
                )
            )
        return results

    def search_symbols(
        self,
        query: str,
        limit: int = 15,
        kind: Optional[str] = None,
        file_filter: Optional[str] = None,
        passport: Optional[str] = None,
    ) -> List[SearchResult]:
        """Search code symbols (classes, functions, methods) via Graphify AST.

        Args:
            query: Symbol name, prefix, or regex
            limit: Maximum results
            kind: Optional entity kind ('class', 'function', 'method')
            file_filter: Optional file path filter
            passport: Optional passport partition tag ('cloud', 'ml', 'kubernetes', 'skill')

        Returns:
            List of SearchResult objects with precise AST locations
        """
        if not self.graphify_searcher or not getattr(self.graphify_searcher, "is_available", False):
            logger.debug("Graphify searcher not available")
            return []

        raw_hits = self.graphify_searcher.search_symbols(
            query=query, limit=limit, kind=kind, file_filter=file_filter
        )
        results = []
        for hit in raw_hits:
            results.append(
                SearchResult(
                    id=hit["id"],
                    path=hit["path"],
                    line_number=hit["line_number"],
                    content=hit["content"],
                    score=hit["score"],
                    source="graphify",
                    metadata=hit.get("metadata", {}),
                )
            )

        if passport and PassportResolver:
            results = PassportResolver.filter_results(results, passport)

        return results

    def search_everything(
        self,
        query: str,
        limit: int = 10,
        passport: Optional[str] = None,
    ) -> List[SearchResult]:
        """Broad full-text search across all workspace and code files using Tantivy BM25.

        Args:
            query: Full-text or boolean query
            limit: Maximum results
            passport: Optional passport partition tag ('cloud', 'ml', 'kubernetes', 'skill')

        Returns:
            List of SearchResult objects
        """
        results = self.search_tantivy(query=query, limit=limit)
        if passport and PassportResolver:
            results = PassportResolver.filter_results(results, passport)
        return results

    def get_router_stats(self) -> Dict[str, Any]:
        """Get statistics about router and all indexed engines.

        Returns:
            Dictionary with stats for ripgrep, chroma, tantivy, and graphify
        """
        stats = {
            "ripgrep_available": self.rg_searcher.rg_available,
            "semantic_available": True,
            "tantivy_available": bool(self.tantivy_searcher and getattr(self.tantivy_searcher, "is_available", False)),
            "graphify_available": bool(self.graphify_searcher and getattr(self.graphify_searcher, "is_available", False)),
        }

        try:
            semantic_stats = self.semantic_provider.get_stats(self.collection_name)
            stats["semantic_stats"] = semantic_stats
        except Exception as e:
            logger.warning(f"Failed to get semantic stats: {e}")
            stats["semantic_available"] = False

        if self.tantivy_searcher and hasattr(self.tantivy_searcher, "get_stats"):
            stats["tantivy_stats"] = self.tantivy_searcher.get_stats()

        if self.graphify_searcher and hasattr(self.graphify_searcher, "get_stats"):
            stats["graphify_stats"] = self.graphify_searcher.get_stats()

        return stats

        return stats


if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    print("=== Unified Search Router Demo ===\n")

    # Initialize router
    router = UnifiedSearchRouter(".", ".chroma")

    # Example 1: Hybrid search
    print("Example 1: Hybrid Search (keyword + semantic)")
    results = router.search_hybrid("def deploy", limit=5, curate_for_llm=False)
    print(f"Found {len(results)} results")
    for result in results[:3]:
        print(f"  {result.id}: {result.content[:50]}")

    print("\n" + "=" * 60)

    # Example 2: Code search only
    print("\nExample 2: Code Search (ripgrep only)")
    results = router.search_code("def ", language="python", limit=5)
    print(f"Found {len(results)} results")
    for result in results[:3]:
        print(f"  {result.id}: {result.content[:50]}")

    print("\n" + "=" * 60)

    # Example 3: Semantic search
    print("\nExample 3: Semantic Search (ChromaDB only)")
    results = router.search_semantic("how to deploy", limit=3)
    print(f"Found {len(results)} results")
    for result in results:
        print(f"  {result.id}: {result.content[:50]}")

    print("\n" + "=" * 60)

    # Example 4: Router stats
    print("\nRouter Statistics:")
    stats = router.get_router_stats()
    print(f"  Ripgrep available: {stats['ripgrep_available']}")
    if "semantic_stats" in stats:
        print(f"  Semantic documents: {stats['semantic_stats'].get('document_count', 'N/A')}")
