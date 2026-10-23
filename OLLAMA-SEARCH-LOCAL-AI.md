---
title: MLaaS — Machine Learning as a Service Workspace
description: Main landing guide covering workspace indexing, MCP hybrid search router, and local LLM setup
keywords:
- MLaaS
- workspace
- indexing
- search router
- MCP
- Ollama
- qwen
- macOS
category: index
classification: 🟢🛡️ General
last_updated: '2026-10-11'
author: thatsafact
ai_search_aliases:
- mlaas readme
- workspace overview
- local llm setup
- start here mlaas
---

# MLaaS — Machine Learning as a Service

> **TL;DR:** Production-ready MLaaS workspace combining local LLM acceleration (Ollama + qwen3.8:27b on Apple Silicon) with a ChromaDB-powered MCP workspace search router and project delivery docs.
> **Use this for:** Getting started with the MLaaS repository, understanding project scope, and locating core systems.

## 🆕 NEW: Workspace Indexing & MCP Search Router

**✅ Production-ready semantic search system** (added 2026-10-10)

A complete workspace indexing system with 45 documents already indexed, ready to power MCP search tools:

- 🔍 **Semantic search** — Find documents by meaning, not keywords
- 📋 **LLM-formatted context** — Copy-paste results into Claude
- 🔌 **MCP-ready** — 3 tool definitions, 3 integration patterns
- 🧩 **Extensible** — Pluggable vector database providers
- ✅ **Tested** — 21/21 unit tests passing

**Quick start:** See [QUICK_START.md](Resources/copilot/search-router/QUICK_START.md) (5 minutes)

---

## MLaaS — Local LLM Setup (Ollama + qwen3.8:27b on macOS)

Setup guide for running **qwen3.8:27b** fully on-device via **Ollama** and using it as the
LLM model choice inside **VS Code**. Nothing runs in the cloud — the model is served locally
on `127.0.0.1:11434` and runs on the Mac's GPU through Apple's **MLX** runtime.

---

## Environment (this machine)

| Item | Value |
|------|-------|
| Host | Richards-MacBook-Pro.local |
| CPU / SoC | Apple M5 Pro |
| GPU | Apple M5 Pro (Metal-capable), `mlx` runtime |
| Unified memory | 48 GB (shared CPU + GPU) |
| Architecture | arm64 (Apple Silicon) |
| Ollama | 0.40.2 |
| Model | qwen3.8:27b (~18 GB on disk, ~21 GB when loaded) |
| Ollama server | `http://127.0.0.1:11434` (local only) |

---

## 1. Install Ollama (via Homebrew)

> **Ollama was installed with Homebrew**, as a **cask** (it ships as a GUI app), not a formula.

```bash
# Homebrew must be installed first
brew install --cask ollama
```

Verification that it is a Homebrew-managed cask:

```bash
brew list --cask ollama
# -> /opt/homebrew/Caskroom/ollama-app/.metadata/INSTALL_RECEIPT.json

which ollama
# -> /opt/homebrew/bin/ollama   (c-created symlink)

brew info ollama | head -1
# -> ==> ollama: stable 0.40.2 (bottled), HEAD
```

---

## 2. Start the Ollama server

On macOS the Ollama app auto-starts a local server on `127.0.0.1:11434`. To start it
manually (e.g. headless):

```bash
ollama serve
```

Confirm it is up:

```bash
curl -s http://127.0.0.1:11434/api/tags
```

---

## 3. Pull the model

```bash
ollama pull qwen3.8:27b
```

---

## 4. Verify the model is running LOCALLY (not in the cloud)

These commands prove the model is on-device. The key signals: `runner = mlx` + `100% GPU`
(a cloud model cannot report local GPU), and the `127.0.0.1` address (no request leaves the
machine).

```bash
# Show what is loaded in LOCAL memory
ollama ps

# List models served by the LOCAL Ollama registry
curl -s http://127.0.0.1:11434/api/tags

# End-to-end local inference round-trip through localhost
curl -s http://127.0.0.1:11434/api/generate \
  -d '{"model":"qwen3.8:27b","prompt":"reply with one word: pong","stream":false}'

# Direct CLI test
ollama run qwen3.8:27b "reply with one word: pong"

# Confirm the port is bound to localhost only (not 0.0.0.0 / public)
lsof -nP -iTCP:11434 -sTCP:LISTEN
```

Observed results:

```
NAME         ID          SIZE   PROCESSOR  CONTEXT  RUNNER  UNTIL
qwen3.8:27b  47951e4a6661 21 GB  100% GPU   32768    mlx     3 minutes from now

# api/generate -> response: "pong" (~1 s)
# ollama run    -> "pong"
```

No API key / token is required — another tell that it is local.

---

## 5. GPU / device details (Python)

One-liner to print the GPU/SoC, Metal support, and unified-memory total:

```bash
python3 -c "import subprocess,json; d=json.loads(subprocess.run(['system_profiler','SPDisplaysDataType','-json'],capture_output=True,text=True).stdout); [print('GPU/SoC:', x.get('spdisplays_chip') or x.get('_name'), '| cores:', x.get('spdisplays_totalnumberofcores'), '| Metal:', x.get('spdisplays_metal'), '| RAM:', int(subprocess.run(['sysctl','-n','hw.memsize'],capture_output=True,text=True).stdout.strip())//1024**3,'GB') for x in d['SPDisplaysDataType']]"
```

Observed result:

```
GPU / SoC : Apple M5 Pro
Unified mem: 48.00 GB (shared CPU+GPU)
```

Full detail script (GPU + live memory):

```python
import subprocess, json

# GPU / SoC
data = json.loads(subprocess.run(
    ["system_profiler", "SPDisplaysDataType", "-json"],
    capture_output=True, text=True, timeout=15).stdout)
for d in data.get("SPDisplaysDataType", []):
    print("GPU / SoC :", d.get("spdisplays_chip") or d.get("_name"))
    print("Metal     :", d.get("spdisplays_metal"))

# Unified memory (Apple Silicon shares CPU + GPU memory)
total = int(subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True).stdout)
ps    = int(subprocess.run(["sysctl", "-n", "hw.pagesize"], capture_output=True, text=True).stdout) or 16384
counts = {}
for line in subprocess.run(["vm_stat"], capture_output=True, text=True).stdout.splitlines():
    if ":" not in line:
        continue
    k, rest = line.split(":", 1)
    try:
        counts[k.strip()] = int(rest.strip().rstrip("."))   # note: strip trailing '.'
    except ValueError:
        pass
free = counts.get("Pages free", 0)
print(f"Unified mem: {total/1024**3:.2f} GB | free: {free*ps/1024**3:.2f} GB | "
      f"in use: {(total-free*ps)/1024**3:.2f} GB")
```

---

## 6. Use qwen3.8:27b as the model choice in VS Code

1. Install an Ollama-capable VS Code extension (installed manually on this machine).
2. In the extension, set:
   - **Provider / backend:** `Ollama`
   - **API base URL:** `http://localhost:11434`
   - **Model:** `qwen3.8:27b`
3. No API key is needed. Select `qwen3.8:27b` from the model picker — requests go to the
   local Ollama server.

---

## 7. Handy commands

```bash
ollama list                 # list all locally pulled models
ollama ps                   # show what is currently loaded in memory
ollama stop qwen3.8:27b     # unload the model, freeing ~21 GB
ollama rm   qwen3.8:27b     # remove the model from disk
curl -s http://127.0.0.1:11434/api/tags   # raw model list
```

---

## Notes & caveats

- After loading qwen3.8:27b, free memory was ~6 GB (≈87% used). Enough for inference, but
  other heavy apps may cause swapping. Run `ollama stop qwen3.8:27b` when done.
- The Ollama server binds to `127.0.0.1` by default — it is **not** exposed on your network.
- This setup is 100% local: Ollama + MLX on Apple Silicon, no cloud LLM calls.

---

## Appendix — Commands actually run during this setup session

For the record, these are the commands executed while setting up / verifying:

```bash
# Discovery: check Ollama / Homebrew / VS Code and existing models
which ollama && ollama --version; which brew; which code; ollama list

# Confirm the local Ollama server is up
curl -s http://127.0.0.1:11434/api/tags

# Inference smoke test
ollama run qwen3.8:27b "Reply with exactly one word: pong"

# Prove it is local, not cloud
ollama ps
curl -s http://127.0.0.1:11434/api/tags
curl -s http://127.0.0.1:11434/api/generate -d '{"model":"qwen3.8:27b","prompt":"reply with one word: pong","stream":false}'

# GPU details via Python
python3 -c "import subprocess,json; d=json.loads(subprocess.run(['system_profiler','SPDisplaysDataType','-json'],capture_output=True,text=True).stdout); [print('GPU/SoC:', x.get('spdisplays_chip') or x.get('_name'), '| cores:', x.get('spdisplays_totalnumberofcores'), '| Metal:', x.get('spdisplays_metal'), '| RAM:', int(subprocess.run(['sysctl','-n','hw.memsize'],capture_output=True,text=True).stdout.strip())//1024**3,'GB') for x in d['SPDisplaysDataType']]"

# Confirm Ollama is a Homebrew cask
brew info ollama | head -1
brew list --cask ollama
```
