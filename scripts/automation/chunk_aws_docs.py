#!/usr/bin/env python3
"""Chunk oversized AI-searchable docs into <1.5MB pieces for good retrieval.

Raising the indexer size cap makes a 4MB doc *visible* to search, but a single
giant document is a poor retrieval target (low precision, dominates results).
Good retrieval comes from chunking. This script:

  * keeps the original full doc for reading (zero data loss), and
  * writes sequential <MAX_BYTES chunks into <doc>.chunks/<slug>.NNN.md, each a
    self-contained AI-searchable fragment (frontmatter + a slice of the body).

Idempotent: the .chunks dir is cleared and rebuilt on each run. Docs under the
cap are left untouched.
"""
import argparse
import datetime
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
AWS = ROOT / "Resources" / "third_party_docs" / "aws"
MAX_BYTES = 1_500_000  # keep each chunk comfortably under the 16MB cap / 2MB norm
DATE = datetime.datetime.now().strftime("%Y-%m-%d")

# frontmatter per base doc (title/desc/keywords/aliases)
META = {
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
    "ec2-ug": {
        "title": "Amazon EC2 User Guide",
        "desc": "Comprehensive Amazon EC2 user guide covering instance types, AMIs, launch and connect, EC2 Fleet/Spot Fleet, networking, security, storage, monitoring, and troubleshooting.",
        "keywords": ["Amazon EC2", "AWS", "instances", "AMIs", "EC2 Fleet", "Spot", "EBS", "security groups", "CloudWatch", "troubleshooting"],
        "aliases": ["ec2 user guide", "aws ec2", "ec2 instances"],
    },
}

# also chunk the 3 under-cap-but-large-ish ones? No — only over-cap. But we can
# also chunk anything over MAX_BYTES regardless of cap.


def chunk_document(md_path: Path, base: str) -> int:
    text = md_path.read_text(encoding="utf-8")
    meta = META.get(base)
    if not meta:
        return 0
    chunks_dir = md_path.parent / f"{base}.chunks"
    if chunks_dir.exists():
        import shutil
        shutil.rmtree(chunks_dir)
    chunks_dir.mkdir(parents=True, exist_ok=True)

    # Split on "## Page " boundaries so chunks align to doc structure.
    lines = text.split("\n")
    # find the body start (after the first frontmatter block)
    body_start = 0
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                body_start = i + 1
                break
    body_lines = lines[body_start:]
    pre = lines[:body_start]  # original frontmatter (kept only on chunk 0)

    page_splits: list[list[str]] = []
    cur: list[str] = []
    for ln in body_lines:
        if ln.startswith("## Page "):
            if cur:
                page_splits.append(cur)
            cur = [ln]
        else:
            cur.append(ln)
    if cur:
        page_splits.append(cur)

    chunks = []
    buf: list[str] = []
    buf_len = 0
    for ps in page_splits:
        ps_text = "\n".join(ps) + "\n"
        if buf and buf_len + len(ps_text.encode("utf-8")) > MAX_BYTES:
            chunks.append(buf)
            buf, buf_len = [], 0
        buf.append(ps_text)
        buf_len += len(ps_text.encode("utf-8"))
    if buf:
        chunks.append(buf)

    # Flatten chunk-of-pages back to text
    chunk_texts = ["".join(c) for c in chunks]

    written = 0
    for i, ctext in enumerate(chunk_texts, 1):
        kw = "\n".join(f"- {k}" for k in meta["keywords"])
        al = "\n".join(f"- {a}" for a in meta["aliases"])
        n_pages = ctext.count("## Page ")
        doc = (
            "---\n"
            f"title: {meta['title']} (part {i}/{len(chunk_texts)})\n"
            f"description: {meta['desc']} Chunk {i} of {len(chunk_texts)} for "
            f"searchable retrieval.\n"
            "keywords:\n"
            f"{kw}\n"
            "category: reference\n"
            "classification: \U0001F7E2\U0001F6E1️ General\n"
            f"last_updated: '{DATE}'\n"
            "author: thatsafact\n"
            "ai_search_aliases:\n"
            f"{al}\n"
            f"source_doc: {base}.md\n"
            f"chunk: {i} of {len(chunk_texts)}\n"
            "---\n\n"
            f"# {meta['title']} — part {i}/{len(chunk_texts)}\n\n"
            f"> **TL;DR:** {meta['desc']} This chunk covers ~{n_pages} pages "
            f"of the source document.\n"
            f"> **Full document:** [{base}.md](../{base}.md)\n\n"
            f"## Pages in this chunk\n\n"
            + ctext
        )
        out = chunks_dir / f"{base}.{i:03d}.md"
        out.write_text(doc, encoding="utf-8")
        written += 1
    return written


def main() -> int:
    ap = argparse.ArgumentParser(description="Chunk oversized docs for retrieval")
    ap.add_argument("bases", nargs="*",
                    help="Doc basenames (default: all over 1.5MB in Resources/third_party_docs/aws)")
    args = ap.parse_args()

    if args.bases:
        bases = args.bases
    else:
        bases = [p.stem for p in AWS.glob("*.md")
                 if p.stat().st_size > MAX_BYTES and p.name != "_INDEX.md"]

    total = 0
    for base in bases:
        md = AWS / f"{base}.md"
        if not md.exists():
            print(f"SKIP (missing): {base}.md")
            continue
        n = chunk_document(md, base)
        size = md.stat().st_size
        status = f"{n} chunks" if n else "under cap — not chunked"
        print(f"{base:45s} {size:>9} bytes  -> {status}")
        total += n
    print(f"Total chunks written: {total}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
