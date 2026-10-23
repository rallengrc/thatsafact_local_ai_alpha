"""
test_sqlite_mcp.py — Unit and integration tests for SQLite MCP Server.
Tests table listing, table schema description, safe read queries, MLaaS metrics retrieval,
and self-referential session store access.
"""

import os
import json
import sqlite3
import tempfile
from pathlib import Path
import pytest

from sqlite_server import (
    list_tables,
    describe_table,
    read_query,
    get_benchmark_metrics,
    get_feature_attributions,
    get_recent_copilot_turns,
    search_team_prompts,
    get_doc_effectiveness_rankings,
    get_team_token_usage,
    _resolve_db_path,
    DEFAULT_METRICS_DB,
    DEFAULT_COPILOT_DB,
    DEFAULT_PROMPTS_DB,
)


def test_resolve_db_path():
    assert _resolve_db_path("metrics") == DEFAULT_METRICS_DB
    assert _resolve_db_path("copilot") == DEFAULT_COPILOT_DB
    assert _resolve_db_path("prompts") == DEFAULT_PROMPTS_DB
    custom_path = str(Path(tempfile.gettempdir()) / "test.db")
    assert _resolve_db_path(custom_path) == custom_path


def test_list_tables_metrics():
    res_str = list_tables(db="metrics")
    data = json.loads(res_str)
    assert "pipeline_benchmarks" in data["tables"]
    assert "feature_attribution" in data["tables"]


def test_describe_table():
    res_str = describe_table("pipeline_benchmarks", db="metrics")
    data = json.loads(res_str)
    assert data["table"] == "pipeline_benchmarks"
    col_names = [c["name"] for c in data["columns"]]
    assert "run_id" in col_names
    assert "total_wall_time_ms" in col_names
    assert "speedup_factor" in col_names


def test_read_query_safe():
    res_str = read_query("SELECT count(*) as total FROM pipeline_benchmarks;", db="metrics")
    data = json.loads(res_str)
    assert data["row_count"] == 1
    assert data["results"][0]["total"] >= 1


def test_read_query_guard_non_select():
    res_str = read_query("DROP TABLE pipeline_benchmarks;", db="metrics")
    assert "Error: read_query only allows read-only SELECT" in res_str


def test_get_benchmark_metrics():
    res_str = get_benchmark_metrics(limit=3)
    data = json.loads(res_str)
    assert "benchmark_runs" in data
    assert len(data["benchmark_runs"]) >= 1


def test_get_feature_attributions():
    res_str = get_feature_attributions()
    data = json.loads(res_str)
    assert "feature_attributions" in data
    assert len(data["feature_attributions"]) >= 1
    frameworks = [f["framework"] for f in data["feature_attributions"]]
    assert "Ray" in frameworks or "Flyte" in frameworks


def test_get_recent_copilot_turns():
    if os.path.exists(DEFAULT_COPILOT_DB):
        res_str = get_recent_copilot_turns(limit=2)
        data = json.loads(res_str)
        assert "recent_turns" in data
        assert len(data["recent_turns"]) >= 1


def test_search_team_prompts_mcp():
    if os.path.exists(DEFAULT_PROMPTS_DB):
        res_str = search_team_prompts("Tantivy", limit=3)
        data = json.loads(res_str)
        assert "results" in data
        assert data["match_count"] >= 1
        assert "match_snippet" in data["results"][0]


def test_get_doc_effectiveness_rankings_mcp():
    if os.path.exists(DEFAULT_PROMPTS_DB):
        res_str = get_doc_effectiveness_rankings(limit=5)
        data = json.loads(res_str)
        assert "doc_rankings" in data
        assert len(data["doc_rankings"]) >= 1


def test_get_team_token_usage_mcp():
    if os.path.exists(DEFAULT_PROMPTS_DB):
        res_str = get_team_token_usage()
        data = json.loads(res_str)
        assert "usage_by_user" in data
        assert "usage_by_model" in data
        assert len(data["usage_by_user"]) >= 1
