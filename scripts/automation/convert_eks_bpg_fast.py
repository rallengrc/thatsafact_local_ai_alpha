#!/usr/bin/env python3
"""
convert_eks_bpg.py — Fast converter for Resources/third_party_docs/aws/eks-bpg.pdf to Markdown
with embedded image assets and Diamond YAML frontmatter.
"""

import os
import sys
import time
import hashlib
from pathlib import Path

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SCRIPTS_DIR not in sys.path and os.path.exists(SCRIPTS_DIR):
    sys.path.insert(0, SCRIPTS_DIR)
from common_platform import ensure_venv_site_packages

ensure_venv_site_packages(Path(REPO_ROOT))

try:
    import pymupdf as fitz
except ImportError:
    import fitz

PDF_PATH = os.path.join(REPO_ROOT, "Resources", "third_party_docs", "aws", "eks-bpg.pdf")
OUT_MD = os.path.join(REPO_ROOT, "Resources", "third_party_docs", "aws", "eks-bpg.md")
ASSETS_DIR = os.path.join(REPO_ROOT, "Resources", "third_party_docs", "aws", "eks-bpg.assets")
REL_PREFIX = "eks-bpg.assets"


def is_content_image(w: int, h: int) -> bool:
    """Filter out icons (<1000px area) and full-page background rectangles."""
    area = w * h
    if area < 1000:
        return False
    if w >= 1500 and h >= 1500:
        return False
    return True


def main():
    print(f"Opening {PDF_PATH}...")
    doc = fitz.open(PDF_PATH)
    total_pages = doc.page_count
    print(f"PDF opened successfully. Total pages: {total_pages}")

    os.makedirs(ASSETS_DIR, exist_ok=True)

    # 1. Scan unique xrefs
    print("Scanning image xrefs across all pages...")
    t0 = time.time()
    xref_first = {}
    for i in range(total_pages):
        for im in doc[i].get_images():
            xref_first.setdefault(im[0], i + 1)
    print(f"Discovered {len(xref_first)} distinct image xrefs in {time.time() - t0:.2f}s.")

    # 2. Extract unique content images
    print("Extracting content images to disk...")
    saved_images = {}
    seen_hashes = {}
    t1 = time.time()
    for xref, first_page in xref_first.items():
        try:
            info = doc.extract_image(xref)
            data = info.get("image") or b""
            if not data:
                continue
            w, h = info.get("width", 0), info.get("height", 0)
            if not is_content_image(w, h):
                continue
            hsh = hashlib.sha1(data).hexdigest()
            if hsh in seen_hashes:
                saved_images[xref] = seen_hashes[hsh]
                continue
            ext = info.get("ext", "png")
            if ext.lower() in ("", "png"):
                if data[:8] == b"\x89PNG\r\n\x1a\n":
                    ext = "png"
                elif data[:3] == b"\xff\xd8\xff":
                    ext = "jpg"
                else:
                    ext = "png"
            fname = f"{hsh[:16]}.{ext.lower()}"
            out_path = os.path.join(ASSETS_DIR, fname)
            with open(out_path, "wb") as f_out:
                f_out.write(data)
            record = {"file": fname, "w": w, "h": h, "page": first_page}
            seen_hashes[hsh] = record
            saved_images[xref] = record
        except Exception:
            continue
    print(f"Extracted {len(seen_hashes)} unique content images in {time.time() - t1:.2f}s.")

    # 3. Extract text page by page
    print("Extracting text and assembling Markdown document...")
    t2 = time.time()
    ts = time.strftime("%Y-%m-%d %H:%M")

    frontmatter = """---
title: Amazon EKS Best Practices Guide
description: Comprehensive Amazon EKS best practices guide covering security, cluster management, networking, and performance.
keywords:
- Amazon EKS
- AWS
- Kubernetes
- best practices
- security
- autoscaling
- networking
- GPU
- cluster
category: reference
classification: 🟢🛡️ General
last_updated: '2026-10-15'
author: Amazon Web Services (AWS)
related:
- Resources/third_party_docs/aws/eks-ug.md
- Projects/hello-mlaas-burst/aws-batch-ecs-vs-karp-ray-flyte.md
ai_search_aliases:
- eks best practices
- eks bpg
- kubernetes best practices on aws
---

# 📌 Amazon EKS Best Practices Guide

> **Source:** `Resources/third_party_docs/aws/eks-bpg.pdf`  
> **Generated:** """ + ts + """ | **Converter:** `scripts/automation/convert_eks_bpg.py` | **Status:** Active

---

## 🎯 TL;DR

- Authoritative AWS best practices manual for architecture, deployment, and operation of Amazon Elastic Kubernetes Service (EKS) clusters.
- In-depth security best practices including IAM authentication, pod security standards, KMS envelope encryption, and network policies.
- Comprehensive guidance on cluster autoscaling using Karpenter and Cluster Autoscaler for dynamic compute optimization.
- Covers networking configurations (VPC CNI, IPv6, security groups per pod), reliability, cost optimization, and observability.

> **Use this for:** Designing, hardening, scaling, and validating enterprise Amazon EKS clusters and Kubernetes workloads on AWS.

---
"""

    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write(frontmatter + "\n")

        for i in range(total_pages):
            f.write(f"## Page {i + 1}\n\n")
            text = doc[i].get_text("text").rstrip()
            if text:
                f.write(text + "\n\n")
            else:
                f.write("_[no text on this page]_\n\n")

        # 4. Embedded content image gallery
        f.write("\n---\n\n## 🖼️ Architectural Diagrams & Extracted Images\n\n")
        f.write(f"This document contains {len(seen_hashes)} distinct architectural diagrams and technical illustrations extracted from `eks-bpg.pdf`:\n\n")
        for hsh, r in sorted(seen_hashes.items(), key=lambda x: x[1]["page"]):
            rel_link = f"./{REL_PREFIX}/{r['file']}"
            f.write(f"### Diagram: Page {r['page']} ({r['w']}x{r['h']})\n\n")
            f.write(f"![EKS Best Practice Diagram p.{r['page']}]({rel_link})\n\n")

    doc.close()
    md_size_mb = os.path.getsize(OUT_MD) / (1024 * 1024)
    print(f"Generated {OUT_MD} ({md_size_mb:.2f} MB) in {time.time() - t2:.2f}s.")


if __name__ == "__main__":
    main()
