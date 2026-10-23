---
name: copilot-internals
description: 'Access AI session storage (session-store.db, transcripts, debug logs, telemetry). USE FOR: prompt recovery, session mining, backfill, team prompt analytics, doc attribution. TRIGGERS: "copilot internals", "session mining", "prompt recovery", "backfill", "search history", "debug logs", "team prompts".'
---

# Copilot Internals — Self-Referential Data Access

**Deep reference:** `Resources/self-referential.md` (full schemas, code samples)
**DR Recovery Pattern:** `references/dr-recovery.md` (reconstructing session logs from git commits)
**Team Prompt Telemetry:** `references/team-prompt-telemetry.md` (FTS5 search, namespacing, eviction defense)

## Decision Tree

| Goal | Method | Key / Target |
|------|--------|--------------|
| **Query cross-session turns** | SQLite `session-store.db` via `session_store_sql` (VS Code) or `sql` (CLI) | `SELECT turn_index, user_message, assistant_response FROM turns WHERE session_id = '<UUID>'` |
| **Search session history** | SQLite `session-store.db` FTS5 index | `SELECT * FROM search_index WHERE content MATCH '<query>'` |
| **Search cross-team prompts** | SQLite `prompts_analytics.db` FTS5 index via MCP or python | `SELECT * FROM prompt_fts WHERE prompt_fts MATCH '<query>'` |
| **Audit doc effectiveness** | Query `doc_citations` table in `prompts_analytics.db` | `SELECT doc_path, count(*) FROM doc_citations GROUP BY doc_path ORDER BY 2 DESC` |
| **Recover lost prompts** | 1. `session-store.db` (turns table) → 2. JSONL `<userRequest>` → 3. transcripts `data.content` | Exact SQL or `re.findall(r'<userRequest>([\s\S]*?)</userRequest>', content)` |
| **Audit touched files** | SQLite `session-store.db` → `session_files` table | `SELECT file_path, tool_name, turn_index FROM session_files WHERE session_id = '<UUID>'` |
| **Browse legacy prompt buffer** | SQLite `state.vscdb` → `memento/interactive-session` | Rolling buffer ~40 prompts (no timestamps) |
| **Audit edit operations** | `chatEditingSessions/{UUID}/state.json` → `timeline.operations` | `create` / `textEdit` types |
| **Backfill stale entries** | Use `/backfill-session-log` or `cob-xref` protocol | Maps prompt→Actions/Result/Nav |
| **Export namespaced memory** | Run `export_memories.py --user <username>` | Prevents git merge conflicts in `memories/<user>/` |
| **Defend 3-day roll-off** | Sync to git before circular buffer evicts turns | See `references/team-prompt-telemetry.md` |

## Key Paths

### Global Storage (Cross-Session, Multi-Peer SQLite)
```
macOS:   ~/Library/Application Support/Code/User/globalStorage/github.copilot-chat/
Windows: %APPDATA%\Code\User\globalStorage\github.copilot-chat\
CLI/All: ~/.copilot/
```

| Store | Subpath | Format & Purpose |
|-------|---------|------------------|
| **Session Store (SQLite)** | `session-store.db` | **Primary telemetry lake.** 85+ sessions, 1300+ turns. Tables: `sessions`, `turns`, `checkpoints`, `session_files`, `session_refs`, and FTS5 `search_index`. Queryable via `session_store_sql` (VS Code) or `sql` (CLI). |

### Workspace Storage (Workspace-Scoped Files)
```
macOS:   ~/Library/Application Support/Code/User/workspaceStorage/{WORKSPACE_HASH}/
Windows: %APPDATA%\Code\User\workspaceStorage\{WORKSPACE_HASH}\
```

| Store | Subpath | Format & Purpose |
|-------|---------|------------------|
| JSONL sessions | `chatSessions/{UUID}.jsonl` | Append-log: `kind=1` result entries for API token metadata (`promptTokens`, `outputTokens`); `<userRequest>` tags for full prompt |
| JSONL transcripts | `GitHub.copilot-chat/transcripts/{UUID}.jsonl` | Stream format: `data.content` in `type:"user.message"`, ISO UTC timestamps |
| State SQLite | `state.vscdb` | VS Code Memento KV store (`ItemTable`: `memento/interactive-session`, `chat.ChatSessionStore.index`, `mcpToolCache`) |
| Local Keyword Index | `GitHub.copilot-chat/local-index.1.db` | SQLite BM25/keyword search index (`Documents`, `Chunks`, `ChunkOccurrences`) |
| Semantic Chunks | `GitHub.copilot-chat/workspace-chunks.db` | SQLite vector embedding index (`Files`, `FileChunks` with binary embeddings) |
| Codebase External | `GitHub.copilot-chat/codebase-external.sqlite` | External symbol/repo tracking (`Files`, `Metadata`) |
| File ops | `chatEditingSessions/{UUID}/state.json` | Timeline of create/edit operations |
| Debug logs | `GitHub.copilot-chat/debug-logs/{UUID}/main.jsonl` | Tool calls, errors, runtime timings |
| Model limits | `GitHub.copilot-chat/debug-logs/{UUID}/models.json` | Model parameters (`max_prompt_tokens=167997`, tokenizer) |

**Template vars:** `{{VSCODE_TARGET_SESSION_LOG}}` = debug log path for current session (UUID is the last path segment).

## Primary SQLite Store: `session-store.db` Schema

```sql
-- Core tables: sessions, turns, session_files, search_index (FTS5)
CREATE TABLE sessions (id TEXT PRIMARY KEY, cwd TEXT, repository TEXT, branch TEXT, summary TEXT, created_at TEXT);
CREATE TABLE turns (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT NOT NULL REFERENCES sessions(id), turn_index INTEGER NOT NULL, user_message TEXT, assistant_response TEXT, timestamp TEXT);
CREATE TABLE session_files (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT NOT NULL REFERENCES sessions(id), file_path TEXT NOT NULL, tool_name TEXT, turn_index INTEGER);
CREATE VIRTUAL TABLE search_index USING fts5(content, session_id UNINDEXED);
```

## JSONL `kind` Values & Gotchas

- **`kind` Values:** 0 = Init, 1 = State update (promptTokens/outputTokens), 2 = Request (`<userRequest>`).
- **Single-statement:** Queries to `session_store_sql` cannot combine statements with semicolons.
- **Store preference:** `session-store.db` (complete ISO 8601 timestamps, full history) >> `state.vscdb` (40 rolling prompts).
- **Paths & Scopes:** Use `session_store_sql` or terminal `rg` for storage paths outside workspace root.
