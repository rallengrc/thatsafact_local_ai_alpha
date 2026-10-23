#!/usr/bin/env python3
"""Add AI-searchable YAML frontmatter to the AWS reference .md files produced by
scripts/automation/pdf_to_md.py (which emits only a # Title + Source/Generated block).

Inserts a compliant frontmatter block (per AI-SEARCHABLE-DOC-TEMPLATE.md) at the
top of each target file and adds a TL;DR / Use-this-for pair, matching the
existing AmazonBedrock_UserGuide.md and next-generation-sagemaker-ug.md.

Idempotent: skips files that already begin with '---\ntitle:'.
"""
import datetime
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
AWS = ROOT / "Resources" / "third_party_docs" / "aws"
DATE = datetime.datetime.now().strftime("%Y-%m-%d")

# Per-file frontmatter. keys match the produced .md basenames.
META = {
    "amazon-eks-observability-best-practices": {
        "title": "Amazon EKS Observability Best Practices",
        "desc": "Reference for instrumenting and monitoring Amazon EKS clusters with CloudWatch, Prometheus, and Fluent Bit for AI/ML workloads.",
        "keywords": ["Amazon EKS", "AWS", "observability", "monitoring", "Prometheus", "CloudWatch", "Fluent Bit", "Grafana"],
        "aliases": ["eks observability", "eks monitoring", "aws eks metrics"],
    },
    "AmazonEksEksctlDocs": {
        "title": "Amazon EKS & eksctl Documentation",
        "desc": "Reference for provisioning and managing Amazon EKS clusters with eksctl, including node groups, IAM, and add-ons.",
        "keywords": ["Amazon EKS", "eksctl", "AWS", "Kubernetes", "cluster", "node group", "IAM"],
        "aliases": ["eksctl docs", "eks reference", "aws eks kubernetes"],
    },
    "Amazon SageMaker": {
        "title": "Amazon SageMaker User Guide",
        "desc": "Comprehensive Amazon SageMaker reference covering training jobs, HyperPod, model deployment, and MLOps pipelines.",
        "keywords": ["Amazon SageMaker", "AWS", "HyperPod", "ML training", "MLOps", "model serving", "GPU"],
        "aliases": ["sagemaker guide", "aws sagemaker", "hyperpod"],
    },
    "bedrock-api": {
        "title": "Amazon Bedrock API Reference",
        "desc": "Complete Amazon Bedrock API reference covering foundation model invocation, guardrails, knowledge bases, and agents.",
        "keywords": ["Amazon Bedrock", "AWS", "API reference", "foundation models", "guardrails", "agents", "knowledge bases"],
        "aliases": ["bedrock api", "bedrock reference", "aws bedrock invoke"],
    },
    "ecs-dg": {
        "title": "Amazon ECS Developer Guide",
        "desc": "Reference for building, deploying, and operating container workloads on Amazon Elastic Container Service (ECS).",
        "keywords": ["Amazon ECS", "AWS", "containers", "Fargate", "task definition", "service", "orchestration"],
        "aliases": ["ecs developer guide", "ecs reference", "aws ecs fargate"],
    },
    "eks-ug": {
        "title": "Amazon EKS User Guide",
        "desc": "Comprehensive Amazon EKS user guide covering cluster setup, node groups, add-ons, autoscaling, and GPU workloads.",
        "keywords": ["Amazon EKS", "AWS", "Kubernetes", "cluster", "node group", "autoscaling", "GPU", "add-ons"],
        "aliases": ["eks user guide", "aws eks", "kubernetes on aws"],
    },
}


def build_fm(meta: dict) -> str:
    def block(title):
        return "\n".join(f"- {k}" for k in title)
    lines = [
        "---",
        f"title: {meta['title']}",
        f"description: {meta['desc']}",
        "keywords:",
        block(meta["keywords"]),
        "category: reference",
        "classification: \U0001F7E2\U0001F6E1️ General",
        f"last_updated: '{DATE}'",
        "author: thatsafact",
        "ai_search_aliases:",
        block(meta["aliases"]),
        "---",
        "",
        f"# {meta['title']}",
        "",
        f"> **TL;DR:** {meta['desc']}",
        f"> **Use this for:** Reference lookup across the {meta['title']}.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    for base, meta in META.items():
        md = AWS / f"{base}.md"
        if not md.exists():
            print(f"SKIP (missing): {base}.md")
            continue
        text = md.read_text(encoding="utf-8")
        if text.startswith("---\ntitle:"):
            print(f"SKIP (has frontmatter): {base}.md")
            continue
        # Drop the bare "# stem" heading the script emitted, keep the rest.
        lines = text.split("\n")
        if lines and lines[0].startswith("# "):
            lines = lines[1:]
        # collapse leading blank lines
        while lines and not lines[0].strip():
            lines.pop(0)
        fm = build_fm(meta)
        md.write_text(fm + "\n".join(lines) + "\n", encoding="utf-8")
        print(f"WROTE frontmatter: {base}.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
