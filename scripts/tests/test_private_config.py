"""
test_private_config.py — Tests for loading client-specific generator metadata from the private project dir.

Fixtures use a made-up client name; the real name never appears here.
"""

import json
from pathlib import Path

import pytest

import private_config as pc


def write_cfg(root: Path, data) -> Path:
    cfg = root / pc.PRIVATE_CONFIG
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_text(json.dumps(data), encoding="utf-8")
    return cfg


def test_missing_file_returns_empty_sections(tmp_path):
    cfg = pc.load_private_config(tmp_path)
    assert cfg == {"doc_metadata": {}, "indices": {}}


def test_loads_both_sections(tmp_path):
    write_cfg(tmp_path, {
        "doc_metadata": {"Projects/smaas/Home.md": {"title": "Zorblax Home"}},
        "indices": {"Projects/smaas/_INDEX.md": {"title": "Zorblax Index"}},
    })
    cfg = pc.load_private_config(tmp_path)
    assert cfg["doc_metadata"]["Projects/smaas/Home.md"]["title"] == "Zorblax Home"
    assert cfg["indices"]["Projects/smaas/_INDEX.md"]["title"] == "Zorblax Index"


def test_missing_section_defaults_to_empty(tmp_path):
    write_cfg(tmp_path, {"doc_metadata": {"Projects/smaas/a.md": {"title": "A"}}})
    assert pc.load_private_config(tmp_path)["indices"] == {}


def test_keys_outside_private_dir_are_rejected(tmp_path):
    write_cfg(tmp_path, {"doc_metadata": {"README.MD": {"title": "x"}}})
    with pytest.raises(ValueError, match="outside"):
        pc.load_private_config(tmp_path)


def test_path_traversal_keys_are_rejected(tmp_path):
    write_cfg(tmp_path, {"doc_metadata": {"Projects/smaas/../../x.md": {"title": "x"}}})
    with pytest.raises(ValueError, match="outside"):
        pc.load_private_config(tmp_path)


def test_invalid_json_raises_clear_error(tmp_path):
    cfg = tmp_path / pc.PRIVATE_CONFIG
    cfg.parent.mkdir(parents=True)
    cfg.write_text("{not json", encoding="utf-8")
    with pytest.raises(ValueError, match="not valid JSON"):
        pc.load_private_config(tmp_path)


def test_merged_adds_private_entries_without_mutating_base(tmp_path):
    write_cfg(tmp_path, {"doc_metadata": {"Projects/smaas/a.md": {"title": "A"}}})
    base = {"README.MD": {"title": "R"}}
    merged = pc.merged_doc_metadata(base, tmp_path)
    assert set(merged) == {"README.MD", "Projects/smaas/a.md"}
    assert set(base) == {"README.MD"}


def test_merged_indices_without_private_file_equals_base(tmp_path):
    base = {"Areas/_INDEX.md": {"title": "Areas"}}
    assert pc.merged_indices(base, tmp_path) == base
