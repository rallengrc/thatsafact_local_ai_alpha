# Domain Lenses & Adversarial Review Checklists

Apply these lenses during Stage 7 (Adversarial Review) to systematically stress-test proposed architecture pivots against critical engineering concerns.

## Domain Lenses

| Domain | Primary Evidence to Seek | Critical Failure Modes to Prioritize |
|---|---|---|
| **Software & Debugging** | Reproductions, minimal failing test cases, recent diffs | Wrong abstraction layer, masked errors, race conditions, non-deterministic execution. |
| **Distributed Systems** | Contracts, sequence diagrams, state sync flows | Partial network failure, split-brain, clock skew, out-of-order delivery, unhandled retries. |
| **Database & Schema** | DDL, execution plans, lock contention, transaction bounds | Table locks, lock escalation, isolation anomalies, unindexed full table scans, rollback feasibility. |
| **Security & Auth** | Trust boundaries, privilege models, token/secret lifecycles | Credential exposure, privilege escalation, bypass of audit logs, unintended data egress. |
| **Performance & Scale** | Profiling data, latency percentiles (p95/p99), memory usage | Optimizing wrong bottleneck, memory leaks, connection pool exhaustion, N+1 query patterns. |
| **Reliability & SRE** | Health checks, backpressure mechanisms, error budgets | Retry storms, cascading failures, lack of circuit breakers, degraded dependencies. |
| **Data Engineering** | Lineage, volume/throughput metrics, idempotency keys | Duplicate processing, missing replay capabilities, schema migration drifts. |

---

## Adversarial Review Checklist

When attacking the leading solution and user proposals, evaluate:

1. **Correctness:** Are there counterexamples where this fails? What happens on boundary values or null states?
2. **Partial Failure:** If step 3 of 5 crashes, what is the cleanup path? Are operations idempotent?
3. **Data Integrity:** What happens if the service crashes mid-transaction? How is data rolled back?
4. **Security Boundaries:** Does the change require elevated permissions or grant wider access than needed?
5. **Operability & Observability:** How will an on-call engineer know this is failing at 3 AM? Where are the metrics/logs?
6. **Reversibility:** Is this a two-way door (trivial rollback) or a one-way door (schema destruction, state conversion)?
