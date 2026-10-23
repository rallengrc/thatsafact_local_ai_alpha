#!/usr/bin/env python3
"""
ingest_aws_ray_blogs.py — Ingest AWS blog posts covering Ray & KubeRay architectures
into Diamond-compliant Markdown files with locally embedded image assets.
"""

import os
import re
import tempfile
import urllib.request
from html.parser import HTMLParser
from urllib.parse import urlparse, unquote, quote

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TARGET_DIR = os.path.join(REPO_ROOT, "Resources", "third_party_docs", "aws")

DOCS = [
    {
        "slug": "building-reliable-scalable-genai-infrastructure-aws-ray-anyscale",
        "url": "https://aws.amazon.com/blogs/apn/building-reliable-and-scalable-generative-ai-infrastructure-on-aws-with-ray-and-anyscale/",
        "title": "Building Reliable and Scalable Generative AI Infrastructure on AWS with Ray and Anyscale",
        "desc": "Architectural guide for deploying Ray and Anyscale on AWS with EKS, KubeRay, Trainium, and Inferentia2.",
        "keywords": ["Ray", "Anyscale", "AWS", "EKS", "KubeRay", "Generative AI", "Trainium", "Inferentia2", "Ray Serve"],
        "date": "2023-12-06",
        "authors": "Phi Nguyen (Anyscale), Vedant Jain (AWS)",
        "aliases": ["ray anyscale aws", "kuberay genai infrastructure", "ray trainium inferentia"],
        "tldr": [
            "Comprehensive architectural overview of deploying Ray and Anyscale on AWS for Generative AI workloads.",
            "Details self-managed deployments on EC2 and Amazon EKS using the KubeRay operator.",
            "Explores distributed LLM training partitioning strategies (inter-operator, intra-operator, and hybrid tensor parallelism).",
            "Highlights Ray Serve integration with AWS Trainium (trn1) and Inferentia2 (inf2) accelerators for cost-effective inference."
        ],
        "use_for": "Architecting resilient generative AI clusters on AWS with Ray, EKS, KubeRay, and specialized silicon."
    },
    {
        "slug": "how-vannevar-labs-cut-ml-inference-costs-45-percent-ray-eks",
        "url": "https://aws.amazon.com/blogs/containers/how-vannevar-labs-cut-ml-inference-costs-by-45-using-ray-on-amazon-eks/",
        "title": "How Vannevar Labs Cut ML Inference Costs by 45% Using Ray on Amazon EKS",
        "desc": "Case study of Vannevar Labs cutting inference costs by 45% using KubeRay and Karpenter on Amazon EKS.",
        "keywords": ["Ray", "Amazon EKS", "KubeRay", "Karpenter", "Ray Serve", "cost optimization", "autoscaling", "inference"],
        "date": "2024-11-20",
        "authors": "Sabari Sawant (AWS)",
        "aliases": ["vannevar labs ray eks", "kuberay karpenter cost optimization", "ray serve eks"],
        "tldr": [
            "Case study of Vannevar Labs optimizing multi-model production inference on Amazon EKS using KubeRay and Ray Serve.",
            "Details dynamic autoscaling and cluster management using Karpenter alongside the KubeRay operator.",
            "Demonstrates specialized container image architecture that reduced incoming container traffic and cold start times.",
            "Slashed ML inference compute costs by 45% while managing variable 24-hour CPU/GPU traffic fluctuations."
        ],
        "use_for": "Designing cost-optimized, autoscaling Ray Serve deployments on EKS with Karpenter and specialized images."
    },
    {
        "slug": "introducing-new-ray-capabilities-sagemaker-hyperpod",
        "url": "https://aws.amazon.com/blogs/machine-learning/introducing-new-ray-capabilities-on-sagemaker-hyperpod/",
        "title": "Introducing New Ray Capabilities on SageMaker HyperPod",
        "desc": "Technical guide on native Ray cluster lifecycle management, remote endpoints, and Grafana monitoring on HyperPod.",
        "keywords": ["Ray", "SageMaker HyperPod", "Amazon SageMaker", "distributed compute", "JupyterLab", "Amazon Managed Grafana"],
        "date": "2026-08-24",
        "authors": "Nilesh PS, Shreyas Adiyodi, Vishal Shahane (AWS)",
        "aliases": ["ray on hyperpod", "sagemaker hyperpod ray", "hyperpod ray clusters"],
        "tldr": [
            "Announces and details native Ray cluster lifecycle management on Amazon SageMaker HyperPod.",
            "Demonstrates creating and configuring Ray clusters with remote endpoints via SageMaker Studio.",
            "Explains attaching Ray clusters directly to HyperPod workspaces and JupyterLab notebooks for interactive distributed compute.",
            "Details centralized cluster monitoring and telemetry integration with Amazon Managed Grafana."
        ],
        "use_for": "Configuring and operating managed Ray clusters within SageMaker HyperPod environments."
    },
    {
        "slug": "scaling-ai-ml-workloads-ray-aws",
        "url": "https://aws.amazon.com/blogs/opensource/scaling-ai-and-machine-learning-workloads-with-ray-on-aws/",
        "title": "Scaling AI and Machine Learning Workloads with Ray on AWS",
        "desc": "Foundation guide for deploying distributed Ray clusters across Amazon EKS, EC2, and SageMaker with MLflow.",
        "keywords": ["Ray", "Amazon EKS", "Amazon EC2", "SageMaker", "KubeRay", "MLflow", "Grafana", "distributed training"],
        "date": "2022-08-26",
        "authors": "Chris Fregly, Antje Barth, Daniel Yeo, Apoorva Kulkarni, Patrick Ames, Simon Zamarin, Yiqin Zhu (AWS)",
        "aliases": ["scaling ray aws", "kuberay aws foundation", "ray mlflow sagemaker"],
        "tldr": [
            "Foundational reference for running distributed Ray clusters across Amazon EKS, EC2, and Amazon SageMaker.",
            "Details KubeRay operator integration on EKS for managing Ray cluster and worker pod lifecycles.",
            "Covers observability, metrics export, and cluster monitoring using Ray Dashboard and Grafana.",
            "Integrates distributed training, hyperparameter tuning, and model tracking with MLflow and Ray Train."
        ],
        "use_for": "Implementing production Ray cluster deployments, monitoring setups, and tracking pipelines on AWS."
    },
    {
        "slug": "run-multi-node-inference-ray-llm-deep-learning-containers",
        "url": "https://aws.amazon.com/blogs/machine-learning/run-multi-node-inference-workloads-using-ray-llm-deep-learning-containers/",
        "title": "Run Multi-Node Inference Workloads Using Ray LLM Deep Learning Containers",
        "desc": "Architectural guide for multi-node LLM serving with AWS Deep Learning Containers and KubeRay on Amazon EKS.",
        "keywords": ["Ray", "LLM", "Deep Learning Containers", "DLC", "Amazon EKS", "KubeRay", "multi-node inference", "vLLM"],
        "date": "2026-10-12",
        "authors": "Ananth Raghavendra, Felipe Lopez, Jinyan Li (AWS)",
        "aliases": ["multi-node inference ray", "ray dlc inference", "kuberay disaggregated prefill decode"],
        "tldr": [
            "Comprehensive guide on executing distributed, multi-node LLM inference using AWS Deep Learning Containers (DLCs) and Ray.",
            "Details disaggregated prefill and decode phase architecture on Amazon EKS with GPU worker nodes.",
            "Provides KubeRay RayCluster custom resource manifests and vLLM / TensorRT-LLM container configurations.",
            "Covers multi-node networking, NCCL inter-node communications, and high-throughput serving endpoints."
        ],
        "use_for": "Deploying multi-node, disaggregated LLM serving architectures on EKS using official AWS DLCs."
    }
]


class AWSBlogParser(HTMLParser):
    def __init__(self, asset_dir: str, rel_asset_path: str):
        super().__init__()
        self.asset_dir = asset_dir
        self.rel_asset_path = rel_asset_path
        self.md_lines: list[str] = []
        self.tag_stack: list[tuple[str, dict]] = []
        self.list_depth = 0
        self.in_pre = False
        self.code_lang = ""
        self.in_table = False
        self.table_row: list[str] = []
        self.table_headers: list[str] = []
        self.table_rows: list[list[str]] = []
        self.is_header_cell = False
        self.current_cell: list[str] = []
        self.image_idx = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]):
        attrs_dict = dict(attrs)
        self.tag_stack.append((tag, attrs_dict))

        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            level = int(tag[1])
            self.md_lines.append("\n\n" + "#" * level + " ")
        elif tag == "p":
            if not self.in_pre and not self.in_table:
                self.md_lines.append("\n\n")
        elif tag in ("ul", "ol"):
            self.list_depth += 1
            self.md_lines.append("\n")
        elif tag == "li":
            indent = "  " * max(0, self.list_depth - 1)
            self.md_lines.append(f"\n{indent}* ")
        elif tag == "pre":
            self.in_pre = True
            # inspect code child class if any
            self.code_lang = ""
            self.md_lines.append("\n\n```")
        elif tag == "code":
            if self.in_pre:
                cls = attrs_dict.get("class", "")
                m = re.search(r"language-(\w+)", cls)
                if m:
                    self.code_lang = m.group(1)
                    # replace the bare ``` with ```<lang>
                    if self.md_lines and self.md_lines[-1] == "\n\n```":
                        self.md_lines[-1] = f"\n\n```{self.code_lang}\n"
            else:
                self.md_lines.append("`")
        elif tag == "blockquote":
            self.md_lines.append("\n\n> ")
        elif tag in ("strong", "b"):
            self.md_lines.append("**")
        elif tag in ("em", "i"):
            self.md_lines.append("*")
        elif tag == "a":
            self.md_lines.append("[")
        elif tag == "table":
            self.in_table = True
            self.table_headers = []
            self.table_rows = []
        elif tag == "tr":
            self.table_row = []
        elif tag == "th":
            self.is_header_cell = True
            self.current_cell = []
        elif tag == "td":
            self.is_header_cell = False
            self.current_cell = []
        elif tag == "hr":
            self.md_lines.append("\n\n---\n\n")
        elif tag == "img":
            src = attrs_dict.get("src") or attrs_dict.get("data-src") or ""
            alt = attrs_dict.get("alt", "").strip()
            # skip social icons, badges, small buttons, and tracking pixels
            skip_patterns = ["facebook", "twitter", "linkedin", "instagram", "youtube", "twitch", "email", "ccpa", "opt-out", "icon", "share", "button"]
            if src and not any(p in src.lower() for p in skip_patterns):
                # skip author headshots
                if any(x in src.lower() for x in ["headshot", "fregly", "antje_barth", "dyeo", "kulkarni", "ames", "zamarin", "zhu", "nilesh", "vishal", "shreyas", "ananth", "jinyan", "felipe"]):
                    return
                self.image_idx += 1
                parsed = urlparse(src)
                orig_name = os.path.basename(parsed.path)
                if not orig_name or len(orig_name) > 60:
                    ext = ".png" if ".png" in src else ".jpg"
                    orig_name = f"image_{self.image_idx}{ext}"
                orig_name = re.sub(r"[^\w\-.]", "_", orig_name)
                target_path = os.path.join(self.asset_dir, orig_name)
                
                try:
                    parsed_src = urlparse(src)
                    safe_path = quote(unquote(parsed_src.path))
                    safe_url = parsed_src._replace(path=safe_path).geturl()
                    req = urllib.request.Request(safe_url, headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(req, timeout=15) as r, open(target_path, "wb") as f_out:
                        f_out.write(r.read())
                    rel_link = f"./{self.rel_asset_path}/{orig_name}"
                    alt_display = alt or f"Figure {self.image_idx}"
                    self.md_lines.append(f"\n\n![{alt_display}]({rel_link})\n\n")
                    print(f"    Saved image: {orig_name}")
                except Exception as e:
                    print(f"    Warning: Failed to fetch image {src}: {e}")

    def handle_endtag(self, tag: str):
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.md_lines.append("\n\n")
        elif tag in ("ul", "ol"):
            self.list_depth = max(0, self.list_depth - 1)
            self.md_lines.append("\n")
        elif tag == "pre":
            self.in_pre = False
            self.md_lines.append("\n```\n\n")
        elif tag == "code":
            if not self.in_pre:
                self.md_lines.append("`")
        elif tag in ("strong", "b"):
            self.md_lines.append("**")
        elif tag in ("em", "i"):
            self.md_lines.append("*")
        elif tag == "a":
            href = ""
            for t, attrs in reversed(self.tag_stack):
                if t == "a":
                    href = attrs.get("href", "")
                    break
            self.md_lines.append(f"]({href})")
        elif tag == "th":
            cell_txt = "".join(self.current_cell).strip().replace("\n", " ")
            self.table_headers.append(cell_txt)
        elif tag == "td":
            cell_txt = "".join(self.current_cell).strip().replace("\n", " ")
            self.table_row.append(cell_txt)
        elif tag == "tr":
            if self.table_row:
                self.table_rows.append(self.table_row)
        elif tag == "table":
            self.in_table = False
            if self.table_headers or self.table_rows:
                # render markdown table
                cols = max(len(self.table_headers), max((len(r) for r in self.table_rows), default=0))
                headers = self.table_headers if self.table_headers else [f"Col {i+1}" for i in range(cols)]
                while len(headers) < cols:
                    headers.append("")
                hdr_line = "| " + " | ".join(headers) + " |"
                sep_line = "| " + " | ".join(["---"] * cols) + " |"
                row_lines = []
                for row in self.table_rows:
                    while len(row) < cols:
                        row.append("")
                    row_lines.append("| " + " | ".join(row) + " |")
                table_md = "\n\n" + "\n".join([hdr_line, sep_line] + row_lines) + "\n\n"
                self.md_lines.append(table_md)

        if self.tag_stack and self.tag_stack[-1][0] == tag:
            self.tag_stack.pop()

    def handle_data(self, data: str):
        if self.in_table and (self.is_header_cell or self.current_cell is not None):
            self.current_cell.append(data)
        else:
            self.md_lines.append(data)

    def get_markdown(self) -> str:
        text = "".join(self.md_lines)
        # normalize whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()


def process_doc(doc_info: dict):
    slug = doc_info["slug"]
    print(f"\nProcessing {slug}...")
    html_path = os.path.join(tempfile.gettempdir(), f"{slug}.html")
    if not os.path.exists(html_path):
        print(f"Error: {html_path} missing")
        return

    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    # extract main articleBody
    m = re.search(r"<section class=\"blog-post-content[^\"]*\"[^>]*>(.*?)</section>", html, re.DOTALL)
    body_html = m.group(1) if m else ""
    if not body_html:
        m2 = re.search(r"<article[^>]*>(.*?)</article>", html, re.DOTALL)
        body_html = m2.group(1) if m2 else html

    asset_dir_name = f"{slug}.assets"
    asset_dir = os.path.join(TARGET_DIR, asset_dir_name)
    os.makedirs(asset_dir, exist_ok=True)

    parser = AWSBlogParser(asset_dir=asset_dir, rel_asset_path=asset_dir_name)
    parser.feed(body_html)
    body_md = parser.get_markdown()

    # format frontmatter
    keywords_yaml = "\n".join(f"- {kw}" for kw in doc_info["keywords"])
    aliases_yaml = "\n".join(f"- {alias}" for alias in doc_info["aliases"])
    tldr_bullets = "\n".join(f"- {bullet}" for bullet in doc_info["tldr"])

    md_content = f"""---
title: "{doc_info['title']}"
description: "{doc_info['desc']}"
keywords:
{keywords_yaml}
category: reference
classification: 🟢🛡️ General
last_updated: '2026-10-15'
author: "{doc_info['authors']}"
related:
- Resources/third_party_docs/ray/RayV2Architecture.md
- Projects/hello-mlaas-burst/aws-batch-ecs-vs-karp-ray-flyte.md
ai_search_aliases:
{aliases_yaml}
---

# 📌 {doc_info['title']}

> **Source:** [{doc_info['url']}]({doc_info['url']})  
> **Publication Date:** {doc_info['date']} | **Author(s):** {doc_info['authors']} | **Status:** Active

---

## 🎯 TL;DR

{tldr_bullets}

> **Use this for:** {doc_info['use_for']}

---

{body_md}
"""

    out_file = os.path.join(TARGET_DIR, f"{slug}.md")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"Successfully generated: {out_file}")


def main():
    os.makedirs(TARGET_DIR, exist_ok=True)
    for doc in DOCS:
        process_doc(doc)
    print("\nAll 5 AWS Ray blog posts successfully processed!")


if __name__ == "__main__":
    main()
