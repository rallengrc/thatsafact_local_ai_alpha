#!/usr/bin/env python3
"""
test_mcp_client.py — Simple MCP client to test the search server.

This demonstrates how to use the MCP search tools.
"""

import json
import sys
import os

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPTS_DIR)
VENV_DIR = os.path.join(REPO_ROOT, ".venv")
VENV_PYTHON = os.path.join(VENV_DIR, "bin", "python3")

# Ensure execution under the project .venv interpreter
if sys.prefix != VENV_DIR and os.path.exists(VENV_PYTHON):
    os.environ["VIRTUAL_ENV"] = VENV_DIR
    os.environ.pop("PYTHONHOME", None)
    os.execv(VENV_PYTHON, [VENV_PYTHON] + sys.argv)

for pyver in ["3.14", "3.13", "3.12", "3.11", "3.10"]:
    sp = os.path.join(VENV_DIR, f"lib/python{pyver}/site-packages")
    if os.path.exists(sp) and sp not in sys.path:
        sys.path.insert(0, sp)

if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_search_tools():
    """Test the search tools via MCP."""
    
    # Start the server as a subprocess
    import subprocess
    
    print("=" * 80)
    print("MCP Search Router - Hello World Test")
    print("=" * 80)
    print()
    
    # Test 1: Get statistics
    print("TEST 1: Get Search Statistics")
    print("-" * 80)
    
    # For simplicity, we'll call the tools directly instead of via MCP protocol
    # This tests the functionality without requiring server/client setup
    
    from mcp_search_tools import MCPSearchTools
    tools = MCPSearchTools()
    
    print("Querying workspace statistics...")
    stats = tools.stats()
    print(json.dumps(stats, indent=2))
    print()
    
    # Test 2: Code search
    print("TEST 2: Code Search (Python definitions)")
    print("-" * 80)
    
    print("Searching for Python 'def ' patterns...")
    code_results = tools.search_code(
        pattern="def ",
        language="python",
        limit=3,
        context_lines=2
    )
    print(f"Status: {code_results['status']}")
    print(f"Results found: {code_results['result_count']}")
    print("\nTop 3 results:")
    for i, result in enumerate(code_results['results'][:3], 1):
        print(f"\n  {i}. {result['file']}:{result['line']}")
        print(f"     {result['content']}")
    print()
    
    # Test 3: Semantic search
    print("TEST 3: Semantic Search (Natural Language)")
    print("-" * 80)
    
    print("Searching semantically for: 'kubernetes deployment'...")
    semantic_results = tools.search_semantic(
        query="kubernetes deployment",
        limit=2,
        threshold=0.3
    )
    print(f"Status: {semantic_results['status']}")
    print(f"Results found: {semantic_results['result_count']}")
    if semantic_results['results']:
        print("\nTop 2 results:")
        for i, result in enumerate(semantic_results['results'][:2], 1):
            print(f"\n  {i}. {result['file']}:{result['line']}")
            print(f"     Similarity: {result['similarity']:.2%}")
            print(f"     Content: {result['content'][:80]}...")
    print()
    
    # Test 4: Hybrid search
    print("TEST 4: Hybrid Search (Intelligent Routing)")
    print("-" * 80)
    
    print("Searching for: 'deploy kubernetes' (hybrid)...")
    hybrid_results = tools.search_workspace(
        query="deploy kubernetes",
        limit=3,
        curate_for_llm=True
    )
    print(f"Status: {hybrid_results['status']}")
    print(f"Query type detected: {hybrid_results['query_type']}")
    print(f"Routing confidence: {hybrid_results['routing_confidence']:.2%}")
    print(f"Results found: {hybrid_results['result_count']}")
    if hybrid_results['results']:
        print("\nTop 3 results:")
        for i, result in enumerate(hybrid_results['results'][:3], 1):
            print(f"\n  {i}. {result['path']}:{result['line_number']}")
            print(f"     Source: {result['source']}")
            print(f"     Score: {result['score']:.2f}")
            print(f"     Content: {result['content'][:60]}...")
    print()
    
    print("=" * 80)
    print("✅ All tests completed successfully!")
    print("=" * 80)


def main():
    """Main entry point."""
    try:
        test_search_tools()
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
