#!/usr/bin/env python3
"""
mcp_examples.py — Usage examples for the MCP search tools.

This file demonstrates how to use each of the 4 MCP search tools
with different queries and parameters.

Run with:
  python3 scripts/mcp_examples.py
"""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from mcp_search_tools import MCPSearchTools


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")


def print_result(title: str, result: dict):
    """Print a formatted result."""
    print(f"{title}")
    print(f"{'-' * 80}")
    if result.get("status") == "error":
        print(f"❌ Error: {result.get('message')}")
    else:
        print(f"✅ Status: {result.get('status')}")
        if "result_count" in result:
            print(f"📊 Results found: {result.get('result_count')}")
        if "query_type" in result:
            print(f"🎯 Query type: {result.get('query_type')}")
            print(f"📈 Confidence: {result.get('routing_confidence', 0):.0%}")
    
    # Show first 2 results
    results = result.get("results", [])
    if results:
        print(f"\n📋 First {min(2, len(results))} result(s):")
        for i, r in enumerate(results[:2], 1):
            if isinstance(r, dict):
                print(f"\n  {i}. {r.get('file', r.get('path', 'unknown'))}:{r.get('line', r.get('line_number', '?'))}")
                content = r.get('content', '')
                if content:
                    print(f"     {content[:70]}...")
                if 'similarity' in r:
                    print(f"     Similarity: {r['similarity']:.1%}")
    print()


def main():
    """Run all examples."""
    tools = MCPSearchTools()
    
    print_section("MCP Search Tools — Usage Examples")
    
    # =========================================================================
    # EXAMPLE 1: Statistics
    # =========================================================================
    print_section("EXAMPLE 1: Get Workspace Statistics")
    print("""
The get_search_stats tool returns information about your indexed workspace
and available search tools. Use this to verify the system is healthy.
    """)
    
    print("Command:")
    print("  tools.stats()")
    print("\nCode:")
    print("  stats = tools.stats()")
    print("  print(json.dumps(stats, indent=2))")
    
    result = tools.stats()
    print("\nResult:")
    print(json.dumps(result, indent=2)[:300] + "...")
    
    # =========================================================================
    # EXAMPLE 2: Code Search - Python Functions
    # =========================================================================
    print_section("EXAMPLE 2: Search for Python Function Definitions")
    print("""
Find all function definitions in Python files. Great for:
  - Finding where functions are defined
  - Code navigation
  - Understanding codebase structure
    """)
    
    print("Command:")
    print("  tools.search_code(")
    print('    pattern="def ",')
    print('    language="python",')
    print('    limit=3,')
    print('    context_lines=2')
    print("  )")
    
    result = tools.search_code(
        pattern="def ",
        language="python",
        limit=3,
        context_lines=2
    )
    print_result("Result:", result)
    
    # =========================================================================
    # EXAMPLE 3: Code Search - Imports
    # =========================================================================
    print_section("EXAMPLE 3: Search for Specific Python Imports")
    print("""
Find where a module is imported. Useful for:
  - Dependency analysis
  - Understanding module usage
  - Refactoring
    """)
    
    print("Command:")
    print("  tools.search_code(")
    print('    pattern="^import|^from",')
    print('    language="python",')
    print('    limit=5')
    print("  )")
    
    result = tools.search_code(
        pattern="^import|^from",
        language="python",
        limit=5
    )
    print_result("Result:", result)
    
    # =========================================================================
    # EXAMPLE 4: Code Search - TypeScript Classes
    # =========================================================================
    print_section("EXAMPLE 4: Search for TypeScript Class Definitions")
    print("""
Find all class definitions in TypeScript. Useful for:
  - Object-oriented structure analysis
  - API interface discovery
  - Type definitions
    """)
    
    print("Command:")
    print("  tools.search_code(")
    print('    pattern="class ",')
    print('    language="typescript",')
    print('    limit=3')
    print("  )")
    
    result = tools.search_code(
        pattern="class ",
        language="typescript",
        limit=3
    )
    print_result("Result:", result)
    
    # =========================================================================
    # EXAMPLE 5: Semantic Search - Architecture
    # =========================================================================
    print_section("EXAMPLE 5: Semantic Search - System Architecture")
    print("""
Search for content semantically related to "system architecture".
This demonstrates natural language understanding. Useful for:
  - Conceptual searching
  - Documentation discovery
  - Understanding design patterns
    """)
    
    print("Command:")
    print("  tools.search_semantic(")
    print('    query="system architecture and design patterns",')
    print('    limit=3,')
    print('    threshold=0.3')
    print("  )")
    
    result = tools.search_semantic(
        query="system architecture and design patterns",
        limit=3,
        threshold=0.3
    )
    print_result("Result:", result)
    
    # =========================================================================
    # EXAMPLE 6: Semantic Search - Deployment
    # =========================================================================
    print_section("EXAMPLE 6: Semantic Search - Kubernetes & Deployment")
    print("""
Find content related to "kubernetes and deployment". 
Uses semantic similarity to find related concepts.
    """)
    
    print("Command:")
    print("  tools.search_semantic(")
    print('    query="kubernetes deployment and orchestration",')
    print('    limit=2,')
    print('    threshold=0.2')
    print("  )")
    
    result = tools.search_semantic(
        query="kubernetes deployment and orchestration",
        limit=2,
        threshold=0.2
    )
    print_result("Result:", result)
    
    # =========================================================================
    # EXAMPLE 7: Hybrid Search - Code Pattern
    # =========================================================================
    print_section("EXAMPLE 7: Hybrid Search - Code Pattern Query")
    print("""
Query "def deploy" - this looks like code, so it routes to ripgrep,
but also searches semantically. Hybrid gives you both perspectives.
    """)
    
    print("Command:")
    print("  tools.search_workspace(")
    print('    query="def deploy",')
    print('    limit=3,')
    print('    curate_for_llm=False')
    print("  )")
    
    result = tools.search_workspace(
        query="def deploy",
        limit=3,
        curate_for_llm=False
    )
    print_result("Result:", result)
    
    # =========================================================================
    # EXAMPLE 8: Hybrid Search - Natural Language
    # =========================================================================
    print_section("EXAMPLE 8: Hybrid Search - Natural Language Query")
    print("""
Query "how to handle errors in async code" - this is natural language,
so it routes to semantic search, but also checks for code patterns.
    """)
    
    print("Command:")
    print("  tools.search_workspace(")
    print('    query="error handling patterns",')
    print('    limit=3,')
    print('    curate_for_llm=True')
    print("  )")
    
    result = tools.search_workspace(
        query="error handling patterns",
        limit=3,
        curate_for_llm=True
    )
    print_result("Result:", result)
    
    # =========================================================================
    # EXAMPLE 9: Hybrid Search with Language Filter
    # =========================================================================
    print_section("EXAMPLE 9: Hybrid Search with Language Filter")
    print("""
Specify a language to focus on Python results only.
This is useful when you know you're looking for a specific technology.
    """)
    
    print("Command:")
    print("  tools.search_workspace(")
    print('    query="async await",')
    print('    language="python",')
    print('    limit=3')
    print("  )")
    
    result = tools.search_workspace(
        query="async await",
        language="python",
        limit=3
    )
    print_result("Result:", result)
    
    # =========================================================================
    # SUMMARY
    # =========================================================================
    print_section("Summary: When to Use Each Tool")
    
    summary = """
┌─ search_code (RIPGREP) ────────────────────────────────────────┐
│ Use when you:                                                  │
│  • Know the exact pattern you're looking for                   │
│  • Need fast, reliable code searching                          │
│  • Want regex pattern matching                                 │
│  • Need a specific programming language                        │
│                                                                │
│ Example: Find all "async def" in Python                        │
│  tools.search_code("async def", language="python")             │
└────────────────────────────────────────────────────────────────┘

┌─ search_semantic (CHROMADB) ───────────────────────────────────┐
│ Use when you:                                                  │
│  • Need natural language understanding                         │
│  • Don't know exact terms to search for                        │
│  • Want conceptually similar content                           │
│  • Need fuzzy matching                                         │
│                                                                │
│ Example: Find docs about error handling                        │
│  tools.search_semantic("exception handling best practices")    │
└────────────────────────────────────────────────────────────────┘

┌─ search_workspace (HYBRID) ────────────────────────────────────┐
│ Use when you:                                                  │
│  • Aren't sure if query is code or natural language            │
│  • Want best results from both sources                         │
│  • Need intelligent query routing                              │
│  • Want LLM-optimized results                                  │
│                                                                │
│ Example: Search for anything                                   │
│  tools.search_workspace("deployment configuration")            │
└────────────────────────────────────────────────────────────────┘

┌─ get_search_stats (DIAGNOSTICS) ───────────────────────────────┐
│ Use when you:                                                  │
│  • Need to check system health                                 │
│  • Want indexed document count                                 │
│  • Need to verify tool availability                            │
│  • Diagnosing issues                                           │
│                                                                │
│ Example: Get system info                                       │
│  tools.stats()                                                 │
└────────────────────────────────────────────────────────────────┘
    """
    print(summary)
    
    print_section("✅ All examples completed successfully!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
