#!/usr/bin/env python3
"""
probe.py — Quick probe of local prompt history + live Ollama token usage.

Two read-only looks at your own machine:
  1. VS Code global chat session index  -> prompt history
  2. Local Ollama /api/generate          -> tokens IN (prompt_eval_count) / OUT (eval_count)

No network beyond localhost. No secrets printed.
"""
import os
import sys
import json
import sqlite3
import urllib.request

SCRIPTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SCRIPTS_DIR not in sys.path and os.path.exists(SCRIPTS_DIR):
    sys.path.insert(0, SCRIPTS_DIR)
from common_platform import get_vscode_user_dir

VS = str(get_vscode_user_dir())
GLOBAL_VSCDB = os.path.join(VS, "globalStorage", "state.vscdb")


def item(path, key):
    c = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    row = c.execute("SELECT value FROM ItemTable WHERE key=?", (key,)).fetchone()
    c.close()
    return json.loads(row[0]) if row and row[0] else None


def print_session_index():
    idx = item(GLOBAL_VSCDB, "chat.ChatSessionStore.index") or {"entries": {}}
    print("== VS Code chat sessions (prompt history index) ==")
    for sid, e in idx.get("entries", {}).items():
        t = e.get("timing", {})
        print(f" - {str(e.get('title', '(untitled)'))[:60]:62} {sid}")
        print(f"     created={t.get('created')} last_request={t.get('lastRequestEnded')}")
    if not idx.get("entries"):
        print(" (no sessions indexed)")


def ollama_tokens(model, prompt, host="http://127.0.0.1:11434"):
    req = urllib.request.Request(
        f"{host}/api/generate",
        data=json.dumps({"model": model, "prompt": prompt, "stream": False}).encode(),
        headers={"Content-Type": "application/json"},
    )
    d = json.load(urllib.request.urlopen(req, timeout=120))
    return {
        "tokens_in": d["prompt_eval_count"],   # tokens INTO the LLM
        "tokens_out": d["eval_count"],          # tokens OUT of the LLM
        "total": d["prompt_eval_count"] + d["eval_count"],
        "text": d["response"].strip(),
    }


if __name__ == "__main__":
    print_session_index()
    print()
    print("== Local Ollama token probe ==")
    try:
        r = ollama_tokens("qwen3.8:27b", "hello")
        print(f"qwen3.8:27b -> tokens IN {r['tokens_in']}, OUT {r['tokens_out']}, total {r['total']}")
        print("reply:", r["text"][:120])
    except Exception as e:
        print(f"Ollama probe failed (is the server up on 127.0.0.1:11434?): {e}")
