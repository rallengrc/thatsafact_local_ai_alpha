---
title: "Hello MLaaS Burst Architecture Diagram"
description: "Architecture diagram showing Flyte macro-orchestration, Ray micro-compute, 4-node KinD topology, and Karpenter burst scaling"
keywords: [hello mlaas, burstable gpu, flyte, ray, kind, karpenter, kubeway, architecture diagram]
category: reference
classification: 🟢🛡️ General
last_updated: "2026-10-11"
author: thatsafact
related:
  - ../../Hello-MLaaS.md
  - ../../Projects/hello-mlaas-burst/PLAN.md
---

# Hello MLaaS Burst Architecture Diagram

> **TL;DR:** Visual architectural representation of the Hello MLaaS Burst pipeline: Flyte macro-DAG workflow (`generate_mesh_data` → `train_surrogate_burst` → `evaluate_surrogate`), Ray micro-distributed compute, and Tri-Environment target execution (Local Mac 4-node KinD, AWS EKS GPU burst, and On-Prem Firewall VMs).

## 🖼️ Diagram Preview

![Hello MLaaS Burst Architecture](hello-mlaas-burst-architecture.png)

## 📋 Diagram Source Files

- **PlantUML Specification:** [hello-mlaas-burst-architecture.puml](./hello-mlaas-burst-architecture.puml)
- **Rendered PNG:** [hello-mlaas-burst-architecture.png](./hello-mlaas-burst-architecture.png)
- **Mermaid Specification:** [hello-mlaas-burst-architecture.mmd](./hello-mlaas-burst-architecture.mmd)
