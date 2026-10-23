---
title: "AWS Batch & Distributed Compute Patterns Reference"
description: "Concrete implementation patterns for AWS Batch, Flytekit task integration, and Karpenter batch job disruption protection."
shield: "internal"
last_updated: "2026-10-23"
keywords: [aws-batch, flyte, karpenter, spot, compute-environment, job-queue]
---

# AWS Batch & Distributed Compute Patterns Reference

📄 **Orchestrator Skill:** `.github/skills/aws-batch-compute/SKILL.md`  
**Sources:** `code/flytekit/plugins/flytekit-aws-batch/`, `code/flytesnacks/examples/aws_batch_plugin/`, `code/karpenter-blueprints/blueprints/batch-jobs/`

---

## 1. Flytekit Native AWS Batch Integration

When workflows require bursting beyond local Kubernetes clusters to AWS Batch managed compute environments:

```python
from flytekit import task, workflow
from flytekitplugins.awsbatch import AWSBatch

# Configure AWS Batch job parameters
batch_config = AWSBatch(
    platformCapabilities="EC2",  # or "FARGATE"
    parameters={"max_vcpus": "128"},
    retryStrategy={"attempts": 3},
    timeout={"attemptDurationSeconds": 3600},
    propagateTags=True,
    tags={"Workload": "SurrogateBatchInference"},
)

@task(task_config=batch_config, cache=True, cache_version="1.0")
def run_batch_simulation(case_id: str, parameters: dict) -> float:
    """Executes heavy physics or surrogate simulation directly in AWS Batch."""
    return 42.0
```

---

## 2. Karpenter Disruption Defense for Long-Running Batch Jobs

When running batch workloads on spot nodes via Karpenter, prevent premature node consolidation from interrupting executing jobs:

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: surrogate-batch-job
spec:
  template:
    metadata:
      annotations:
        # Crucial: Tells Karpenter NOT to disrupt or consolidate the node while this pod runs
        karpenter.sh/do-not-disrupt: "true"
      labels:
        app.kubernetes.io/component: batch-worker
    spec:
      restartPolicy: OnFailure
      containers:
        - name: worker
          image: mlaas/surrogate:latest
          resources:
            requests:
              cpu: "4000m"
              memory: "16Gi"
```

---

## 3. Terraform AWS Batch Infrastructure Blueprint

```hcl
resource "aws_batch_compute_environment" "spot_env" {
  compute_environment_name = "mlaas-spot-compute"
  type                     = "MANAGED"
  state                    = "ENABLED"

  compute_resources {
    type               = "SPOT"
    allocation_strategy = "SPOT_CAPACITY_OPTIMIZED"
    min_vcpus          = 0
    max_vcpus          = 256
    instance_types     = ["optimal", "c6i.4xlarge", "c6a.4xlarge"]
    subnets            = module.vpc.private_subnets
    security_group_ids = [aws_security_group.batch_sg.id]
    instance_role      = aws_iam_instance_profile.batch_profile.arn
  }
}

resource "aws_batch_job_queue" "batch_queue" {
  name                 = "mlaas-batch-queue"
  state                = "ENABLED"
  priority             = 1
  compute_environments = [aws_batch_compute_environment.spot_env.arn]
}
```
