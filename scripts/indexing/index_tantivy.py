#!/usr/bin/env python3
"""
index_tantivy.py — Build Tantivy BM25 inverted index for fast workspace & code search.

Scans workspace files (markdown, code, configs) and writes documents to a Tantivy
inverted index directory (`.tantivy/`).

Usage:
    .venv/bin/python3 scripts/indexing/index_tantivy.py --workspace . --index-path .tantivy
    .venv/bin/python3 scripts/indexing/index_tantivy.py --stats
    .venv/bin/python3 scripts/indexing/index_tantivy.py --clear
"""

import argparse
import logging
import os
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Optional

_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_SCRIPTS_DIR = os.path.dirname(_CURRENT_DIR)
_ROUTER_DIR = os.path.join(_SCRIPTS_DIR, "search_router")
for _p in [_CURRENT_DIR, _SCRIPTS_DIR, _ROUTER_DIR]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from common_platform import ensure_venv_site_packages, normalize_posix_path
ensure_venv_site_packages()

try:
    from tantivy_searcher import get_tantivy_schema, TANTIVY_AVAILABLE
    import tantivy
    from tantivy import Document, Index
except ImportError:
    TANTIVY_AVAILABLE = False
    get_tantivy_schema = None

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("index_tantivy")

INDEXABLE_EXTENSIONS = {
    ".md",
    ".py",
    ".json",
    ".yaml",
    ".yml",
    ".sh",
    ".txt",
    ".rst",
    ".toml",
    ".go",
    ".rs",
    ".ts",
    ".js",
}

EXCLUDE_DIRS = {
    ".git",
    ".venv",
    ".chroma",
    ".tantivy",
    ".graphify",
    "__pycache__",
    "node_modules",
    "Archives",
    "build",
    "dist",
}

MAX_FILE_SIZE_BYTES = 16 * 1024 * 1024  # 16MB — large reference PDFs (EKS/ECS/Bedrock)


class TantivyIndexer:
    """Discovers and indexes text & code files into a Tantivy index."""

    def __init__(
        self,
        workspace_root: str = ".",
        index_path: str = ".tantivy",
        include_code: bool = True,
    ):
        self.workspace_root = Path(workspace_root).resolve()
        self.index_path = Path(index_path).resolve()
        self.include_code = include_code
        self.schema = get_tantivy_schema() if TANTIVY_AVAILABLE else None

    def should_index_file(self, path: Path) -> bool:
        """Check if file should be included in Tantivy index."""
        if not path.is_file():
            return False

        # Check path parts for excluded directory names
        for part in path.parts:
            if part in EXCLUDE_DIRS or part.startswith(".git"):
                return False

        # Exclude code/ directory unless explicitly requested
        try:
            rel = path.relative_to(self.workspace_root)
            if not self.include_code and rel.parts and rel.parts[0] == "code":
                return False
        except ValueError:
            pass

        if path.suffix.lower() not in INDEXABLE_EXTENSIONS:
            return False

        try:
            if path.stat().st_size > MAX_FILE_SIZE_BYTES:
                return False
        except OSError:
            return False

        return True

    def discover_files(self) -> List[Path]:
        """Scan workspace recursively for indexable files."""
        discovered: List[Path] = []
        for root, dirs, files in os.walk(self.workspace_root):
            # Prune excluded directories
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith(".")]

            # If not including code, skip code directory
            rel_root = os.path.relpath(root, self.workspace_root)
            if not self.include_code and rel_root.split(os.sep)[0] == "code":
                dirs[:] = []
                continue

            for file_name in files:
                file_path = Path(root) / file_name
                if self.should_index_file(file_path):
                    discovered.append(file_path)

        return discovered

    def index(self, clear_first: bool = False) -> Dict[str, int]:
        """Index all discovered workspace files into Tantivy.

        Args:
            clear_first: If True, removes existing index directory before indexing.

        Returns:
            Dictionary with indexing stats (indexed_count, error_count).
        """
        if not TANTIVY_AVAILABLE:
            raise RuntimeError("tantivy library is not installed in the current environment")

        if clear_first and self.index_path.exists():
            logger.info(f"Clearing existing Tantivy index at {self.index_path}")
            shutil.rmtree(self.index_path)

        self.index_path.mkdir(parents=True, exist_ok=True)

        index = Index(self.schema, str(self.index_path))
        writer = index.writer()

        files = self.discover_files()
        logger.info(f"Discovered {len(files)} files for Tantivy indexing")

        indexed_count = 0
        error_count = 0

        for file_path in files:
            try:
                rel_path = file_path.relative_to(self.workspace_root).as_posix()
                repo = "workspace"
                parts = Path(rel_path).parts
                if parts and parts[0] == "code" and len(parts) > 1:
                    repo = parts[1]

                title = file_path.stem.replace("_", " ").replace("-", " ").title()
                extension = file_path.suffix.lower()

                # Read text safely
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()

                # Index whole file as primary entry
                doc = Document()
                doc.add_text("doc_id", rel_path)
                doc.add_text("path", rel_path)
                doc.add_text("title", title)
                doc.add_text("body", content)
                doc.add_text("extension", extension)
                doc.add_text("repo", repo)
                doc.add_integer("line_number", 1)

                writer.add_document(doc)
                indexed_count += 1

                if indexed_count % 100 == 0:
                    logger.info(f"Indexed {indexed_count}/{len(files)} files...")

            except Exception as e:
                logger.warning(f"Error indexing {file_path}: {e}")
                error_count += 1

        logger.info(f"Committing {indexed_count} documents to Tantivy index...")
        writer.commit()
        index.reload()
        logger.info("Tantivy indexing complete.")

        return {
            "indexed_count": indexed_count,
            "error_count": error_count,
            "total_files": len(files),
        }

    def stats(self) -> Dict[str, Any]:
        """Get stats on the current Tantivy index."""
        if not self.index_path.exists():
            return {"exists": False, "index_path": str(self.index_path)}

        try:
            index = Index(self.schema, str(self.index_path))
            searcher = index.searcher()
            num_docs = getattr(searcher, "num_docs", 0)
            return {
                "exists": True,
                "index_path": str(self.index_path),
                "num_docs": num_docs,
            }
        except Exception as e:
            return {"exists": True, "index_path": str(self.index_path), "error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Tantivy BM25 inverted indexer")
    parser.add_argument("--workspace", default=".", help="Workspace root path")
    parser.add_argument("--index-path", default=".tantivy", help="Tantivy storage path")
    parser.add_argument("--clear", action="store_true", help="Clear index before running")
    parser.add_argument("--stats", action="store_true", help="Print index statistics and exit")
    parser.add_argument(
        "--include-code",
        action="store_true",
        default=False,
        help="Include external repos in code/ directory",
    )

    args = parser.parse_args()
    indexer = TantivyIndexer(
        workspace_root=args.workspace,
        index_path=args.index_path,
        include_code=args.include_code,
    )

    if args.stats:
        stats = indexer.stats()
        print(f"Tantivy Index Stats:\n  Path: {stats.get('index_path')}\n  Documents: {stats.get('num_docs', 0)}")
        return

    results = indexer.index(clear_first=args.clear)
    print(f"Indexing completed: {results['indexed_count']} documents indexed, {results['error_count']} errors.")


if __name__ == "__main__":
    main()
