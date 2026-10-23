"""
indexing package — Workspace document scanning, filtering, and vector database providers.
"""

import sys
import os

_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_SCRIPTS_DIR = os.path.dirname(_CURRENT_DIR)
_REPO_ROOT = os.path.dirname(_SCRIPTS_DIR)

for _d in [_CURRENT_DIR, _SCRIPTS_DIR, _REPO_ROOT]:
    if _d not in sys.path:
        sys.path.insert(0, _d)

from .vectordb_provider import (
    VectorDBProvider,
    ChromaDBProvider,
    get_provider,
)
from .index_workspace import WorkspaceIndexer, FileInfo

__all__ = [
    "VectorDBProvider",
    "ChromaDBProvider",
    "get_provider",
    "WorkspaceIndexer",
    "FileInfo",
]
