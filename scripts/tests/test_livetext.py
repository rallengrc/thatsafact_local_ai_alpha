#!/usr/bin/env python3
"""
test_livetext.py — Unit tests for ripgrep wrapper (livetext.py).

Tests ripgrep integration, pattern matching, file type filtering,
context extraction, and result normalization.

Run with: python3 -m pytest scripts/test_livetext.py -v
"""

import sys
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, os.path.dirname(__file__))

import pytest
from livetext import RipgrepSearcher, SearchMatch, LANGUAGE_TO_TYPES


class TestRipgrepAvailability:
    """Tests for ripgrep availability detection."""

    def test_ripgrep_check_success(self):
        """Test detecting available ripgrep."""
        searcher = RipgrepSearcher()
        # rg_available will be True if installed, False otherwise
        assert isinstance(searcher.rg_available, bool)

    def test_ripgrep_check_sets_attribute(self):
        """Test that check sets rg_available attribute."""
        searcher = RipgrepSearcher()
        assert hasattr(searcher, "rg_available")

    @patch("subprocess.run")
    def test_ripgrep_check_failure(self, mock_run):
        """Test handling when ripgrep is not available."""
        mock_run.side_effect = FileNotFoundError()
        searcher = RipgrepSearcher()
        assert searcher.rg_available is False

    def test_ripgrep_uses_find_executable_and_sets_rg_bin(self):
        """Test that RipgrepSearcher stores resolved rg_bin."""
        searcher = RipgrepSearcher()
        assert hasattr(searcher, "rg_bin")
        assert isinstance(searcher.rg_bin, str)
        assert len(searcher.rg_bin) > 0


class TestSearchMatch:
    """Tests for SearchMatch dataclass."""

    def test_search_match_creation(self):
        """Test creating SearchMatch object."""
        match = SearchMatch(
            id="file.py:42",
            path="file.py",
            line_number=42,
            content="def function():",
            context_before=["# comment"],
            context_after=["    pass"],
        )
        assert match.id == "file.py:42"
        assert match.path == "file.py"
        assert match.line_number == 42
        assert match.content == "def function():"

    def test_search_match_to_dict(self):
        """Test converting SearchMatch to dict."""
        match = SearchMatch(
            id="file.py:1",
            path="file.py",
            line_number=1,
            content="import os",
            context_before=[],
            context_after=[],
        )
        d = match.to_dict()
        assert d["id"] == "file.py:1"
        assert d["content"] == "import os"

    def test_search_match_to_chromadb_format(self):
        """Test converting to ChromaDB-compatible format."""
        match = SearchMatch(
            id="file.py:10",
            path="file.py",
            line_number=10,
            content="x = 42",
            context_before=["y = 10"],
            context_after=["z = x + y"],
            confidence=0.95,
        )
        formatted = match.to_chromadb_format()
        assert formatted["id"] == "file.py:10"
        assert formatted["text"] == "x = 42"
        assert formatted["metadata"]["path"] == "file.py"
        assert formatted["metadata"]["line_number"] == 10
        assert formatted["metadata"]["confidence"] == 0.95


class TestBuildCommand:
    """Tests for ripgrep command building."""

    def test_build_basic_command(self):
        """Test building basic search command."""
        searcher = RipgrepSearcher()
        cmd = searcher._build_rg_command(
            pattern="test",
            file_types=None,
            limit=10,
        )
        assert searcher.rg_bin in cmd
        assert "--json" in cmd
        assert "--max-count" in cmd
        assert "test" in cmd

    def test_build_command_with_file_types(self):
        """Test building command with file type filters."""
        searcher = RipgrepSearcher()
        cmd = searcher._build_rg_command(
            pattern="pattern",
            file_types=["py", "md"],
            limit=20,
        )
        assert "-t" in cmd
        assert "py" in cmd
        assert "md" in cmd

    def test_build_command_with_context(self):
        """Test building command with context lines."""
        searcher = RipgrepSearcher()
        cmd = searcher._build_rg_command(
            pattern="pattern",
            context_lines=3,
        )
        assert "-C" in cmd
        assert "3" in cmd

    def test_build_command_whole_word(self):
        """Test building command with whole word flag."""
        searcher = RipgrepSearcher()
        cmd = searcher._build_rg_command(
            pattern="word",
            whole_word=True,
        )
        assert "--whole-word" in cmd

    def test_build_command_case_insensitive(self):
        """Test building command with case insensitive flag."""
        searcher = RipgrepSearcher()
        cmd = searcher._build_rg_command(
            pattern="pattern",
            case_sensitive=False,
        )
        assert "-i" in cmd


class TestLanguageMapping:
    """Tests for language to file type mapping."""

    def test_python_mapping(self):
        """Test Python language mapping."""
        assert LANGUAGE_TO_TYPES["python"] == ["py"]

    def test_shell_mapping(self):
        """Test shell language mapping."""
        assert LANGUAGE_TO_TYPES["shell"] == ["sh", "bash"]

    def test_multiple_types_for_language(self):
        """Test languages with multiple file type associations."""
        for lang_types in LANGUAGE_TO_TYPES.values():
            assert isinstance(lang_types, list)
            assert len(lang_types) > 0

    def test_search_code_with_language(self):
        """Test search_code method with language parameter."""
        searcher = RipgrepSearcher()
        with patch.object(searcher, "search") as mock_search:
            mock_search.return_value = []
            searcher.search_code("test", language="python")
            mock_search.assert_called_once()
            call_args = mock_search.call_args
            assert call_args[1]["file_types"] == ["py"]

    def test_search_code_unknown_language(self):
        """Test search_code with unknown language."""
        searcher = RipgrepSearcher()
        with patch.object(searcher, "search") as mock_search:
            mock_search.return_value = []
            searcher.search_code("test", language="unknown_lang")
            # Should still call search even with unknown language
            mock_search.assert_called_once()


class TestDefinitionSearch:
    """Tests for definition-specific searching."""

    def test_search_python_definitions(self):
        """Test searching for Python function/class definitions."""
        searcher = RipgrepSearcher()
        with patch.object(searcher, "search") as mock_search:
            mock_search.return_value = []
            searcher.search_definitions("python")
            mock_search.assert_called_once()
            call_args = mock_search.call_args
            pattern = call_args[1]["pattern"]
            # Should search for def or class
            assert "def" in pattern or "class" in pattern

    def test_search_shell_definitions(self):
        """Test searching for shell function definitions."""
        searcher = RipgrepSearcher()
        with patch.object(searcher, "search") as mock_search:
            mock_search.return_value = []
            searcher.search_definitions("shell")
            mock_search.assert_called_once()

    def test_search_go_definitions(self):
        """Test searching for Go function definitions."""
        searcher = RipgrepSearcher()
        with patch.object(searcher, "search") as mock_search:
            mock_search.return_value = []
            searcher.search_definitions("go")
            mock_search.assert_called_once()
            call_args = mock_search.call_args
            pattern = call_args[1]["pattern"]
            assert "func" in pattern


class TestJSONParsing:
    """Tests for ripgrep JSON output parsing."""

    def test_parse_empty_output(self):
        """Test parsing empty output."""
        searcher = RipgrepSearcher()
        results = searcher._parse_json_output("")
        assert results == []

    def test_parse_single_match(self):
        """Test parsing single match."""
        searcher = RipgrepSearcher()
        json_output = '{"type":"begin","data":{"path":"file.py"}}\n'
        json_output += (
            '{"type":"match","data":{"path":"file.py","line_number":1,'
            '"lines":{"text":"def test():"}}}\n'
        )
        json_output += '{"type":"end","data":{"path":"file.py"}}\n'

        results = searcher._parse_json_output(json_output)
        assert len(results) > 0

    def test_parse_multiple_matches(self):
        """Test parsing multiple matches."""
        searcher = RipgrepSearcher()
        json_output = '{"type":"begin","data":{"path":"file.py"}}\n'
        json_output += (
            '{"type":"match","data":{"path":"file.py","line_number":1,'
            '"lines":{"text":"def test1():"}}}\n'
        )
        json_output += (
            '{"type":"match","data":{"path":"file.py","line_number":5,'
            '"lines":{"text":"def test2():"}}}\n'
        )
        json_output += '{"type":"end","data":{"path":"file.py"}}\n'

        results = searcher._parse_json_output(json_output)
        assert len(results) >= 1

    def test_parse_invalid_json_line(self):
        """Test handling invalid JSON lines."""
        searcher = RipgrepSearcher()
        json_output = '{"type":"begin","data":{"path":"file.py"}}\n'
        json_output += "invalid json line\n"
        json_output += (
            '{"type":"match","data":{"path":"file.py","line_number":1,'
            '"lines":{"text":"valid line"}}}\n'
        )

        # Should not raise exception, just skip invalid line
        results = searcher._parse_json_output(json_output)
        assert isinstance(results, list)

    def test_parse_json_output_normalizes_windows_paths(self):
        """Test that Windows backslash paths are normalized to POSIX forward slashes."""
        searcher = RipgrepSearcher()
        json_output = (
            '{"type":"begin","data":{"path":"folder\\\\sub\\\\file.py"}}\n'
            '{"type":"match","data":{"path":"folder\\\\sub\\\\file.py","line_number":10,'
            '"lines":{"text":"def test():"}}}\n'
            '{"type":"end","data":{"path":"folder\\\\sub\\\\file.py"}}\n'
        )
        results = searcher._parse_json_output(json_output)
        assert len(results) == 1
        assert results[0].path == "folder/sub/file.py"
        assert results[0].id == "folder/sub/file.py:10"


class TestFileTypeDetection:
    """Tests for file type detection."""

    def test_get_file_type_python(self):
        """Test detecting Python file type."""
        searcher = RipgrepSearcher()
        ft = searcher.get_file_type_for_path("script.py")
        assert ft == "python"

    def test_get_file_type_shell(self):
        """Test detecting shell file type."""
        searcher = RipgrepSearcher()
        ft = searcher.get_file_type_for_path("script.sh")
        assert ft == "shell"

    def test_get_file_type_markdown(self):
        """Test detecting markdown file type."""
        searcher = RipgrepSearcher()
        ft = searcher.get_file_type_for_path("README.md")
        assert ft == "markdown"

    def test_get_file_type_unknown(self):
        """Test handling unknown file type."""
        searcher = RipgrepSearcher()
        ft = searcher.get_file_type_for_path("unknown.xyz")
        assert ft is None


class TestSearchWithMocking:
    """Tests for search methods with mocked subprocess."""

    @patch("subprocess.run")
    def test_search_success(self, mock_run):
        """Test successful search."""
        mock_run.return_value = Mock(
            returncode=0,
            stdout='{"type":"begin","data":{"path":"test.py"}}\n',
        )
        searcher = RipgrepSearcher()
        searcher.rg_available = True

        results = searcher.search("test")
        assert isinstance(results, list)

    @patch("subprocess.run")
    def test_search_not_available(self, mock_run):
        """Test search when ripgrep not available."""
        searcher = RipgrepSearcher()
        searcher.rg_available = False

        results = searcher.search("test")
        assert results == []

    @patch("subprocess.run")
    def test_search_timeout(self, mock_run):
        """Test search timeout handling."""
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired("rg", 10)
        searcher = RipgrepSearcher()
        searcher.rg_available = True

        results = searcher.search("test")
        assert results == []

    @patch("subprocess.run")
    def test_search_error_handling(self, mock_run):
        """Test search error handling."""
        mock_run.return_value = Mock(
            returncode=2,
            stderr="Error message",
        )
        searcher = RipgrepSearcher()
        searcher.rg_available = True

        results = searcher.search("test")
        assert results == []


class TestSearchIntegration:
    """Integration tests with actual ripgrep (if available)."""

    def test_list_supported_types(self):
        """Test listing supported file types."""
        searcher = RipgrepSearcher()
        if searcher.rg_available:
            types = searcher.list_supported_types()
            assert isinstance(types, list)
            # Should have at least some types
            if types:
                assert len(types) > 0
        else:
            pytest.skip("ripgrep not available")

    def test_real_workspace_search(self):
        """Test searching in actual workspace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("def hello():\n    return 'world'\n", encoding="utf-8")

            searcher = RipgrepSearcher(tmpdir)
            if searcher.rg_available:
                results = searcher.search("def hello")
                assert len(results) > 0
                assert results[0].content == "def hello():"
            else:
                pytest.skip("ripgrep not available")

    def test_search_code_integration(self):
        """Test search_code in actual workspace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create Python file
            test_file = Path(tmpdir) / "module.py"
            test_file.write_text(
                "def process(data):\n    result = transform(data)\n    return result\n",
                encoding="utf-8",
            )

            searcher = RipgrepSearcher(tmpdir)
            if searcher.rg_available:
                results = searcher.search_code("def ", language="python")
                assert len(results) > 0
            else:
                pytest.skip("ripgrep not available")
