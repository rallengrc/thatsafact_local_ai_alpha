# Verification Patterns & Concrete Commands

> **Source:** Superpowers v7.0.0 (`code/superpowers/skills/verification-before-completion/SKILL.md`)

Concrete execution patterns for proving claims across test, build, container, and benchmark workloads.

---

## 1. Test Verification

### Python / Pytest (MLaaS Environment):
```bash
# Targeted test verification (fastest)
.venv/bin/pytest scripts/tests/test_search_router.py -v

# Single test function
.venv/bin/pytest scripts/tests/test_search_router.py::test_deduplication -v

# Proof requirement:
# MUST see "== 1 passed in 0.05s ==" and exit code 0.
```

### Red-Green Regression Verification:
1. Write test for reported bug.
2. Run test → **MUST FAIL** with the exact bug symptom.
3. Apply surgical fix.
4. Run test → **MUST PASS**.
5. Temporarily revert fix → **MUST FAIL AGAIN**.
6. Restore fix → **MUST PASS**.

---

## 2. Infrastructure & Kubernetes Verification

### KinD / Local K8s Cluster:
```bash
# Pod state verification:
kubectl get pods -n default -l app.kubernetes.io/name=ray-cluster
# MUST see: STATUS Running and READY 1/1 (no CrashLoopBackOff or Error).

# Service endpoint probe:
curl -s -o /dev/null -w "%{http_code}" http://localhost:8265/api/version
# MUST see: 200
```

---

## 3. SQLite Benchmark & Metrics Verification

```bash
# Query the database to verify row insertion:
.venv/bin/python3 -c "
import sqlite3
conn = sqlite3.connect('Projects/hello-mlaas-burst/benchmark_metrics.db')
c = conn.cursor()
c.execute('SELECT run_id, total_wall_time_ms, speedup_factor FROM pipeline_benchmarks ORDER BY timestamp DESC LIMIT 1')
print('Latest row:', c.fetchone())
"
# MUST see: valid tuple with run_id, numeric wall time, and numeric speedup.
```

---

## 4. Multi-Agent Delegation Verification

When receiving output from an implementer subagent:
1. Do **not** trust the summary text ("I implemented X and all tests pass").
2. Run: `git status -s` to verify modified and untracked files.
3. Run: `git diff --stat` to verify changed line counts.
4. Run the test command independently in the parent session.
