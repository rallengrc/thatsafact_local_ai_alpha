#!/usr/bin/env python3
"""
index_graphify.py — Extract Tree-sitter AST and build code knowledge graph.

Uses Tree-sitter parsers to extract structural code entities (classes, functions,
methods, and dependencies) across the workspace and code repositories, saving the
resulting graph to `.graphify/graph.json`.

Enforces local Ollama LLM (`qwen3.8:27b` via `http://localhost:11434`) for any semantic
enrichment, guaranteeing ZERO cloud token expenditure and zero cloud network transit.

Usage:
    .venv/bin/python3 scripts/indexing/index_graphify.py --workspace . --graph-path .graphify/graph.json
    .venv/bin/python3 scripts/indexing/index_graphify.py --stats
    .venv/bin/python3 scripts/indexing/index_graphify.py --clear
"""

import argparse
import json
import logging
import os
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_SCRIPTS_DIR = os.path.dirname(_CURRENT_DIR)
_ROUTER_DIR = os.path.join(_SCRIPTS_DIR, "search_router")
_REPO_ROOT = os.path.dirname(_SCRIPTS_DIR)
_GRAPHIFY_DIR = os.path.join(_REPO_ROOT, "code", "graphify")

for _p in [_CURRENT_DIR, _SCRIPTS_DIR, _ROUTER_DIR, _GRAPHIFY_DIR]:
    if _p not in sys.path and os.path.exists(_p):
        sys.path.insert(0, _p)

from common_platform import normalize_posix_path, ensure_venv_site_packages
ensure_venv_site_packages()

try:
    from graphify.extract import extract_python
    from graphify.extractors.markdown import extract_markdown
    import networkx as nx

    GRAPHIFY_AVAILABLE = True
except ImportError:
    GRAPHIFY_AVAILABLE = False
    extract_python = None
    extract_markdown = None
    nx = None

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("index_graphify")

DEFAULT_TARGET_DIRS = [
    "scripts",
    "Projects",
    "Resources",
    "Areas",
    "memories",
    "code/flyte-vscode-demo",
    "code/flytekit/plugins/flytekit-ray",
    "code/flytesnacks/examples/ray_plugin",
    "code/flyte-sdk/src",
    "code/enhancements/reps",
    "code/unionai-docs",
    "code/awesome-copilot",
]
EXCLUDE_DIRS = {".git", ".venv", ".chroma", ".tantivy", ".graphify", "__pycache__", "Archives"}


class GraphifyIndexer:
    """Discovers and parses Python source files and Markdown docs into a Graphify AST graph."""

    def __init__(
        self,
        workspace_root: str = ".",
        graph_path: str = ".graphify/graph.json",
        target_dirs: Optional[List[str]] = None,
        ollama_model: str = "qwen3.8:27b",
        ollama_base_url: str = "http://localhost:11434",
    ):
        self.workspace_root = Path(workspace_root).resolve()
        self.graph_path = Path(graph_path)
        if not self.graph_path.is_absolute():
            self.graph_path = self.workspace_root / self.graph_path

        self.target_dirs = target_dirs or DEFAULT_TARGET_DIRS
        self.ollama_model = ollama_model
        self.ollama_base_url = ollama_base_url

    def discover_files(self) -> List[Path]:
        """Find Python and Markdown files in specified target directories.

        Safely skips nonexistent directories without raising errors, ensuring clean
        execution for team members who may not have all optional sub-repos cloned.
        """
        discovered: List[Path] = []
        for target_dir_name in self.target_dirs:
            target_path = self.workspace_root / target_dir_name
            if not target_path.exists():
                logger.debug(f"Target directory '{target_dir_name}' not present on disk; safely skipping.")
                continue

            for root, dirs, files in os.walk(target_path):
                dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith(".")]
                for f in files:
                    ext = Path(f).suffix.lower()
                    if ext in (".py", ".md"):
                        discovered.append(Path(root) / f)

        return discovered

    def index(self, clear_first: bool = False) -> Dict[str, Any]:
        """Parse discovered files and save the graph to disk."""
        if not GRAPHIFY_AVAILABLE or extract_python is None or nx is None:
            logger.warning("Graphify or NetworkX is not available in environment. Skipping Graphify indexing.")
            return {"status": "skipped", "reason": "Graphify or NetworkX not available in environment"}

        if clear_first and self.graph_path.parent.exists():
            shutil.rmtree(self.graph_path.parent, ignore_errors=True)

        self.graph_path.parent.mkdir(parents=True, exist_ok=True)

        g = nx.DiGraph()
        files = self.discover_files()
        logger.info(f"Discovered {len(files)} files (Python + Markdown) for AST extraction")

        parsed_files = 0
        error_count = 0
        total_nodes = 0
        total_edges = 0

        for file_path in files:
            try:
                ext = file_path.suffix.lower()
                if ext == ".py":
                    res = extract_python(file_path, root=self.workspace_root)
                elif ext == ".md" and extract_markdown is not None:
                    res = extract_markdown(file_path)
                else:
                    continue

                nodes = res.get("nodes", [])
                edges = res.get("edges", [])

                for n in nodes:
                    norm_id = normalize_posix_path(n["id"])
                    n["id"] = norm_id
                    for k in ("source_file", "path", "relative_path", "file"):
                        if k in n and isinstance(n[k], (str, Path)):
                            n[k] = normalize_posix_path(n[k])
                    g.add_node(norm_id, **n)
                    total_nodes += 1
                for e in edges:
                    norm_src = normalize_posix_path(e["source"])
                    norm_dst = normalize_posix_path(e["target"])
                    e["source"] = norm_src
                    e["target"] = norm_dst
                    for k in ("source_file", "path", "relative_path", "file"):
                        if k in e and isinstance(e[k], (str, Path)):
                            e[k] = normalize_posix_path(e[k])
                    g.add_edge(norm_src, norm_dst, **e)
                    total_edges += 1

                parsed_files += 1
            except Exception as e:
                logger.warning(f"Error parsing {file_path}: {e}")
                error_count += 1

        # Serialize graph to JSON
        nodes_list = []
        for node_id, data in g.nodes(data=True):
            node_record = dict(data)
            norm_id = normalize_posix_path(node_id)
            node_record["id"] = norm_id
            for k in ("source_file", "path", "relative_path", "file"):
                if k in node_record and isinstance(node_record[k], (str, Path)):
                    node_record[k] = normalize_posix_path(node_record[k])
            nodes_list.append(node_record)

        edges_list = []
        for src, dst, data in g.edges(data=True):
            edge_record = dict(data)
            edge_record["source"] = normalize_posix_path(src)
            edge_record["target"] = normalize_posix_path(dst)
            for k in ("source_file", "path", "relative_path", "file"):
                if k in edge_record and isinstance(edge_record[k], (str, Path)):
                    edge_record[k] = normalize_posix_path(edge_record[k])
            edges_list.append(edge_record)

        graph_payload = {
            "meta": {
                "nodes_count": len(nodes_list),
                "edges_count": len(edges_list),
                "files_parsed": parsed_files,
                "local_llm_model": self.ollama_model,
                "local_llm_url": self.ollama_base_url,
            },
            "nodes": nodes_list,
            "edges": edges_list,
        }

        with open(self.graph_path, "w", encoding="utf-8") as f:
            json.dump(graph_payload, f, indent=2)

        logger.info(
            f"Saved Graphify AST graph to {self.graph_path}: "
            f"{len(nodes_list)} nodes, {len(edges_list)} edges across {parsed_files} files"
        )

        return {
            "nodes": len(nodes_list),
            "edges": len(edges_list),
            "files_parsed": parsed_files,
            "errors": error_count,
        }

    def stats(self) -> Dict[str, Any]:
        """Return graph stats from disk."""
        if not self.graph_path.exists():
            return {"exists": False, "graph_path": str(self.graph_path)}

        try:
            with open(self.graph_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            meta = data.get("meta", {})
            return {
                "exists": True,
                "graph_path": str(self.graph_path),
                "nodes": meta.get("nodes_count", len(data.get("nodes", []))),
                "edges": meta.get("edges_count", len(data.get("edges", []))),
                "files_parsed": meta.get("files_parsed", 0),
                "local_llm_model": meta.get("local_llm_model", self.ollama_model),
            }
        except Exception as e:
            return {"exists": True, "error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Graphify Tree-sitter AST Indexer")
    parser.add_argument("--workspace", default=".", help="Workspace root path")
    parser.add_argument("--graph-path", default=".graphify/graph.json", help="Output graph.json path")
    parser.add_argument("--clear", action="store_true", help="Clear graph before running")
    parser.add_argument("--stats", action="store_true", help="Print graph statistics and exit")
    parser.add_argument(
        "--target-dirs",
        nargs="+",
        default=DEFAULT_TARGET_DIRS,
        help="Directories to extract Python AST from",
    )
    parser.add_argument("--ollama-model", default="qwen3.8:27b", help="Local Ollama model")

    args = parser.parse_args()
    indexer = GraphifyIndexer(
        workspace_root=args.workspace,
        graph_path=args.graph_path,
        target_dirs=args.target_dirs,
        ollama_model=args.ollama_model,
    )

    if args.stats:
        s = indexer.stats()
        print(f"Graphify Stats:\n  Path: {s.get('graph_path')}\n  Nodes: {s.get('nodes', 0)}\n  Edges: {s.get('edges', 0)}")
        return

    results = indexer.index(clear_first=args.clear)
    if results.get("status") == "skipped":
        print(f"Graphify Indexing skipped: {results.get('reason')}")
        return
    print(f"Graphify Indexing completed: {results['nodes']} nodes, {results['edges']} edges across {results['files_parsed']} files.")


if __name__ == "__main__":
    main()
