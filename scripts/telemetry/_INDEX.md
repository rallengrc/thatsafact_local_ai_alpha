---
title: Prompt Telemetry Subsystem Index
description: Index of Python modules for team prompt telemetry synchronization, FTS5 full-text indexing, and analytics
keywords:
- telemetry index
- prompt telemetry
- FTS5 analytics
- doc citations
category: index
classification: 🟢🛡️ General
last_updated: '2026-10-16'
author: thatsafact
ai_search_aliases:
- telemetry index
- prompt telemetry scripts
- sync prompts db
---

# Prompt Telemetry Subsystem Index

> **TL;DR:** Subsystem for ingesting multi-user prompt histories from `memories/<username>/` into an ephemeral SQLite FTS5 database (`prompts_analytics.db`).
> **Use this for:** Synchronizing prompt transcripts, running Okapi BM25 keyword searches, and measuring workspace documentation citations.

## Contents

| File / Folder | Description | Keywords |
|---------------|-------------|----------|
| 🐍 [`sync_prompts_db.py`](sync_prompts_db.py) | Ingestion engine populating SQLite FTS5 tables and tracking doc citations | sync prompts, FTS5, BM25, doc citations, telemetry |
