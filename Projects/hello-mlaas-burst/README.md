# 🚀 Hello MLaaS Burst — Quickstart & Reference

![Hello MLaaS Burst Architecture](../../Resources/visualization/hello-mlaas-burst-architecture.png)

This directory contains the runnable code and architectural plan for **Hello MLaaS Burst**, demonstrating the Flyte (Macro Orchestrator) + Ray (Micro Distributed Compute) surrogate modeling pipeline across **Local Mac**, **AWS EKS**, and **On-Premises VMs**.

📄 **Full Architecture & Implementation Plan:** See [PLAN.md](./PLAN.md)

---

## 📂 File Directory

- **[PLAN.md](./PLAN.md)** — In-depth architectural blueprint, options matrix, cluster evaluation (Docker Desktop vs Kind vs Kubeadm), and citations.
- **[aws-batch-ecs-vs-karp-ray-flyte.md](./aws-batch-ecs-vs-karp-ray-flyte.md)** — Architecture trade-off analysis comparing Karpenter/Ray/Flyte vs. AWS Batch & ECS managed instances.
- **[workflow.py](./workflow.py)** — Production Flyte pipeline with distributed Ray surrogate model training.
- **[local_runner.py](./local_runner.py)** — Standalone zero-cloud local verification test (supports `--benchmark` mode).
- **[benchmark_runner.py](./benchmark_runner.py)** — Comparative performance benchmarking suite (Old Way vs New Way Cold vs New Way Warm).
- **[benchmark_db.py](./benchmark_db.py)** — SQLite performance metrics database and feature attribution logger (`benchmark_metrics.db`).
- **[kind-config.yaml](./kind-config.yaml)** — 4-Node Kubernetes in Docker (KinD) cluster configuration with node roles and port mappings.
- **[k8s-rayjob.yaml](./k8s-rayjob.yaml)** — KubeRay `RayJob` custom resource manifest for AWS EKS & On-Prem Kubernetes.
- **[requirements.txt](./requirements.txt)** — Python dependencies for the pipeline.
- **[Dockerfile](./Dockerfile)** — Multi-arch container image definition.

---

## ⚡ Quickstart (Run in 5 Seconds)

Run the verification runner directly on your Mac:

```bash
python3 local_runner.py
```

---

## 🔬 Empirical Performance Benchmark: Old Way vs. New Way

To run the scientific comparative benchmark (Old Way with serial loop and disk pickling vs. Flyte+Ray in-memory parallel with execution caching) and record metrics to SQLite:

```bash
python3 local_runner.py --benchmark --samples 200000 --workers 4
```

### Empirical Results (from SQLite `benchmark_metrics.db`):

| Metric | Old Way (Serial + Disk) | New Way (Cold Start) | New Way (Warm Cache) | Ray / Flyte Feature Attribution |
|---|---|---|---|---|
| **Total Wall Time** | **58.2 ms** | **23.3 ms** | **16.2 ms** | Combined compound acceleration |
| **Data Prep / ETL** | 15.0 ms | 5.5 ms | **0.05 ms (⚡ HIT)** | **Flyte:** Content-addressed execution caching |
| **Disk I/O Overhead** | 1.6 ms (7.63 MB) | **0.0 ms (0-copy)** | **0.0 ms (0-copy)** | **Ray:** Shared-memory object store zero-copy |
| **Surrogate Training** | 41.5 ms | 17.7 ms | 16.2 ms | **Ray:** `@ray.remote` task parallelism (4 workers) |
| **Throughput (samples/s)** | 3.4M / sec | 8.6M / sec | **12.3M / sec** | 3.6x throughput enhancement |
| **Physics Accuracy (R²)** | 0.9913 | 0.9913 | 0.9913 | Parity verified across all modes |
| **Idle GPU Waste** | **28.7% wasted** | **0.0% wasted** | **0.0% wasted** | **Flyte+Ray:** Burstable Karpenter node slicing |
| **Speedup vs Baseline** | 1.00x (Baseline) | **⚡ 2.50x** | **🚀 3.59x** | Empirical speedup on Mac CPU |

### Querying the SQLite Database:

```bash
# View all benchmark runs
sqlite3 benchmark_metrics.db "SELECT run_id, pipeline_type, total_wall_time_ms, speedup_factor, cache_status FROM pipeline_benchmarks;"

# View feature attribution
sqlite3 benchmark_metrics.db "SELECT framework, feature_name, metric_improvement FROM feature_attribution;"
```

---

## ☸️ Launching the 4-Node KinD Cluster

To test multi-node Kubernetes scheduling with Flyte and KubeRay on macOS:

```bash
# 1. Install kind and helm via Homebrew
brew install kind helm

# 2. Create the 4-node cluster
kind create cluster --name mlaas-burst --config kind-config.yaml

# 3. Verify node roles and labels
kubectl get nodes -L topology.kubernetes.io/zone,karpenter.sh/nodepool,node.kubernetes.io/role
```

Expected output:
```text
NAME                        STATUS   ROLES           AGE   VERSION   ZONE      NODEPOOL    ROLE
mlaas-burst-control-plane   Ready    control-plane   2m    v1.30.0                         
mlaas-burst-worker          Ready    <none>          2m    v1.30.0   local-a               platform-infra
mlaas-burst-worker2         Ready    <none>          2m    v1.30.0   local-a               ray-head
mlaas-burst-worker3         Ready    <none>          2m    v1.30.0             gpu-burst   ray-worker
```

> **Node Role Mapping Note:** KinD automatically names worker containers `worker`, `worker2`, `worker3`. Kubernetes schedules workloads based on **labels**, not hostnames:
> - `mlaas-burst-worker` = Platform Infra (Flyte + MinIO + KubeRay Operator)
> - `mlaas-burst-worker2` = Ray Head Coordinator (Host port 8265 forwarded)
> - `mlaas-burst-worker3` = Burstable GPU Simulator (`karpenter.sh/nodepool: gpu-burst`)

