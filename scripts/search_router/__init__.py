"""
search_router package — Unified hybrid search (ripgrep + ChromaDB) and MCP tools.
"""

import sys
import os

_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_SCRIPTS_DIR = os.path.dirname(_CURRENT_DIR)
_INDEXING_DIR = os.path.join(_SCRIPTS_DIR, "indexing")
_REPO_ROOT = os.path.dirname(_SCRIPTS_DIR)

for _d in [_CURRENT_DIR, _INDEXING_DIR, _SCRIPTS_DIR, _REPO_ROOT]:
    if _d not in sys.path:
        sys.path.insert(0, _d)

from .search_router import (
    UnifiedSearchRouter,
    QueryType,
    SearchResult,
    QueryAnalysis,
    QueryAnalyzer,
    ResultDeduplicator,
    ResultRanker,
    LLMCurator,
    get_provider,
)
from .livetext import RipgrepSearcher, SearchMatch
from .mcp_search_tools import MCPSearchTools, MCP_TOOLS, create_mcp_handlers
from .mcp_tool_adapter import MCPSearchAdapter
from .mcp_search_router import SearchRouter

__all__ = [
    "UnifiedSearchRouter",
    "QueryType",
    "SearchResult",
    "QueryAnalysis",
    "QueryAnalyzer",
    "ResultDeduplicator",
    "ResultRanker",
    "LLMCurator",
    "RipgrepSearcher",
    "SearchMatch",
    "MCPSearchTools",
    "MCP_TOOLS",
    "create_mcp_handlers",
    "MCPSearchAdapter",
    "SearchRouter",
    "get_provider",
]
