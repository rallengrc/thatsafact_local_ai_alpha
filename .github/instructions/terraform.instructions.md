---
description: 'Terraform IaC standards: AWS provider conventions, least-privilege IAM, remote state, security hardening, and validation.'
applyTo: '**/*.tf, **/*.tfvars'
---

# Terraform IaC Standards (Auto-Apply)

> **Execution:** Validate with `terraform fmt -check`, `terraform validate`, and `tflint`.

1. **Security & Least Privilege:** Enforce least-privilege IAM (no wildcards `*`), enable S3 public access blocks, require encryption at rest (KMS) and in transit (TLS), and deploy workloads in private subnets.
2. **Secrets & State Management:** Never hardcode secrets or commit state. Use AWS Secrets Manager/SSM and mark variables `sensitive = true`. Store remote state in S3 with DynamoDB locking.
3. **Module-First Architecture:** Prefer standard `terraform-aws-modules` over raw resources. Avoid deep nesting; maintain clean `main.tf`, `variables.tf`, `outputs.tf`, `locals.tf`, and `versions.tf`.
4. **Ordering & Formatting:** Place `depends_on` first, followed by `for_each`/`count`, resource attributes, and `lifecycle` blocks last. Use 2-space indentation.
5. **Testing & Validation:** Write tests using `.tftest.hcl` and verify configurations with `terraform plan`.

📄 **See Also:** [.github/skills/terraform-aws/references/terraform-conventions-and-security.md](../skills/terraform-aws/references/terraform-conventions-and-security.md) for full WAF alignment, checklists, and code templates.