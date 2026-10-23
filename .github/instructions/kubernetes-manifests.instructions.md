---
applyTo: 'k8s/**/*.yaml,k8s/**/*.yml,manifests/**/*.yaml,manifests/**/*.yml,deploy/**/*.yaml,deploy/**/*.yml,Projects/**/*.yaml'
description: 'Production standards for Kubernetes manifests: recommended labels, non-root security contexts, resource requests/limits, and health probes.'
---

# Kubernetes Manifests — Production Standards

> **TL;DR:** Production-grade standards for Kubernetes manifests across KinD, KubeRay, and AWS EKS. Dispatches to references for detailed specs.

---

## Standard Labeling Schema

All manifests MUST include standard Kubernetes labels:

```yaml
metadata:
  labels:
    app.kubernetes.io/name: "ray-cluster"
    app.kubernetes.io/instance: "mlaas-burst-ray"
    app.kubernetes.io/component: "worker" # head, worker, or controller
    app.kubernetes.io/part-of: "mlaas-pipeline"
    app.kubernetes.io/managed-by: "kuberay-operator"
```

---

## Security Context Defaults (Restricted Profile)

Never run containers as root or allow privilege escalation:

```yaml
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    runAsGroup: 1000
    fsGroup: 1000
    seccompProfile:
      type: RuntimeDefault
  containers:
    - name: worker
      securityContext:
        allowPrivilegeEscalation: false
        readOnlyRootFilesystem: true
        capabilities:
          drop: ["ALL"]
```

---

## Resource Requests & Limits

Always specify both requests and limits to establish clean QoS classes:
- **CPU:** Specify in millicores (e.g. `requests: 500m`, `limits: 2000m`).
- **Memory:** Specify in Mi/Gi (e.g. `requests: 2Gi`, `limits: 4Gi`).
- **GPU:** Integer units (e.g. `nvidia.com/gpu: 1`). Note: requests must equal limits for GPUs.

---

## References

- 📄 [Kubernetes Security & Probes Reference](references/kubernetes-security-and-probes.md) — Liveness/readiness probes, volume mounts, and validation commands.
- **Source:** `code/awesome-copilot/instructions/kubernetes-manifests.instructions.md`
