---
title: Sub-Repositories in code/ Index
description: Catalog of 34 cloned external open-source sub-repositories in code/ used for reference and indexing
keywords:
- code repositories
- sub-repos
- Flyte
- Ray
- Tantivy
- MCP
- Kubernetes
- Karpenter
- KubeRay
- git clones
- reference
category: index
classification: 🟢🛡️ General
last_updated: '2026-10-18'
author: thatsafact
ai_search_aliases:
- code repos
- external repositories
- submodules
- cloned repos in code
---

# Sub-Repositories in `code/`

> **TL;DR:** Comprehensive directory of 34 external reference repositories stored under `code/`, covering Flyte orchestration, Ray distributed compute, KubeRay Kubernetes operators, Karpenter autoscaling, Tantivy search, MCP implementations, Kubernetes documentation, local LLM runtimes (Ollama), plasma-physics simulation (EPOCH), and temporal contact-network analysis (Tacoma).
> **Use this for:** Discovering and locating cloned open-source reference codebases in the workspace.

The `code/` directory is git-ignored and is **not published** with this repository. It holds local clones of the external open-source repositories listed below, used for reference, indexing, and architecture research. Each heading links to the upstream project; the `Remote` line is the clone URL. Each project carries its own license.

---

## Repositories

### 1. [awesome-copilot](https://github.com/github/awesome-copilot)
* **Remote**: `git@github.com:github/awesome-copilot.git`
* **Description**: A curated community collection maintained by GitHub containing custom agents, instructions, skills, hooks, workflows, and extension patterns for GitHub Copilot and Copilot CLI.

### 2. [boilerplate](https://github.com/flyteorg/boilerplate)
* **Remote**: `git@github.com:flyteorg/boilerplate.git`
* **Description**: Shared CI/CD configurations, linting suites, image builds, and development conventions reused across Flyte repositories.

### 3. [flyte](https://github.com/flyteorg/flyte)
* **Remote**: `git@github.com:flyteorg/flyte.git`
* **Description**: Core monorepo for Flyte (v2 & v1), a Kubernetes-native, production-grade workflow automation platform for distributed machine learning and data processing pipelines.

### 4. [flyte-agent-plugins](https://github.com/flyteorg/flyte-agent-plugins)
* **Remote**: `git@github.com:flyteorg/flyte-agent-plugins.git`
* **Description**: A plugin marketplace for working with Flyte across AI coding agents and harnesses, including Claude Code, OpenAI Codex, and Google Antigravity.

### 5. [flyte-benchmarks](https://github.com/flyteorg/flyte-benchmarks)
* **Remote**: `git@github.com:flyteorg/flyte-benchmarks.git`
* **Description**: Reproducible Flyte scaling benchmark suite comparing Flyte v1, Flyte v2 (OSS), and Union on workloads with wall-clock, peak memory, and OOM metrics.

### 6. [flyte-pyodide-test](https://github.com/flyteorg/flyte-pyodide-test)
* **Remote**: `git@github.com:flyteorg/flyte-pyodide-test.git`
* **Description**: Headless local reproduction harness for verifying `flyte-sdk` package installation and runtime imports in Pyodide via Node.js.

### 7. [flyte-sdk-go](https://github.com/flyteorg/flyte-sdk-go)
* **Remote**: `git@github.com:flyteorg/flyte-sdk-go.git`
* **Description**: Flyte Go SDK for launching, monitoring, and authoring tasks and workflows in Go with control-plane parity to the Python SDK.

### 8. [flyte-vscode-demo](https://github.com/flyteorg/flyte-vscode-demo)
* **Remote**: `git@github.com:flyteorg/flyte-vscode-demo.git`
* **Description**: Demonstration workspace for the Flyte VS Code extension, featuring sample ML training workflows, migration steps, and interactive Jupyter notebook walkthroughs.

### 9. [flyteconsole](https://github.com/flyteorg/flyteconsole)
* **Remote**: `git@github.com:flyteorg/flyteconsole.git`
* **Description**: Web-based user interface and management dashboard for the Flyte platform to visualize execution graphs, inspect node outputs, and manage schedules.

### 10. [flytectl](https://github.com/flyteorg/flytectl)
* **Remote**: `git@github.com:flyteorg/flytectl.git`
* **Description**: Official command-line tool (CLI) for Flyte, providing cluster administration, project/domain management, and workflow execution control (now developed in the flyte monorepo).

### 11. [flytekit](https://github.com/flyteorg/flytekit)
* **Remote**: `git@github.com:flyteorg/flytekit.git`
* **Description**: Python SDK for Flyte, enabling type-annotated task/workflow authoring, dynamic DAGs, and integrations with ML frameworks (PyTorch, TensorFlow, Spark, Ray).

### 12. [flytekit-java](https://github.com/flyteorg/flytekit-java)
* **Remote**: `git@github.com:flyteorg/flytekit-java.git`
* **Description**: Java and Scala SDK for Flyte (archived), providing language bindings and workflow definitions for JVM-based data pipelines.

### 13. [flytekit-python-template](https://github.com/flyteorg/flytekit-python-template)
* **Remote**: `git@github.com:flyteorg/flytekit-python-template.git`
* **Description**: Cookiecutter project templates for scaffolding new Flyte projects with pre-configured container images, dependencies, and sample workflows.

### 14. [flyteorg.github.io](https://github.com/flyteorg/flyteorg.github.io)
* **Remote**: `git@github.com:flyteorg/flyteorg.github.io.git`
* **Description**: Source code repository for the official Flyte community website (flyte.org) and portal.

### 15. [flytesnacks](https://github.com/flyteorg/flytesnacks)
* **Remote**: `git@github.com:flyteorg/flytesnacks.git`
* **Description**: Official tutorials, code examples, and integration patterns demonstrating Flyte capabilities across machine learning, data engineering, and MLOps.

### 16. [flytetools](https://github.com/flyteorg/flytetools)
* **Remote**: `git@github.com:flyteorg/flytetools.git`
* **Description**: Miscellaneous utilities and build tools for Flyte contributors, including Swagger client code generation for Flyte IDL gRPC services.

### 17. [graphify](https://github.com/Graphify-Labs/graphify)
* **Remote**: `git@github.com:Graphify-Labs/graphify.git`
* **Description**: Knowledge graph extraction engine converting codebases, documentation, and multimodal assets into queryable AST graphs (via tree-sitter) for AI coding assistants.

### 18. [ray](https://github.com/ray-project/ray)
* **Remote**: `git@github.com:ray-project/ray.git`
* **Description**: An open-source unified compute framework for scaling AI and Python workloads, including distributed training, hyperparameter tuning, model serving (Ray Serve), and data processing (Ray Data).

### 19. [servers](https://github.com/modelcontextprotocol/servers)
* **Remote**: `git@github.com:modelcontextprotocol/servers.git`
* **Description**: Official reference implementations of Model Context Protocol (MCP) servers maintained by the MCP steering committee, showcasing stdio and SSE server patterns, tool integrations, and protocol features.

### 20. [static-resources](https://github.com/flyteorg/static-resources)
* **Remote**: `git@github.com:flyteorg/static-resources.git`
* **Description**: Central image and asset repository housing logos, diagrams, and brand graphics for Flyte ecosystem projects.

### 21. [superpowers](https://github.com/obra/superpowers)
* **Remote**: `git@github.com:obra/superpowers.git`
* **Description**: Software development methodology and composable skill framework designed for coding agents to enforce disciplined planning, testing, and implementation.

### 22. [tantivy](https://github.com/quickwit-oss/tantivy)
* **Remote**: `git@github.com:quickwit-oss/tantivy.git`
* **Description**: High-performance, full-text search engine library written in Rust, strongly inspired by Apache Lucene and powering search engines like Quickwit.

### 23. [tantivy-cli](https://github.com/quickwit-oss/tantivy-cli)
* **Remote**: `git@github.com:quickwit-oss/tantivy-cli.git`
* **Description**: Command-line interface for the Tantivy search engine library, supporting index creation, document indexing, and command-line querying.

### 24. [tantivy-py](https://github.com/quickwit-oss/tantivy-py)
* **Remote**: `git@github.com:quickwit-oss/tantivy-py.git`
* **Description**: Python bindings for the Tantivy search engine library, providing native access to Tantivy schema definition, indexing, and search from Python.

### 25. [unionai-docs](https://github.com/unionai/unionai-docs)
* **Remote**: `git@github.com:unionai/unionai-docs.git`
* **Description**: Source documentation for the Flyte open-source workflow orchestration platform and Union.ai enterprise products (covers BYOC and self-managed deployments, distributed tasks, and pipelines).

### 26. [website](https://github.com/kubernetes/website)
* **Remote**: `git@github.com:kubernetes/website.git`
* **Description**: Official documentation and source for the Kubernetes website (kubernetes.io), including architecture guides, API references, cluster administration patterns, and workload specifications for container orchestration.

### 27. [karpenter](https://github.com/kubernetes-sigs/karpenter)
* **Remote**: `git@github.com:kubernetes-sigs/karpenter.git`
* **Description**: Kubernetes-native, just-in-time node auto-provisioning and dynamic consolidation engine (CNCF / SIGs). Bypasses static AWS Auto Scaling Groups (ASGs) to launch right-sized EC2 compute and GPU instances directly in response to unschedulable pod resource requirements and scales to zero when jobs finish.

### 28. [epoch](https://github.com/epochpic/epoch)
* **Remote**: `git@github.com:epochpic/epoch.git`
* **Description**: Open-source space plasma-physics simulation code with 1D, 2D, and 3D variants (`epoch1d`, `epoch2d`, `epoch3d`) for modeling electromagnetic wave–particle interactions in magnetized plasmas (Warwick Plasma group); uses an SDF subdirectory for writing simulation data and is compiled from per-variant Makefiles.

### 29. [ollama](https://github.com/ollama/ollama)
* **Remote**: `git@github.com:ollama/ollama.git`
* **Description**: Open-source runtime for building with and running local large language models; provides a cross-platform tool (macOS, Linux, Windows, and Docker) to download, run, and manage open models locally.

### 30. [tacoma](https://github.com/benmaier/tacoma)
* **Remote**: `git@github.com:benmaier/tacoma.git`
* **Description**: TemporAl COntact Modeling and Analysis (Tacoma): a joint C++/Python package for modeling and analyzing undirected, unweighted temporal contact networks, producing surrogate networks from qualitative models, and simulating Gillespie (e.g., epidemic-spreading) processes on them.

### 31. [big_model_radar](https://github.com/bkutasi/big_model_radar)
* **Remote**: `git@github.com:bkutasi/big_model_radar.git`
* **Description**: Automated AI radar tracking GitHub activity from AI CLI tools, OpenClaw, Anthropic, and OpenAI research, generating bilingual (English/Chinese) digests and trending repo rollups.

### 32. [enhancements](https://github.com/ray-project/enhancements)
* **Remote**: `git@github.com:ray-project/enhancements.git`
* **Description**: Official Ray Enhancement Proposals (REPs) repository documenting design proposals, architectural evolutions, and consensus decisions for the Ray distributed computing framework.

### 33. [flyte-sdk](https://github.com/flyteorg/flyte-sdk)
* **Remote**: `git@github.com:flyteorg/flyte-sdk.git`
* **Description**: Official Next-Generation Flyte 2 Python SDK for durable execution, local devbox workflows, and Apple Silicon/GPU-accelerated ML task orchestration.

### 34. [kuberay](https://github.com/ray-project/kuberay)
* **Remote**: `git@github.com:ray-project/kuberay.git`
* **Description**: Kubernetes operator for Ray, managing CRDs (`RayCluster`, `RayJob`, `RayService`) for distributed training, Ray Serve deployments, and autoscaling across KinD, EKS, and on-premises clusters.

