# 11 Design Transformation Levers & Examples

When an apparent constraint makes a goal impossible or complex, do not merely accumulate workarounds. Apply one of the 11 transformation levers to change the architecture so that the constraint no longer applies.

## The 11 Levers

| Lever | Core Mechanism | Example of Transformation |
|---|---|---|
| **1. Interface or Contract** | Change interaction shape | Push → pull; sync → async; per-item → batch; expose a narrower, purpose-built API. |
| **2. Protocol** | Change transport/serialization | Replace a chatty REST protocol with streaming or bulk endpoint; change serialization boundary. |
| **3. Abstraction Layer** | Move responsibility across tiers | Enforce an invariant in the database instead of application code; use a platform capability instead of custom code. |
| **4. Architecture** | Move compute vs data | Move computation to the data (stored proc/batch vs loading to memory); split or merge components; add/remove boundary. |
| **5. Dependency** | Replace or bypass library/service | Replace, remove, upgrade, or adopt the officially supported alternative. |
| **6. Data Flow** | Alter state propagation timing | Precompute, cache, make operations idempotent, switch to event-driven/CDC propagation. |
| **7. Deployment / Runtime** | Change execution environment | Change where/how workload runs — daemonless/rootless build instead of privileged container. |
| **8. Integration Boundary** | Alter touchpoint | Integrate at the message queue/table instead of API; intercept at storage layer. |
| **9. Ownership Boundary** | Upstream vs downstream | Have the owning team/vendor fix it upstream; adopt a fix from a newer platform release. |
| **10. Workflow** | Re-order or eliminate human/system steps | Change when or by whom a step is done; eliminate redundant validation step entirely. |
| **11. Requirement** | Re-scope outcome vs implementation | Negotiate or relax a requirement with its owner, supported by evidence of cost and risk. |

---

## Architectural Guidelines

- **Subtract before adding:** Prefer removing a component, step, requirement, or dependency over introducing an adapter, wrapper, bridge, or proxy.
- **Look for the intended path first:** Platforms often ship a supported mechanism for exactly the blocked case — a scoped permission, an official extension point, or an existing batch API.
- **Pivot question:** *"If the current approach did not exist, how would we reach the objective?"*

---

## Reference Case Studies

1. **Transforming an Inbound Network Constraint:**
   - *Problem:* A service must react to SaaS webhook events, but enterprise policy forbids inbound ports.
   - *Workaround:* Open firewall hole or establish reverse SSH tunnel (requires security exception).
   - *Transformation:* Lever 1 & 6 (Contract & Data Flow). Switch from push to pull: poll SaaS events API or subscribe to an outbound-initiated Kafka/SQS topic.

2. **Treating Security Control as Information:**
   - *Problem:* CI job needs to build container images, but runners forbid privileged containers.
   - *Workaround:* Request root/privileged execution on CI runners.
   - *Transformation:* Lever 7 (Runtime Model). Use rootless/daemonless image builders (Kaniko, Buildah) or offload image build to dedicated build cluster.
