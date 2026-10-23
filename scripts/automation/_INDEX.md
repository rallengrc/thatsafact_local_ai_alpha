---
title: Automation & Tooling Scripts Index
description: Index of documentation maintenance, metadata enrichment, PDF conversion, and diagnostic tools
keywords:
- automation scripts
- metadata enrichment
- master toc
- pdf converter
- utilities
category: index
classification: 🟢🛡️ General
last_updated: '2026-10-22'
author: thatsafact
ai_search_aliases:
- automation scripts
- utility scripts
- maintenance scripts
---

# Automation & Tooling Scripts Index

> **TL;DR:** Index of utility and automation scripts maintaining documentation metadata, table of contents, and data ingestion.
> **Use this for:** Updating frontmatter, regenerating indices, converting PDFs, and checking environment health.

## Contents

| File / Folder | Description | Keywords |
|---------------|-------------|----------|
| 🐍 [`generate_indices_and_master_toc.py`](generate_indices_and_master_toc.py) | Generator script creating standardized _INDEX.md files and MASTER_TOC.md | generate index, master toc, documentation tooling |
| 🐍 [`update_markdown_metadata.py`](update_markdown_metadata.py) | Batch tool to enrich workspace Markdown files with standardized YAML frontmatter and TL;DR | update metadata, YAML frontmatter, TLDR, automation |
| 🐍 [`pdf_to_md.py`](pdf_to_md.py) | PyMuPDF-based converter extracting text, images, and layout from PDFs into Markdown | pdf to md, converter, PyMuPDF, document extraction |
| 🐍 [`export_memories.py`](export_memories.py) | Diagnostic extractor mining VS Code state and prompt histories into memory files | export memories, session mining, SQLite, telemetry |
| 🐍 [`probe.py`](probe.py) | Environment probe checking Apple Silicon hardware, MLX, and Ollama configurations | probe, environment check, Apple Silicon, hardware |
| 🐍 [`ingest_aws_ray_blogs.py`](ingest_aws_ray_blogs.py) | Ingest AWS blog posts covering Ray & KubeRay architectures into Diamond-compliant Markdown with local image assets | ingest blogs, AWS, Ray, KubeRay, markdown |
| 🐍 [`convert_eks_bpg_fast.py`](convert_eks_bpg_fast.py) | Fast converter for Resources/third_party_docs/aws/eks-bpg.pdf to Markdown with embedded image assets | eks-bpg, converter, PyMuPDF, fast pdf to md |
| 🐍 [`pdf_to_md_fast.py`](pdf_to_md_fast.py) | Fast text + deduplicated-image-gallery converter for very large PDFs (avoids per-page image-parse cost) | pdf to md, fast, large docs, image gallery |
| 🐍 [`add_aws_frontmatter.py`](add_aws_frontmatter.py) | Adds AI-searchable YAML frontmatter to AWS reference .md files produced by the PDF converter | frontmatter, AWS, metadata enrichment |
| 🐍 [`chunk_aws_docs.py`](chunk_aws_docs.py) | Splits oversized docs into <1.5MB self-contained chunks so every byte is retrievable | chunking, retrieval, oversized docs |
| 🐍 [`ocr_packt_figures.py`](ocr_packt_figures.py) | Tesseract OCR of text-bearing Packt figures into Markdown sidecars (line-art skipped) | OCR, tesseract, image text, packt |
| 🐍 [`insert_ocr_links.py`](insert_ocr_links.py) | Inserts idempotent OCR-transcript links under each figure in the Packt guide | OCR links, cross-reference, idempotent |
| 🐍 [`setup_memory_link.py`](setup_memory_link.py) | Per-machine setup linking Claude Code's project memory directory to the tracked `memories/mlaas/` folder | memory link, symlink, junction, claude code, machine setup |
| 🐍 [`client_term_scan.py`](client_term_scan.py) | Client-neutral content scanner: reports `path:line: [class]` for client terms (private list), resolved labels, internal hosts and emails; never prints the matched term | client neutral, scrub, oss hygiene, scanner, de-brand |
