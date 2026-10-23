#!/usr/bin/env python3
"""
private_config.py — Load client-specific generator metadata from the private project directory.

The OSS-scope generators (update_markdown_metadata.py, generate_indices_and_master_toc.py)
keep only generic entries. Entries describing client documents live in a private JSON file
inside Projects/Burstable MLaaS/, which is gitignored where the OSS repo is published:

    {
      "doc_metadata": {"Projects/Burstable MLaaS/<doc>.md": {...frontmatter fields...}},
      "indices":      {"Projects/Burstable MLaaS/<dir>/_INDEX.md": {...index definition...}}
    }

Every key must stay inside the private directory. A missing file means "no private entries".
"""

from __future__ import annotations

import json
from pathlib import Path, PurePosixPath

PRIVATE_DIR = "Projects/Burstable_MLaaS"
LEGACY_PRIVATE_DIR = "Projects/Burstable MLaaS"
PRIVATE_CONFIG = f"{PRIVATE_DIR}/.generator-config.json"
LEGACY_PRIVATE_CONFIG = f"{LEGACY_PRIVATE_DIR}/.generator-config.json"
SECTIONS = ("doc_metadata", "indices")


def _inside_private_dir(key: str) -> bool:
    parts = PurePosixPath(key).parts
    base = PurePosixPath(PRIVATE_DIR).parts
    legacy_base = PurePosixPath(LEGACY_PRIVATE_DIR).parts
    is_inside = (parts[: len(base)] == base or parts[: len(legacy_base)] == legacy_base)
    return is_inside and ".." not in parts and not PurePosixPath(key).is_absolute()


def load_private_config(workspace: Path | str) -> dict[str, dict]:
    """Return {"doc_metadata": {...}, "indices": {...}}; empty sections when the file is absent."""
    path = Path(workspace) / PRIVATE_CONFIG
    if not path.is_file():
        legacy_path = Path(workspace) / LEGACY_PRIVATE_CONFIG
        if legacy_path.is_file():
            path = legacy_path
        else:
            return {name: {} for name in SECTIONS}
    result: dict[str, dict] = {name: {} for name in SECTIONS}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path} is not valid JSON: {exc}") from exc
    for name in SECTIONS:
        section = data.get(name, {})
        for key in section:
            if not _inside_private_dir(key):
                raise ValueError(f"{path}: key '{key}' is outside private directory")
        result[name] = section
    return result


def merged_doc_metadata(base: dict, workspace: Path | str) -> dict:
    return {**base, **load_private_config(workspace)["doc_metadata"]}


def merged_indices(base: dict, workspace: Path | str) -> dict:
    return {**base, **load_private_config(workspace)["indices"]}
