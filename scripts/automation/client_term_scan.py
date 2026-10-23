#!/usr/bin/env python3
"""
client_term_scan.py — Scan OSS-scope files for client-specific content.

Part of the client-neutral-content guardrail. Reports `path:line: [class]` and
never prints the matched text, so a hit does not leak the term into logs or chat.

Term sources:
  1. Private file (default: Projects/Burstable MLaaS/.client-terms.txt), one entry per line:
       client: <name>     the client name (also treated as a term)
       term: <text>       literal, case-insensitive; applied everywhere, including third-party docs
       re: <regex>        regex, case-insensitive; first-party files only
       cs: <regex>        regex, case-sensitive; first-party files only
       # comment
     (re:/cs: skip third-party vendor docs because short acronyms collide with vendor text.)
  2. Generic classes built into this script (internal hostnames, emails,
     resolved classification labels, unresolved client placeholder).

Exit code 0 = clean, 1 = hits found.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path

try:
    from common_platform import get_repo_root
except ImportError:  # standalone use
    def get_repo_root(anchor_file=None) -> Path:
        return Path(anchor_file).resolve().parents[2]

DEFAULT_TERMS = "Projects/Burstable_MLaaS/.client-terms.txt"
LEGACY_TERMS = "Projects/Burstable MLaaS/.client-terms.txt"

# Areas that hold private or generated material and are never scanned.
EXEMPT_PREFIXES = (
    "Projects/Burstable_MLaaS/", "Projects/Burstable MLaaS/", "Inbox/", "memories/", "Archives/", "code/",
    ".git/", ".venv/", ".chroma/", ".tantivy/", ".graphify/", ".pytest_cache/",
    "node_modules/", "__pycache__/", ".mcp.json",  # .mcp.json: gitignored, machine-local interpreter paths
)

# Placeholder and generic-class examples live in these two files, so only private terms apply to them.
SELF_FILES = ("scripts/automation/client_term_scan.py", "scripts/tests/test_client_term_scan.py")

# Places where the unresolved placeholder is legitimate (templates and rule text).
PLACEHOLDER_OK_PREFIXES = (
    ".github/", "Resources/Templates/", "Resources/copilot/stanford-llm-creativity/",
) + SELF_FILES

# Third-party documentation only gets the private-term check.
THIRD_PARTY_PREFIXES = (
    "Resources/aws/", "Resources/flyte/", "Resources/ray/", "Resources/docker-k8s/",
    "Resources/third_party_docs/aws/", "Resources/third_party_docs/flyte/", "Resources/third_party_docs/ray/", "Resources/third_party_docs/docker-k8s/",
)

BINARY_EXT = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".pdf", ".db", ".sqlite", ".zip", ".gz",
    ".ico", ".woff", ".woff2", ".pyc",
}
SKIP_DIR_NAMES = {"__pycache__", ".git", ".venv", "node_modules", ".pytest_cache"}
MAX_BYTES = 5 * 1024 * 1024

SHIELD = "\U0001F535\U0001F6E1"  # blue shield label
PLACEHOLDER = "[" + "client" + "]"

RE_RESOLVED_LABEL = re.compile(SHIELD + r"\uFE0F?[ \t]*(?!" + re.escape(PLACEHOLDER) + r")[^\s|\uFE0F]")
RE_PLACEHOLDER = re.compile(re.escape(PLACEHOLDER))
RE_INTERNAL_HOST = re.compile(r"\b[a-z0-9][a-z0-9-]*\.(?:corp|intranet|internal\.corp)\b", re.I)
RE_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
EMAIL_OK = re.compile(r"^git@|@(?:users\.noreply\.github\.com|example\.(?:com|org|net))$", re.I)
# Home-directory paths of a real user; placeholders (<user>, username, ...) are allowed.
RE_PERSONAL_PATH = re.compile(
    r"(?:/Users/|[A-Za-z]:\\[Uu]sers\\)"
    r"(?![<\[{$%.]|(?i:user|username|you|name|me|yourname|your-name)[/\\\s`'\")\]]|(?i:user|username|you|name|me)$)"
    r"[^/\\\s`'\")\]]+[/\\]",
)
RE_SOURCE_LINE = re.compile(r"^>\s*\*\*Source:\*\*")


@dataclass(frozen=True)
class Hit:
    path: str
    line: int
    cls: str


@dataclass
class Terms:
    client: str | None
    strict: list[re.Pattern]  # client:/term: entries; also applied to third-party docs
    loose: list[re.Pattern]   # re:/cs: entries; first-party files only (acronyms collide with vendor text)

    def match(self, line: str, third_party: bool) -> bool:
        pats = self.strict if third_party else self.strict + self.loose
        return any(p.search(line) for p in pats)


def load_terms(terms_file: Path | None) -> Terms | None:
    """Parse the private terms file; None when it is missing."""
    if terms_file is None or not Path(terms_file).is_file():
        return None
    client = None
    strict: list[re.Pattern] = []
    loose: list[re.Pattern] = []
    for raw in Path(terms_file).read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        key, value = key.strip().lower(), value.strip()
        if not value:
            continue
        if key == "client":
            client = value
            strict.append(re.compile(re.escape(value), re.I))
        elif key == "term":
            strict.append(re.compile(re.escape(value), re.I))
        elif key == "re":
            loose.append(re.compile(value, re.I))
        elif key == "cs":
            loose.append(re.compile(value))
    return Terms(client, strict, loose)


def load_client_name(terms_file: Path | None) -> str | None:
    terms = load_terms(terms_file)
    return terms.client if terms else None


def _is_exempt(rel: str) -> bool:
    return any(rel.startswith(p) for p in EXEMPT_PREFIXES)


def _read_text(path: Path) -> str | None:
    try:
        if path.suffix.lower() in BINARY_EXT or path.stat().st_size > MAX_BYTES:
            return None
        data = path.read_bytes()
    except OSError:
        return None
    if b"\0" in data[:8192]:
        return None
    return data.decode("utf-8", errors="replace")


def _iter_files(root: Path, paths: list[str] | None):
    starts = [root / p for p in paths] if paths else [root]
    for start in starts:
        if start.is_file():
            yield start
            continue
        for dirpath, dirnames, filenames in os.walk(start):
            rel_dir = Path(dirpath).relative_to(root).as_posix()
            prefix = "" if rel_dir == "." else rel_dir + "/"
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIR_NAMES and not _is_exempt(prefix + d + "/")]
            for name in filenames:
                yield Path(dirpath) / name


def scan(root: Path, terms_file: Path | None = None, paths: list[str] | None = None) -> list[Hit]:
    root = Path(root)
    terms = load_terms(terms_file)
    terms_path = Path(terms_file).resolve() if terms_file else None
    hits: list[Hit] = []
    for file in _iter_files(root, paths):
        rel = file.relative_to(root).as_posix()
        if _is_exempt(rel) or (terms_path and file.resolve() == terms_path):
            continue
        text = _read_text(file)
        if text is None:
            continue
        third_party = rel.startswith(THIRD_PARTY_PREFIXES)
        placeholder_ok = rel.startswith(PLACEHOLDER_OK_PREFIXES)
        generic = not third_party and rel not in SELF_FILES
        check_path = rel not in SELF_FILES
        for n, line in enumerate(text.splitlines(), 1):
            found: set[str] = set()
            if terms and terms.match(line, third_party):
                found.add("private-term")
            if check_path and (not third_party or RE_SOURCE_LINE.match(line)) and RE_PERSONAL_PATH.search(line):
                found.add("personal-abs-path")
            if generic:
                if RE_RESOLVED_LABEL.search(line):
                    found.add("resolved-label")
                if not placeholder_ok and RE_PLACEHOLDER.search(line):
                    found.add("unresolved-client-placeholder")
                if RE_INTERNAL_HOST.search(line):
                    found.add("internal-host")
                if any(not EMAIL_OK.search(m.group(0)) for m in RE_EMAIL.finditer(line)):
                    found.add("email-address")
            hits.extend(Hit(rel, n, c) for c in sorted(found))
    return sorted(hits, key=lambda h: (h.path, h.line, h.cls))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan OSS-scope files for client-specific content.")
    parser.add_argument("--root", type=Path, default=None, help="Repository root (default: auto)")
    parser.add_argument("--terms-file", type=Path, default=None, help=f"Private terms file (default: {DEFAULT_TERMS})")
    parser.add_argument("--paths", nargs="*", default=None, help="Limit the scan to these paths under the root")
    args = parser.parse_args(argv)

    root = (args.root or get_repo_root(__file__)).resolve()
    terms_file = args.terms_file or (root / DEFAULT_TERMS)
    if not Path(terms_file).is_file():
        legacy = root / LEGACY_TERMS
        if legacy.is_file():
            terms_file = legacy
        else:
            print("notice: private terms file not found; generic classes only")
            terms_file = None

    hits = scan(root, terms_file, args.paths)
    for h in hits:
        print(f"{h.path}:{h.line}: [{h.cls}]")
    print(f"{len(hits)} hit(s)")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
