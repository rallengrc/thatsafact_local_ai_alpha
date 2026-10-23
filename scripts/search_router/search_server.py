#!/usr/bin/env python3
"""
search_server.py — MCP Server exposing hybrid search tools.

MCP 2.x version using MCPServer and stdio transport.

Must be launched with the project virtualenv interpreter (.venv/bin/python3),
since the system python does not have the `mcp` package installed.
"""

import logging
import sys
import os
import json
from pathlib import Path

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.dirname(CURRENT_DIR)
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from common_platform import (
    get_repo_root,
    get_venv_python,
    ensure_venv_site_packages,
)

REPO_ROOT = get_repo_root(SCRIPTS_DIR)
INDEXING_DIR = os.path.join(SCRIPTS_DIR, "indexing")
VENV_DIR = REPO_ROOT / ".venv"
venv_python = get_venv_python(REPO_ROOT)

# Ensure execution under the project .venv interpreter
if sys.prefix != str(VENV_DIR) and venv_python.exists() and Path(sys.executable) != venv_python:
    os.environ["VIRTUAL_ENV"] = str(VENV_DIR)
    os.environ.pop("PYTHONHOME", None)
    try:
        os.execv(str(venv_python), [str(venv_python)] + sys.argv)
    except OSError:
        import subprocess
        sys.exit(subprocess.call([str(venv_python)] + sys.argv))

# Fallback: ensure .venv site-packages is in sys.path
ensure_venv_site_packages(REPO_ROOT)

for d in [CURRENT_DIR, INDEXING_DIR, SCRIPTS_DIR, str(REPO_ROOT)]:
    if d not in sys.path:
        sys.path.insert(0, d)

from mcp.server import MCPServer
from mcp_search_tools import MCPSearchTools

# stdout is reserved for JSON-RPC; all logging must go to stderr
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger(__name__)

mcp = MCPServer("search-router")
tools = MCPSearchTools(
    db_path=os.path.join(str(REPO_ROOT), ".chroma"),
    workspace_root=str(REPO_ROOT),
)


@mcp.tool()
def search_workspace(query: str, limit: int = 10, curate_for_llm: bool = True, language: str = None) -> str:
    """Search the workspace semantically and by code patterns."""
    logger.info(f"search_workspace called: query={query}, limit={limit}")
    result = tools.search_workspace(
        query=query,
        limit=limit,
        curate_for_llm=curate_for_llm,
        language=language,
    )
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
def search_code(pattern: str, language: str = None, limit: int = 20, context_lines: int = 3) -> str:
    """Search code by regex pattern."""
    logger.info(f"search_code called: pattern={pattern}, language={language}")
    result = tools.search_code(
        pattern=pattern,
        language=language,
        limit=limit,
        context_lines=context_lines,
    )
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
def search_semantic(query: str, limit: int = 10, threshold: float = 0.3) -> str:
    """Search semantically using embeddings."""
    logger.info(f"search_semantic called: query={query}, limit={limit}")
    result = tools.search_semantic(
        query=query,
        limit=limit,
        threshold=threshold,
    )
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
def search_symbols(query: str, limit: int = 15, kind: str = None, file_filter: str = None) -> str:
    """Search code symbols (classes, functions, methods) via Graphify AST."""
    logger.info(f"search_symbols called: query={query}, kind={kind}")
    result = tools.search_symbols(
        query=query,
        limit=limit,
        kind=kind,
        file_filter=file_filter,
    )
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
def search_everything(query: str, limit: int = 10) -> str:
    """Broad full-text search across all workspace files using Tantivy BM25."""
    logger.info(f"search_everything called: query={query}, limit={limit}")
    result = tools.search_everything(
        query=query,
        limit=limit,
    )
    return json.dumps(result, indent=2, default=str)


@mcp.tool()
def get_search_stats() -> str:
    """Get statistics about the search index."""
    logger.info("get_search_stats called")
    result = tools.stats()
    return json.dumps(result, indent=2, default=str)


if __name__ == "__main__":
    mcp.run()
