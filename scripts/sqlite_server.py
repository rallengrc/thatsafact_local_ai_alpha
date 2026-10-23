#!/usr/bin/env python3
"""
sqlite_server.py — MCP 2.x Server for SQLite Databases.

Exposes tools to query, inspect, and analyze:
1. MLaaS Benchmark Metrics (`benchmark_metrics.db`): Performance comparisons,
   latencies, throughput, and Ray/Flyte feature attribution.
2. Self-Referential Copilot Data (`~/.copilot/session-store.db`): Historical prompts,
   interactive turns, checkpoints, and session files.

Built with native MCP 2.x MCPServer over stdio.
"""

import os
import sys
import json
import sqlite3
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from common_platform import (
    get_repo_root,
    get_venv_python,
    ensure_venv_site_packages,
    get_copilot_dir,
)

REPO_ROOT = get_repo_root(Path(__file__))
VENV_DIR = REPO_ROOT / ".venv"
venv_python = get_venv_python(REPO_ROOT)

# Ensure execution under project .venv
if sys.prefix != str(VENV_DIR) and venv_python.exists() and Path(sys.executable) != venv_python:
    os.environ["VIRTUAL_ENV"] = str(VENV_DIR)
    os.environ.pop("PYTHONHOME", None)
    try:
        os.execv(str(venv_python), [str(venv_python)] + sys.argv)
    except OSError:
        import subprocess
        sys.exit(subprocess.call([str(venv_python)] + sys.argv))

ensure_venv_site_packages(REPO_ROOT)

from mcp.server import MCPServer

# Reserve stdout strictly for JSON-RPC
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger("sqlite-mcp-server")

mcp = MCPServer("sqlite-server")

# Default database targets
DEFAULT_METRICS_DB = os.path.join(
    str(REPO_ROOT), "Projects", "hello-mlaas-burst", "benchmark_metrics.db"
)
DEFAULT_COPILOT_DB = str(get_copilot_dir() / "session-store.db")
DEFAULT_PROMPTS_DB = os.path.join(str(REPO_ROOT), "prompts_analytics.db")


def _resolve_db_path(db: str) -> str:
    """Resolves friendly db aliases ('metrics', 'copilot', 'prompts') to absolute paths."""
    if db in ("metrics", "mlaas", "benchmark", "benchmarks"):
        return DEFAULT_METRICS_DB
    elif db in ("copilot", "self-referential", "session-store", "sessions"):
        return DEFAULT_COPILOT_DB
    elif db in ("prompts", "telemetry", "prompt_telemetry", "analytics", "prompts_analytics"):
        return DEFAULT_PROMPTS_DB
    expanded = os.path.expanduser(db)
    if os.path.isabs(expanded):
        return expanded
    return os.path.join(str(REPO_ROOT), expanded)


@mcp.tool()
def list_tables(db: str = "metrics") -> str:
    """
    List all tables in the specified SQLite database.
    
    Args:
        db: Target database ('metrics' for MLaaS benchmark DB, 'copilot' for session-store DB, or an absolute path).
    """
    path = _resolve_db_path(db)
    if not os.path.exists(path):
        return f"Error: Database file not found at {path}"

    try:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        cur = conn.cursor()
        tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;").fetchall()]
        views = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='view' ORDER BY name;").fetchall()]
        conn.close()
        return json.dumps({"database": path, "tables": tables, "views": views}, indent=2)
    except Exception as e:
        return f"Error querying tables: {str(e)}"


@mcp.tool()
def describe_table(table_name: str, db: str = "metrics") -> str:
    """
    Get column schema and row count for a specific table in SQLite.
    
    Args:
        table_name: Name of the table to describe.
        db: Target database ('metrics', 'copilot', or path).
    """
    path = _resolve_db_path(db)
    if not os.path.exists(path):
        return f"Error: Database file not found at {path}"

    try:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        columns = [dict(r) for r in cur.execute(f"PRAGMA table_info('{table_name}');").fetchall()]
        count = cur.execute(f"SELECT COUNT(*) FROM '{table_name}';").fetchone()[0]
        conn.close()
        return json.dumps({"database": path, "table": table_name, "row_count": count, "columns": columns}, indent=2)
    except Exception as e:
        return f"Error describing table '{table_name}': {str(e)}"


@mcp.tool()
def read_query(query: str, db: str = "metrics") -> str:
    """
    Execute a read-only SQL query on the specified database.
    
    Args:
        query: SQL SELECT query to execute.
        db: Target database ('metrics' for MLaaS benchmarks, 'copilot' for session store, or file path).
    """
    # Guard against non-read queries
    q_strip = query.strip().upper()
    if not q_strip.startswith(("SELECT", "WITH", "PRAGMA", "EXPLAIN")):
        return "Error: read_query only allows read-only SELECT or PRAGMA statements."

    path = _resolve_db_path(db)
    if not os.path.exists(path):
        return f"Error: Database file not found at {path}"

    try:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        rows = [dict(r) for r in cur.execute(query).fetchall()]
        conn.close()
        return json.dumps({"row_count": len(rows), "results": rows}, indent=2)
    except Exception as e:
        return f"SQL execution error: {str(e)}"


@mcp.tool()
def get_benchmark_metrics(limit: int = 5) -> str:
    """
    Quickly retrieve the latest MLaaS empirical performance benchmarks comparing Old vs New way.
    """
    path = DEFAULT_METRICS_DB
    if not os.path.exists(path):
        return "No benchmark runs recorded yet in benchmark_metrics.db."

    try:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        rows = [
            dict(r)
            for r in cur.execute(
                """
            SELECT pipeline_type, total_wall_time_ms, data_prep_ms, disk_io_ms, training_ms,
                   throughput_samples_sec, speedup_factor, cache_status, r2_score, timestamp
            FROM pipeline_benchmarks
            ORDER BY timestamp DESC
            LIMIT ?;
            """,
                (limit,),
            ).fetchall()
        ]
        conn.close()
        return json.dumps({"benchmark_runs": rows}, indent=2)
    except Exception as e:
        return f"Error retrieving benchmark metrics: {str(e)}"


@mcp.tool()
def get_feature_attributions(run_id: str = "") -> str:
    """
    Retrieve Ray and Flyte architectural feature attributions explaining the performance speedups.
    """
    path = DEFAULT_METRICS_DB
    if not os.path.exists(path):
        return "No benchmark runs recorded yet in benchmark_metrics.db."

    try:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        if run_id:
            rows = [
                dict(r)
                for r in cur.execute(
                    "SELECT framework, feature_name, feature_category, technical_mechanism, empirical_impact, metric_improvement FROM feature_attribution WHERE run_id = ?;",
                    (run_id,),
                ).fetchall()
            ]
        else:
            rows = [
                dict(r)
                for r in cur.execute(
                    "SELECT DISTINCT framework, feature_name, feature_category, technical_mechanism, empirical_impact, metric_improvement FROM feature_attribution LIMIT 10;"
                ).fetchall()
            ]
        conn.close()
        return json.dumps({"feature_attributions": rows}, indent=2)
    except Exception as e:
        return f"Error retrieving feature attributions: {str(e)}"


@mcp.tool()
def get_recent_copilot_turns(limit: int = 10) -> str:
    """
    Query historical user prompts and conversation turns from the self-referential session-store.db.
    """
    path = DEFAULT_COPILOT_DB
    if not os.path.exists(path):
        return f"Copilot session store not found at {path}."

    try:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        rows = [
            dict(r)
            for r in cur.execute(
                """
            SELECT s.id as session_id, s.summary, t.turn_index, t.user_message, t.timestamp
            FROM turns t
            JOIN sessions s ON t.session_id = s.id
            ORDER BY t.timestamp DESC
            LIMIT ?;
            """,
                (limit,),
            ).fetchall()
        ]
        conn.close()
        return json.dumps({"recent_turns": rows}, indent=2)
    except Exception as e:
        return f"Error reading self-referential turns: {str(e)}"


@mcp.tool()
def search_team_prompts(query: str, user: str = "", limit: int = 10) -> str:
    """
    Search cross-team prompt history using high-speed SQLite FTS5 Okapi BM25 ranking.

    Args:
        query: Full-text search query (supports boolean operators and prefix matching e.g. 'karpenter*', 'plasma OR ray').
        user: Optional filter by user ID (e.g. 'alice', 'bob', 'carol', 'dave').
        limit: Maximum results to return (default: 10).
    """
    path = DEFAULT_PROMPTS_DB
    if not os.path.exists(path):
        return f"Team prompt analytics database not found at {path}. Run sync_prompts_db.py to generate it."

    try:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        if user:
            sql = """
                SELECT p.turn_id, p.user_id, p.session_nickname, p.timestamp, p.prompt_text,
                       snippet(prompt_fts, 3, '<b>', '</b>', '...', 15) AS match_snippet,
                       bm25(prompt_fts) AS rank_score
                FROM prompt_fts f
                JOIN prompt_turns p ON f.turn_id = p.turn_id
                WHERE prompt_fts MATCH ? AND p.user_id = ?
                ORDER BY rank_score ASC
                LIMIT ?;
            """
            rows = [dict(r) for r in cur.execute(sql, (query, user, limit)).fetchall()]
        else:
            sql = """
                SELECT p.turn_id, p.user_id, p.session_nickname, p.timestamp, p.prompt_text,
                       snippet(prompt_fts, 3, '<b>', '</b>', '...', 15) AS match_snippet,
                       bm25(prompt_fts) AS rank_score
                FROM prompt_fts f
                JOIN prompt_turns p ON f.turn_id = p.turn_id
                WHERE prompt_fts MATCH ?
                ORDER BY rank_score ASC
                LIMIT ?;
            """
            rows = [dict(r) for r in cur.execute(sql, (query, limit)).fetchall()]
        conn.close()
        return json.dumps({"query": query, "match_count": len(rows), "results": rows}, indent=2)
    except Exception as e:
        return f"Error searching team prompts: {str(e)}"


@mcp.tool()
def get_doc_effectiveness_rankings(limit: int = 10) -> str:
    """
    Return top workspace documentation and code files ranked by how frequently they assisted AI prompt resolution.
    """
    path = DEFAULT_PROMPTS_DB
    if not os.path.exists(path):
        return f"Team prompt analytics database not found at {path}."

    try:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        sql = """
            SELECT doc_path, count(*) as citation_count,
                   count(DISTINCT user_id) as distinct_users,
                   count(DISTINCT turn_id) as distinct_turns
            FROM doc_citations
            GROUP BY doc_path
            ORDER BY citation_count DESC
            LIMIT ?;
        """
        rows = [dict(r) for r in cur.execute(sql, (limit,)).fetchall()]
        conn.close()
        return json.dumps({"doc_rankings": rows}, indent=2)
    except Exception as e:
        return f"Error ranking doc effectiveness: {str(e)}"


@mcp.tool()
def get_team_token_usage() -> str:
    """
    Summarize token consumption, turn counts, and model usage across users from prompt telemetry.
    """
    path = DEFAULT_PROMPTS_DB
    if not os.path.exists(path):
        return f"Team prompt analytics database not found at {path}."

    try:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        by_user = [
            dict(r)
            for r in cur.execute(
                """
            SELECT user_id, count(*) as turns_count,
                   count(DISTINCT session_id) as sessions_count
            FROM prompt_turns
            GROUP BY user_id
            ORDER BY turns_count DESC;
            """
            ).fetchall()
        ]
        by_model = [
            dict(r)
            for r in cur.execute(
                """
            SELECT model, count(*) as turns_count
            FROM prompt_turns
            GROUP BY model
            ORDER BY turns_count DESC;
            """
            ).fetchall()
        ]
        conn.close()
        return json.dumps({"usage_by_user": by_user, "usage_by_model": by_model}, indent=2)
    except Exception as e:
        return f"Error retrieving token usage: {str(e)}"


if __name__ == "__main__":
    mcp.run()
