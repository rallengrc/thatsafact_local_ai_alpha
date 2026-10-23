---
name: aws-cost-optimize
description: "Audit AWS cloud infrastructure and ML compute pipelines for cost optimization, GPU idle waste elimination, and Karpenter spot provisioning."
---

# AWS Cost Optimization — MLaaS Cloud Economics

**Triggers:** `aws cost`, `cost optimize`, `gpu waste`, `karpenter spot`, `reduce cloud bill`

**Upstream:** Infrastructure architecture specs and cloud benchmarks
**Downstream:** IaC optimizations (`terraform`, `cdk`, `kubernetes-manifests`)

---

## Core Mission in Burstable MLaaS

ML compute on GPU-laden cloud instances (e.g. `g5.12xlarge`, `p4d.24xlarge`) costs between **$7.00 and $32.00/hour**. In traditional monolithic ML architectures:
- **47% of wall time** is spent in single-threaded CPU preprocessing, unpickling, or disk serialization.
- GPUs sit **100% idle** while incurring full hourly billing.

**The MLaaS Cost Solution:**
1. **Ray Task Distribution:** Preprocessing runs on cheap burstable CPU spot instances ($0.08/hr).
2. **Flyte Memoization:** Identical pipeline stages hit content-addressed cache (0.05ms, $0.00).
3. **Karpenter Dynamic Provisioning:** GPU nodes scale from 0 to N just-in-time and terminate the second the inference task finishes.

---

## Discovery & Audit Checklist

```
1. DISCOVER: Identify running EC2 GPU instances and provisioned EBS volumes.
2. METRICS: Query CloudWatch for GPU Utilization and CPU idle time over 7 days.
3. DETECT WASTE: Identify unattached EBS volumes, idle NAT gateways, and static GPU clusters.
4. SPOT AUDIT: Identify interruptible batch workloads suitable for Karpenter spot nodepools.
5. REPORT: Quantify hourly savings and generate remediation actions.
```

---

## References

- [CloudWatch Metrics & Karpenter NodePool Policies](references/cloudwatch-and-karpenter-metrics.md) — AWS CLI commands & Karpenter configs
- **Source:** `code/awesome-copilot/skills/aws-cost-optimize/SKILL.md`
