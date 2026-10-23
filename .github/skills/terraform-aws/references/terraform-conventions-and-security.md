---
title: "Terraform AWS Conventions & Security Reference"
description: "Detailed conventions, IAM patterns, S3 security blocks, module structures, and Well-Architected Framework alignment for AWS Terraform IaC."
shield: "internal"
last_updated: "2026-10-23"
keywords: [terraform, aws, iac, security, iam, modules, waf, remote-state]
---

# Terraform AWS Conventions & Security Reference

📄 **Instruction Hub:** `.github/instructions/terraform.instructions.md`  
📄 **Orchestrator Skill:** `.github/skills/terraform-aws/SKILL.md`

---

## 1. Remote State Backend Architecture

All AWS infrastructure must use remote state in S3 with server-side encryption and DynamoDB state locking:

```hcl
terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  backend "s3" {
    bucket         = "<state-bucket>"
    key            = "<workload>/terraform.tfstate"
    region         = "<region>"
    dynamodb_table = "<lock-table>"
    encrypt        = true
  }
}
```

---

## 2. Secure Defaults & Code Patterns

### S3 Public Access Block
```hcl
resource "aws_s3_bucket_public_access_block" "this" {
  bucket                  = aws_s3_bucket.this.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
```

### Least-Privilege IAM Policy
```hcl
resource "aws_iam_role_policy" "workload" {
  name = "${var.environment}-workload-policy"
  role = aws_iam_role.workload.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:PutObject"]
        Resource = "${aws_s3_bucket.this.arn}/*"
      }
    ]
  })
}
```

---

## 3. Standard File Structure

```
infrastructure/
├── main.tf          # Core resources and provider configuration
├── variables.tf     # Typed variables with descriptions and validation
├── outputs.tf       # Exported resource outputs
├── locals.tf        # Local computed values and common tags
├── versions.tf      # Provider version constraints
├── backend.tf       # Remote state configuration
└── modules/         # Encapsulated component modules
```

---

## 4. Pre-Commit Review Checklist

- [ ] All IAM policies avoid wildcards (`*`) and enforce resource-level ARNs.
- [ ] No plaintext credentials or secrets in code or state (Secrets Manager/SSM used).
- [ ] Stateful resources (`aws_db_instance`, `aws_s3_bucket`) have `lifecycle { prevent_destroy = true }`.
- [ ] Sensitive outputs and input variables are tagged `sensitive = true`.
- [ ] Validation suite passes: `terraform fmt -recursive && terraform validate`.
