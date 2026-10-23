---
title: Workspace Indexing Subsystem Scripts Index
description: Index of workspace document scanning, ChromaDB vector storage, and provider abstraction modules
keywords:
- indexing scripts
- ChromaDB
- vector database
- provider abstraction
- workspace indexer
category: index
classification: 🟢🛡️ General
last_updated: '2026-10-16'
author: thatsafact
ai_search_aliases:
- indexing scripts
- chromadb scripts
- vectordb provider scripts
---

# Workspace Indexing Subsystem Scripts Index

> **TL;DR:** Index of Python modules for scanning workspace files, generating embeddings, and persisting into ChromaDB.
> **Use this for:** Managing workspace indexing, extending vector DB providers, and running indexing examples.

## Contents

| File / Folder | Description | Keywords |
|---------------|-------------|----------|
| 🐍 [`index_workspace.py`](index_workspace.py) | CLI script to recursively scan, filter, and index workspace documents into ChromaDB | index workspace, ChromaDB, CLI, batch indexing |
| 🐍 [`vectordb_provider.py`](vectordb_provider.py) | Abstract base class VectorDBProvider and ChromaDBProvider implementation with defensive path handling | vector DB provider, ChromaDB, abstraction, factory |
| 🐍 [`examples.py`](examples.py) | Demonstration script covering basic indexing, custom collections, and search queries | indexing examples, chromadb demo, usage |
| 🐍 [`index_tantivy.py`](index_tantivy.py) | High-performance Tantivy BM25 inverted indexer CLI for workspace text and code files | index tantivy, BM25, inverted index, full-text |
| 🐍 [`index_graphify.py`](index_graphify.py) | Tree-sitter AST & Markdown Knowledge Graph indexer extracting code definitions and doc sections | index graphify, AST, tree-sitter, knowledge graph |
