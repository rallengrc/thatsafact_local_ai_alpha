#!/usr/bin/env python3
"""
sync_prompts_db.py — Ingestion engine & SQLite FTS5 synchronization for team prompt telemetry.

Scans git-partitioned session memories (memories/<username>/sessions/) and populates
an ephemeral, high-speed SQLite FTS5 database (prompts_analytics.db).

Features:
- Sub-millisecond Okapi BM25 full-text search across all team prompts.
- Document attribution tracking linking prompts to workspace markdown and code files.
- Token consumption and tool usage analytics.
- Zero cloud egress; completely air-gap compliant.
"""

import argparse
import json
import logging
import os
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

_CURRENT_DIR = Path(__file__).resolve().parent
_SCRIPTS_DIR = _CURRENT_DIR.parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from common_platform import get_repo_root, normalize_posix_path

REPO_ROOT = get_repo_root(Path(__file__))
DEFAULT_DB_PATH = REPO_ROOT / "prompts_analytics.db"
DEFAULT_MEMORIES_DIR = REPO_ROOT / "memories"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("sync_prompts_db")

# Regex to detect workspace documentation / code citations in prompts and transcripts
DOC_PATH_RE = re.compile(
    r"(?:(?:Projects|Resources|scripts|memories|code|\.github)[/\\].+?\.[a-zA-Z0-9]{1,5})"
)

EXCLUDED_MEMORIES_DIRS = {"mlaas", "repo", "session", "sessions", "__pycache__", ".DS_Store"}


def get_sqlite_connection(db_path: Path) -> sqlite3.Connection:
    """Connect to SQLite database with foreign keys and row factory."""
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection, clear: bool = False) -> None:
    """Create relational tables and FTS5 virtual table."""
    with conn:
        if clear:
            logger.info("Clearing existing telemetry tables...")
            conn.execute("DROP TABLE IF EXISTS doc_citations;")
            conn.execute("DROP TABLE IF EXISTS prompt_fts;")
            conn.execute("DROP TABLE IF EXISTS prompt_turns;")

        conn.execute("""
        CREATE TABLE IF NOT EXISTS prompt_turns (
            turn_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            session_id TEXT NOT NULL,
            session_nickname TEXT,
            turn_index INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            model TEXT NOT NULL,
            prompt_text TEXT NOT NULL,
            response_preview TEXT,
            prompt_tokens INTEGER DEFAULT 0,
            completion_tokens INTEGER DEFAULT 0,
            total_tokens INTEGER DEFAULT 0,
            tools_used TEXT DEFAULT '[]',
            tool_count INTEGER DEFAULT 0,
            execution_time_ms REAL DEFAULT 0.0,
            helpful_docs TEXT DEFAULT '[]',
            classification TEXT DEFAULT 'general'
        );
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS doc_citations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            turn_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            doc_path TEXT NOT NULL,
            citation_type TEXT NOT NULL,
            relevance_score REAL DEFAULT 1.0,
            FOREIGN KEY (turn_id) REFERENCES prompt_turns (turn_id) ON DELETE CASCADE
        );
        """)

        conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS prompt_fts USING fts5(
            turn_id UNINDEXED,
            user_id,
            session_nickname,
            prompt_text,
            response_preview,
            tools_used,
            helpful_docs,
            tokenize = 'unicode61 remove_diacritics 1'
        );
        """)

        conn.execute("CREATE INDEX IF NOT EXISTS idx_turns_user ON prompt_turns(user_id);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_turns_session ON prompt_turns(session_id);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_citations_doc ON doc_citations(doc_path);")


def extract_cited_docs(text: str) -> List[str]:
    """Extract referenced workspace paths from text."""
    if not text:
        return []
    matches = DOC_PATH_RE.findall(text)
    cleaned = []
    for m in matches:
        m = m.rstrip(".,;:)`'\"")
        m = normalize_posix_path(m)
        if (REPO_ROOT / m).exists() or m.endswith((".md", ".py", ".json", ".yaml", ".yml", ".sh")):
            cleaned.append(m)
    return sorted(list(set(cleaned)))


def discover_user_partitions(memories_dir: Path) -> List[Tuple[str, Path]]:
    """Find user memory directories under memories/."""
    partitions = []
    if not memories_dir.exists():
        return partitions

    for entry in memories_dir.iterdir():
        if entry.is_dir() and entry.name not in EXCLUDED_MEMORIES_DIRS:
            sessions_dir = entry / "sessions"
            if sessions_dir.exists():
                partitions.append((entry.name, entry))

    # Also include legacy root memories/sessions if no user partitions found
    if not partitions and (memories_dir / "sessions").exists():
        partitions.append(("shared", memories_dir))

    return partitions


def parse_session_md(md_path: Path) -> Dict[str, Any]:
    """Parse an individual session Markdown log into structured turns."""
    try:
        text = md_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        logger.warning(f"Could not read {md_path}: {e}")
        return {}

    sess_id = ""
    id_match = re.search(r"\*\*Session ID\*\*:\s*`([^`]+)`", text)
    if id_match:
        sess_id = id_match.group(1).strip()

    nick_match = re.search(r"# Session Record:\s*(.+)", text)
    nickname = nick_match.group(1).strip() if nick_match else md_path.stem

    # Extract user prompts
    prompts = []
    prompt_blocks = re.split(r"### Prompt\s+\d+\s*\((?:`([^`]+)`)?\)", text)
    # prompt_blocks alternates [header, timestamp1, content1, timestamp2, content2, ...]
    if len(prompt_blocks) > 1:
        for i in range(1, len(prompt_blocks), 2):
            ts = prompt_blocks[i] or ""
            raw_content = prompt_blocks[i + 1] if (i + 1) < len(prompt_blocks) else ""
            # Extract code block
            code_match = re.search(r"```(?:text)?\n(.*?)```", raw_content, re.DOTALL)
            p_text = code_match.group(1).strip() if code_match else raw_content.strip()
            if p_text:
                prompts.append({"timestamp": ts, "content": p_text})

    return {
        "session_id": sess_id,
        "nickname": nickname,
        "prompts": prompts,
    }


def sync_user_partition(
    conn: sqlite3.Connection,
    user_id: str,
    user_dir: Path,
) -> Dict[str, int]:
    """Sync a single user's session memories into prompt_turns, doc_citations, and prompt_fts."""
    sessions_dir = user_dir / "sessions"
    meta_file = sessions_dir / "sessions_metadata.json"

    turns_synced = 0
    citations_synced = 0

    known_sessions_meta = {}
    if meta_file.exists():
        try:
            meta_data = json.loads(meta_file.read_text(encoding="utf-8", errors="replace"))
            for s in meta_data.get("sessions", []):
                sid = s.get("id")
                if sid:
                    known_sessions_meta[sid] = s
        except Exception as e:
            logger.warning(f"Error reading metadata from {meta_file}: {e}")

    # Process all session-*.md files
    for md_file in sorted(sessions_dir.glob("session-*.md")):
        parsed = parse_session_md(md_file)
        sid = parsed.get("session_id") or md_file.stem
        nick = parsed.get("nickname") or md_file.stem
        prompts = parsed.get("prompts", [])

        meta_info = known_sessions_meta.get(sid, {})
        assistant_turns = meta_info.get("assistant_turns", [])
        tool_calls = meta_info.get("tool_calls", [])

        # Default model tag
        default_model = meta_info.get("usage", {}).get("lastActiveModel") or "copilot-agent"

        for idx, p in enumerate(prompts, 1):
            turn_id = f"{user_id}-{sid[:12]}-turn{idx:02d}"
            prompt_text = p.get("content", "").strip()
            ts = p.get("timestamp") or meta_info.get("timing", {}).get("first_event") or ""

            # Correlate assistant response preview if available
            resp_preview = ""
            turn_model = default_model
            tools = []
            if idx <= len(assistant_turns):
                a_turn = assistant_turns[idx - 1]
                resp_preview = a_turn.get("content_preview", "")
                turn_model = a_turn.get("model") or default_model
                tools = a_turn.get("tools", [])

            # Extract docs
            cited = extract_cited_docs(prompt_text + " " + resp_preview)

            conn.execute(
                """
                INSERT OR REPLACE INTO prompt_turns (
                    turn_id, user_id, session_id, session_nickname, turn_index,
                    timestamp, model, prompt_text, response_preview,
                    tools_used, tool_count, helpful_docs
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    turn_id,
                    user_id,
                    sid,
                    nick,
                    idx,
                    ts,
                    turn_model,
                    prompt_text,
                    resp_preview,
                    json.dumps(tools),
                    len(tools),
                    json.dumps(cited),
                ),
            )

            # Insert FTS index
            conn.execute(
                """
                INSERT INTO prompt_fts (
                    turn_id, user_id, session_nickname, prompt_text,
                    response_preview, tools_used, helpful_docs
                ) VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    turn_id,
                    user_id,
                    nick,
                    prompt_text,
                    resp_preview,
                    json.dumps(tools),
                    json.dumps(cited),
                ),
            )
            turns_synced += 1

            # Insert doc citations
            for doc in cited:
                conn.execute(
                    """
                    INSERT INTO doc_citations (turn_id, user_id, doc_path, citation_type, relevance_score)
                    VALUES (?, ?, ?, ?, ?);
                    """,
                    (turn_id, user_id, doc, "prompt_reference", 1.0),
                )
                citations_synced += 1

    return {"turns": turns_synced, "citations": citations_synced}


def sync_all(
    db_path: Path = DEFAULT_DB_PATH,
    memories_dir: Path = DEFAULT_MEMORIES_DIR,
    clear: bool = False,
    user_filter: Optional[str] = None,
) -> Dict[str, Any]:
    """Execute complete synchronization of memories into SQLite FTS5."""
    conn = get_sqlite_connection(db_path)
    init_db(conn, clear=clear)

    partitions = discover_user_partitions(memories_dir)
    total_turns = 0
    total_citations = 0
    users_synced = []

    with conn:
        # If not clear, wipe FTS table before re-populating to prevent duplicates
        conn.execute("DELETE FROM prompt_fts;")
        conn.execute("DELETE FROM doc_citations;")
        conn.execute("DELETE FROM prompt_turns;")

        for user_id, user_dir in partitions:
            if user_filter and user_id != user_filter:
                continue
            logger.info(f"Syncing partition for user '{user_id}' from {user_dir}...")
            res = sync_user_partition(conn, user_id, user_dir)
            total_turns += res["turns"]
            total_citations += res["citations"]
            users_synced.append(user_id)

    conn.close()
    return {
        "status": "success",
        "db_path": str(db_path),
        "users": users_synced,
        "turns_synced": total_turns,
        "citations_synced": total_citations,
    }


def get_db_stats(db_path: Path = DEFAULT_DB_PATH) -> Dict[str, Any]:
    """Return summary statistics of prompt telemetry database."""
    if not db_path.exists():
        return {"exists": False, "db_path": str(db_path)}

    conn = get_sqlite_connection(db_path)
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM prompt_turns;")
    total_turns = cur.fetchone()[0]

    cur.execute("SELECT count(DISTINCT user_id) FROM prompt_turns;")
    user_count = cur.fetchone()[0]

    cur.execute("SELECT count(DISTINCT session_id) FROM prompt_turns;")
    session_count = cur.fetchone()[0]

    cur.execute("SELECT count(*) FROM doc_citations;")
    citation_count = cur.fetchone()[0]

    cur.execute("SELECT doc_path, count(*) as cnt FROM doc_citations GROUP BY doc_path ORDER BY cnt DESC LIMIT 5;")
    top_docs = [dict(r) for r in cur.fetchall()]

    conn.close()
    return {
        "exists": True,
        "db_path": str(db_path),
        "total_turns": total_turns,
        "users": user_count,
        "sessions": session_count,
        "doc_citations": citation_count,
        "top_cited_docs": top_docs,
    }


def search_prompts(query: str, db_path: Path = DEFAULT_DB_PATH, limit: int = 10) -> List[Dict[str, Any]]:
    """Execute Okapi BM25 full-text search against prompt_fts."""
    if not db_path.exists():
        return []

    conn = get_sqlite_connection(db_path)
    cur = conn.cursor()
    sql = """
        SELECT
            p.turn_id,
            p.user_id,
            p.session_nickname,
            p.timestamp,
            p.prompt_text,
            p.tools_used,
            snippet(prompt_fts, 3, '<b>', '</b>', '...', 15) AS match_snippet,
            bm25(prompt_fts) AS rank_score
        FROM prompt_fts f
        JOIN prompt_turns p ON f.turn_id = p.turn_id
        WHERE prompt_fts MATCH ?
        ORDER BY rank_score ASC
        LIMIT ?;
    """
    try:
        cur.execute(sql, (query, limit))
        results = [dict(r) for r in cur.fetchall()]
    except Exception as e:
        logger.error(f"FTS search error: {e}")
        results = []
    finally:
        conn.close()
    return results


def main():
    parser = argparse.ArgumentParser(description="Team Prompt Telemetry Sync & Search Engine")
    parser.add_argument("--db-path", default=str(DEFAULT_DB_PATH), help="Path to SQLite database")
    parser.add_argument("--memories-dir", default=str(DEFAULT_MEMORIES_DIR), help="Path to memories directory")
    parser.add_argument("--clear", action="store_true", help="Clear and reinitialize database")
    parser.add_argument("--user", default=None, help="Filter sync to single username")
    parser.add_argument("--stats", action="store_true", help="Print telemetry database stats and exit")
    parser.add_argument("--search", default=None, help="Execute BM25 search on prompt history")
    parser.add_argument("--limit", type=int, default=5, help="Result limit for search")

    args = parser.parse_args()
    db_path = Path(args.db_path)

    if args.stats:
        stats = get_db_stats(db_path)
        print(json.dumps(stats, indent=2))
        return

    if args.search:
        results = search_prompts(args.search, db_path=db_path, limit=args.limit)
        print(f"--- Prompt Search Results for '{args.search}' ({len(results)} matches) ---")
        for idx, r in enumerate(results, 1):
            print(f"\n[{idx}] User: {r['user_id']} | Session: {r['session_nickname']} | Turn: {r['turn_id']}")
            print(f"    Snippet: {r['match_snippet']}")
            print(f"    Prompt:  {r['prompt_text'][:120]}...")
        return

    res = sync_all(
        db_path=db_path,
        memories_dir=Path(args.memories_dir),
        clear=args.clear,
        user_filter=args.user,
    )
    print(f"Prompt Telemetry Sync Complete:")
    print(f"  Database:        {res['db_path']}")
    print(f"  Users Synced:    {', '.join(res['users'])}")
    print(f"  Turns Synced:    {res['turns_synced']}")
    print(f"  Citations Found: {res['citations_synced']}")


if __name__ == "__main__":
    main()
