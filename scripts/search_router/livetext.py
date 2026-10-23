#!/usr/bin/env python3
"""
livetext.py — Ripgrep wrapper for code-aware searching.

Provides RipgrepSearcher class for fast keyword/regex searching with language
detection, context extraction, and result normalization. Designed to be
integrated with ChromaDB semantic search for hybrid searching.

Usage:
    from livetext import RipgrepSearcher
    searcher = RipgrepSearcher()
    results = searcher.search("pattern", file_types=["py", "md"])
    results = searcher.search_code("def.*deploy", language="python")
"""

import subprocess
import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
_SCRIPTS_DIR = os.path.dirname(_CURRENT_DIR)
for _d in [_CURRENT_DIR, _SCRIPTS_DIR]:
    if _d not in sys.path and os.path.exists(_d):
        sys.path.insert(0, _d)

from common_platform import find_executable, normalize_posix_path

logger = logging.getLogger(__name__)

# Language to ripgrep type mappings
LANGUAGE_TO_TYPES = {
    "python": ["py"],
    "shell": ["sh", "bash"],
    "yaml": ["yaml", "yml"],
    "json": ["json"],
    "markdown": ["md", "markdown"],
    "typescript": ["ts", "tsx"],
    "javascript": ["js", "jsx"],
    "rust": ["rs"],
    "go": ["go"],
    "c": ["c"],
    "cpp": ["cpp", "cc", "cxx", "c++"],
}

FILE_EXTENSION_TO_LANGUAGE = {
    ".py": "python",
    ".sh": "shell",
    ".bash": "shell",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".json": "json",
    ".md": "markdown",
    ".markdown": "markdown",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
    ".rs": "rust",
    ".go": "go",
    ".c": "c",
    ".cpp": "cpp",
}


@dataclass
class SearchMatch:
    """Result from ripgrep search."""
    id: str
    path: str
    line_number: int
    content: str
    context_before: List[str]
    context_after: List[str]
    match_type: str = "ripgrep"
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_chromadb_format(self) -> Dict[str, Any]:
        """Convert to ChromaDB result format for compatibility."""
        return {
            "id": self.id,
            "text": self.content,
            "metadata": {
                "path": self.path,
                "line_number": self.line_number,
                "context_before": self.context_before,
                "context_after": self.context_after,
                "match_type": self.match_type,
                "confidence": self.confidence,
            },
            "distance": 1.0 - self.confidence,
        }


class RipgrepSearcher:
    """Ripgrep wrapper for code-aware searching."""

    def __init__(self, workspace_root: str = "."):
        """Initialize ripgrep searcher.

        Args:
            workspace_root: Root directory for searches (default: current dir)
        """
        self.workspace_root = Path(workspace_root)
        self.rg_bin = find_executable("rg") or "rg"
        self.rg_available = self._check_ripgrep()
        if not self.rg_available:
            logger.warning("ripgrep (rg) not found in PATH; fallback disabled")

    def _check_ripgrep(self) -> bool:
        """Check if ripgrep is available in PATH."""
        exe = find_executable("rg")
        if not exe:
            return False
        self.rg_bin = exe
        try:
            result = subprocess.run(
                [self.rg_bin, "--version"],
                capture_output=True,
                timeout=2,
                encoding="utf-8",
                errors="replace",
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def search(
        self,
        pattern: str,
        file_types: Optional[List[str]] = None,
        limit: int = 20,
        context_lines: int = 2,
        whole_word: bool = False,
        case_sensitive: bool = True,
    ) -> List[SearchMatch]:
        """Generic search with ripgrep.

        Args:
            pattern: Regex or literal pattern to search for
            file_types: List of file types to filter (e.g., ["py", "md"])
            limit: Maximum number of results
            context_lines: Lines of context before/after match
            whole_word: Match whole words only
            case_sensitive: Case-sensitive search (default True)

        Returns:
            List of SearchMatch results
        """
        if not self.rg_available:
            logger.warning("ripgrep not available; returning empty results")
            return []

        cmd = self._build_rg_command(
            pattern=pattern,
            file_types=file_types,
            limit=limit,
            context_lines=context_lines,
            whole_word=whole_word,
            case_sensitive=case_sensitive,
        )

        try:
            result = subprocess.run(
                cmd,
                cwd=self.workspace_root,
                capture_output=True,
                text=True,
                timeout=10,
                encoding="utf-8",
                errors="replace",
            )
            if result.returncode != 0 and result.returncode != 1:
                logger.error(f"ripgrep error: {result.stderr}")
                return []

            return self._parse_json_output(result.stdout)
        except subprocess.TimeoutExpired:
            logger.error("ripgrep search timed out")
            return []
        except Exception as e:
            logger.error(f"ripgrep search failed: {e}")
            return []

    def search_code(
        self,
        pattern: str,
        language: Optional[str] = None,
        context_lines: int = 3,
    ) -> List[SearchMatch]:
        """Code-specific search with language detection.

        Args:
            pattern: Regex or literal pattern to search for
            language: Programming language (e.g., "python", "shell")
                     Auto-detected from context if not provided
            context_lines: Lines of context before/after match

        Returns:
            List of SearchMatch results
        """
        file_types = None
        if language:
            file_types = LANGUAGE_TO_TYPES.get(language.lower())
            if not file_types:
                logger.warning(f"Unknown language: {language}")

        return self.search(
            pattern=pattern,
            file_types=file_types,
            limit=30,
            context_lines=context_lines,
            whole_word=False,
            case_sensitive=True,
        )

    def search_definitions(
        self,
        language: str,
        pattern: Optional[str] = None,
    ) -> List[SearchMatch]:
        """Search for function/class definitions.

        Args:
            language: Programming language ("python", "shell", "go", etc.)
            pattern: Optional pattern to filter definitions

        Returns:
            List of SearchMatch results
        """
        if language.lower() == "python":
            # Match: def function_name or class ClassName
            search_pattern = pattern or r"^(def|class)\s+\w+"
        elif language.lower() in ("shell", "bash"):
            # Match: function_name() or function function_name
            search_pattern = pattern or r"^(function\s+)?\w+\(\)|^function\s+\w+"
        elif language.lower() == "go":
            # Match: func FunctionName
            search_pattern = pattern or r"^func\s+\w+"
        else:
            search_pattern = pattern or r"^(def|class|func)\s+\w+"

        return self.search_code(
            pattern=search_pattern,
            language=language,
            context_lines=5,
        )

    def _build_rg_command(
        self,
        pattern: str,
        file_types: Optional[List[str]] = None,
        limit: int = 20,
        context_lines: int = 2,
        whole_word: bool = False,
        case_sensitive: bool = True,
    ) -> List[str]:
        """Build ripgrep command."""
        cmd = [self.rg_bin, "--json", "--max-count", str(limit)]

        # Context lines
        if context_lines > 0:
            cmd.extend(["-C", str(context_lines)])

        # File type filtering
        if file_types:
            for ft in file_types:
                cmd.extend(["-t", ft])

        # Whole word matching
        if whole_word:
            cmd.append("--whole-word")

        # Case sensitivity
        if not case_sensitive:
            cmd.append("-i")

        # Pattern (treated as regex by default)
        cmd.append(pattern)

        return cmd

    def _parse_json_output(self, output: str) -> List[SearchMatch]:
        """Parse ripgrep JSON output to SearchMatch results.

        Ripgrep JSON format:
        ```json
        {"type":"begin","data":{"path":{"text":"file.py"}}}
        {"type":"match","data":{"path":{"text":"file.py"},"line_number":42,...}}
        {"type":"context","data":{"path":{"text":"file.py"},"line_number":41,...}}
        {"type":"end","data":{"path":{"text":"file.py"}}}
        ```
        """
        results = []
        current_file = None
        matches_by_id: Dict[str, Dict[str, Any]] = {}

        for line in output.strip().split("\n"):
            if not line:
                continue

            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                logger.debug(f"Failed to parse ripgrep JSON: {line}")
                continue

            entry_type = entry.get("type")
            if entry_type == "summary":
                # Skip summary entries
                continue

            data = entry.get("data", {})

            if entry_type == "begin":
                path_data = data.get("path")
                # Handle both old format (string) and new format ({"text": "..."})
                current_file = (
                    path_data["text"] if isinstance(path_data, dict) else path_data
                )
                if current_file:
                    current_file = normalize_posix_path(current_file)
            elif entry_type == "match":
                path_data = data.get("path", current_file)
                path = (
                    path_data["text"] if isinstance(path_data, dict) else path_data
                )
                if path:
                    path = normalize_posix_path(path)
                line_num = data.get("line_number", 0)
                line_text = data.get("lines", {}).get("text", "")

                match_id = f"{path}:{line_num}"
                if match_id not in matches_by_id:
                    matches_by_id[match_id] = {
                        "path": path,
                        "line_number": line_num,
                        "content": line_text.rstrip(),
                        "context_before": [],
                        "context_after": [],
                    }
            elif entry_type == "context":
                path_data = data.get("path", current_file)
                path = (
                    path_data["text"] if isinstance(path_data, dict) else path_data
                )
                if path:
                    path = normalize_posix_path(path)
                line_num = data.get("line_number", 0)
                line_text = data.get("lines", {}).get("text", "")

                # Find which match this context belongs to and add it
                for match_id, match_data in matches_by_id.items():
                    if match_data["path"] == path:
                        match_line = match_data["line_number"]
                        if line_num < match_line:
                            # Context before
                            match_data["context_before"].append(line_text.rstrip())
                        elif line_num > match_line:
                            # Context after
                            match_data["context_after"].append(line_text.rstrip())

        # Convert matches to SearchMatch objects
        for match_id, match_data in matches_by_id.items():
            # Sort context lines by line position (approximate)
            match_data["context_before"].sort()
            match_data["context_after"].sort()

            results.append(
                SearchMatch(
                    id=match_id,
                    path=match_data["path"],
                    line_number=match_data["line_number"],
                    content=match_data["content"],
                    context_before=match_data["context_before"][-2:],
                    context_after=match_data["context_after"][:2],
                    match_type="ripgrep",
                    confidence=1.0,
                )
            )

        return results

    def get_file_type_for_path(self, path: str) -> Optional[str]:
        """Get language for a file path."""
        ext = Path(path).suffix.lower()
        return FILE_EXTENSION_TO_LANGUAGE.get(ext)

    def list_supported_types(self) -> List[str]:
        """List file types supported by ripgrep."""
        if not self.rg_available:
            return []

        try:
            result = subprocess.run(
                [self.rg_bin, "--type-list"],
                capture_output=True,
                text=True,
                timeout=5,
                encoding="utf-8",
                errors="replace",
            )
            if result.returncode == 0:
                types = []
                for line in result.stdout.strip().split("\n"):
                    parts = line.split(":")
                    if parts:
                        types.append(parts[0].strip())
                return types
            return []
        except Exception as e:
            logger.error(f"Failed to list ripgrep types: {e}")
            return []


if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    # Example usage
    searcher = RipgrepSearcher()

    if not searcher.rg_available:
        print("ripgrep (rg) not found. Install with: brew install ripgrep")
        sys.exit(1)

    # Search examples
    print("=== Example 1: Basic Python Search ===")
    results = searcher.search_code("def ", language="python", context_lines=1)
    for result in results[:3]:
        print(f"{result.id}: {result.content[:60]}")

    print("\n=== Example 2: Search by File Type ===")
    results = searcher.search("import", file_types=["py"], limit=5)
    for result in results:
        print(f"{result.id}: {result.content[:60]}")

    print("\n=== Example 3: Whole Word Search ===")
    results = searcher.search("class", whole_word=True, limit=3)
    for result in results:
        print(f"{result.id}: {result.content[:60]}")
