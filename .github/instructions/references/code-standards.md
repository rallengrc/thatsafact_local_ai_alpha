---
title: "MLaaS Code Standards & Conventions Reference"
description: "Architecture patterns, naming conventions, import ordering, and error handling for the MLaaS codebase"
shield: "internal"
last_updated: "2026-10-11"
keywords: [code-standards, conventions, python, imports, naming, architecture, patterns]
---

# MLaaS Code Standards & Conventions Reference

> **TL;DR:** Core engineering standards for Python, Kubernetes manifests, and AI instruction files in the MLaaS workspace.
> **Use this for:** Structuring new modules, writing tests, and maintaining architectural consistency.

---

## 1. Naming Conventions

- **Classes:** PascalCase (e.g. `UnifiedSearchRouter`, `GraphifySearcher`, `TantivySearcher`).
- **Functions & Methods:** snake_case (e.g. `search_symbols()`, `search_everything()`).
- **Constants:** UPPER_SNAKE_CASE (e.g. `DEFAULT_BATCH_SIZE`, `SLA_TARGETS_MS`).
- **File Names:** snake_case (e.g. `tantivy_searcher.py`, `speed_test.py`).
- **Kubernetes Resources:** kebab-case (e.g. `hello-mlaas-surrogate-burst`, `mlaas-platform-infra`).

---

## 2. Import Organization Pattern

Always order Python imports in three distinct blocks:

```python
# 1. Standard library
import os
import sys
import time
import logging
from typing import Dict, List, Any, Optional

# 2. Third-party dependencies
import numpy as np
import pytest

# 3. Local package imports (with sys.path guards)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vectordb_provider import get_provider
from livetext import RipgrepSearcher
```

---

## 3. Error Handling & Logging

- **Logging:** Use `logging.getLogger(__name__)` directed to `sys.stderr`. Never use `print()` in library code.
- **Exceptions:** Raise explicit `ValueError` for configuration issues and `IOError` / `FileNotFoundError` for storage faults.
- **Graceful Degradation:** If optional native tools are unavailable (e.g., Ripgrep binary or remote Ray cluster), modules must log a warning and fall back to local execution without crashing.

---

## 4. Key Design Patterns

1. **Provider Abstraction:** Abstract base class (`VectorDBProvider`) + factory (`get_provider()`).
2. **Intent-Based Pre-Routing:** `QueryAnalyzer` classifies queries to prevent expensive broadcast fan-out.
3. **Multi-Engine Fusion:** Reciprocal Rank Fusion (RRF) blends scores across heterogeneous search engines.
4. **Macro vs Micro Layering:** Flyte orchestrates between tasks; Ray parallelizes inside the task.
