#!/usr/bin/env python3
"""
test_passport_and_skill_search.py — Unit tests for Passport partitioning & find_skill tool.
"""

import os
import sys
import time
import pytest
from pathlib import Path

_SCRIPTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ROUTER_DIR = os.path.join(_SCRIPTS_DIR, "search_router")
for _p in [_ROUTER_DIR, _SCRIPTS_DIR]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from passport import Passport, PassportResolver
from skill_distiller import TimedExpiringCache, LeanSkillDistiller
from mcp_search_tools import MCPSearchTools


class TestPassportResolver:
    """Test deterministic and dynamic passport categorization."""

    def test_deterministic_paths(self):
        assert PassportResolver.resolve_from_path(".github/skills/kiss-mode/SKILL.md") == "skill"
        assert PassportResolver.resolve_from_path("code/superpowers/skills/brainstorming/SKILL.md") == "skill"
        assert PassportResolver.resolve_from_path("code/flyte-agent-plugins/plugins/flyte/skills/deploy/SKILL.md") == "skill"
        assert PassportResolver.resolve_from_path(".github/instructions/code-standards.instructions.md") == "skill"

        assert PassportResolver.resolve_from_path("k8s/kind-cluster.yaml") == "kubernetes"
        assert PassportResolver.resolve_from_path("manifests/kuberay-operator.yaml") == "kubernetes"
        assert PassportResolver.resolve_from_path("code/karpenter/pkg/controllers/node.go") == "kubernetes"

        assert PassportResolver.resolve_from_path("Projects/Burstable MLaaS/Phase2.md") == "ml"
        assert PassportResolver.resolve_from_path("Projects/hello-mlaas-burst/local_runner.py") == "ml"
        assert PassportResolver.resolve_from_path("Resources/ray/ray-core.md") == "ml"

        assert PassportResolver.resolve_from_path("terraform/main.tf") == "cloud"
        assert PassportResolver.resolve_from_path("code/karpenter-blueprints/vpc.tfvars") == "cloud"

        assert PassportResolver.resolve_from_path("random_unrelated_doc.txt") == "all"

    def test_dynamic_fallback(self):
        k8s_content = "This document describes how to deploy a pod on kubernetes using kubectl."
        assert PassportResolver.resolve_dynamic("notes.txt", k8s_content) == "kubernetes"

        ml_content = "Distributed training using Ray actors and flytekit task definitions."
        assert PassportResolver.resolve_dynamic("notes.txt", ml_content) == "ml"

        cloud_content = "AWS infrastructure provisioning with Terraform and IAM roles."
        assert PassportResolver.resolve_dynamic("notes.txt", cloud_content) == "cloud"

    def test_filter_results_zero_overhead_for_all(self):
        items = [{"path": "k8s/kind.yaml"}, {"path": ".github/skills/foo/SKILL.md"}]
        # None or 'all' should return identical list reference
        assert len(PassportResolver.filter_results(items, None)) == 2
        assert len(PassportResolver.filter_results(items, "all")) == 2

    def test_filter_results_by_passport(self):
        items = [
            {"path": "k8s/kind.yaml"},
            {"path": ".github/skills/foo/SKILL.md"},
            {"path": "terraform/main.tf"},
        ]
        k8s_items = PassportResolver.filter_results(items, "kubernetes")
        assert len(k8s_items) == 1
        assert k8s_items[0]["path"] == "k8s/kind.yaml"

        skill_items = PassportResolver.filter_results(items, "skill")
        assert len(skill_items) == 1
        assert skill_items[0]["path"] == ".github/skills/foo/SKILL.md"


class TestTimedExpiringCache:
    """Test passive expiring cache behavior."""

    def test_set_and_get(self):
        cache = TimedExpiringCache(default_ttl_seconds=10.0)
        cache.set("foo", {"data": 123})
        val = cache.get("foo")
        assert val is not None
        assert val["data"] == 123

    def test_expiration(self):
        cache = TimedExpiringCache(default_ttl_seconds=0.05)
        cache.set("fast", "value")
        assert cache.get("fast") == "value"
        time.sleep(0.08)
        assert cache.get("fast") is None


class TestLeanSkillDistiller:
    """Test distillation of verbose SKILL.md into lean actionable markdown."""

    def test_distill_already_lean(self):
        lean_text = "---\nname: lean-skill\ndescription: A short skill\n---\n# Step 1\nDo this."
        distilled = LeanSkillDistiller.distill_text(lean_text, "/path/SKILL.md", max_lines=100)
        assert distilled["distilled_lines"] <= 10
        assert distilled["skill_name"] == "lean-skill"

    def test_distill_long_markdown(self):
        # Generate 200 lines of verbose markdown
        lines = ["---", "name: verbose-skill", "description: Very verbose", "---"]
        lines.append("# Verbose Skill Overview")
        lines.extend([f"- Step {i}: perform action {i}" for i in range(150)])
        raw_text = "\n".join(lines)

        distilled = LeanSkillDistiller.distill_text(raw_text, "/path/verbose/SKILL.md", max_lines=100)
        assert distilled["distilled_lines"] <= 100
        assert distilled["total_raw_lines"] > 150
        assert "Reference Source:" in distilled["lean_markdown"]
        assert "/path/verbose/SKILL.md" in distilled["reference_note"]


class TestMCPSkillSearch:
    """Test MCPSearchTools.find_skill discovery and integration."""

    @pytest.fixture
    def tools(self):
        repo_root = Path(_SCRIPTS_DIR).parent
        return MCPSearchTools(db_path=str(repo_root / ".chroma"), workspace_root=str(repo_root))

    def test_find_superpowers_skill(self, tools):
        res = tools.find_skill("brainstorming")
        assert res["status"] == "success"
        assert "brainstorming" in res["skill_name"].lower()
        assert res["distilled_lines"] <= 100
        assert "SKILL.md" in res["source_path"]
        assert Path(res["source_path"]).exists()

    def test_find_flyte_skill(self, tools):
        res = tools.find_skill("flyte deploy aws")
        assert res["status"] == "success"
        assert "flyte-deploy-aws" in res["skill_name"]
        assert res["distilled_lines"] <= 100
        assert Path(res["source_path"]).exists()

    def test_find_nonexistent_skill(self, tools):
        res = tools.find_skill("xyzzy-completely-unknown-skill-999")
        assert res["status"] == "not_found"

    def test_search_workspace_with_passport(self, tools):
        res = tools.search_workspace("deploy", limit=5, passport="skill")
        assert res["status"] == "success"
        assert res["passport"] == "skill"
