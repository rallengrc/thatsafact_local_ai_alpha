#!/usr/bin/env python3
"""
graphify_searcher.py — Graphify Tree-sitter AST & code knowledge graph searcher.

Provides code intelligence, symbol lookups, AST hierarchy inspection, caller/callee
traversal, and local semantic reasoning powered by Ollama (qwen3.8:27b).

Key capabilities:
- Tree-sitter AST extraction for classes, methods, functions, and imports
- Line-accurate symbol location (L<line>)
- Multi-repo code symbol search across workspace and code/
- Call-graph and dependency edge traversal via NetworkX
- 100% Local LLM enrichment via Ollama (zero cloud egress & zero cloud spend)
"""

import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

# Ensure code/graphify is on sys.path
_REPO_ROOT = Path(__file__).resolve().parents[2]
_GRAPHIFY_PATH = _REPO_ROOT / "code" / "graphify"
if str(_GRAPHIFY_PATH) not in sys.path and _GRAPHIFY_PATH.exists():
    sys.path.insert(0, str(_GRAPHIFY_PATH))

try:
    from graphify.extract import extract_python
    from graphify.extractors.markdown import extract_markdown
    import networkx as nx

    GRAPHIFY_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Graphify / NetworkX not fully importable: {e}")
    GRAPHIFY_AVAILABLE = False
    extract_python = None
    extract_markdown = None
    nx = None

# Ollama local configuration
OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen3.8:27b")


class GraphifySearcher:
    """AST code intelligence and knowledge graph searcher."""

    def __init__(
        self,
        workspace_root: str = ".",
        graph_path: str = ".graphify/graph.json",
        ollama_model: str = OLLAMA_MODEL,
        ollama_base_url: str = OLLAMA_BASE_URL,
    ):
        """Initialize Graphify searcher.

        Args:
            workspace_root: Root workspace directory.
            graph_path: Path to serialized graph JSON.
            ollama_model: Local Ollama model identifier.
            ollama_base_url: Local Ollama daemon URL.
        """
        self.workspace_root = Path(workspace_root).resolve()
        self.graph_path = Path(graph_path)
        if not self.graph_path.is_absolute():
            self.graph_path = self.workspace_root / self.graph_path

        self.ollama_model = ollama_model
        self.ollama_base_url = ollama_base_url.rstrip("/")
        self.is_available = GRAPHIFY_AVAILABLE
        self._graph: Optional[Any] = None

        if self.is_available:
            self._load_or_init_graph()

    def _load_or_init_graph(self) -> None:
        """Load graph from disk or initialize empty DiGraph."""
        if nx is None:
            return

        if self.graph_path.exists():
            try:
                with open(self.graph_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                g = nx.DiGraph()
                for node in data.get("nodes", []):
                    g.add_node(node["id"], **node)
                for edge in data.get("edges", []):
                    g.add_edge(edge["source"], edge["target"], **edge)
                self._graph = g
                logger.info(
                    f"Loaded Graphify graph from {self.graph_path}: "
                    f"{g.number_of_nodes()} nodes, {g.number_of_edges()} edges"
                )
                return
            except Exception as e:
                logger.warning(f"Could not load graph from {self.graph_path}: {e}")

        self._graph = nx.DiGraph()

    @property
    def has_graph(self) -> bool:
        """Return True if graph contains nodes."""
        return self._graph is not None and self._graph.number_of_nodes() > 0

    def parse_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Extract AST nodes and edges from a single Python or Markdown file."""
        if not self.is_available:
            return []
        try:
            path_obj = Path(file_path)
            ext = path_obj.suffix.lower()
            if ext == ".py" and extract_python is not None:
                res = extract_python(path_obj, root=self.workspace_root)
            elif ext == ".md" and extract_markdown is not None:
                res = extract_markdown(path_obj)
            else:
                return []

            nodes = res.get("nodes", [])
            edges = res.get("edges", [])

            if self._graph is not None:
                for n in nodes:
                    self._graph.add_node(n["id"], **n)
                for e in edges:
                    self._graph.add_edge(e["source"], e["target"], **e)

            return nodes
        except Exception as e:
            logger.debug(f"Failed to parse {file_path} with Graphify: {e}")
            return []

    def search_symbols(
        self,
        query: str,
        limit: int = 15,
        kind: Optional[str] = None,
        file_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Search code symbols (classes, functions, methods) and document sections in the AST graph.

        Args:
            query: Symbol name, section title, substring, or regex.
            limit: Maximum results to return.
            kind: Optional filter ("class", "function", "method", "section", "document").
            file_filter: Optional substring match on file path.

        Returns:
            List of SearchResult-compatible dicts.
        """
        if not self.is_available or self._graph is None:
            return []

        # If graph is empty, attempt a quick scan of scripts/
        if self._graph.number_of_nodes() == 0:
            scripts_dir = self.workspace_root / "scripts"
            if scripts_dir.exists():
                for py_path in scripts_dir.glob("**/*.py"):
                    self.parse_file(py_path)

        query_lower = query.lower().strip()
        is_regex = any(c in query for c in r".*+?[]^$")
        pattern = None
        if is_regex:
            try:
                pattern = re.compile(query, re.IGNORECASE)
            except re.error:
                pattern = None

        matches: List[Tuple[float, Dict[str, Any]]] = []

        for node_id, data in self._graph.nodes(data=True):
            label = str(data.get("label", ""))
            source_file = str(data.get("source_file", ""))
            source_loc = str(data.get("source_location", ""))

            # Skip nodes without source file or without location
            if not source_file or not source_loc:
                continue

            # Apply file filter if provided
            if file_filter and file_filter not in source_file:
                continue

            # Determine entity kind
            is_class = data.get("_callable_class", False) or "class" in data.get("kind", "")
            is_callable = data.get("_callable", False) or "def" in data.get("kind", "")
            is_heading = data.get("node_kind") == "heading" or "heading" in data.get("kind", "")
            is_doc = data.get("node_kind") == "page" or data.get("file_type") in ("document", "doc")

            if is_class:
                entity_kind = "class"
            elif is_callable:
                entity_kind = "function"
            elif is_heading:
                entity_kind = "section"
            elif is_doc:
                entity_kind = "document"
            else:
                entity_kind = "symbol"

            if kind:
                k_lower = kind.lower()
                if k_lower == "class" and not is_class:
                    continue
                if k_lower in ("function", "method") and (not is_callable or is_class):
                    continue
                if k_lower in ("section", "heading") and not is_heading:
                    continue
                if k_lower in ("document", "doc", "page") and not is_doc:
                    continue

            # Match label
            score = 0.0
            label_lower = label.lower()

            if pattern and pattern.search(label):
                score = 0.95
            elif label_lower == query_lower:
                score = 1.0  # Exact match
            elif label_lower.startswith(query_lower):
                score = 0.85  # Prefix match
            elif query_lower in label_lower:
                score = 0.70  # Substring match
            elif query_lower in node_id.lower():
                score = 0.60  # ID match

            if score > 0.0:
                # Extract line number from L<digits>
                line_number = 1
                if source_loc.startswith("L") and source_loc[1:].isdigit():
                    line_number = int(source_loc[1:])

                # Read preview snippet from source file if accessible
                full_file_path = self.workspace_root / source_file
                content_excerpt = f"{entity_kind.upper()} {label} defined at {source_file}:{line_number}"
                if full_file_path.exists():
                    try:
                        with open(full_file_path, "r", encoding="utf-8", errors="replace") as f:
                            lines = f.readlines()
                            start_idx = max(0, line_number - 1)
                            end_idx = min(len(lines), line_number + 10)
                            snippet_lines = lines[start_idx:end_idx]
                            if snippet_lines:
                                content_excerpt = "".join(snippet_lines).strip()
                    except Exception:
                        pass

                result_dict = {
                    "id": f"{source_file}:{line_number}",
                    "path": source_file,
                    "line_number": line_number,
                    "content": content_excerpt,
                    "score": score,
                    "source": "graphify",
                    "metadata": {
                        "symbol": label,
                        "kind": entity_kind,
                        "node_id": node_id,
                        "source_location": source_loc,
                    },
                }
                matches.append((score, result_dict))

        # Sort descending by score
        matches.sort(key=lambda x: x[0], reverse=True)
        return [m[1] for m in matches[:limit]]

    def get_neighbors(self, node_id_or_label: str) -> Dict[str, List[Dict[str, Any]]]:
        """Get callers, callees, and dependencies for a symbol."""
        if not self.is_available or self._graph is None:
            return {"callers": [], "callees": [], "dependencies": []}

        target_node = None
        for n, d in self._graph.nodes(data=True):
            if n == node_id_or_label or d.get("label") == node_id_or_label:
                target_node = n
                break

        if not target_node:
            return {"callers": [], "callees": [], "dependencies": []}

        callers = []
        for pred in self._graph.predecessors(target_node):
            callers.append(self._graph.nodes[pred])

        callees = []
        for succ in self._graph.successors(target_node):
            callees.append(self._graph.nodes[succ])

        return {"callers": callers, "callees": callees}

    def ask_local_llm(
        self,
        prompt: str,
        timeout_seconds: int = 45,
    ) -> Optional[str]:
        """Query local Ollama LLM (qwen3.8:27b) with zero cloud egress/spend.

        Args:
            prompt: Question or instruction for the code intelligence model.
            timeout_seconds: Max seconds to wait for generation.

        Returns:
            Clean text reply from the local model, or None if Ollama is unreachable.
        """
        import urllib.request
        import urllib.error

        url = f"{self.ollama_base_url}/api/generate"
        payload = json.dumps(
            {
                "model": self.ollama_model,
                "prompt": prompt,
                "stream": False,
            }
        ).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("response", "").strip()
        except Exception as e:
            logger.debug(f"Local Ollama query failed ({self.ollama_model}): {e}")
            return None

    def get_stats(self) -> Dict[str, Any]:
        """Return Graphify AST statistics."""
        if not self.is_available:
            return {"available": False, "reason": "graphify / tree-sitter not installed"}

        nodes_count = self._graph.number_of_nodes() if self._graph else 0
        edges_count = self._graph.number_of_edges() if self._graph else 0

        return {
            "available": True,
            "nodes": nodes_count,
            "edges": edges_count,
            "graph_path": str(self.graph_path),
            "local_llm_model": self.ollama_model,
            "local_llm_url": self.ollama_base_url,
        }
