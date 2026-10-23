---
applyTo: 'k8s/**/*.yaml,k8s/**/*.yml,manifests/**/*.yaml,manifests/**/*.yml,deploy/**/*.yaml,deploy/**/*.yml,Projects/**/*.yaml'
description: 'Production standards for Kubernetes manifests: recommended labels, non-root security contexts, resource requests/limits, and health probes.'
---

# Kubernetes Manifests — Production Standards

> **TL;DR:** Production-grade standards for Kubernetes manifests across KinD, KubeRay, and AWS EKS.

1. **Standard Labels:** Manifests must include `app.kubernetes.io/name`, `instance`, `component`, `part-of`, and `managed-by`.
2. **Security Contexts (Restricted):** Never run containers as root. Enforce `runAsNonRoot: true`, `readOnlyRootFilesystem: true`, `allowPrivilegeEscalation: false`, drop all capabilities, and use `RuntimeDefault` seccomp.
3. **QoS Resource Requests & Limits:** Always specify both `requests` and `limits` for CPU (millicores) and Memory (Mi/Gi). For GPU (`nvidia.com/gpu`), requests must equal limits.
4. **Probes & Writable Volumes:** Provide liveness/readiness probes and mount `emptyDir` tmpfs (`/tmp`, `/dev/shm`) when using read-only root filesystems.

📄 **See Also:** [kubernetes-security-and-probes.md](references/kubernetes-security-and-probes.md) for full YAML snippets, probe examples, and validation commands.
