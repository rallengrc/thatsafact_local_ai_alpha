# CloudWatch Metrics & Karpenter Optimization Patterns

> **Source:** Awesome Copilot (`code/awesome-copilot/skills/aws-cost-optimize/`)

---

## 1. AWS CLI Resource Discovery Commands

```bash
# Discover GPU instances running in account
aws ec2 describe-instances \
  --filters "Name=instance-type,Values=g4dn.*,g5.*,p3.*,p4d.*" "Name=instance-state-name,Values=running" \
  --query "Reservations[].Instances[].[InstanceId,InstanceType,LaunchTime,Tags[?Key=='Name'].Value|[0]]" \
  --output table

# Identify unattached EBS volumes (wasted storage spend)
aws ec2 describe-volumes \
  --filters "Name=status,Values=available" \
  --query "Volumes[].[VolumeId,Size,VolumeType,CreateTime]" \
  --output table

# Query CloudWatch GPU utilization (CloudWatch agent namespace)
aws cloudwatch get-metric-statistics \
  --namespace "CWAgent" \
  --metric-name "utilization_gpu" \
  --dimensions Name=InstanceId,Value=<INSTANCE_ID> \
  --start-time $(date -u -v-7d +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 3600 \
  --statistics Average Maximum
```

---

## 2. Karpenter Just-in-Time Spot NodePool Pattern

To eliminate idle GPU billing, Karpenter spins up spot GPU nodes on demand and terminates them immediately after batch execution:

```yaml
apiVersion: karpenter.sh/v1beta1
kind: NodePool
metadata:
  name: gpu-burst-spot
spec:
  template:
    spec:
      requirements:
        - key: "karpenter.sh/capacity-type"
          operator: In
          values: ["spot"]
        - key: "node.kubernetes.io/instance-type"
          operator: In
          values: ["g5.xlarge", "g5.2xlarge", "g4dn.xlarge"]
      nodeClassRef:
        name: default-gpu
  disruption:
    consolidationPolicy: WhenEmpty
    consolidateAfter: 30s # Terminate 30 seconds after Ray worker completes
```
