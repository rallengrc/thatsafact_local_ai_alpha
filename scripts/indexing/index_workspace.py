#!/usr/bin/env python3
"""
index_workspace.py — Index workspace with chromadb for MCP search router.

Recursively indexes text files in the workspace (excluding Archives, binaries, etc.)
into a vector database. Uses pluggable providers for flexibility (chromadb default,
extensible to OpenAI embeddings, Pinecone, etc.).

Usage:
    python3 index_workspace.py --provider chromadb --db-path .chroma
    python3 index_workspace.py --clear  # Clear existing index
    python3 index_workspace.py --stats  # Show collection stats
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

_SCRIPTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)
sys.path.insert(0, os.path.dirname(__file__))

from common_platform import ensure_venv_site_packages
ensure_venv_site_packages()

_ROUTER_DIR = os.path.join(_SCRIPTS_DIR, "search_router")
if _ROUTER_DIR not in sys.path:
    sys.path.insert(0, _ROUTER_DIR)

try:
    from passport import PassportResolver
except ImportError:
    PassportResolver = None

from vectordb_provider import get_provider, VectorDBProvider

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)

# File extensions to index
INDEXABLE_EXTENSIONS = {
    ".md",
    ".markdown",
    ".txt",
    ".py",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".csv",
    ".sql",
    ".sh",
    ".bash",
}

# File extensions to skip (binaries, media, etc.)
SKIP_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".xlsx",
    ".pptx",
    ".zip",
    ".tar",
    ".gz",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".mp3",
    ".mp4",
    ".mov",
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    ".o",
    ".a",
}

# Directories to exclude from indexing
SKIP_DIRECTORIES = {
    "Archives",
    "code",
    ".chroma",
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".egg-info",
    "dist",
    "build",
    ".DS_Store",
}


@dataclass
class FileInfo:
    """Information about a file to be indexed."""

    path: Path
    relative_path: str
    file_size: int
    content: str

    def to_doc(self) -> Dict[str, Any]:
        """Convert to document format for vectordb."""
        passport_tag = PassportResolver.resolve_dynamic(self.relative_path, self.content) if PassportResolver else "all"
        return {
            "id": self.relative_path,
            "text": self.content,
            "metadata": {
                "path": self.relative_path,
                "file_type": self.path.suffix,
                "file_size": self.file_size,
                "passport": passport_tag,
            },
        }


class WorkspaceIndexer:
    """Index workspace files into a vector database."""

    def __init__(
        self,
        workspace_root: Path,
        provider: VectorDBProvider,
        collection_name: str = "workspace",
    ):
        """
        Initialize the indexer.

        Args:
            workspace_root: Root directory of the workspace.
            provider: Vector database provider instance.
            collection_name: Name of the collection to index into.
        """
        self.workspace_root = workspace_root
        self.provider = provider
        self.collection_name = collection_name
        self.indexed_count = 0
        self.skipped_count = 0
        self.error_count = 0

    def _should_skip_directory(self, path: Path) -> bool:
        """Check if directory should be skipped."""
        for part in path.parts:
            if part in SKIP_DIRECTORIES:
                return True
            # Skip any directory that looks like a stringified Python dict or set
            if part.startswith("{") and part.endswith("}"):
                return True
        return False

    def _should_skip_file(self, path: Path) -> bool:
        """Check if file should be skipped."""
        if path.suffix.lower() in SKIP_EXTENSIONS:
            return True
        if path.suffix.lower() and path.suffix.lower() not in INDEXABLE_EXTENSIONS:
            return True
        if path.name.startswith("."):
            return True
        return False

    def _is_text_file(self, path: Path) -> bool:
        """Check if file is likely text by reading first bytes."""
        try:
            with open(path, "rb") as f:
                chunk = f.read(512)
            # Check for null bytes (common in binaries)
            return b"\x00" not in chunk
        except Exception:
            return False

    def _read_file_safely(self, path: Path, max_size: int = 16 * 1024 * 1024) -> Optional[str]:
        """
        Safely read file content with size limits and encoding handling.

        Args:
            path: File path.
            max_size: Maximum file size to read (16 MB default; large reference
                PDFs like EKS/ECS/Bedrock docs can exceed 2 MB).

        Returns:
            File content or None if read failed.
        """
        try:
            if path.stat().st_size > max_size:
                logger.debug(f"Skipping {path.relative_to(self.workspace_root)} (too large)")
                self.skipped_count += 1
                return None

            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read().strip()

            if not content:
                logger.debug(f"Skipping {path.relative_to(self.workspace_root)} (empty)")
                self.skipped_count += 1
                return None

            return content

        except Exception as e:
            logger.warning(
                f"Error reading {path.relative_to(self.workspace_root)}: {e}"
            )
            self.error_count += 1
            return None

    def collect_files(self) -> List[FileInfo]:
        """
        Recursively collect indexable files from workspace.

        Returns:
            List of FileInfo objects for files to index.
        """
        files = []

        for root, dirs, filenames in os.walk(self.workspace_root):
            root_path = Path(root)

            # Skip excluded directories
            dirs[:] = [
                d for d in dirs if not self._should_skip_directory(root_path / d)
            ]

            for filename in filenames:
                file_path = root_path / filename

                if self._should_skip_file(file_path):
                    continue

                if not self._is_text_file(file_path):
                    logger.debug(f"Skipping binary file: {file_path.relative_to(self.workspace_root)}")
                    self.skipped_count += 1
                    continue

                content = self._read_file_safely(file_path)
                if content is None:
                    continue

                relative_path = file_path.relative_to(self.workspace_root).as_posix()
                files.append(
                    FileInfo(
                        path=file_path,
                        relative_path=relative_path,
                        file_size=file_path.stat().st_size,
                        content=content,
                    )
                )
                logger.debug(f"Collected: {relative_path}")

        return files

    def index(self, batch_size: int = 50) -> Dict[str, Any]:
        """
        Index all collected files.

        Args:
            batch_size: Number of files to index per batch.

        Returns:
            Dictionary with indexing statistics.
        """
        logger.info(f"Collecting files from {self.workspace_root}...")
        files = self.collect_files()

        if not files:
            logger.warning("No indexable files found")
            return {
                "status": "no_files",
                "indexed": 0,
                "skipped": self.skipped_count,
                "errors": self.error_count,
            }

        logger.info(f"Found {len(files)} files to index")

        for i in range(0, len(files), batch_size):
            batch = files[i : i + batch_size]
            docs = [f.to_doc() for f in batch]

            try:
                count = self.provider.index_documents(docs, self.collection_name)
                self.indexed_count += count
                logger.info(
                    f"Indexed batch {i // batch_size + 1} "
                    f"({self.indexed_count} total)"
                )
            except Exception as e:
                logger.error(f"Error indexing batch: {e}")
                self.error_count += len(batch)

        stats = self.provider.get_stats(self.collection_name)
        logger.info(f"Indexing complete: {stats}")

        return {
            "status": "success",
            "workspace": str(self.workspace_root),
            "collection": self.collection_name,
            "indexed": self.indexed_count,
            "skipped": self.skipped_count,
            "errors": self.error_count,
            "stats": stats,
        }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Index workspace files into vector database"
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        default=Path.cwd(),
        help="Workspace root directory (default: current directory)",
    )
    parser.add_argument(
        "--provider",
        type=str,
        default="chromadb",
        choices=["chromadb"],
        help="Vector database provider",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=Path.cwd() / ".chroma",
        help="Database path (for chromadb)",
    )
    parser.add_argument(
        "--collection",
        type=str,
        default="workspace",
        help="Collection name",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="Batch size for indexing",
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing collection before indexing",
    )
    parser.add_argument(
        "--stats-only",
        action="store_true",
        help="Print collection stats and exit",
    )
    parser.add_argument(
        "--test-search",
        type=str,
        help="Test search with query string",
    )

    args = parser.parse_args()

    # Ensure workspace exists
    if not args.workspace.exists():
        logger.error(f"Workspace not found: {args.workspace}")
        sys.exit(1)

    # Initialize provider
    provider_config = {"db_path": str(args.db_path)}
    provider = get_provider(args.provider, provider_config)

    # Handle stats-only mode
    if args.stats_only:
        stats = provider.get_stats(args.collection)
        print(json.dumps(stats, indent=2))
        return 0

    # Handle clear mode
    if args.clear:
        logger.info(f"Clearing collection '{args.collection}'...")
        provider.clear_collection(args.collection)

    # Index workspace
    indexer = WorkspaceIndexer(args.workspace, provider, args.collection)
    result = indexer.index(batch_size=args.batch_size)

    logger.info(f"\n{json.dumps(result, indent=2)}")

    # Handle test search
    if args.test_search:
        logger.info(f"\nSearching for: '{args.test_search}'")
        results = provider.search(args.test_search, args.collection, limit=5)
        print(json.dumps(results, indent=2, default=str))

    return 0 if result["status"] == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
