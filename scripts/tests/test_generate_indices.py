"""
test_generate_indices.py — The index/TOC generator must not link to git-ignored (unpublished) paths.
"""

import generate_indices_and_master_toc as gen


def make_workspace(tmp_path, monkeypatch, ignore_lines):
    (tmp_path / ".gitignore").write_text("\n".join(ignore_lines) + "\n", encoding="utf-8")
    monkeypatch.setattr(gen, "WORKSPACE", str(tmp_path))
    return tmp_path


def test_plain_ignore_entries_cover_nested_paths(tmp_path, monkeypatch):
    root = make_workspace(tmp_path, monkeypatch, ["memories/", "Areas/book/", "notes.md"])
    assert gen._is_gitignored(str(root / "memories" / "_INDEX.md"))
    assert gen._is_gitignored(str(root / "Areas" / "book" / "a.md"))
    assert gen._is_gitignored(str(root / "deep" / "notes.md"))
    assert not gen._is_gitignored(str(root / "Areas" / "other.md"))


def test_globs_negations_and_comments_are_skipped(tmp_path, monkeypatch):
    root = make_workspace(tmp_path, monkeypatch, ["# memories/", "*.db", "!keep.md", "build/*"])
    assert not gen._is_gitignored(str(root / "memories" / "a.md"))
    assert not gen._is_gitignored(str(root / "x.db"))


def test_published_exists_requires_file_and_not_ignored(tmp_path, monkeypatch):
    root = make_workspace(tmp_path, monkeypatch, ["private/"])
    (root / "private").mkdir()
    (root / "private" / "a.md").write_text("x", encoding="utf-8")
    (root / "public.md").write_text("x", encoding="utf-8")
    assert gen._published_exists(str(root / "public.md"))
    assert not gen._published_exists(str(root / "private" / "a.md"))
    assert not gen._published_exists(str(root / "missing.md"))


def test_paths_outside_workspace_are_not_ignored(tmp_path, monkeypatch):
    make_workspace(tmp_path, monkeypatch, ["private/"])
    assert not gen._is_gitignored("/somewhere/else/private/a.md")


def test_dir_star_entry_ignores_contents_but_not_negated_keepfile(tmp_path, monkeypatch):
    root = make_workspace(tmp_path, monkeypatch, ["memories/*", "!memories/.gitkeep"])
    assert gen._is_gitignored(str(root / "memories" / "_INDEX.md"))
    assert gen._is_gitignored(str(root / "memories" / "sub" / "a.md"))
    assert not gen._is_gitignored(str(root / "Areas" / "a.md"))
