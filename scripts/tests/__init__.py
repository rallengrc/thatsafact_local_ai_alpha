"""
tests package — Test suites for indexing, search routing, MCP tools, and utilities.
"""

import sys
import os

_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_SCRIPTS_DIR = os.path.dirname(_CURRENT_DIR)
_INDEXING_DIR = os.path.join(_SCRIPTS_DIR, "indexing")
_SEARCH_DIR = os.path.join(_SCRIPTS_DIR, "search_router")
_AUTOMATION_DIR = os.path.join(_SCRIPTS_DIR, "automation")
_REPO_ROOT = os.path.dirname(_SCRIPTS_DIR)

for _d in [_CURRENT_DIR, _SEARCH_DIR, _INDEXING_DIR, _AUTOMATION_DIR, _SCRIPTS_DIR, _REPO_ROOT]:
    if _d not in sys.path:
        sys.path.insert(0, _d)
