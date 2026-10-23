---
title: "Architecture Comparison — Karpenter/Ray/Flyte vs. AWS Batch & ECS Managed Instances"
description: "In-depth comparative analysis evaluating the Kubernetes-native Karpenter/Ray/Flyte stack against AWS Batch and ECS managed instances for MLaaS surrogate modeling."
keywords: [AWS Batch, ECS, Karpenter, Flyte, Ray, KubeRay, Argo Workflows, multi-node parallel, gang scheduling, cloud architecture, surrogate modeling, tri-environment, GPU scaling, MLaaS]
category: architecture
classification: 🟢🛡️ General
last_updated: '2026-10-15'
author: thatsafact
related:
  - PLAN.md
  - ../../Hello-MLaaS.md
  - ../../Resources/visualization/hello-mlaas-burst-architecture.md
ai_search_aliases:
  - aws batch vs karpenter
  - ecs vs flyte ray
  - batch architecture trade-offs
  - modular mlaas architecture
  - can batch ray karpenter flyte work together
  - flyte vs argo workflows
  - batch on eks ray kuberay limitation
  - can karpenter ray flyte run on ecs
  - ecs managed instances gpu
  - ecs gang scheduling
---

# ⚖️ Cloud Architecture Comparison: Karpenter/Ray/Flyte vs. AWS Batch & ECS Managed Instances

> **TL;DR:** Deep comparative trade-off analysis evaluating the Kubernetes-native **Flyte + Ray + Karpenter** architecture against AWS-managed **Batch + ECS** for high-throughput surrogate ML pipelines. Establishes why Kubernetes is mandatory for the Tri-Environment contract (Mac, AWS, On-Prem) and defines the modular boundaries separating architectural invariants from trial-swappable plugins. **§6 answers the combination question directly: Batch cannot be layered under Karpenter, and cannot run Ray at all; §6.7 answers whether this stack can run on ECS — it cannot.**
> **Use this for:** Architectural trade-off reviews, cloud infrastructure sizing, evaluating alternatives to Kubernetes in enterprise ML platforms, settling whether AWS Batch, Karpenter, Ray and Flyte can be combined (§6), and whether the stack can run on ECS (§6.7).

---

## 1. 💎 Concierge Note (Teach-Mode)

💎 **Concierge Note:** The **Flyte + Ray + Karpenter** stack is a high-performance, Kubernetes-native Formula 1 racing engine built for low-latency in-memory data movement and tri-environment portability (Mac, AWS, On-Prem); **AWS Batch + ECS** is a reliable postal freight service designed for fire-and-forget batch jobs that only ever runs inside AWS.

**The Formula 1 Paddock vs. The Freight Depot:**  
Think of **Flyte/Ray/Karpenter** as a **Formula 1 team**: Flyte is the Chief Race Engineer tracking every lap and caching previous tire telemetry; Ray is the V6 hybrid turbo engine transferring kinetic energy to electric boost in microseconds without ever stopping to unbolt parts (in-memory zero-copy shared memory); and Karpenter is the pneumatic pit crew that bolts on fresh aerodynamic wings in 45 seconds and packs the garage away the instant the car crosses the finish line.  
By contrast, **AWS Batch + ECS** is **freight shipping**: you drop work into a queue; AWS figures out when an ECS-managed EC2 truck is free, loads your container, runs the job, writes everything to an S3 warehouse, and drives away. It works out of the box with zero Kubernetes operations, but every step must pack and unpack its cargo to disk/S3, and **it cannot drive onto a local Mac laptop or cross the air-gapped firewall into an on-premises VM cluster**.

* **Shortcut:** Compare `Projects/hello-mlaas-burst/PLAN.md` vs. AWS ECS/Batch architecture.
* **Applies:** When evaluating cloud economics, engineering velocity, and the delivery contract.

---

## 2. 🔧 How It Works: Architectural Head-to-Head

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                           ARCHITECTURAL PATTERN COMPARISON                              │
├───────────────────────────────┬─────────────────────────────────────────────────────────┤
│    Karpenter + Ray + Flyte    │               AWS Batch + ECS Managed Instances         │
│     (Kubernetes-Native)       │                     (AWS Managed Services)              │
├───────────────────────────────┼─────────────────────────────────────────────────────────┤
│ • Macro Orchestration: Flyte  │ • Macro Orchestration: AWS Step Functions / Airflow     │
│ • Micro Compute: Ray Engine   │ • Micro Compute: Isolated Docker Containers (No shared) │
│ • Provisioner: Karpenter      │ • Provisioner: ECS Managed Instances, or Batch CE       │
│ • Inter-task: Zero-copy shm   │ • Inter-task: S3 Put/Get Object Serialization           │
│ • Targets: Mac, EKS, On-Prem  │ • Targets: AWS Only (Zero on-prem / local parity)       │
└───────────────────────────────┴─────────────────────────────────────────────────────────┘
```

### Layer 1: Macro-Orchestration & Workflow DAGs
* **Flyte:** Native typed data contracts, parameter hashing, and **content-addressed memoization**. If mesh generation or CFD parameters were run previously, Flyte returns the cached output in **0.05 ms** at **$0.00 compute cost**. Workflows run locally in Python (`local_runner.py`) or on any Kubernetes cluster.
* **AWS Batch:** AWS Batch has no native DAG concept. It relies on **AWS Step Functions** or Apache Airflow to chain jobs. There is **no built-in memoization cache**—every execution triggers full compute billing unless you write custom DynamoDB caching logic by hand.

### Layer 2: Micro-Compute & Distributed Data Movement
* **Ray (KubeRay):** Stateful Python actors and task graphs communicating via **Ray's built-in shared-memory object store (`/dev/shm`)**. Data handoffs between distributed workers take **0.0 ms** (zero-copy pointer exchange).
* **AWS ECS / Batch:** Each container is an isolated execution unit. There is **no shared in-memory object store across containers**. If Step 1 creates a 5 GB mesh, it **must serialize to disk, upload to S3, and Step 2 must download from S3 and unpickle it**. At high sample throughput, disk/S3 serialization becomes the primary bottleneck.

### Layer 3: Dynamic Node Provisioning & Scaling
* **Karpenter:** Direct, group-less EC2 Fleet API integration. Watches the Kubernetes pending pod queue in real time (zero polling delay). Provisions tailored GPU nodes in **45–60 seconds**. Consolidates and scales to zero in **30 seconds** after jobs exit.
* **ECS capacity providers backed by Auto Scaling Groups:** scale-out requires ASG evaluation loops (**3–8 minutes**), and scale-in enforces cooling periods (typically 10–15 minutes), during which **expensive GPU instances linger idle at full hourly rates**.
* **ECS Managed Instances** *(corrected 2026-10-15 — this section previously conflated the two)*: a **distinct, AWS-managed** capacity model, GA across commercial regions since October 2025, not the ASG path above. AWS selects instances from declared `instanceRequirements` and owns provisioning, **NVIDIA driver management**, patching and scaling. Since GA it has added [GPU health monitoring and auto-repair](https://aws.amazon.com/about-aws/whats-new/2026/04/amazon-ecs-gpu-auto-repair/) (enabled by default) and [fractional GPU scheduling on G6f](https://aws.amazon.com/about-aws/whats-new/2026/08/amazon-ecs-fractional-gpu/). AWS publishes a [GPU batch inference pattern with scale to zero](https://aws.amazon.com/blogs/containers/run-gpu-batch-inference-on-amazon-ecs-managed-instances-with-scale-to-zero/), so the "idle GPUs linger through a cooldown" objection **does not apply to this model**. Treat ECS Managed Instances as a genuine ECS-native answer to the job Karpenter does — more managed, less controllable.
* **Fargate** supports no GPUs at all, multi-GPU or otherwise.
* **Neither ECS model runs this stack**, however — see §6.7. Karpenter and Flyte are Kubernetes-native by construction, and ECS has no gang scheduling for multi-node training.

### Layer 4: The Portability Contract (Tri-Environment Parity)
* **Flyte + Ray + K8s:** Runs identically on **Local Mac (KinD 4-node)**, **AWS EKS (Production Burst)**, and **On-Prem (Air-gapped VMs)**. A single codebase satisfies all three milestones.
* **AWS Batch + ECS:** Completely proprietary to AWS. Cannot run on a local developer laptop. Cannot run inside a corporate firewall on-prem without AWS Outposts hardware.

---

## 3. ⚡ Optimal Conditions: When Each Architecture Wins

| Workload Characteristic | Choose Karpenter / Ray / Flyte | Choose AWS Batch | Choose ECS Managed Instances |
|---|---|---|---|
| **Multi-Step Surrogate ML & Physics AI** | 🏆 **Optimal** (zero-copy tensors, 0.05ms caching) | ⚠️ High S3 serialization latency | ⚠️ Same serialization cost; no DAG engine |
| **Multi-Node Distributed Training** | 🏆 Ray gang-schedules natively | 🏆 MNP gang-schedules; EFA on EKS undocumented (§6.3) | ❌ **No gang scheduling primitive** — build it, or fall back to Batch MNP |
| **Tri-Environment Delivery (Mac / Cloud / On-Prem)** | 🏆 **Mandatory** (100% K8s portability) | ❌ Incompatible with non-AWS targets | ❌ Incompatible with non-AWS targets |
| **Bursty, High-Frequency Training Runs** | 🏆 **Optimal** (45s launch, 30s scale-to-zero) | 🏆 Queue-driven, scale-to-zero native | 🏆 Scale-to-zero supported (Managed Instances) |
| **Simple Standalone Batch Inference** | ⚠️ Overkill if no DAG or Ray needed | 🏆 **Optimal** (Managed queue, no K8s ops) | 🏆 **Optimal** (no K8s, no queue to model) |
| **Small-Model Inference / Right-Sizing** | Whole-GPU granularity | Whole-GPU granularity | 🏆 **Fractional GPU** on G6f (down to ⅛ L4) |
| **Legacy Black-Box C++/Fortran Binaries** | Moderate (wrap in containers) | 🏆 **Optimal** (Drop executable into a job) | 🏆 **Optimal** (Drop executable into a task) |
| **GPU Fleet Operations** | Yours: drivers, AMIs, node health | AWS manages the compute environment | 🏆 **Most managed** — AWS owns drivers, patching, GPU auto-repair |
| **Team Kubernetes Expertise** | Requires K8s/Helm awareness | Still EKS on the Batch-on-EKS path | 🏆 **Genuinely zero Kubernetes** |
| **Running *this* stack (Karpenter + Ray + Flyte)** | 🏆 Native | ❌ No CRDs → no KubeRay, no Flyte | ❌ **Karpenter and Flyte cannot run at all** (§6.7) |

---

## 4. 📊 By The Numbers: Side-by-Side Architectural Metrics

| Metric | Karpenter + Ray + Flyte (EKS) | AWS Batch + ECS Managed Instances | Advantage |
|---|---|---|---|
| **Node Cold-Start Latency** | **45 – 60 seconds** | 3 – 8 minutes | **Karpenter is 4x–8x faster** |
| **Inter-Step Data Transfer** | **0.0 ms** (shared-memory `/dev/shm`) | 1,500 – 5,000 ms (S3 Put/Get) | **Ray eliminates serialization** |
| **Step 1 Repeat Execution** | **0.05 ms** (Flyte Cache Hit) | Full runtime (No native cache) | **Flyte saves 100% of compute** |
| **Idle GPU Billing After Run** | **0%** (Terminates in 30s) | 15% – 35% (ASG cooldown lag) | **Karpenter saves $7–$30/hr** |
| **Local Dev Loop (Mac)** | **Yes** (4-node KinD in 45s) | **No** (Mocking required) | **Zero-cloud developer testing** |
| **On-Prem Air-Gapped Support** | **Yes** (Standard K8s manifests) | **No** (AWS API dependency) | **Direct SOW milestone compliance** |

---

## 5. 🧩 The Modular Architecture: What MUST STAY vs. What CAN BE SWAPPED

To design an adaptable platform where we can iteratively experiment with components without breaking the system contract, we divide the architecture into **Invariants (Must Stay)** and **Changeable Parts (Trial Swaps)**:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   THE MODULAR MLAAS ARCHITECTURE                       │
├───────────────────────────────────┬────────────────────────────────────┤
│     🔒 MUST STAY (INVARIANTS)     │    🔄 CHANGEABLE (TRIAL SWAPS)     │
├───────────────────────────────────┼────────────────────────────────────┤
│ 1. Macro vs Micro Separation      │ 1. Autoscaler Engine               │
│ 2. Kubernetes API Substrate       │ 2. Workflow Orchestration Engine   │
│ 3. Shared In-Memory Tensor Engine │ 3. GPU Instance Families & Spot    │
│ 4. S3-Compatible Storage Contract │ 4. Local Execution Runtime         │
└───────────────────────────────────┴────────────────────────────────────┘
```

### 🔒 The Invariants ("Must Stay")

These architectural foundations cannot be removed without violating the project requirements:

1. **The Macro vs. Micro Separation of Concerns:**  
   * *Why:* A single tool cannot both orchestrate multi-day pipeline DAGs and coordinate microsecond GPU tensor sharding. Flyte (or its equivalent) owns container boundaries; Ray (or its equivalent) owns Python memory pointers.
2. **The Kubernetes API as the Common Substrate:**  
   * *Why:* Kubernetes is the **only runtime abstraction** that exists simultaneously in Docker Desktop on your Mac (KinD), AWS (EKS), and corporate data centers (OpenShift / standard K8s). Moving to ECS breaks the Tri-Environment contract.
3. **An In-Memory Distributed Object Store (Ray shared-memory object store):**  
   * *Why:* High-throughput surrogate models (processing 8,000,000 samples/sec) cannot afford disk pickling or S3 roundtrips between pipeline tasks. Zero-copy shared memory is non-negotiable.
4. **S3-Compatible Object Storage Abstraction:**  
   * *Why:* All artifacts must speak standard S3 APIs so the pipeline points to AWS S3 in production and internal MinIO on Mac/On-Prem without changing a single line of application code.

---

### 🔄 The Changeable Parts ("Try Until We Find the Best Fit")

These components are modular plugins that can be swapped, benchmarked, and tuned:

| Component | Current Working Choice | Alternative Parts We Can Try | How to Test & Swap |
|---|---|---|---|
| **Node Autoscaler** | **Karpenter** (SIGs) | • **Kubernetes Cluster Autoscaler (CA)**<br>• **Cast.ai**<br>• ~~AWS Batch on EKS (Hybrid)~~ — **not a swap, see §6** | Switch node provisioner Helm chart; pod specs and Ray workloads remain identical. **Exception:** AWS Batch is *not* a Helm-swappable provisioner — it owns its own tainted nodes and cannot run Ray (§6.1). |
| **Macro Orchestrator** | **Flyte 2** | • **Argo Workflows** ← *named at the [[2026-10-12 Research Team Kickoff]]*<br>• **Kubeflow Pipelines (KFP)**<br>• **Prefect / Dagster** (K8s agents) | Replace Flyte tasks with Argo DAG templates; the underlying `@ray.remote` Python functions remain identical. **Live decision — see §6.6**, including whether "Argo" means Workflows or CD. |
| **GPU Hardware Class** | **AWS G5 (`g5.12xlarge`, A10G)** | • **AWS G6 (NVIDIA L4)**<br>• **AWS P4d / P5 (A100 / H100)**<br>• **Spot vs. On-Demand** | Change 2 lines in Karpenter `NodePool` YAML (`instance-family: [g6, g5]`). Karpenter automatically negotiates the cheapest fleet. |
| **Local Dev Runtime** | **KinD 4-Node (Active)** | • **K3s / K3d**<br>• **Local Python multiprocess**<br>• **In-process Ray (`ray.init()`)** | Toggle via `local_runner.py` environment flag (`local`, `kind`, or `aws`). |
| **Storage Backend** | **MinIO (Local) / S3 (AWS)** | • **Ceph** (On-Prem)<br>• **AWS EFS** (Shared POSIX)<br>• **JuiceFS / SeaweedFS** | Change `FLYTE_STORAGE_ENDPOINT` in Helm values. |

---

## 6. ⚠️ Can Batch, Karpenter, Ray and Flyte Be Combined?

> **Corrected 2026-10-12.** An earlier version of this section proposed a "best of both worlds" experiment in which *"Karpenter handles node autoscaling, while AWS Batch provides the multi-tenant managed queuing layer,"* with Flyte and Ray running natively inside Batch-submitted pods. **That configuration does not exist.** The correction below is sourced to AWS documentation; the original claim is retained here so the error is traceable rather than silently rewritten.

### 6.1 The two hard blockers

**Blocker 1 — AWS Batch on EKS manages its own nodes, exclusively.** Per the [AWS Batch on EKS documentation](https://docs.aws.amazon.com/batch/latest/userguide/eks.html):

> AWS Batch has built-in scaling logic to scale Kubernetes nodes based on job queue load... **AWS Batch manages the full lifecycle of these nodes, and decorates the nodes with labels and taints.** This way, other Kubernetes workloads aren't placed on the nodes managed by AWS Batch... Additionally, **AWS Batch doesn't run jobs, specifically pods, on nodes in your cluster that it doesn't manage.**

The exclusion is symmetric: Karpenter cannot scale Batch capacity, and Batch will not schedule onto Karpenter-provisioned nodes. They can **coexist on disjoint node pools** in one cluster — Batch owning its tainted set, Karpenter owning everything else — but that is partitioning, not layering. **AWS Batch is an alternative to Karpenter, not a complement to it.**

**Blocker 2 — Batch submits podspecs, not CRDs.** The same document describes an "overlay" model in which *"there are no Kubernetes components (for example, Operators or **Custom Resources**) to install or manage in your cluster,"* and in which *"AWS Batch translates jobs into `podspecs`."*

Ray on Kubernetes runs through **KubeRay** (`RayCluster` / `RayJob` custom resources), and Flyte's Ray integration targets KubeRay. Since Batch submits no custom resources, **Ray workloads cannot execute on Batch-managed capacity** — whether launched directly or through Flyte.

### 6.2 What each combination actually does

| Combination | Verdict | Notes |
|---|---|---|
| **Karpenter + Ray (KubeRay) + Flyte** | ✅ **Works** — the stack this document recommends | Unchanged by this correction |
| **Batch on EKS + Karpenter, same cluster, separate node pools** | ✅ Coexist | Two scaling systems, two capacity models. Neither scales the other |
| **Batch on EKS + Karpenter managing the same nodes** | ❌ **Impossible** | Batch taints and owns its nodes; the original §6 claim |
| **Ray (KubeRay) on Batch-managed nodes** | ❌ **Impossible** | No CRDs in the Batch overlay model |
| **Flyte's Ray tasks dispatched to Batch** | ❌ **Impossible** | Same CRD wall, one layer up |
| **Flyte container / array tasks dispatched to Batch** | ⚠️ Legacy path | See §6.4 |
| **Ray bootstrapped on Batch multi-node parallel jobs** | ⚠️ Hand-rolled | See §6.3 |

### 6.3 The one path that does put Ray on Batch

[Multi-node parallel (MNP) jobs](https://docs.aws.amazon.com/batch/latest/userguide/mnp-eks-jobs.html) — gang scheduling, [GA on EKS since July 2024](https://aws.amazon.com/about-aws/whats-new/2024/07/aws-batch-gang-scheduling-eks-multi-node-parallel-jobs/) — give you a main node plus child nodes and support any IP-based inter-node framework. You can bootstrap `ray start --head` on the main node and `ray start --address=…` on the children.

This works, but you are hand-building the cluster lifecycle KubeRay provides, and the [compute environment constraints](https://docs.aws.amazon.com/batch/latest/userguide/mnp-ce.html) bite:

* **No Spot Instances for MNP jobs** — removes the single largest GPU cost lever, which matters against the ~$122k/month exposure tracked in [[Risks & Open Questions]].
* **One instance type per job.**
* **Requires a cluster placement group in a single Availability Zone** — which is consistent with the single-AZ placement requested at the [[2026-10-12 Research Team Kickoff]], and with what multi-node Ray training wants anyway.

### 6.4 Flyte and Batch specifically

Flyte ships [`flytekitplugins-awsbatch`](https://github.com/flyteorg/flytekit/tree/master/plugins/flytekit-aws-batch) and an [`awsbatch` propeller plugin](https://pkg.go.dev/github.com/flyteorg/flyte/flyteplugins/go/tasks/plugins/array/awsbatch), but note what they are and are not:

* It is an **array / map-task** backend that farms plain containerized tasks out to AWS Batch. **Array jobs are independent parallel tasks; MNP is gang-scheduled with inter-node communication.** The plugin does not do MNP, so it cannot produce a Ray cluster.
* It **predates AWS Batch on EKS** and targets classic ECS/EC2 compute environments.
* It is documented only on the [legacy Flyte docs site](https://docs-legacy.flyte.org/en/latest/deployment/plugins/aws/batch.html). The current Flyte integrations index lists Dask, Databricks, DBT, Spark, Ray and Slurm — **AWS Batch is no longer among them.** The code exists; the support posture has clearly changed. Treat it as legacy.

### 6.5 The honest shape of "all three together"

Flyte, Ray and Batch can share one platform, provided the division is **by task type rather than by layer**:

```
┌──────────────────────────────────────────────────────────────────────┐
│  Flyte (control plane) — routes tasks by type                        │
├────────────────────────────────────┬─────────────────────────────────┤
│  Ray tasks  →  KubeRay CRDs        │  Array tasks  →  AWS Batch      │
│  on Karpenter-scaled GPU nodes     │  on Batch-managed nodes         │
│  (zero-copy, gang-scheduled)       │  (independent containers)       │
└────────────────────────────────────┴─────────────────────────────────┘
          Ray workloads never cross into the Batch pool
```

**Recommendation for this engagement: do not add Batch.** It introduces a second scaling system, a second capacity model, and AWS lock-in that breaks the tri-environment parity §5 treats as an invariant — in exchange for managed queuing no stakeholder has requested. The [[2026-10-12 Research Team Kickoff]] in fact points the other way, calling for researchers to work *"without waiting for production-level ticketing systems or formal deployment queues."* The surrogate-training workload is the gang-scheduled multi-node kind, which is precisely what Batch cannot hand to Ray.

The one case where Batch would genuinely pay off: if mesh generation or parameter sweeps turn out to be large numbers of **independent single-container runs**. That work sits *beside* Ray, not under it.

### 6.6 Flyte vs. Argo — an open project question

Three documents now name three different orchestrators:

| Source | Orchestrator |
|---|---|
| [[Surrogate ML Accelerator - Electrification]] (2026-10-06) | Flyte |
| [[2026-10-12 Research Team Kickoff]] | **Argo** |
| This prototype (`hello-mlaas-burst`) | Flyte |

**"Argo" is ambiguous, and the two readings give opposite answers:**

* **Argo Workflows** — a genuine competitor to Flyte. Both are Kubernetes DAG engines; you would pick one.
* **Argo CD** — **not an orchestrator at all.** It is GitOps deployment tooling, and Argo CD + Flyte is a coherent pairing with no conflict to resolve.

That one-word clarification from research leadership decides whether a conflict exists. It is the cheapest open question on the register with the largest blast radius.

If it *is* Argo Workflows: Flyte offers Python-native authoring, typed interfaces and content-addressed caching, which suits researchers writing surrogate models; Argo Workflows is YAML-shaped, lighter to operate and far more common in platform teams. One caveat when reusing §2's analysis here: the "no built-in memoization cache" point is made about **AWS Batch** and does not transfer to Argo, which **does** support step-level memoization. The caching gap between Flyte and Argo is a matter of degree, not presence. Per §5 the macro orchestrator is a **swappable** part, and the `@ray.remote` functions survive the swap either way.

**Sequencing note:** the kickoff's stated priorities are shell/SSH access and the absence of deployment queues. Neither Flyte nor Argo serves that first milestone — interactive GPU access does. The orchestrator decision can wait until researchers are on the box.

---

### 6.7 Can this stack run on ECS instead of EKS?

**No.** Two of the three components are Kubernetes-native by construction, and the third would be hand-rolled.

| Component | On ECS? | Why |
|---|---|---|
| **Karpenter** | ❌ **Impossible** | It watches *unscheduled pods* through the Kubernetes API and provisions nodes that join a *Kubernetes* cluster; its entire configuration surface is CRDs (`NodePool`, `EC2NodeClass`). ECS has no pods, no Kubernetes API and no CRDs. No ECS port exists. |
| **Flyte** | ❌ **Impossible in production** | [FlytePropeller is "a Kubernetes native operator… designed as a Kubernetes Controller"](https://github.com/flyteorg/flytepropeller) — it executes workflows by creating Kubernetes resources. `pyflyte run` executes locally in-process, but that is a development loop, not a deployment substrate. |
| **Ray** | ⚠️ **Possible, unsupported** | Ray is processes over IP, so head and worker containers could run as ECS services with Cloud Map discovery. But KubeRay is the supported Kubernetes path, and there is **no ECS node provider for the Ray autoscaler** — cluster lifecycle and scaling become yours to build. |

This is the same shape as the Batch analysis in §6.1–6.2: **Ray survives as a library; the orchestration layer does not survive at all.**

**The decisive gap for this workload is gang scheduling.** Starting N tasks together as a unit, with inter-node communication, is not an ECS primitive — which is precisely why AWS Batch multi-node parallel jobs exist. Multi-node surrogate training on raw ECS means building gang scheduling yourself, or running Batch MNP on top of ECS.

> **The ECS path and the Batch path converge.** Choosing ECS for distributed training leads back to [[Alternative Architecture - AWS Batch]], which already documents the trade-offs including the EFA caveat. And as with Batch, ECS forfeits the tri-environment invariant in §5: no Mac, no KinD, no on-prem.

Adopting ECS is therefore **a different stack, not this stack relocated**: ECS Managed Instances + ECS tasks + Step Functions or MWAA, with `torchrun` for distributed training.

## 7. 📚 Authoritative Bibliography (Dual-Engine Search)

🟢 **High Relevance (Architecture & Local Execution):**
* [Hello-MLaaS.md](../../Hello-MLaaS.md) — Executive summary, empirical benchmark comparisons, and Karpenter blueprint.
* [PLAN.md](PLAN.md) — Implementation plan with Old vs. New Way benchmark data and local Docker testing tiers.
* [Resources/visualization/hello-mlaas-burst-architecture.md](../../Resources/visualization/hello-mlaas-burst-architecture.md) — Visual architecture diagram showing Flyte macro-DAG, Ray micro-compute, KinD topology, and Karpenter scaling.

🟡 **Medium Relevance (AWS Infrastructure):**
* 📦 `Resources/third_party_docs/aws/ecs-dg.md` (local-only vendor doc, not published) — Comprehensive reference manual for Amazon ECS, task definitions, and container management.
* 📦 *EKS architecture summary* (internal reference, not published) — EKS infrastructure summary detailing ALB, OIDC, Karpenter, and S3 storage.
* [.github/skills/aws-cost-optimize/SKILL.md](../../.github/skills/aws-cost-optimize/SKILL.md) — Automated audit checklist for eliminating GPU idle waste with Karpenter Spot policies.

🔵 **Related Context:**
* 📦 `Resources/third_party_docs/ray/RayV2Architecture.md` (local-only vendor doc, not published) — Technical breakdown of the Ray distributed scheduler and shared-memory object store.
* [CODE_REPOSITORIES.md](../../CODE_REPOSITORIES.md) — Index of 27 reference repositories including `flyte`, `ray`, `karpenter`, and `website`.
* [[2026-10-12 Research Team Kickoff]] — where the research team named the EKS / Ray / **Argo** stack; the source of the §6.6 orchestrator question.

🔴 **Primary Sources for §6 (AWS & Flyte documentation, verified 2026-10-12):**
* [AWS Batch on Amazon EKS](https://docs.aws.amazon.com/batch/latest/userguide/eks.html) — the overlay model, Batch-managed node lifecycle, node taints/labels, and `podspec` translation. **Source for both blockers in §6.1.**
* [Multi-node parallel jobs on Amazon EKS](https://docs.aws.amazon.com/batch/latest/userguide/mnp-eks-jobs.html) — gang scheduling, one pod per node, IP-based inter-node frameworks.
* [Compute environment considerations for MNP](https://docs.aws.amazon.com/batch/latest/userguide/mnp-ce.html) — no Spot, one instance type per job, single-AZ cluster placement group.
* [AWS Batch gang scheduling on EKS announcement (July 2024)](https://aws.amazon.com/about-aws/whats-new/2024/07/aws-batch-gang-scheduling-eks-multi-node-parallel-jobs/) — GA date for MNP on EKS.
* [`flytekitplugins-awsbatch`](https://github.com/flyteorg/flytekit/tree/master/plugins/flytekit-aws-batch) and [`awsbatch` propeller plugin](https://pkg.go.dev/github.com/flyteorg/flyte/flyteplugins/go/tasks/plugins/array/awsbatch) — the array/map-task plugin discussed in §6.4.
* [Legacy Flyte AWS Batch deployment docs](https://docs-legacy.flyte.org/en/latest/deployment/plugins/aws/batch.html) — the only remaining documentation for that plugin.
* [Karpenter best practices (Amazon EKS)](https://docs.aws.amazon.com/eks/latest/best-practices/karpenter.html) — guidance against running two autoscalers over the same capacity.
* [Amazon ECS Managed Instances](https://aws.amazon.com/ecs/managed-instances/) and [GA announcement](https://aws.amazon.com/about-aws/whats-new/2025/10/amazon-ecs-managed-instances-commercial-regions/) — the corrected §2 Layer 3 characterisation.
* [GPU batch inference on ECS Managed Instances with scale to zero](https://aws.amazon.com/blogs/containers/run-gpu-batch-inference-on-amazon-ecs-managed-instances-with-scale-to-zero/) — contradicts the previous ASG-cooldown framing.
* [FlytePropeller](https://github.com/flyteorg/flytepropeller) — "a Kubernetes native operator"; the source for §6.7's Flyte row.
