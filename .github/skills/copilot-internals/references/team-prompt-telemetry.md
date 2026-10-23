# Team Prompt Telemetry & Cross-User Mining Reference

**Related Skill:** `.github/skills/copilot-internals/SKILL.md`  
**Purpose:** Guide cross-team prompt analysis, conflict-free memory namespacing, and 3-day buffer eviction defense.

---

## 1. Multi-User Directory Protocol (`memories/<username>/`)

To prevent Git merge conflicts across concurrent developers (`alice`, `bob`, `carol`, `dave`), all prompt history and session memories are partitioned by developer handle:

```
memories/
├── <username>/
│   ├── sessions/
│   │   ├── all-prompts-history.md        # Verbatim chronological prompt logs
│   │   ├── session-<id>-<topic>.md       # Detailed session transcript
│   │   └── sessions_metadata.json        # Machine-readable turn & tool metrics
│   ├── repo-memory.md                    # User's repository notes & patterns
│   └── user-memory.md                    # User's model & agent configurations
```

**Export Rule:**
```bash
# Export using current OS user handle
.venv/bin/python3 scripts/automation/export_memories.py --user <your-user>
```

---

## 2. Ephemeral SQLite FTS5 Database (`prompts_analytics.db`)

The database is built on the fly from team markdown files and excluded from Git via `.gitignore`.

### Schema Summary:
- `prompt_turns`: Quantitative turn metrics (prompt text, tokens in/out, execution ms, tools used).
- `doc_citations`: Qualitative ROI tracking linking prompt turns to workspace markdown docs.
- `prompt_fts`: SQLite FTS5 virtual table indexing prompt text, response previews, and cited docs.

### Synchronization Command:
```bash
.venv/bin/python3 scripts/telemetry/sync_prompts_db.py
```

---

## 3. Core Telemetry SQL Queries

### A. Full-Text Search Across All Team Prompts (FTS5 BM25):
```sql
SELECT p.user_id, p.timestamp, p.model, p.prompt_text, snippet(prompt_fts, 2, '<b>', '</b>', '...', 15) as match_snippet
FROM prompt_fts f
JOIN prompt_turns p ON f.turn_id = p.turn_id
WHERE prompt_fts MATCH 'karpenter OR "plasma memory"'
ORDER BY rank
LIMIT 10;
```

### B. Document Effectiveness & Citation Frequency:
```sql
SELECT doc_path, count(*) as citation_count, GROUP_CONCAT(DISTINCT user_id) as used_by
FROM doc_citations
GROUP BY doc_path
ORDER BY citation_count DESC
LIMIT 10;
```

### C. Token Consumption & Cost by Model:
```sql
SELECT model, count(*) as turn_count, sum(prompt_tokens) as total_in, sum(completion_tokens) as total_out
FROM prompt_turns
GROUP BY model
ORDER BY total_in DESC;
```

---

## 4. The 3-Day History Eviction Defense Protocol

VS Code's internal memento (`state.vscdb`) and Copilot CLI session-state stores maintain rolling buffers (~40 turns) that purge prompts older than ~72 hours.

**Defense Protocol:**
1. **Periodic Sync:** Run `export_memories.py --user <username>` at the end of each working day.
2. **Git Commit:** Commit `memories/<username>/` to Git; Git history provides immutable cold storage.
3. **Reconstitution:** If a workstation is wiped or a teammate needs historical context, `sync_prompts_db.py` reconstructs the entire searchable SQLite index in <2 seconds.
