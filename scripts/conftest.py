"""
pytest configuration for scripts/ directory.
Ensures all subdirectories are available on sys.path.
"""

import sys
import os

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPTS_DIR)

for sub in ["search_router", "indexing", "automation", "tests"]:
    p = os.path.join(SCRIPTS_DIR, sub)
    if p not in sys.path:
        sys.path.insert(0, p)

if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
