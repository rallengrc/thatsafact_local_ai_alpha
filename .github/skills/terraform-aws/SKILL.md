---
name: terraform-aws
description: "Plan, author, review, and validate Terraform Infrastructure as Code for AWS workloads with least-privilege IAM, module-first design, and secure defaults. TRIGGERS: 'terraform aws', 'aws terraform', 'plan terraform', 'iac review', 'tfplan'."
---

# AWS Terraform IaC — Planning & Implementation

> **Core Objective:** Deliver production-ready, secure, and Well-Architected AWS infrastructure using Terraform and community modules (`terraform-aws-modules`).

---

## ⚡ Workflow Dispatch Matrix

| Phase | Action | Key Verification |
|---|---|---|
| **1. Plan** | Classify workload, evaluate dependencies, and design remote state (S3 + DynamoDB) | Verify least-privilege IAM boundaries and VPC private subnet placement |
| **2. Module First** | Leverage verified modules from `terraform-aws-modules` registry | Pin explicit major/minor module versions; avoid raw boilerplate |
| **3. Harden** | Enforce S3 block public access, KMS encryption at rest, TLS in transit, and secret management | Audit for zero `0.0.0.0/0` ingress on sensitive ports and zero hardcoded tokens |
| **4. Validate** | Execute static analysis and dry-run execution | `terraform fmt -check`, `terraform validate`, `tflint`, and `terraform plan` |

---

## 🛡️ Operational Hard Gates

1. **State Protection:** Never run shared infrastructure on local state. Always define an encrypted S3 backend with DynamoDB locking.
2. **Zero Secrets in Code:** Sensitive values must originate from AWS Secrets Manager, SSM Parameter Store, or environment variables (`TF_VAR_*`).
3. **Destructive Changes:** Flag any plan destroying databases, VPCs, or buckets before execution.

---

## 📄 See Also

- 📄 [terraform-conventions-and-security.md](./references/terraform-conventions-and-security.md) — IAM patterns, S3 security blocks, and module layout.
- 📄 [terraform.instructions.md](../../instructions/terraform.instructions.md) — Auto-applying syntax and style rules for `**/*.tf` files.
- 📄 [aws-cost-optimize](../aws-cost-optimize/SKILL.md) — Companion skill for auditing spot instance and GPU resource waste.
