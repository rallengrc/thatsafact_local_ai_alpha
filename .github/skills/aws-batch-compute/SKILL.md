---
name: aws-batch-compute
description: "Orchestrate large-scale batch workloads using AWS Batch, Flytekit task plugins, and Karpenter disruption protection on AWS EKS. TRIGGERS: 'aws batch', 'batch job', 'flyte batch', 'batch compute environment', 'batch queue'."
---

# AWS Batch & Distributed Batch Workloads

> **Core Objective:** Design, provision, and operate scalable batch computing pipelines leveraging AWS Batch compute environments, Flyte workflow tasks, and Karpenter disruption-safe spot nodes.

---

## ⚡ Architecture & Tooling Matrix

| Layer | Technology | Key Responsibility & Pattern |
|---|---|---|
| **Macro Orchestration** | `flytekitplugins-awsbatch` | Moves task execution from local pods to managed AWS Batch job queues; sets retries, timeouts, and cache keys |
| **Compute Engine** | AWS Batch (`MANAGED` EC2 / Fargate) | Manages auto-scaling compute pools (Spot Capacity Optimized) with zero idle worker spend |
| **Kubernetes Batch** | Karpenter on AWS EKS | Disruption protection using `karpenter.sh/do-not-disrupt: "true"` to prevent consolidation evictions during runs |
| **IaC Provisioning** | Terraform (`terraform-aws`) | Declares compute environments, launch templates, job definitions, and job queues |

---

## 🛡️ Operational Best Practices

1. **Spot Allocation Strategy:** Always use `SPOT_CAPACITY_OPTIMIZED` for Batch compute environments to minimize spot interruption rates.
2. **Annotation Protection:** When deploying K8s batch jobs on spot nodes, always annotate pods with `karpenter.sh/do-not-disrupt: "true"` until job completion.
3. **Queue Prioritization:** Separate high-priority ad-hoc jobs from background bulk processing using tiered `aws_batch_job_queue` priorities.

---

## 📄 See Also

- 📄 [batch-patterns-and-karpenter.md](./references/batch-patterns-and-karpenter.md) — Concrete Flytekit task code, Kubernetes job specs, and Terraform Batch definitions.
- 📄 [terraform-aws](../terraform-aws/SKILL.md) — Companion skill for provisioning Batch VPCs, IAM roles, and compute environments.
- 📄 [aws-cost-optimize](../aws-cost-optimize/SKILL.md) — Cost auditing and GPU idle elimination.
