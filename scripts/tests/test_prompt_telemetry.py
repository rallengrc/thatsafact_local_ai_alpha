"""
test_prompt_telemetry.py — Unit and integration tests for Team Prompt Telemetry & FTS5 Analytics.

Tests:
1. Schema initialization and table creation (prompt_turns, doc_citations, prompt_fts).
2. Citation extraction for workspace paths.
3. Full synchronization across user partitions into ephemeral SQLite.
4. FTS5 BM25 search queries and snippet generation.
5. Database statistics reporting.
"""

import os
import sys
import json
import sqlite3
import tempfile
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"
TELEMETRY_DIR = SCRIPTS_DIR / "telemetry"
AUTOMATION_DIR = SCRIPTS_DIR / "automation"

for p in [str(SCRIPTS_DIR), str(TELEMETRY_DIR), str(AUTOMATION_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from sync_prompts_db import (
    get_sqlite_connection,
    init_db,
    extract_cited_docs,
    sync_all,
    get_db_stats,
    search_prompts,
    discover_user_partitions,
)
import export_memories


@pytest.fixture
def temp_db():
    """Provides a temporary SQLite database path."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    yield Path(path)
    if os.path.exists(path):
        os.remove(path)


def test_init_db(temp_db):
    conn = get_sqlite_connection(temp_db)
    init_db(conn, clear=True)

    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type IN ('table', 'view');")
    tables = [r[0] for r in cur.fetchall()]

    assert "prompt_turns" in tables
    assert "doc_citations" in tables
    assert "prompt_fts" in tables
    conn.close()


def test_extract_cited_docs():
    text = (
        "Please inspect Resources/Templates/AI-SEARCHABLE-DOC-TEMPLATE.md and "
        "update Projects/Burstable MLaaS/PLAN.md as needed."
    )
    docs = extract_cited_docs(text)
    assert "Resources/Templates/AI-SEARCHABLE-DOC-TEMPLATE.md" in docs
    assert any("PLAN.md" in d for d in docs)


def test_sync_real_memories(temp_db):
    memories_dir = REPO_ROOT / "memories"
    if not any(memories_dir.glob("*/sessions/*.md")):
        pytest.skip("no local memories (memories/ contents are gitignored)")

    res = sync_all(db_path=temp_db, memories_dir=memories_dir, clear=True)
    assert res["status"] == "success"
    assert res["turns_synced"] > 0
    assert res["users"]

    # Verify rows in DB
    stats = get_db_stats(temp_db)
    assert stats["exists"] is True
    assert stats["total_turns"] >= 100
    assert stats["users"] >= 1


def test_search_prompts_fts5(temp_db):
    memories_dir = REPO_ROOT / "memories"
    if not any(memories_dir.glob("*/sessions/*.md")):
        pytest.skip("no local memories (memories/ contents are gitignored)")

    sync_all(db_path=temp_db, memories_dir=memories_dir, clear=True)

    # Search for Tantivy
    results = search_prompts("Tantivy", db_path=temp_db, limit=5)
    assert len(results) > 0
    assert any("tantivy" in r["prompt_text"].lower() for r in results)
    assert "match_snippet" in results[0]
    assert "<b>" in results[0]["match_snippet"].lower()


def test_multi_user_isolation(temp_db, tmp_path):
    """Test that two separate user partitions sync cleanly without collisions."""
    mem_dir = tmp_path / "memories"
    u1_dir = mem_dir / "user_alpha" / "sessions"
    u2_dir = mem_dir / "user_beta" / "sessions"
    u1_dir.mkdir(parents=True)
    u2_dir.mkdir(parents=True)

    # User Alpha session
    (u1_dir / "session-alpha.md").write_text(
        "# Session Record: session-alpha\n**Session ID**: `alpha-uuid-1234`\n"
        "### Prompt 1 (`2026-10-15T10:00:00Z`)\n```text\nAlpha prompt testing Ray actors\n```\n",
        encoding="utf-8",
    )

    # User Beta session
    (u2_dir / "session-beta.md").write_text(
        "# Session Record: session-beta\n**Session ID**: `beta-uuid-5678`\n"
        "### Prompt 1 (`2026-10-15T11:00:00Z`)\n```text\nBeta prompt testing Flyte workflows\n```\n",
        encoding="utf-8",
    )

    res = sync_all(db_path=temp_db, memories_dir=mem_dir, clear=True)
    assert res["turns_synced"] == 2
    assert set(res["users"]) == {"user_alpha", "user_beta"}

    stats = get_db_stats(temp_db)
    assert stats["total_turns"] == 2
    assert stats["users"] == 2

    # Query Alpha only
    alpha_matches = search_prompts("Ray", db_path=temp_db)
    assert len(alpha_matches) == 1
    assert alpha_matches[0]["user_id"] == "user_alpha"

    # Query Beta only
    beta_matches = search_prompts("Flyte", db_path=temp_db)
    assert len(beta_matches) == 1
    assert beta_matches[0]["user_id"] == "user_beta"


@pytest.mark.parametrize(
    ("client", "peer"),
    [("github/cli", "CLI"), ("vscode-agent-host", "VS Code"), ("vscode", "VS Code"), ("", "Unknown")],
)
def test_prompt_peer_uses_client_not_model(client, peer):
    session = {"yaml": {"client_name": client, "model": "agent-host-copilotcli:test"}}
    assert export_memories.session_peer(session) == peer


def test_prompt_recovery_preserves_human_and_agent_provenance(tmp_path, monkeypatch):
    session_dir = tmp_path / "test-session"
    session_dir.mkdir()
    (session_dir / "workspace.yaml").write_text("client_name: vscode-agent-host\n", encoding="utf-8")
    events = [
        {"type": "user.message", "id": "human", "timestamp": "2026-10-18T10:00:00Z",
         "data": {"content": "Human instruction"}},
        {"type": "user.message", "id": "agent", "timestamp": "2026-10-18T10:01:00Z",
         "data": {"content": "Delegated instruction", "source": "agent-parent"}},
    ]
    (session_dir / "events.jsonl").write_text(
        "\n".join(json.dumps(event) for event in events), encoding="utf-8"
    )
    monkeypatch.setattr(export_memories, "SSSTATE", str(tmp_path))

    session, = export_memories.get_all_session_states()
    human, agent = session["prompts"]
    assert (human["peer"], human["actor"]) == ("VS Code", "Human")
    assert (agent["peer"], agent["actor"], agent["source"]) == ("VS Code", "Agent", "agent-parent")
    assert human["id"] == "human"
    assert human["source_file"] == (session_dir / "events.jsonl").as_posix()


def test_prompt_backup_retains_evicted_events_and_is_idempotent():
    old_prompt = {"id": "old", "timestamp": "2026-10-15T10:00:00Z", "content": "continue"}
    previous = {
        "sessions": [
            {"id": "cli", "nickname": "cli", "yaml": {"client_name": "github/cli"},
             "prompts": [old_prompt]},
            {"id": "evicted", "nickname": "evicted", "prompts": [
                {"id": "gone", "timestamp": "", "content": "Keep this session"}]},
        ]
    }
    live = [{
        "id": "cli", "nickname": "cli", "yaml": {"client_name": "github/cli"},
        "prompts": [
            {**old_prompt, "actor": "Human"},
            {"id": "new", "timestamp": "2026-10-18T10:00:00Z", "content": "continue", "actor": "Human"},
        ],
    }]
    sessions, turns = export_memories.merge_prompt_backups(live, {}, previous)
    assert [p["id"] for p in sessions[0]["prompts"]] == ["old", "new"]
    assert sessions[0]["peer"] == "CLI"
    assert sessions[1]["prompts"][0]["content"] == "Keep this session"
    assert sessions[1]["peer"] == "Unknown"
    saved = export_memories.build_prompt_metadata(sessions, turns)
    restored, restored_turns = export_memories.merge_prompt_backups(live, {}, saved)
    assert export_memories.build_prompt_metadata(restored, restored_turns) == saved
    without_metadata = [{**live[0], "yaml": {}}]
    restored, _ = export_memories.merge_prompt_backups(without_metadata, {}, saved)
    assert restored[0]["peer"] == "CLI"


def test_prompt_backup_preserves_rolling_memento_repetitions():
    def turn(prompt):
        return {"prompt": prompt, "model": "agent-host-copilotcli:test", "mode": "agent"}

    previous = {"interactive_turns": {
        "workspace": [turn("first"), turn("continue"), turn("continue")],
        "evicted-workspace": [turn("retained")],
    }}
    current = {"workspace": [turn("continue"), turn("continue"), turn("last")]}
    sessions, turns = export_memories.merge_prompt_backups([], current, previous)
    assert [t["prompt"] for t in turns["workspace"]] == ["first", "continue", "continue", "last"]
    assert turns["evicted-workspace"][0]["prompt"] == "retained"
    assert all(t["peer"] == "VS Code" for t in turns["workspace"])
    saved = export_memories.build_prompt_metadata(sessions, turns)
    assert export_memories.merge_prompt_backups([], current, saved) == (sessions, turns)


def test_prompt_history_labels_agents_and_preserves_embedded_fences():
    content = "Keep the whole prompt:\n```python\nprint('hello')\n```"
    sessions = [{
        "id": "cli", "nickname": "cli", "yaml": {"client_name": "github/cli"},
        "prompts": [{"id": "event", "content": content, "actor": "Agent", "source": "agent-parent"}],
    }]
    history = export_memories.build_all_prompts_history(sessions, {})
    assert "Peer: **CLI** | Actor: **Agent**" in history
    assert "Event ID: `event`" in history
    assert f"````text\n{content}\n````" in history
