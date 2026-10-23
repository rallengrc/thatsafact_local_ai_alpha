# Kubernetes Security Contexts, Health Probes & Validation

> **Source:** Awesome Copilot (`code/awesome-copilot/instructions/kubernetes-manifests.instructions.md`)  
> 📄 **Instruction Hub:** `.github/instructions/kubernetes-manifests.instructions.md`

---

## 1. Standard Labels & Metadata

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

## 2. Security Context Defaults (Restricted Profile)

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

## 3. Health & Liveness Probes

Configure probes to prevent routing traffic to deadlocked or initialising pods:

```yaml
livenessProbe:
  httpGet:
    path: /api/local_raylet_healthz
    port: 52365
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3

readinessProbe:
  httpGet:
    path: /api/local_raylet_healthz
    port: 52365
  initialDelaySeconds: 15
  periodSeconds: 5
  timeoutSeconds: 3
  successThreshold: 1
  failureThreshold: 2
```

---

## 2. Temporary Writable Volumes with Read-Only Root

When `readOnlyRootFilesystem: true` is enabled, mount `emptyDir` tmpfs for temporary files, caches, and IPC sockets:

```yaml
volumeMounts:
  - name: tmp-volume
    mountPath: /tmp
  - name: shm-volume
    mountPath: /dev/shm
volumes:
  - name: tmp-volume
    emptyDir: {}
  - name: shm-volume
    emptyDir:
      medium: Memory
      sizeLimit: 2Gi # Essential for Ray's shared-memory object store
```

---

## 3. Manifest Validation Commands

```bash
# Dry-run validation against active cluster
kubectl apply -f manifests/ray-cluster.yaml --dry-run=client

# Server-side validation (checks schema + API admission)
kubectl apply -f manifests/ray-cluster.yaml --dry-run=server

# Linting with kubeconform
kubeconform -strict -summary manifests/
```
