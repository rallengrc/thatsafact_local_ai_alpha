#!/usr/bin/env python3
"""
tantivy_searcher.py — Tantivy BM25 inverted index searcher for broad workspace search.

Provides ultra-fast full-text inverted index querying across markdown documents,
configuration files, and code repositories.

Features:
- Rust-powered BM25 inverted index querying (<5ms latency)
- Multi-field scoring (title, body, path, repo)
- Snippet and highlight generation
- Graceful degradation if index is unbuilt
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    import tantivy
    from tantivy import Document, Index, SchemaBuilder

    TANTIVY_AVAILABLE = True
except ImportError:
    TANTIVY_AVAILABLE = False
    Index = None
    Document = None
    SchemaBuilder = None


def get_tantivy_schema():
    """Build standardized Tantivy schema for workspace indexing."""
    if not TANTIVY_AVAILABLE:
        return None
    builder = SchemaBuilder()
    builder.add_text_field("doc_id", stored=True)
    builder.add_text_field("path", stored=True)
    builder.add_text_field("title", stored=True)
    builder.add_text_field("body", stored=True)
    builder.add_text_field("extension", stored=True)
    builder.add_text_field("repo", stored=True)
    builder.add_integer_field("line_number", stored=True, indexed=True)
    return builder.build()


class TantivySearcher:
    """Fast BM25 full-text searcher powered by Tantivy."""

    def __init__(self, index_path: str = ".tantivy"):
        """Initialize Tantivy searcher.

        Args:
            index_path: Directory path where Tantivy index is stored.
        """
        self.index_path = Path(index_path).resolve()
        self.is_available = TANTIVY_AVAILABLE
        self._index: Optional[Any] = None
        self._schema = get_tantivy_schema() if self.is_available else None

        if self.is_available and self.index_path.exists():
            self._load_index()

    def _load_index(self) -> bool:
        """Load an existing Tantivy index from disk."""
        if not self.is_available or not self.index_path.exists():
            return False
        try:
            self._index = Index(self._schema, str(self.index_path))
            return True
        except Exception as e:
            logger.warning(f"Could not load Tantivy index from {self.index_path}: {e}")
            self._index = None
            return False

    @property
    def has_index(self) -> bool:
        """Return True if index exists and is loaded."""
        if self._index is None and self.is_available and self.index_path.exists():
            self._load_index()
        return self._index is not None

    def _parse_query_robust(self, query: str, search_fields: List[str]) -> Optional[Any]:
        """Parse query with automatic fallback sanitization for code punctuation and boolean syntax."""
        import re
        if not query or not query.strip():
            return None

        # 1. Attempt standard query parsing
        try:
            return self._index.parse_query(query, search_fields)
        except Exception:
            pass

        # 2. Strip reserved punctuation / symbols (e.g. def test_(), foo:bar, --flag)
        cleaned = re.sub(r"[^\w\s]", " ", query).strip()
        cleaned = re.sub(r"\b(AND|OR|NOT)\b\s*$", "", cleaned, flags=re.IGNORECASE).strip()
        if cleaned:
            try:
                return self._index.parse_query(cleaned, search_fields)
            except Exception:
                pass

        # 3. Strip standalone boolean operators and search keywords
        tokens = [t for t in cleaned.split() if t.upper() not in ("AND", "OR", "NOT")]
        if tokens:
            try:
                return self._index.parse_query(" ".join(tokens), search_fields)
            except Exception as e:
                logger.debug(f"Tantivy query parse fallback failed for '{query}': {e}")

        return None

    def search(
        self,
        query: str,
        limit: int = 10,
        fields: Optional[List[str]] = None,
        snippet_chars: int = 300,
    ) -> List[Dict[str, Any]]:
        """Search the Tantivy inverted index.

        Args:
            query: Keyword query string.
            limit: Maximum number of results.
            fields: Target fields to match (defaults to title, body, path).
            snippet_chars: Max characters to extract for snippet.

        Returns:
            List of result dicts with doc_id, path, line_number, title, content, score, repo.
        """
        if not self.is_available:
            logger.debug("Tantivy is not installed; returning empty results")
            return []

        if not self.has_index:
            logger.debug(f"Tantivy index at {self.index_path} not found or uninitialized")
            return []

        search_fields = fields or ["title", "body", "path"]

        parsed_query = self._parse_query_robust(query, search_fields)
        if not parsed_query:
            return []

        try:
            searcher = self._index.searcher()
            search_result = searcher.search(parsed_query, limit)

            hits = []
            for score, doc_address in search_result.hits:
                doc = searcher.doc(doc_address)
                doc_dict = doc.to_dict() if hasattr(doc, "to_dict") else {}
                doc_path = doc_dict.get("path", [""])[0] if doc_dict.get("path") else ""
                title = doc_dict.get("title", [""])[0] if doc_dict.get("title") else ""
                body = doc_dict.get("body", [""])[0] if doc_dict.get("body") else ""
                extension = doc_dict.get("extension", [""])[0] if doc_dict.get("extension") else ""
                repo = doc_dict.get("repo", [""])[0] if doc_dict.get("repo") else "workspace"
                line_nums = doc_dict.get("line_number", [1])
                line_number = line_nums[0] if line_nums else 1

                # Generate clean excerpt
                excerpt = body[:snippet_chars]
                if len(body) > snippet_chars:
                    excerpt += "..."

                hits.append(
                    {
                        "id": f"{doc_path}:{line_number}",
                        "path": doc_path,
                        "line_number": line_number,
                        "title": title,
                        "content": excerpt,
                        "score": float(score),
                        "source": "tantivy",
                        "metadata": {
                            "title": title,
                            "repo": repo,
                            "extension": extension,
                        },
                    }
                )

            return hits
        except Exception as e:
            logger.error(f"Tantivy search failed for query '{query}': {e}")
            return []

    def get_stats(self) -> Dict[str, Any]:
        """Return index statistics."""
        if not self.is_available:
            return {"available": False, "reason": "tantivy package not installed"}
        if not self.has_index:
            return {"available": True, "indexed": False, "index_path": str(self.index_path)}

        try:
            searcher = self._index.searcher()
            return {
                "available": True,
                "indexed": True,
                "index_path": str(self.index_path),
                "num_docs": getattr(searcher, "num_docs", 0),
            }
        except Exception as e:
            return {"available": True, "indexed": True, "error": str(e)}
