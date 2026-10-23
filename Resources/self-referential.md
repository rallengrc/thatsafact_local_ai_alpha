---
title: Self-Referential — Accessing Prompt History, Token Usage & Memories
description: Guide to inspecting local VS Code session storage, token usage metrics, and persistent agent memories on macOS
keywords:
- self-referential
- session storage
- prompts
- token usage
- memories
- SQLite
- Ollama
- telemetry
category: guide
classification: 🟢🛡️ General
last_updated: '2026-10-11'
author: thatsafact
ai_search_aliases:
- self-referential guide
- how to access prompt history
- where are vscode memories stored
- read token usage
---

# self-referential — Accessing Prompt History, Token Usage & Memories from Local Metadata

> **TL;DR:** Technical guide explaining how to inspect your own prompt history, token consumption (IN/OUT), and agent memory stores from local VS Code SQLite databases and Ollama endpoints.
> **Use this for:** Auditing session history, inspecting prompt logs, tracking token metrics, and recovering conversation context.

How to read **your own prompt history**, **token usage (tokens IN / tokens OUT)**, and **agent
memories (User / Repo / Session)** from the internal metadata that VS Code and the local Ollama
server write on **macOS**.

- **Prompt history / transcript** → stored by VS Code in SQLite + JSONL files.
- **Token counts (prompt/IN vs. completion/OUT)** → **not** persisted by VS Code; they come
  from the **model layer** (Ollama API fields `prompt_eval_count` / `eval_count`).
- **Memories (User / Repo / Session)** → spread across VS Code storage; the authoritative
  source for the current session (memory **and** token usage) is `~/.copilot/session-store.db`.

> Scope: this is a "read your own machine's own data" guide. It never touches `secret://`
> values and never sends data to a cloud. Ollama is bound to `127.0.0.1` only.

---

## 1. Where VS Code stores session data (macOS)

VS Code stores underlying session data, chat prompts, and extension state under:

```
~/Library/Application Support/Code/User/
```

### 1a. SQLite metadata (`.vscdb` files)

VS Code keeps core internal state and extension config in SQLite3 databases named
`state.vscdb`.

- **Global database** — app-wide settings, UI state, global extension config:

```
~/Library/Application Support/Code/User/globalStorage/state.vscdb
```

- **Workspace-specific database** — each project folder gets a unique hex hash; its
  `state.vscdb` holds metrics/UI state for that folder:

```
~/Library/Application Support/Code/User/workspaceStorage/<workspace-hash>/state.vscdb
```

Open with any SQLite client (both files use an `ItemTable` with columns `key`, `value`):

```bash
# CLI
sqlite3 "$HOME/Library/Application Support/Code/User/globalStorage/state.vscdb" \
  "SELECT key FROM ItemTable;"

# or with python3 (read-only — VS Code may hold a write lock)
python3 -c "import sqlite3;print([r[0] for r in sqlite3.connect('file:$HOME/Library/Application Support/Code/User/globalStorage/state.vscdb?mode=ro',uri=True).execute('SELECT key FROM ItemTable')])"
```

A query such as `SELECT value FROM ItemTable WHERE key = '...'` yields the **serialized
(JSON)** value for that key. (The exact key name depends on the VS Code / extension version —
see the real keys found on this machine in §2.)

---

## 2. The keys that actually hold prompt history (verified on this machine)

Querying `ItemTable` on this machine surfaced these relevant keys.

**Global `state.vscdb`:**

| Key | Size | Holds |
|-----|------|-------|
| `chat.ChatSessionStore.index` | ~434 B | Index of every chat session: `sessionId`, `title`, `timing.created/lastRequestStarted/lastRequestEnded`, `initialLocation`, `permissionLevel`, … |
| `chat.currentLanguageModel.panel` | ~25 B | The model currently selected in the chat panel |
| `chat.cachedLanguageModels.v2` | ~35 KB | Catalog of cached language models (incl. BYOK / Ollama) |
| `chat.usageBasedBilling` | 4 B | `"true"` — whether usage-based billing is on |
| `github-<account>-usages` | ~151 B | Per-extension OAuth **scope** usage (not LLM token counts) |
| `secret://chat.lm.secret.*` | ~268 B | **Encrypted secrets — do NOT print** |

**Workspace `state.vscdb` (hash `1791588465529`):**

| Key | Size | Holds |
|-----|------|-------|
| `memento/interactive-session` | ~5.4 KB | The **transcript**: `history.copilot[]` = one entry per turn with `inputText` (the prompt), `selectedModel`, `modelConfiguration`, `mode`, `permissionLevel`, `attachments` |
| `memento/interactive-session-view-copilot` | ~1 KB | View/UI state for the interactive session |
| `chat.customModes.local` | ~9.6 KB | Custom chat mode definitions |
| `history.entries` | — | Edit/undo history entries |

Note: a generic/older key people cite is `interactive.sessions`; on this machine the real
transcript key is **`memento/interactive-session`** and the registry is
**`chat.ChatSessionStore.index`**.

### Read the transcript (prompt history) with python3

```python
import sqlite3, os, json

def item(base, key, workspace=None):
    p = (f"{base}/workspaceStorage/{workspace}/state.vscdb" if workspace
         else f"{base}/globalStorage/state.vscdb")
    c = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
    r = c.execute("SELECT value FROM ItemTable WHERE key=?", (key,)).fetchone()
    c.close()
    return json.loads(r[0]) if r else None

base = os.path.expanduser("~/Library/Application Support/Code/User")

# 1) session index -> sessionId + title + timing
idx = item(base, "chat.ChatSessionStore.index")
for sid, e in idx["entries"].items():
    print(sid, "|", e["title"], "|", e["timing"])

# 2) transcript -> each prompt (inputText) + selected model, per turn
hist = item(base, "memento/interactive-session", workspace="1791588465529")
for turn in hist["history"]["copilot"]:
    print("PROMPT:", turn["inputText"])
    print("MODEL :", turn.get("selectedModel"), turn.get("modelConfiguration"))
```

---

## 3. Prompt / chat transcripts as JSONL (on disk)

Beyond SQLite, Copilot writes the full conversation to **JSONL** files (one JSON object per
line = one message/turn). Verified locations on this machine:

```
# Empty-window / panel sessions
~/Library/Application Support/Code/User/globalStorage/emptyWindowChatSessions/<sessionId>.jsonl

# Copilot debug logs (per session)
~/Library/Application Support/Code/User/globalStorage/github.copilot-chat/debug-logs/<sessionId>/main.jsonl

# Chat-editing sessions (per workspace)
~/Library/Application Support/Code/User/workspaceStorage/<workspace-hash>/chatEditingSessions/
```

Read a transcript:

```bash
# latest session transcript, newest line first
tail -n 20 "$HOME/Library/Application Support/Code/User/globalStorage/emptyWindowChatSessions/5e6258d7-d1dd-4161-8b4c-9d9e27f1f0c4.jsonl" \
  | python3 -c "import sys,json;[print(json.loads(l).get('role','?'), json.loads(l).get('content','')) for l in sys.stdin]"
```

---

## 4. Token usage — tokens IN vs. tokens OUT

### Key finding

**VS Code's user storage does NOT persist per-request LLM token counts.** The `token` hits in
`ItemTable` are OAuth/`secret://` tokens, not prompt/completion counts. The authoritative
token counts come from the **model layer**.

For this MLaaS setup (Ollama + `qwen3.8:27b`), Ollama's HTTP API returns them on every call:

| Field | Meaning |
|-------|---------|
| `prompt_eval_count` | **tokens IN** — prompt tokens processed |
| `eval_count`        | **tokens OUT** — tokens generated |

### Verify (live) — qwen3.8:27b

```bash
curl -s http://127.0.0.1:11434/api/generate \
  -d '{"model":"qwen3.8:27b","prompt":"count to three","stream":false}' \
  | python3 -c "import sys,json;d=json.load(sys.stdin);print('tokens IN  (prompt_eval_count):',d['prompt_eval_count']);print('tokens OUT (eval_count):',d['eval_count'])"
```

Observed: `tokens IN = 13`, `tokens OUT = 37`.

### Reusable helper (captures IN/OUT for any prompt)

```python
import json, urllib.request

def ollama_tokens(model, prompt, host="http://127.0.0.1:11434"):
    req = urllib.request.Request(
        f"{host}/api/generate",
        data=json.dumps({"model": model, "prompt": prompt, "stream": False}).encode(),
        headers={"Content-Type": "application/json"},
    )
    d = json.load(urllib.request.urlopen(req))
    return {
        "tokens_in":  d["prompt_eval_count"],   # tokens INTO the LLM
        "tokens_out": d["eval_count"],          # tokens OUT of the LLM
        "total":      d["prompt_eval_count"] + d["eval_count"],
        "text":       d["response"].strip(),
    }

print(ollama_tokens("qwen3.8:27b", "Explain quantum entanglement in one sentence."))
```

> `qwen3.8:27b` runs locally via Apple's **MLX** runtime on the M5 Pro; these counts are
> produced on-device. For a **cloud** provider (e.g. Copilot), token counts are not written to
> these local files — use the provider's own usage/telemetry instead.

---

## 5. One-shot script: prompt history + token usage together

```python
import sqlite3, os, json, urllib.request

base = os.path.expanduser("~/Library/Application Support/Code/User")
def item(path, key):
    c = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    r = c.execute("SELECT value FROM ItemTable WHERE key=?", (key,)).fetchone(); c.close()
    return json.loads(r[0]) if r else None

# ---- prompt history (VS Code) ----
idx = item(f"{base}/globalStorage/state.vscdb", "chat.ChatSessionStore.index") or {"entries": {}}
print("Sessions (from chat.ChatSessionStore.index):")
for sid, e in idx["entries"].items():
    print(" -", e.get("title"), "|", sid)

# ---- token usage (Ollama) ----
req = urllib.request.Request(
    "http://127.0.0.1:11434/api/generate",
    data=json.dumps({"model": "qwen3.8:27b", "prompt": "hello", "stream": False}).encode(),
    headers={"Content-Type": "application/json"})
d = json.load(urllib.request.urlopen(req))
print(f"qwen3.8:27b -> tokens IN {d['prompt_eval_count']}, OUT {d['eval_count']}")
```

---

## 6. Memories — the three scopes (User / Repo / Session)

Copilot/VS Code separates agent "memory" into **three scopes**. Unlike the prompt transcripts
above, memory is **not** a single well-known folder — it is spread across the storage layers in
§1–§3, and the Copilot **session store** (a SQLite DB) is the authoritative source for the
current session's memory **and** its per-request token usage.

### 6a. The three scopes — what each holds and where it lives

| Scope | Concept (persists…) | Persisted as | Where (macOS) |
|-------|---------------------|--------------|---------------|
| **User** (`/memories`) | global prefs & patterns, **across workspaces** | `globalStorage/state.vscdb` keys + global `*.agent.md` + global session-store | `~/Library/Application Support/Code/User/globalStorage/` |
| **Repository** (`/memories/repo`) | project conventions & commands, **across sessions in one workspace** | `workspaceStorage/<hash>/state.vscdb` (`memento/interactive-session`, `chat.customModes.local`) + `chatEditingSessions/<sid>/state.json` + session-store `session_files` / `session_refs` | `~/Library/Application Support/Code/User/workspaceStorage/<hash>/` |
| **Session** (`/memories/session`) | **temporary** task context & plans, **this conversation only** | `.copilot/session-state/<sid>/` (`workspace.yaml`, `checkpoints/index.md`, `events.jsonl`) + `.copilot/session-store.db` (`sessions`, `turns`, `checkpoints`, `assistant_usage_events`) | `~/.copilot/` |

### 6b. The authoritative store: `~/.copilot/session-store.db` & `~/.copilot/session-state/`

The Copilot CLI session store (SQLite) and session-state directories hold the current session's memory, past sessions' full event logs, architectural checkpoints, and per-request token usage.

#### 1) The SQLite session store (`~/.copilot/session-store.db`)
Tables found on this machine:

| Table | Rows | Holds |
|-------|------|-------|
| `sessions` | 1 | `id`, `cwd`, `repository`, `host_type`, `branch`, `summary`, created/updated |
| `turns` | 13 | per-turn `user_message` / `assistant_response` — the conversation |
| `checkpoints` | 3 | handoff snapshots (`title`/`overview`/`next_steps`) when present |
| `session_files` | 6+ | files created/edited this session (`file_path`, `tool_name`, `turn_index`) |
| `session_refs` | 0 | commit/PR/issue refs when present |
| `assistant_usage_events` | 122+ | **token usage per request**: `model`, `input_tokens` (IN), `output_tokens` (OUT), `cache_read_tokens`, `cache_write_tokens`, `reasoning_tokens`, `total_nano_aiu` |

#### 2) Deep session state directory (`~/.copilot/session-state/<sessionId>/`)
Every Copilot CLI session maintains an independent session directory under `~/.copilot/session-state/<sessionId>/`:

| File / Subdir | Format | Contents & Purpose |
|---------------|--------|--------------------|
| `workspace.yaml` | YAML | Session metadata: `id`, `cwd`, `git_root`, `repository`, `branch`, `client_name`, `name` (the initial user prompt / summary), `user_id`, timestamps |
| `events.jsonl` | JSONL | Full event-sourced log of every action: `user.message` (prompts), `assistant.message` (replies, tool requests, reasoning blocks), `tool.execution_start/complete`, `session.usage_checkpoint` (token counts, AIU), and `session.start/shutdown` |
| `checkpoints/` | Markdown | Milestone snapshots (`001-*.md`, `002-*.md`, plus `index.md`). These contain `<overview>`, what was accomplished, files created, architectural context, and next steps |
| `session.db` | SQLite3 | Workflow state database (tables for runs, phases, agents, journal, and credit charges) |

#### 3) Workspace interactive session memento (`workspaceStorage/<hash>/state.vscdb`)
Under `~/Library/Application Support/Code/User/workspaceStorage/<workspace-hash>/state.vscdb`, the key `memento/interactive-session` stores the exact chronological log of all turns submitted via the VS Code chat interface:
- Each turn contains `inputText` (the exact prompt), `selectedModel` (model identifier, vendor, max tokens), `mode` (`agent`, `edit`), `permissionLevel`, and `attachments`.
- For the `mlaas` workspace (`hash: e451da945d20aecff0d4acf8398f0685`), this stores **35 complete turns** representing the entire conversation history from initial model selection to ChromaDB indexing, MCP tools setup, document conversion, and memory management.

#### 4) Discovered session catalog (verified on this machine)
The system tracks multiple interrelated sessions across the project:

1. **Session 1 (`43e35f72…`)**: Local `qwen3.8:27b` setup via Ollama, PDF-to-MD converter script, image extraction, and memory documentation (15 prompts, 3 checkpoints: `001-local-qwen3-8-setup-memory-doc.md`, `002-pdf-to-md-converter-image-extr.md`, `003-pdf-to-md-image-extraction-fix.md`).
2. **Session 2 (`6a88fed1…`)**: ChromaDB workspace indexing, ripgrep wrapper implementation, MCP search router architecture, and sequential thinking integration (21 prompts, 5 checkpoints: `001-indexing-system-phase-2-search.md` through `005-session-6a88fed1.md`).
3. **Session 3 (`60f752f2…`)**: Customization migrations, MCP startup troubleshooting, doc reorganization (4 prompts, 1 checkpoint: `001-session-60f752f2.md`).
4. **Session 4 (`2883d071…`)**: MCP startup clean, Ray/Flyte orchestration doc scan & markdown conversion, git repository inventory, and memories persistence (5 prompts).
5. **Session 5 (`bb49bce2…` - current)**: Cross-session prompt retrieval, architectural metadata extraction, and comprehensive memory export to `memories/`.
6. **Micro-sessions (`f1d8c1bb…`, `f49769c2…`)**: Prompt troubleshooting and Gemini Flash LLM model confirmation.
7. **Empty-window session (`5e6258d7…`)**: Initial Gemini API key setup and gitignore generation.

### 6c. Read a scope with python3 (read-only, `secret://` skipped)

```python
import sqlite3, os

HOME = os.path.expanduser("~")
SSDB = os.path.join(HOME, ".copilot", "session-store.db")

def ss_tables(path):
    c = sqlite3.connect(f"file:{path}?mode=ro", uri=True); c.row_factory = sqlite3.Row
    out = {}
    for (t,) in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall():
        try:
            out[t] = [dict(r) for r in c.execute(f"SELECT * FROM {t}")]
        except Exception:
            out[t] = []
    c.close(); return out

t = ss_tables(SSDB)

# Session memory: the conversation, turn by turn
for r in sorted(t.get("turns", []), key=lambda r: r["turn_index"] or 0):
    print(f"turn {r['turn_index']}: {str(r['user_message'])[:80]}")

# Token usage (tokens IN / OUT) across every request in the session
tot = dict(i=0, o=0, cr=0)
for e in t.get("assistant_usage_events", []):
    tot["i"]  += e.get("input_tokens") or 0
    tot["o"]  += e.get("output_tokens") or 0
    tot["cr"] += e.get("cache_read_tokens") or 0
print(f"TOTALS  IN={tot['i']}  OUT={tot['o']}  cache-read={tot['cr']}")
```

### 6d. Persist a local MD copy of all scopes & past session metadata

The enhanced exporter lives at **`scripts/export_memories.py`**. It extracts memories, prompts, architectural checkpoints, and session metadata from both VS Code's internal storage and Copilot CLI session-state directories.

It generates the following structured tree under `memories/`:

```
memories/
├── user-memory.md                               # /memories (User Memory - global settings, models, agents)
├── repo/
│   └── repo-memory.md                           # /memories/repo (Repository Memory - full 35-turn workspace memento)
├── session/
│   └── session-memory.md                        # /memories/session (Active session context & token usage)
└── sessions/
    ├── index.md                                 # Master session index table & cross-session overview
    ├── all-prompts-history.md                   # Verbatim chronological log of EVERY user prompt across turns
    ├── checkpoints-and-learnings.md             # All 9 architectural checkpoints & handoff summaries
    ├── sessions_metadata.json                   # Structured JSON dump for programmatic tooling
    ├── session-1-local-qwen3-8-setup-and-pdf-converter.md
    ├── session-2-chromadb-indexing-and-search-router.md
    ├── session-3-customizations-and-mcp-tools.md
    ├── session-4-mcp-cleanup-ray-docs-and-memories.md
    ├── session-5-current-metadata-and-prompt-extraction.md
    ├── session-micro-mcp-troubleshooting.md
    └── session-micro-gemini-confirmation.md
```

Run with:

```bash
.venv/bin/python3 scripts/export_memories.py
```

It opens every source **read-only**, **skips `secret://`** keys, and sanitizes free-text for
secret patterns (`sk-`, `gh*`, `xoxb-`, `AKIA`, `AIza`, PEM). `scripts/probe.py` is the
quick one-shot for prompt history + a live Ollama token probe.

### 6e. Manage memory inside VS Code (no file digging)

- **Command Palette** (`Cmd+Shift+P`) → `Chat: Show Memory Files` to inspect active memory files.
- Command Palette → `Chat: Clear All Memory Files` to wipe them.
- For **persistent project rules that live in source control** instead of VS Code's internal
  store, add a version-controlled `.github/copilot-instructions.md` (or `AGENTS.md`) to the repo.

---

## 7. Safety & caveats

- **Never print `secret://` values** (`secret://chat.lm.secret.*`, `secret://{"extensionId":...}`) —
  these are encrypted credentials.
- Open `.vscdb` **read-only** (`file:...?mode=ro`) — VS Code may hold a write/WAL lock; a live
  read is safe but avoid writes.
- The `state.vscdb` `ItemTable` values are **JSON strings** — parse them before use.
- Ollama binds to **`127.0.0.1`** by default (`lsof -nP -iTCP:11434 -sTCP:LISTEN`), so nothing
  here leaves the machine.
- Token counts for **local** models (Ollama/MLX) are exact and on-device; counts for **cloud**
  models are not stored in these local files.
- `~/.copilot/session-store.db` (the session store) is also opened **read-only**; it may hold a
  WAL lock while the CLI is running, so avoid writes.
