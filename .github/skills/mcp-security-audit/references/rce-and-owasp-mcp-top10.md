# RCE Vectors & OWASP MCP Top 10 Reference

> **Source:** Awesome Copilot (`code/awesome-copilot/skills/mcp-implementation-security-review/`)

---

## 1. Remote Code Execution (RCE) Vectors in MCP Tools

### Vector 1: Shell Execution (`shell=True`)
```python
# ❌ VULNERABLE:
subprocess.Popen(f"rg {query}", shell=True)

# ✅ SAFE:
subprocess.Popen(["rg", "--fixed-strings", query])
```

### Vector 2: Path Traversal in File Tools
```python
# ❌ VULNERABLE:
with open(os.path.join(REPO_ROOT, user_path)) as f: ...

# ✅ SAFE:
real_target = os.path.realpath(os.path.join(REPO_ROOT, user_path))
if not real_target.startswith(os.path.realpath(REPO_ROOT)):
    raise PermissionError("Path traversal attempt detected")
```

### Vector 3: SQLite Side-Channel Arbitrary Execution
```python
# ❌ VULNERABLE:
cursor.execute(user_query) # Could execute ATTACH DATABASE or load_extension

# ✅ SAFE:
clean = user_query.strip().upper()
if not clean.startswith("SELECT") and not clean.startswith("EXPLAIN"):
    raise PermissionError("Only read-only SELECT queries are allowed")
if any(kw in clean for kw in ["ATTACH", "LOAD_EXTENSION", "PRAGMA WRITABLE_SCHEMA"]):
    raise PermissionError("Dangerous SQLite directive detected")
```

---

## 2. OWASP MCP Top 10 Summary

| ID | Vulnerability Name | Mitigation in MLaaS |
| :--- | :--- | :--- |
| **MCP-01** | Prompt Injection via Tool Outputs | Escape raw file contents and format with typed JSON structures |
| **MCP-02** | Excessive Tool Permissions | Limit tools to read-only where possible; require explicit approvals |
| **MCP-03** | Insecure Transport & Auth | Local stdio transport bound to authenticated desktop session |
| **MCP-04** | Secrets Exposure in Configuration | Use OS keychain or session env variables, never literal keys |
| **MCP-05** | Unvalidated Input Arguments | Pydantic / TypedDict schema validation on all MCP tool params |
| **MCP-06** | Denial of Service via Large Payloads | Pagination (`limit`, `offset`) on search results and DB queries |
| **MCP-07** | Server Impersonation | Pin exact python binary path (`.venv/bin/python3`) in `.mcp.json` |
