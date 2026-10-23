# Token Budgeting & History Pruning Reference

> **Source:** Awesome Copilot (`code/awesome-copilot/instructions/context-engineering.instructions.md`)

---

## 1. Local LLM Context Limits (Ollama qwen3.8:27b)

When running inference via local Ollama models on macOS Apple Silicon:
- **Default Window:** Typically 4k or 8k tokens unless configured via `num_ctx` in Modelfile.
- **Latency Scaling:** Quadratic attention computation above 16k tokens on unified RAM can cause significant slowdown.
- **Budgeting Rule:** Keep prompt payload under 4,000 tokens per call by truncating file listings, formatting tables cleanly, and omitting binary or test fixture data.

---

## 2. Multi-Turn Compaction Protocol

When a conversation exceeds 20 turns or token pressure causes degradation:
1. **Emit Checkpoint:** Summarize:
   - What decisions were made,
   - What files were created or modified,
   - What tests are passing,
   - What next task remains.
2. **Clear Transient Variables:** Do not preserve failed attempts or discarded prototypes in working memory.
3. **Persist State to Disk:** Write durable status to `.ledger.md` or `memories/<user>/` rather than relying on ephemeral conversation memory.

---

## 3. Tool Output Offloading & Narrow Reads

When tools output large payloads (>20KB):
- Never dump the full temp file into context.
- Use `grep` or `rg` on the temp file to extract the matching lines.
- Use `view` with a bounded `view_range: [start, end]` to read only the relevant snippet.
