#!/usr/bin/env python3
"""
export_memories.py — Persist a local copy of the Copilot / VS Code agent "memory"
scopes as Markdown, read from your OWN machine's OWN storage.

Scopes (see ../Resources/self-referential.md and the Copilot Memory docs):
  /memories         -> User Memory      : global prefs & agent configs (cross-workspace)
  /memories/repo    -> Repository Memory: workspace-specific state & files touched
  /memories/session -> Session Memory   : current task context + per-request token usage

Output (mirrors the /memories hierarchy, rooted at $HOME):
  ~/memories/user-memory.md
  ~/memories/repo/repo-memory.md
  ~/memories/session/session-memory.md

Safety:
  * Every source is opened READ-ONLY (file:...?mode=ro).
  * 'secret://' keys (encrypted credentials) are NEVER read or printed.
  * Free-text is sanitized for common secret patterns (sk-, gh*, xoxb-, AKIA, AIza, PEM).
  * No network is used.
"""
import os
import re
import json
import sqlite3
import datetime
import argparse
import sys
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.dirname(SCRIPT_DIR)
REPO_ROOT = os.path.dirname(SCRIPTS_DIR)

if SCRIPTS_DIR not in sys.path and os.path.exists(SCRIPTS_DIR):
    sys.path.insert(0, SCRIPTS_DIR)
from common_platform import get_vscode_user_dir, get_copilot_dir, get_current_user

HOME = os.path.expanduser("~")


def classification_label(terms_file=None) -> str:
    """Private-scope label with the client name read from the private terms file, else the placeholder."""
    from client_term_scan import DEFAULT_TERMS, PLACEHOLDER, load_client_name

    path = Path(terms_file) if terms_file else Path(REPO_ROOT) / DEFAULT_TERMS
    return f"\U0001F535\U0001F6E1\uFE0F {load_client_name(path) or PLACEHOLDER} Proprietary"


VS = str(get_vscode_user_dir())
GLB = os.path.join(VS, "globalStorage", "state.vscdb")
WSG = os.path.join(VS, "workspaceStorage")
GLB_AGENT_DIR = os.path.join(VS, "globalStorage", "github.copilot-chat")
COP = str(get_copilot_dir())
SSDB = os.path.join(COP, "session-store.db")
SSSTATE = os.path.join(COP, "session-state")
CHAT_SSDB = os.path.join(VS, "globalStorage", "github.copilot-chat", "session-store.db")
DEFAULT_OUT_ROOT = os.path.join(REPO_ROOT, "memories")


def find_workspace_hash(repo_root=REPO_ROOT):
    """Return the VS Code workspaceStorage hash whose workspace.json points at repo_root, else None."""
    target = Path(repo_root).resolve()
    for meta in sorted(__import__("glob").glob(os.path.join(WSG, "*", "workspace.json"))):
        try:
            with open(meta, encoding="utf-8") as f:
                folder = json.load(f).get("folder", "")
        except (OSError, ValueError):
            continue
        if not folder.startswith("file://"):
            continue
        path = urllib.request.url2pathname(urllib.parse.urlparse(folder).path)
        try:
            if Path(path).resolve() == target:
                return os.path.basename(os.path.dirname(meta))
        except OSError:
            continue
    return None

NOW = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Known human-friendly nicknames for sessions
SESSION_NAMES = {
    "43e35f72-f62b-4f68-9177-7a5d758fe624": "session-1-local-qwen3-8-setup-and-pdf-converter",
    "6a88fed1-4b2b-4d12-808e-99695ab6357d": "session-2-chromadb-indexing-and-search-router",
    "60f752f2-3026-4701-8708-916bea2ad8ad": "session-3-customizations-and-mcp-tools",
    "2883d071-f3e3-494d-9084-120b925cab3e": "session-4-mcp-cleanup-ray-docs-and-memories",
    "bb49bce2-3c7a-4b97-b29f-f507fee10ec7": "session-5-current-metadata-and-prompt-extraction",
    "795597aa-ed97-4c2f-a637-ea5d201f70bb": "session-6-master-toc-and-scripts-reorg",
    "3abf6061-6380-408d-a3ce-116ce9ce672c": "session-7-phase6-hello-mlaas-burst-and-kind",
    "f3250c12-eb2a-4302-8be8-46f4c0ce96bd": "session-8-code-repositories-update",
    "3a0b330f-77e7-4b8d-9d7b-d8ff22945312": "session-9-telemetry-and-indices",
    "7fd69866-93c9-4950-becc-be16caef4ac3": "session-10-remote-merge-and-kuberay-docs",
    "92bc79b5-0a3b-4f65-8558-85ca40777197": "session-11-cross-platform-modernization-and-architecture-debate",
    "85b3b670-2fd7-43cb-b180-1f9e123d5893": "session-12-url-capture-and-graphify-additions",
    "20f60cd6-1bc4-4378-a5d7-0625eec5884e": "session-13-copilot-internals-and-reindex",
    "4973c7e1-4d94-4871-80c8-596e214e89a8": "session-14-backup-prompts-and-notes",
    "f1d8c1bb-c133-4538-a260-b1e4a08319f4": "session-micro-mcp-troubleshooting",
    "f49769c2-c80f-4f75-a328-ace48713acae": "session-micro-gemini-confirmation",
    "5e6258d7-d1dd-4161-8b4c-9d9e27f1f0c4": "session-vscode-emptywindow-gemini-setup",
}

# --- secret redaction -------------------------------------------------------
REDACT = [
    re.compile(r"\bsk-[A-Za-z0-9]{16,}"),
    re.compile(r"\b(ghp|gho|ghs|ghu|ghr|github_pat)_[A-Za-z0-9]{20,}"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bAIza[0-9A-Za-z\-_]{20,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
]


def redact(s):
    if not isinstance(s, str):
        return s
    for rx in REDACT:
        s = rx.sub("[REDACTED]", s)
    return s


def cap(s, n=600):
    s = redact(s if isinstance(s, str) else str(s))
    return s if len(s) <= n else s[:n] + f" …(+{len(s) - n} chars)"


def vscdb(path):
    """ItemTable -> {key: parsed-value}; 'secret://' keys are skipped (never read)."""
    out = {}
    if not os.path.exists(path):
        return out
    c = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    for k, v in c.execute("SELECT key, value FROM ItemTable"):
        if k.startswith("secret://"):
            out[k] = "<SKIPPED: encrypted secret>"
            continue
        try:
            out[k] = json.loads(v)
        except Exception:
            out[k] = v
    c.close()
    return out


def tables(path):
    """Return a dict of {table: [rows as dicts]} for the tables that exist."""
    res = {}
    if not os.path.exists(path):
        return res
    c = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    c.row_factory = sqlite3.Row
    for (t,) in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall():
        try:
            res[t] = [dict(r) for r in c.execute(f"SELECT * FROM {t}")]
        except Exception:
            res[t] = []
    c.close()
    return res


def read_jsonl(path, limit=200):
    if not os.path.exists(path):
        return []
    out = []
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f):
            if i >= limit:
                break
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                out.append({"_raw": cap(line, 300)})
    return out


def load_yaml(path):
    """Safely parse YAML file, with fallback if yaml package is missing."""
    if not os.path.exists(path):
        return {}
    try:
        import yaml
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            data = yaml.safe_load(f) or {}
            # Normalize datetime/timestamp objects to ISO strings
            for k, v in list(data.items()):
                if hasattr(v, "isoformat"):
                    data[k] = v.isoformat()
            return data
    except Exception:
        out = {}
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if ":" in line and not line.startswith(" "):
                    k, v = line.split(":", 1)
                    out[k.strip()] = v.strip()
        return out


def write(path, text):
    parent = os.path.dirname(path)
    os.makedirs(parent, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=parent, delete=False
        ) as f:
            temporary = f.name
            f.write(text)
        os.replace(temporary, path)
    finally:
        if temporary and os.path.exists(temporary):
            os.unlink(temporary)
    return len(text)


def md_escape(s):
    return redact(str(s)).replace("|", "\\|").replace("\n", " ")


def session_peer(session):
    """Identify the submitting application, not the model or storage location."""
    client = session.get("yaml", {}).get("client_name", "")
    if client == "github/cli":
        return "CLI"
    if client in {"vscode", "vscode-agent-host"}:
        return "VS Code"
    return "Unknown"


def merge_prompt_backups(sessions, interactive_turns, previous):
    """Retain archived events and rolling-buffer turns when sources disappear."""
    merged = {s["id"]: dict(s) for s in previous.get("sessions", [])}
    for session in sessions:
        old = merged.get(session["id"], {})
        prompts = {}
        for prompt in old.get("prompts", []) + session.get("prompts", []):
            key = prompt.get("id") or (prompt.get("timestamp"), prompt["content"])
            prompts[key] = {**prompts.get(key, {}), **prompt}
        combined = {**old, **session}
        combined["yaml"] = {**old.get("yaml", {}), **session.get("yaml", {})}
        combined["prompts"] = sorted(
            prompts.values(), key=lambda p: p.get("timestamp") or ""
        )
        merged[session["id"]] = combined

    for session in merged.values():
        session["peer"] = session_peer(session)
        for prompt in session.get("prompts", []):
            prompt["peer"] = session["peer"]
            prompt.setdefault("actor", "Unknown")
        session["prompts_count"] = len(session.get("prompts", []))

    interactive = {
        workspace: list(turns)
        for workspace, turns in previous.get("interactive_turns", {}).items()
    }
    for workspace, turns in interactive_turns.items():
        saved = interactive.get(workspace, [])
        # Memento has no event IDs or timestamps: match overlapping sequences,
        # not a set of texts, so repeated human prompts remain distinct.
        def identity(turn):
            return json.dumps(
                [turn.get("prompt"), turn.get("model"), turn.get("mode")],
                sort_keys=True,
            )

        old_keys = [identity(t) for t in saved]
        new_keys = [identity(t) for t in turns]
        overlap = 0
        for size in range(min(len(saved), len(turns)), 0, -1):
            if old_keys[-size:] == new_keys[:size]:
                overlap = size
                break
        interactive[workspace] = saved + turns[overlap:]
    for turns in interactive.values():
        for index, turn in enumerate(turns):
            turn.update(peer="VS Code", actor="Human", turn_index=index)
    return list(merged.values()), interactive


def build_prompt_metadata(sessions, interactive_turns):
    """Keep the existing metadata format while preserving event provenance."""
    serializable_sessions = []
    for session in sessions:
        record = {
            key: session[key]
            for key in (
                "id", "nickname", "yaml", "timing", "prompts", "usage", "peer",
                "checkpoints_count", "assistant_turns_count", "tool_calls_count",
            )
            if key in session
        }
        record["prompts_count"] = len(session.get("prompts", []))
        for key in ("checkpoints", "assistant_turns", "tool_calls"):
            record[f"{key}_count"] = (
                len(session[key]) if key in session else session.get(f"{key}_count", 0)
            )
        record["checkpoints"] = [
            {"filename": c["filename"], "title": c["title"]}
            for c in session.get("checkpoints", [])
        ]
        serializable_sessions.append(record)
    return {
        "exported_at": NOW,
        "sessions": serializable_sessions,
        "interactive_turns": interactive_turns,
    }


# --- session discovery and deep extraction ---------------------------------
def get_all_session_states():
    """Extract metadata, checkpoints, prompts, and usage across all session-state folders."""
    sessions = []
    if not os.path.exists(SSSTATE):
        return sessions

    for sdir in sorted(__import__("glob").glob(os.path.join(SSSTATE, "*"))):
        if not os.path.isdir(sdir):
            continue
        sid = os.path.basename(sdir)
        nick = SESSION_NAMES.get(sid, f"session-{sid[:8]}")
        sess = {
            "id": sid,
            "nickname": nick,
            "dir": sdir,
            "yaml": load_yaml(os.path.join(sdir, "workspace.yaml")),
            "checkpoints": [],
            "prompts": [],
            "assistant_turns": [],
            "tool_calls": [],
            "usage": {},
            "timing": {},
        }

        # Checkpoints
        for cp in sorted(__import__("glob").glob(os.path.join(sdir, "checkpoints", "*.md"))):
            fn = os.path.basename(cp)
            if fn == "index.md":
                continue
            try:
                with open(cp, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                # extract title from header or first non-empty line
                title = fn
                for line in content.splitlines():
                    if line.startswith("# "):
                        title = line[2:].strip()
                        break
                    elif line.startswith("<overview>"):
                        continue
                    elif line.strip() and not title.endswith(".md"):
                        title = line.strip()[:80]
                        break
                sess["checkpoints"].append({
                    "filename": fn,
                    "title": title,
                    "content": content,
                })
            except Exception:
                pass

        # Events.jsonl
        evpath = os.path.join(sdir, "events.jsonl")
        if os.path.exists(evpath):
            with open(evpath, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        ev = json.loads(line)
                        etype = ev.get("type")
                        ts = ev.get("timestamp")
                        if not sess["timing"].get("first_event"):
                            sess["timing"]["first_event"] = ts
                        sess["timing"]["last_event"] = ts

                        if etype == "user.message":
                            data = ev.get("data", {})
                            content = data.get("content") or data.get("message") or ev.get("content") or ""
                            source = data.get("source") or ""
                            sess["prompts"].append({
                                "id": ev.get("id"),
                                "timestamp": ts,
                                "content": redact(content),
                                "peer": session_peer(sess),
                                "actor": "Agent" if source.startswith("agent-") else "Human",
                                "source": source,
                                "source_file": Path(evpath).as_posix(),
                            })
                        elif etype == "assistant.message":
                            data = ev.get("data", {})
                            sess["assistant_turns"].append({
                                "id": ev.get("id"),
                                "timestamp": ts,
                                "model": data.get("model"),
                                "tool_count": len(data.get("toolRequests", []) or []),
                                "tools": [t.get("name") for t in (data.get("toolRequests") or []) if isinstance(t, dict)],
                                "content_preview": cap(data.get("content", ""), 200),
                            })
                        elif etype == "tool.execution_complete":
                            data = ev.get("data", {})
                            sess["tool_calls"].append({
                                "id": ev.get("id"),
                                "tool": data.get("name") or ev.get("name"),
                                "success": data.get("success", True),
                            })
                        elif etype == "session.usage_checkpoint":
                            data = ev.get("data", {})
                            sess["usage"] = {
                                "totalNanoAiu": data.get("totalNanoAiu"),
                                "totalPremiumRequests": data.get("totalPremiumRequests"),
                                "lastActiveModel": data.get("lastActiveModel"),
                            }
                    except Exception:
                        pass

        sessions.append(sess)
    return sessions


def get_workspace_interactive_turns():
    """Extract interactive session prompts across all workspaceStorage databases."""
    out = {}
    for w in sorted(__import__("glob").glob(os.path.join(WSG, "*", "state.vscdb"))):
        whash = os.path.basename(os.path.dirname(w))
        g = vscdb(w)
        hist = g.get("memento/interactive-session") or {}
        raw_turns = hist.get("history", {}).get("copilot", []) if isinstance(hist, dict) else []
        parsed = []
        for i, t in enumerate(raw_turns):
            m = t.get("selectedModel")
            m_name = (m.get("id") or m.get("identifier") or m.get("name")) if isinstance(m, dict) else str(m)
            parsed.append({
                "turn_index": i,
                "prompt": redact(t.get("inputText", "")),
                "model": m_name,
                "mode": t.get("mode"),
                "permissionLevel": t.get("permissionLevel"),
                "peer": "VS Code",
                "actor": "Human",
                "source_file": Path(w).as_posix(),
            })
        if parsed:
            out[whash] = parsed
    return out


# --- scope builders ---------------------------------------------------------
def build_user_memory():
    L = []
    L.append("# User Memory  (`/memories`)  — global, cross-workspace\n")
    L.append(f"_Generated {NOW}. Source: local VS Code global storage. Read-only, secrets skipped._\n")

    g = vscdb(GLB)
    L.append("## 1. Global chat configuration (`globalStorage/state.vscdb`)\n")
    for k in ("chat.currentLanguageModel.panel", "chat.usageBasedBilling",
              "chatModelPinned", "chatModelRecentlyUsed", "chatModelVisibility"):
        if k in g:
            L.append(f"- **{k}**: `{json.dumps(g[k]) if not isinstance(g[k], str) else g[k]}`")
    for k in sorted(g):
        if re.fullmatch(r"github-.+-usages", k):
            L.append(f"- **{k}**: `{json.dumps(g[k]) if not isinstance(g[k], str) else g[k]}`")
    # summarize the model catalog without dumping 35 KB
    if "chat.cachedLanguageModels.v2" in g:
        v = g["chat.cachedLanguageModels.v2"]
        names = []
        models = v.get("models", []) if isinstance(v, dict) else (v if isinstance(v, list) else [])
        for m in models:
            if isinstance(m, dict):
                names.append(m.get("name") or m.get("id") or m.get("identifier")
                             or m.get("displayName") or "(unnamed)")
            else:
                names.append(str(m))
        names = [n for n in names if n]
        L.append(f"- **chat.cachedLanguageModels.v2**: {len(v.get('models', [])) if isinstance(v, dict) else '?'} "
                 f"cached models; e.g. {', '.join(names[:12]) or '(none named)'}")

    L.append("\n## 2. Chat session index (`chat.ChatSessionStore.index`)\n")
    idx = g.get("chat.ChatSessionStore.index") or {"entries": {}}
    L.append("| Session ID | Title | Created | Last request |")
    L.append("|---|---|---|---|")
    for sid, e in idx.get("entries", {}).items():
        t = e.get("timing", {})
        L.append(f"| `{sid}` | {md_escape(e.get('title','(untitled)'))} | {t.get('created','')} | {t.get('lastRequestEnded','')} |")
    if not idx.get("entries"):
        L.append("| _none_ | | | |")

    L.append("\n## 3. Agent definitions (global `*.agent.md`)\n")
    for agent_md in sorted(__import__("glob").glob(os.path.join(GLB_AGENT_DIR, "*-agent", "*.agent.md"))):
        rel = os.path.relpath(agent_md, GLB_AGENT_DIR)
        L.append(f"### {rel}\n```\n{cap(open(agent_md, encoding='utf-8', errors='replace').read(), 2000)}\n```\n")

    L.append("\n## 4. Copilot sessions registry (`github.copilot-chat/session-store.db`)\n")
    ss = tables(CHAT_SSDB).get("sessions", [])
    if ss:
        L.append("| id | cwd | repository | branch | agent | created | summary |")
        L.append("|---|---|---|---|---|---|---|")
        for r in ss:
            L.append(f"| `{r.get('id')}` | {md_escape(r.get('cwd'))} | {md_escape(r.get('repository'))} | "
                     f"{md_escape(r.get('branch'))} | {md_escape(r.get('agent_name'))} | "
                     f"{r.get('created_at')} | {md_escape(r.get('summary'))[:60]} |")
    else:
        L.append("_no sessions row_")
    L.append("\n> `secret://` credential keys are intentionally not listed.")
    return "\n".join(L)


def build_sessions_index(sessions, interactive_turns):
    """Builds memories/sessions/index.md: Master catalog of all chat sessions, IDs, dates, prompt counts, checkpoints, tokens, and topics."""
    L = []
    L.append("# Chat Sessions Index (`/memories/sessions`)\n")
    L.append(f"_Generated {NOW}. Discovered from `~/.copilot/session-state/`, `state.vscdb`, and session stores._\n")
    L.append("> This directory contains the complete extracted prompt history, architectural checkpoints, and context metadata across all sessions.\n")

    L.append("## 1. Master Session Catalog\n")
    L.append("| # | Nickname / Role | Session ID | CWD / Scope | Prompts | Checkpoints | Created / Updated | Summary |")
    L.append("|---|---|---|---|---|---|---|---|")

    total_prompts = 0
    total_checkpoints = 0

    for idx, s in enumerate(sessions, 1):
        sid = s["id"]
        nick = s["nickname"]
        meta = s.get("yaml", {})
        cwd = meta.get("cwd") or "(unknown)"
        cwd_short = os.path.basename(cwd) if cwd != "/" else "/"
        name = md_escape(meta.get("name") or "(untitled)")[:70]
        p_cnt = len(s["prompts"])
        cp_cnt = len(s["checkpoints"])
        total_prompts += p_cnt
        total_checkpoints += cp_cnt
        t_start = s["timing"].get("first_event") or meta.get("created_at") or "-"
        t_end = s["timing"].get("last_event") or meta.get("updated_at") or "-"
        if t_start and len(t_start) >= 19:
            t_start = t_start[:19]
        if t_end and len(t_end) >= 19:
            t_end = t_end[:19]
        t_str = f"{t_start} → {t_end}"

        L.append(f"| {idx} | [{nick}](./{nick}.md) | `{sid[:8]}…` | `{cwd_short}` | {p_cnt} | {cp_cnt} | {t_str} | {name} |")

    # Also count interactive turns
    mlaas_turns = interactive_turns.get(find_workspace_hash(), [])

    L.append(f"\n**Totals:** {len(sessions)} session-state stores ({total_prompts} prompts, {total_checkpoints} checkpoints) · "
             f"{len(mlaas_turns)} interactive turns recorded in VS Code workspace memento.\n")

    L.append("## 2. Navigating Session Memories\n")
    L.append("- [**All Prompts History**](./all-prompts-history.md): Full verbatim chronological transcript of every prompt submitted by the user across all chat panel turns and CLI sessions.\n"
             "- [**Checkpoints & Learnings**](./checkpoints-and-learnings.md): All 9 architectural checkpoints and handoff summaries documenting decisions, context, and lessons learned.\n"
             "- [**Sessions Metadata (JSON)**](./sessions_metadata.json): Complete machine-readable structured JSON dump of all sessions, prompts, tools, and token metrics.\n")

    L.append("## 3. High-Level Session Descriptions\n")
    for idx, s in enumerate(sessions, 1):
        meta = s.get("yaml", {})
        nick = s["nickname"]
        L.append(f"### {idx}. {nick}\n")
        L.append(f"- **Session ID**: `{s['id']}`\n"
                 f"- **Working Directory**: `{meta.get('cwd')}`\n"
                 f"- **Git Repository**: `{meta.get('repository')}` (branch: `{meta.get('branch')}`)\n"
                 f"- **Client**: `{meta.get('client_name')}`\n"
                 f"- **Summary / Initial Intent**: {meta.get('name')}\n"
                 f"- **User Prompts Count**: {len(s['prompts'])}\n"
                 f"- **Checkpoints Available**: {len(s['checkpoints'])}\n")
        if s["checkpoints"]:
            L.append("  **Checkpoints in this session:**\n")
            for cp in s["checkpoints"]:
                L.append(f"  - `{cp['filename']}`: {cp['title']}\n")
        if s["usage"]:
            u = s["usage"]
            L.append(f"- **Usage / Token AIU**: {u.get('totalNanoAiu', 0)} nanoAIU (~{round(u.get('totalNanoAiu', 0)/1e9, 2)} AIU), "
                     f"{u.get('totalPremiumRequests', 0)} premium requests\n")

    return "\n".join(L)


def build_all_prompts_history(sessions, interactive_turns):
    """Render preserved prompts with explicit application and author provenance."""
    L = []
    L.append(
        "---\ntitle: All Prompts History\n"
        "description: Human prompts and agent messages with CLI and VS Code provenance\n"
        "keywords: [prompts, backup, CLI, VS Code, provenance, session history]\n"
        "category: memory\n"
        f"last_updated: '{NOW[:10]}'\n"
        "author: GitHub Copilot CLI\n"
        "related: [index.md, sessions_metadata.json]\n"
        f"classification: '{classification_label()}'\n---\n"
    )
    L.append("# 📌 All Prompts History\n")
    L.append(f"_Generated {NOW}. Sourced from VS Code `memento/interactive-session` and `~/.copilot/session-state/*/events.jsonl`._\n")
    L.append("> Local prompt backup with source provenance. **Status:** Active\n")
    L.append(
        "## 🎯 TL;DR\n\n"
        "- **Peer** identifies the submitting app: `CLI`, `VS Code`, or `Unknown`.\n"
        "- **Actor** separates human prompts from agent-origin messages; unknown evidence stays unknown.\n"
        "- Previous exports are retained when live session files or rolling-buffer turns disappear.\n\n"
        "**Use this for:** Prompt recall and recovery, not inferring origin from the model name.\n\n"
        "**Refresh:** `.venv/bin/python3 scripts/automation/export_memories.py --user <username> --prompts-only`.\n"
        "Exports run on demand; this does not install hooks or a background scheduler. "
        "Memento has no timestamps/event IDs, so non-overlapping snapshots may contain duplicate turns. "
        "Session-state and memento entries may also represent the same submission; do not sum them as unique human prompts.\n"
    )

    L.append("## 1. VS Code Interactive Chat History\n")
    for workspace, turns in interactive_turns.items():
        L.append(f"### Workspace `{workspace}` ({len(turns)} retained turns)\n")
        L.append(f"> Source: `workspaceStorage/{workspace}/state.vscdb` (`memento/interactive-session`; timestamps unavailable).\n")

        for t in turns:
            i = t["turn_index"]
            m = t["model"]
            mode = t.get("mode") or "agent"
            prompt = t["prompt"]
            L.append(f"#### Turn {i} (Peer: **VS Code** | Actor: **Human** | Model: `{m}` | Mode: `{mode}`)\n")
            fence = "`" * max(3, max((len(run) for run in re.findall(r"`+", prompt)), default=0) + 1)
            L.append(f"{fence}text\n{redact(prompt)}\n{fence}\n")

    L.append("\n## 2. Session-State Prompts by Session\n")
    L.append("> Sourced from `~/.copilot/session-state/<sessionId>/events.jsonl` (`user.message` events).\n")

    for s in sessions:
        nick = s["nickname"]
        sid = s["id"]
        prompts = s["prompts"]
        peer = session_peer(s)
        client = s.get("yaml", {}).get("client_name") or "Unknown"
        L.append(f"\n### Session: {nick} (`{sid}`)\n")
        L.append(f"- **Peer**: {peer} · **Client**: `{client}`\n")
        L.append(f"- **Recorded message count**: {len(prompts)}\n")
        if not prompts:
            L.append("_No user.message events recorded in this session folder._\n")
            continue
        for idx, p in enumerate(prompts, 1):
            ts = p.get("timestamp") or ""
            actor = p.get("actor", "Unknown")
            L.append(f"#### Prompt {idx} (`{ts}` | Peer: **{peer}** | Actor: **{actor}**)\n")
            L.append(f"Event ID: `{p.get('id') or 'Unavailable'}` · Source: `{p.get('source_file') or 'Archived session-state export'}`\n")
            if p.get("source"):
                L.append(f"Origin: `{md_escape(p['source'])}`\n")
            prompt = redact(p["content"])
            fence = "`" * max(3, max((len(run) for run in re.findall(r"`+", prompt)), default=0) + 1)
            L.append(f"{fence}text\n{prompt}\n{fence}\n")

    return "\n".join(L)


def build_checkpoints_and_learnings(sessions):
    """Builds memories/sessions/checkpoints-and-learnings.md: Consolidated architecture handoffs & context."""
    L = []
    L.append("# Checkpoints & Learnings (`/memories/sessions/checkpoints-and-learnings.md`)\n")
    L.append(f"_Generated {NOW}. Consolidated from all `~/.copilot/session-state/*/checkpoints/*.md`._\n")
    L.append("> Checkpoints represent persistent context handoffs created at milestone boundaries, summarizing architectural decisions, accomplishments, lessons learned, and next steps.\n")

    all_cps = []
    for s in sessions:
        for cp in s["checkpoints"]:
            all_cps.append((s, cp))

    L.append(f"## Master Checkpoint Index ({len(all_cps)} checkpoints total)\n")
    L.append("| # | Session | File | Title |")
    L.append("|---|---|---|---|")
    for i, (s, cp) in enumerate(all_cps, 1):
        L.append(f"| {i} | [{s['nickname']}](./{s['nickname']}.md) | `{cp['filename']}` | {cp['title']} |")

    L.append("\n---\n")

    for i, (s, cp) in enumerate(all_cps, 1):
        L.append(f"\n## Checkpoint {i}: {cp['title']}\n")
        L.append(f"- **Originating Session**: `{s['nickname']}` (`{s['id']}`)\n"
                 f"- **Checkpoint File**: `{cp['filename']}`\n")
        L.append("### Content\n")
        L.append(cp["content"])
        L.append("\n---\n")

    return "\n".join(L)


def build_individual_session_doc(s):
    """Builds a dedicated markdown file for a single session."""
    sid = s["id"]
    nick = s["nickname"]
    meta = s.get("yaml", {})

    L = []
    L.append(f"# Session Record: {nick}\n")
    L.append(f"- **Session ID**: `{sid}`\n"
             f"- **Working Directory**: `{meta.get('cwd')}`\n"
             f"- **Git Repository**: `{meta.get('repository')}` (branch: `{meta.get('branch')}`)\n"
             f"- **Client Name**: `{meta.get('client_name')}`\n"
             f"- **User Intent / Initial Summary**: {meta.get('name')}\n"
             f"- **Timestamps**: {s['timing'].get('first_event', '-')} → {s['timing'].get('last_event', '-')}\n")

    if s["usage"]:
        u = s["usage"]
        L.append(f"- **Token Usage**: {u.get('totalNanoAiu', 0)} nanoAIU, {u.get('totalPremiumRequests', 0)} premium requests\n")

    L.append(f"\n## 1. User Prompts ({len(s['prompts'])})\n")
    if not s["prompts"]:
        L.append("_(No user prompts recorded in events.jsonl)_\n")
    for idx, p in enumerate(s["prompts"], 1):
        L.append(f"### Prompt {idx} (`{p.get('timestamp')}`)\n```text\n{p['content']}\n```\n")

    L.append(f"\n## 2. Checkpoints & Architectural Handoffs ({len(s['checkpoints'])})\n")
    if not s["checkpoints"]:
        L.append("_(No checkpoints generated in this session)_\n")
    for cp in s["checkpoints"]:
        L.append(f"### `{cp['filename']}`: {cp['title']}\n")
        L.append(cp["content"])
        L.append("\n")

    L.append(f"\n## 3. Assistant Interactions & Tool Calls Summary\n")
    L.append(f"- Total Assistant Messages: {len(s['assistant_turns'])}\n")
    L.append(f"- Total Completed Tool Calls: {len(s['tool_calls'])}\n")
    if s["tool_calls"]:
        tool_counts = {}
        for tc in s["tool_calls"]:
            tname = tc["tool"] or "unknown"
            tool_counts[tname] = tool_counts.get(tname, 0) + 1
        L.append("- Tool Usage Breakdown:\n")
        for tname, cnt in sorted(tool_counts.items(), key=lambda x: x[1], reverse=True):
            L.append(f"  * `{tname}`: {cnt} call(s)\n")

    return "\n".join(L)


def build_repo_memory():
    L = []
    L.append("# Repository Memory  (`/memories/repo`)  — workspace-specific\n")
    L.append(f"_Generated {NOW}. Sources: local workspaceStorage + Copilot session store._\n")
    L.append("> For full cross-session prompt histories and architectural checkpoints, see [sessions/index.md](./sessions/index.md).\n")

    L.append("## 1. Workspaces found in `workspaceStorage/`\n")
    hashes = sorted(d for d in __import__("glob").glob(os.path.join(WSG, "*"))
                   if os.path.exists(os.path.join(d, "state.vscdb")))
    if not hashes:
        L.append("_No `workspaceStorage/<hash>/state.vscdb` found._\n")
    for whash in hashes:
        base = os.path.basename(whash)
        L.append(f"### Workspace hash `{base}`\n")
        g = vscdb(os.path.join(whash, "state.vscdb"))

        # transcript turns
        hist = g.get("memento/interactive-session") or {}
        turns = (hist.get("history", {}).get("copilot", [])) if isinstance(hist, dict) else []
        L.append(f"#### Prompt history (`memento/interactive-session`) — {len(turns)} turn(s)\n")
        for i, tr in enumerate(turns):
            m = tr.get("selectedModel")
            m_name = (m.get("id") or m.get("identifier") or m.get("name")) if isinstance(m, dict) else str(m)
            L.append(f"- **turn {i}** (Model: `{m_name}` | Mode: `{tr.get('mode')}`):\n"
                     f"  ```text\n  {cap(tr.get('inputText','(empty)'), 500)}\n  ```")

        # custom modes
        cm = g.get("chat.customModes.local")
        if cm:
            try:
                modes = cm.get("modes", cm) if isinstance(cm, dict) else cm
                L.append(f"\n#### Custom chat modes — {len(modes) if isinstance(modes,(list,dict)) else '?'}")
                for m in (modes if isinstance(modes, list) else modes.values()):
                    if isinstance(m, dict):
                        L.append(f"- **{m.get('name')}**: {md_escape(m.get('description',''))[:100]}")
            except Exception:
                L.append("\n- custom modes: <unparsed>")

        # chat-editing checkpoints
        for st in __import__("glob").glob(os.path.join(whash, "chatEditingSessions", "*", "state.json")):
            try:
                d = json.load(open(st, encoding="utf-8", errors="replace"))
                tl = d.get("timeline", {}).get("checkpoints", [])
                L.append(f"\n#### Chat-editing checkpoints (`{os.path.relpath(st, whash)}`) — {len(tl)}\n")
                for cp in tl:
                    L.append(f"- epoch {cp.get('epoch')}: {md_escape(cp.get('label'))}")
            except Exception:
                pass

    # files touched + refs (from copilot session store) — always listed, not per-workspace
    ss = tables(SSDB)
    files = ss.get("session_files", [])
    refs = ss.get("session_refs", [])
    if files:
        L.append("\n### Files touched (`session_files`)\n")
        for r in files:
            L.append(f"- `{r.get('file_path')}` via {r.get('tool_name')} "
                     f"(first seen {r.get('first_seen_at')}, turn {r.get('turn_index')})")
    if refs:
        L.append("\n### References (`session_refs`)\n")
        for r in refs:
            L.append(f"- {r.get('ref_type')}: `{md_escape(r.get('ref_value'))}` "
                     f"(turn {r.get('turn_index')})")
    if not files and not refs:
        L.append("\n### Files touched / references\n_(none recorded in the Copilot session store)_")

    whash = find_workspace_hash()
    if whash:
        L.append(f"\n> Note: Workspace `{whash}` corresponds to this repository.")
    return "\n".join(L)


def build_session_memory():
    L = []
    L.append("# Session Memory  (`/memories/session`)  — current task context + token usage\n")
    L.append(f"_Generated {NOW}. Scope: task context + per-request tokens (IN/OUT)._")
    L.append("\n> Session memory is **temporary / task-scoped** — it describes active "
             "conversations and context. For full session logs, see [../sessions/index.md](../sessions/index.md).\n")

    L.append("## 1. Active Sessions in `.copilot/session-state/`\n")
    for sd in sorted(__import__("glob").glob(os.path.join(SSSTATE, "*"))):
        if not os.path.isdir(sd):
            continue
        sid = os.path.basename(sd)
        nick = SESSION_NAMES.get(sid, f"session-{sid[:8]}")
        L.append(f"### `{sid}` — [{nick}](../sessions/{nick}.md)\n")
        wpath = os.path.join(sd, "workspace.yaml")
        if os.path.exists(wpath):
            L.append("#### workspace.yaml\n```yaml\n" +
                     cap(open(wpath, encoding="utf-8", errors="replace").read(), 1500) + "\n```\n")
        idx = os.path.join(sd, "checkpoints", "index.md")
        if os.path.exists(idx):
            L.append("#### checkpoints/index.md\n```markdown\n" +
                     cap(open(idx, encoding="utf-8", errors="replace").read(), 1500) + "\n```\n")
        ev = os.path.join(sd, "events.jsonl")
        if os.path.exists(ev):
            evs = read_jsonl(ev, limit=10)
            L.append(f"#### recent events.jsonl ({len(evs)} shown)\n")
            for e in evs:
                L.append(f"- `{e.get('type', e.get('_raw','?'))}` {md_escape(json.dumps(e.get('detail', {})))[:120]}")

    L.append("\n## 2. Conversation turns (Copilot session store)\n")
    ss = tables(SSDB)
    sess = ss.get("sessions", [])
    for s in sess:
        L.append(f"### session `{s.get('id')}` — {md_escape(s.get('summary'))[:120]}\n")
        L.append(f"- cwd: `{s.get('cwd')}` · host: {s.get('host_type')} · "
                 f"created {s.get('created_at')} · updated {s.get('updated_at')}")
    turns = sorted(ss.get("turns", []), key=lambda r: r.get("turn_index") or 0)
    L.append("\n#### Turn transcript\n")
    for t in turns:
        L.append(f"**turn {t.get('turn_index')}** — user: {cap(t.get('user_message'))}\n"
                 f"  assistant: {cap(t.get('assistant_response'), 400)}")

    L.append("\n## 3. Token usage — tokens INTO and OUT of the LLM\n")
    evs = ss.get("assistant_usage_events", [])
    if evs:
        L.append("Per request (most recent 20):\n")
        L.append("| turn | model | tokens IN | tokens OUT | cache read | cache write | reasoning |")
        L.append("|---|---|---|---|---|---|---|")
        tot = dict(inp=0, out=0, cr=0, cw=0, rs=0)
        for e in sorted(evs, key=lambda r: r.get("id") or 0, reverse=True)[:20]:
            L.append(f"| {e.get('turn_index')} | {md_escape(e.get('model'))} | "
                     f"{e.get('input_tokens')} | {e.get('output_tokens')} | "
                     f"{e.get('cache_read_tokens')} | {e.get('cache_write_tokens')} | "
                     f"{e.get('reasoning_tokens')} |")
        for e in evs:
            tot["inp"] += e.get("input_tokens") or 0
            tot["out"] += e.get("output_tokens") or 0
            tot["cr"] += e.get("cache_read_tokens") or 0
            tot["cw"] += e.get("cache_write_tokens") or 0
            tot["rs"] += e.get("reasoning_tokens") or 0
        L.append(f"\n**Totals across {len(evs)} requests** — IN **{tot['inp']}** · OUT **{tot['out']}** · "
                 f"cache-read {tot['cr']} · cache-write {tot['cw']} · reasoning {tot['rs']}")
        L.append("\n> `input_tokens` = tokens **into** the LLM; `output_tokens` = tokens **out** of it.")
    else:
        L.append("_No `assistant_usage_events` rows found._")

    cps = ss.get("checkpoints", [])
    if cps:
        L.append("\n## 4. Checkpoints in session-store.db\n")
        for c in sorted(cps, key=lambda r: r.get("checkpoint_number") or 0):
            L.append(f"- **#{c.get('checkpoint_number')}** {md_escape(c.get('title'))}: "
                     f"{md_escape(c.get('overview'))[:120]}")
    return "\n".join(L)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export Copilot agent memories to markdown.")
    parser.add_argument(
        "--user",
        "-u",
        default=None,
        help="Developer username namespace (default: the current OS user)",
    )
    parser.add_argument(
        "--out",
        "-o",
        default=None,
        help="Explicit target directory to write memories (overrides --user)",
    )
    parser.add_argument(
        "--prompts-only",
        action="store_true",
        help="Update only the additive prompt history and its JSON metadata",
    )
    args = parser.parse_args()

    user = args.user
    if not user:
        user = get_current_user()

    if args.out:
        out_root = os.path.abspath(args.out)
    else:
        out_root = os.path.join(REPO_ROOT, "memories", user)

    print(f"Exporting memory scopes for user '{user}' to {out_root}  (secrets skipped, read-only)\n")

    # 1. Discover sessions and interactive turns
    all_sessions = get_all_session_states()
    interactive_turns = get_workspace_interactive_turns()
    json_path = os.path.join(out_root, "sessions", "sessions_metadata.json")
    history_path = os.path.join(out_root, "sessions", "all-prompts-history.md")
    previous = {}
    if os.path.exists(json_path):
        with open(json_path, encoding="utf-8") as f:
            previous = json.load(f)
    elif os.path.exists(history_path):
        raise FileNotFoundError(
            f"Restore {json_path} before exporting: existing prompt history "
            "must not be overwritten without its structured backup."
        )
    prompt_sessions, interactive_turns = merge_prompt_backups(
        all_sessions, interactive_turns, previous
    )
    write(json_path, json.dumps(
        build_prompt_metadata(prompt_sessions, interactive_turns),
        indent=2, ensure_ascii=False, default=str,
    ) + "\n")

    if args.prompts_only:
        history = build_all_prompts_history(prompt_sessions, interactive_turns) + "\n"
        write(history_path, history)
        print(f"  Prompt history -> {history_path}")
        print(f"  Prompt metadata -> {json_path}")
        sys.exit(0)

    targets = [
        (os.path.join(out_root, "user-memory.md"), build_user_memory, "/memories"),
        (os.path.join(out_root, "repo", "repo-memory.md"), build_repo_memory, "/memories/repo"),
        (os.path.join(out_root, "session", "session-memory.md"), build_session_memory, "/memories/session"),
        (os.path.join(out_root, "sessions", "index.md"), lambda: build_sessions_index(all_sessions, interactive_turns), "/memories/sessions"),
        (os.path.join(out_root, "sessions", "all-prompts-history.md"), lambda: build_all_prompts_history(prompt_sessions, interactive_turns), "/memories/sessions/all-prompts-history.md"),
        (os.path.join(out_root, "sessions", "checkpoints-and-learnings.md"), lambda: build_checkpoints_and_learnings(all_sessions), "/memories/sessions/checkpoints-and-learnings.md"),
    ]

    # Add each individual session file
    for s in all_sessions:
        nick = s["nickname"]
        doc_path = os.path.join(out_root, "sessions", f"{nick}.md")
        targets.append((doc_path, (lambda s_obj=s: build_individual_session_doc(s_obj)), f"/memories/sessions/{nick}.md"))

    for path, builder, scope in targets:
        try:
            n = write(path, builder() + "\n")
            print(f"  {scope:35} -> {path}  ({n} bytes)")
        except Exception as e:
            print(f"  {scope:35} -> FAILED: {e}")

    print(f"  {'/memories/sessions/sessions_metadata.json':35} -> {json_path}  ({os.path.getsize(json_path)} bytes)")

    print("\nDone.")
