#!/usr/bin/env python3
"""
skill_distiller.py — Distills verbose external SKILL.md files into Lean AI format (≤100L).

Provides:
  1. TimedExpiringCache — Memory-safe in-memory cache with TTL (similar to Apache PassiveExpiringMap)
     so repeated prompt lookups do not waste CPU, while automatically purging to avoid memory waste.
  2. LeanSkillDistiller — Trims conversational filler, preserves frontmatter triggers, core commands,
     actionable checklists, and links back to the original full file path for reference.
"""

import os
import re
import time
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class TimedExpiringCache:
    """Lightweight in-memory cache with timed expiration (TTL).

    Prevents memory leaks by passively expiring stale entries on access,
    mirroring Apache Commons Collections PassiveExpiringMap.
    """

    def __init__(self, default_ttl_seconds: float = 300.0):
        self._ttl = default_ttl_seconds
        self._cache: Dict[str, Tuple[float, Any]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        """Retrieve value if unexpired; purges if expired."""
        with self._lock:
            if key not in self._cache:
                return None
            ts, val = self._cache[key]
            if time.time() - ts > self._ttl:
                del self._cache[key]
                return None
            return val

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        """Store value with timestamp."""
        effective_ttl = ttl if ttl is not None else self._ttl
        with self._lock:
            # Passive cleanup of expired keys if cache grows large
            if len(self._cache) > 200:
                self._purge_expired_locked()
            self._cache[key] = (time.time(), value)

    def _purge_expired_locked(self) -> None:
        now = time.time()
        expired = [k for k, (ts, _) in self._cache.items() if now - ts > self._ttl]
        for k in expired:
            del self._cache[k]

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()

    def size(self) -> int:
        with self._lock:
            self._purge_expired_locked()
            return len(self._cache)


# Global process-level cache (5 minute TTL)
_SKILL_CACHE = TimedExpiringCache(default_ttl_seconds=300.0)


class LeanSkillDistiller:
    """Transforms verbose SKILL.md markdown into lean, actionable procedural guides (≤100L)."""

    MAX_LINE_BUDGET = 100

    @classmethod
    def parse_frontmatter(cls, content: str) -> Tuple[Dict[str, str], str]:
        """Extract YAML frontmatter and remaining body text."""
        frontmatter: Dict[str, str] = {}
        body = content

        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                fm_text = parts[1]
                body = parts[2].lstrip()
                for line in fm_text.splitlines():
                    if ":" in line:
                        k, v = line.split(":", 1)
                        frontmatter[k.strip()] = v.strip().strip("'\"")

        return frontmatter, body

    @classmethod
    def distill_text(
        cls,
        raw_text: str,
        source_path: str,
        max_lines: int = MAX_LINE_BUDGET,
    ) -> Dict[str, Any]:
        """Distill raw SKILL.md text into a lean format with line-budget enforcement."""
        frontmatter, body = cls.parse_frontmatter(raw_text)

        name = frontmatter.get("name") or Path(source_path).parent.name
        description = frontmatter.get("description", "").strip()

        raw_lines = raw_text.splitlines()
        total_raw_lines = len(raw_lines)

        # If already lean (<= max_lines), return with clean reference envelope
        if total_raw_lines <= max_lines:
            return {
                "skill_name": name,
                "description": description,
                "source_path": source_path,
                "total_raw_lines": total_raw_lines,
                "distilled_lines": total_raw_lines,
                "lean_markdown": raw_text.strip(),
                "reference_note": f"Original full file ({total_raw_lines}L) matches lean budget: {source_path}",
                "cached": False,
            }

        # Otherwise distill: extract headers, commands, steps, and strip narrative filler
        distilled: List[str] = []

        # 1. Compact Frontmatter Header
        distilled.append(f"# Skill: {name}")
        if description:
            distilled.append(f"> **Purpose:** {description}")
        distilled.append(f"> **Reference Source:** [{Path(source_path).name}]({source_path}) ({total_raw_lines} lines total)")
        distilled.append("")

        body_lines = body.splitlines()
        in_code_block = False
        skip_conversational_intro = True

        for line in body_lines:
            stripped = line.strip()

            if stripped.startswith("```"):
                in_code_block = not in_code_block
                distilled.append(line)
                continue

            if in_code_block:
                distilled.append(line)
                continue

            # Keep headings
            if stripped.startswith("#"):
                skip_conversational_intro = False
                distilled.append(line)
                continue

            # Skip wordy introductions before first section
            if skip_conversational_intro and not stripped.startswith("-") and not stripped.startswith("1."):
                continue

            # Keep bullet points, checklists, commands, quotes, tables
            if (
                stripped.startswith("-")
                or stripped.startswith("*")
                or re.match(r"^\d+\.", stripped)
                or stripped.startswith(">")
                or stripped.startswith("|")
                or "`" in stripped
            ):
                distilled.append(line)
            elif not stripped:
                # Keep single blank lines
                if distilled and distilled[-1] != "":
                    distilled.append("")

            if len(distilled) >= max_lines - 5:
                break

        # Append reference pointer footer
        distilled.append("")
        distilled.append(f"---")
        distilled.append(f"*(Distilled from {total_raw_lines}L to {len(distilled)}L. Full reference at: `{source_path}`)*")

        final_md = "\n".join(distilled[:max_lines])

        return {
            "skill_name": name,
            "description": description,
            "source_path": source_path,
            "total_raw_lines": total_raw_lines,
            "distilled_lines": len(final_md.splitlines()),
            "lean_markdown": final_md,
            "reference_note": f"Full verbose skill ({total_raw_lines}L) available at {source_path}",
            "cached": False,
        }

    @classmethod
    def distill_file(
        cls,
        file_path: str,
        max_lines: int = MAX_LINE_BUDGET,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """Read and distill a SKILL.md file, with timed cache lookup."""
        norm_path = os.path.abspath(file_path)

        if use_cache:
            cached = _SKILL_CACHE.get(norm_path)
            if cached is not None:
                cached_copy = dict(cached)
                cached_copy["cached"] = True
                return cached_copy

        p = Path(norm_path)
        if not p.is_file():
            return {
                "error": f"File not found: {norm_path}",
                "source_path": norm_path,
            }

        try:
            content = p.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            return {
                "error": f"Failed to read file: {e}",
                "source_path": norm_path,
            }

        result = cls.distill_text(content, norm_path, max_lines=max_lines)

        if use_cache and "error" not in result:
            _SKILL_CACHE.set(norm_path, result)

        return result
