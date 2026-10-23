# Root Cause Investigation & Call Stack Tracing

> **Source:** Superpowers v7.0.0 (`code/superpowers/skills/systematic-debugging/SKILL.md`)

Protocol for backward tracing and multi-layer component boundary isolation.

---

## 1. Backward Data-Flow Tracing

When an error presents deep inside a call stack or external library:

1. **Locate the Symptom:** Note the exact line throwing the exception and the invalid value.
2. **Step Backward:**
   - What called this function with the invalid value?
   - Did the caller calculate it, or receive it from its own caller?
   - Trace up the stack until you identify where valid state transitioned into invalid state.
3. **Fix at Source:**
   - Fix where the bad value originated, never where it was consumed.
   - Guard at boundaries, but fix at the root.

---

## 2. Multi-Component Boundary Isolation

In distributed or hybrid systems (e.g., Python script → MCP stdio → Tantivy Rust engine → ChromaDB SQLite):

Add non-invasive boundary instrumentation to discover *which layer* broke before changing logic:

```bash
# Layer 1: Environment & Virtualenv
which python3
echo $VIRTUAL_ENV

# Layer 2: CLI invocation & arguments
echo "Input query: $QUERY"

# Layer 3: Engine interface (Tantivy / ChromaDB)
.venv/bin/python3 -c "from scripts.search_router.tantivy_searcher import TantivySearcher; print(TantivySearcher().search('test'))"

# Layer 4: MCP JSON-RPC protocol output
# Inspect stdout vs stderr isolation (ensure logs go to stderr, only JSON-RPC to stdout)
```

---

## 3. Defense-in-Depth Checklist

When fixing the root cause, ensure:
- [ ] Root cause eliminated at the producer level.
- [ ] Consumer boundary adds input validation / clear error message if violated.
- [ ] Regression unit test added to prevent re-introduction.
- [ ] No unrelated code refactoring mixed into the bugfix commit.
