#!/usr/bin/env python3
"""
passport.py — Coarse-grained category partitioning ("passport") for fast search routing.

Passports provide O(1) partition filtering over search candidates across 96k+ AST nodes
and thousands of workspace/code files:
  - 'cloud': AWS, Terraform, Cloud infrastructure, IAM, S3.
  - 'ml': Ray, Flyte, surrogate ML pipelines, distributed compute, ML scaling.
  - 'kubernetes': KinD, K8s manifests, KubeRay, container architecture, Karpenter.
  - 'skill': AI IDE skills, procedural workflows, prompt engineering, agent instructions.
  - 'all' / None: Unfiltered global search (default, zero overhead).

Dynamic classification is available for new or ambiguous content without taxonomy sprawl.
"""

from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import re
import os


class Passport(str, Enum):
    """Core controlled passport tags."""

    CLOUD = "cloud"
    ML = "ml"
    KUBERNETES = "kubernetes"
    SKILL = "skill"
    ALL = "all"


VALID_PASSPORTS: Set[str] = {p.value for p in Passport}

# Deterministic path signatures (checked in precedence order)
_SKILL_PATTERNS = [
    re.compile(r"(^|[/\\])(skills|\.github[/\\]skills|code[/\\]superpowers[/\\]skills|code[/\\]flyte-agent-plugins[/\\]plugins|code[/\\]awesome-copilot)([/\\]|$)"),
    re.compile(r"SKILL\.md$", re.IGNORECASE),
    re.compile(r"\.instructions\.md$", re.IGNORECASE),
]

_KUBERNETES_PATTERNS = [
    re.compile(r"(^|[/\\])(k8s|manifests|deploy|code[/\\]karpenter|code[/\\]kuberay)([/\\]|$)"),
    re.compile(r"(kind[-_]|k8s[-_]|kuberay[-_]|karpenter[-_]|crd[-_]|deployment[-_]).*\.(ya?ml|json)$", re.IGNORECASE),
]

_ML_PATTERNS = [
    re.compile(r"(^|[/\\])(Projects[/\\]Burstable MLaaS|Projects[/\\]hello-mlaas-burst|Resources[/\\]ray|code[/\\]ray|code[/\\]flyte|code[/\\]flytekit|code[/\\]flytesnacks)([/\\]|$)"),
    re.compile(r"(surrogate|ray_plugin|flyte|mlaas|benchmark_metrics).*", re.IGNORECASE),
]

_CLOUD_PATTERNS = [
    re.compile(r"(^|[/\\])(terraform|aws|infra|code[/\\]karpenter-blueprints)([/\\]|$)"),
    re.compile(r"\.(tf|tfvars)$", re.IGNORECASE),
]


class PassportResolver:
    """Resolves and filters content by passport partition tag."""

    @staticmethod
    def normalize_passport(passport: Optional[str]) -> Optional[str]:
        """Normalize passport string; returns None if 'all' or empty."""
        if not passport:
            return None
        norm = passport.strip().lower()
        if norm in ("all", "*", "none", ""):
            return None
        return norm

    @classmethod
    def resolve_from_path(cls, path_str: str) -> str:
        """Resolve passport tag deterministically from file path.

        Returns one of: 'skill', 'kubernetes', 'ml', 'cloud', or 'all' if uncategorized.
        """
        norm_path = path_str.replace("\\", "/")

        # 1. Skill takes top priority for any procedural instruction file
        for pattern in _SKILL_PATTERNS:
            if pattern.search(norm_path):
                return Passport.SKILL.value

        # 2. Kubernetes
        for pattern in _KUBERNETES_PATTERNS:
            if pattern.search(norm_path):
                return Passport.KUBERNETES.value

        # 3. ML / Distributed compute
        for pattern in _ML_PATTERNS:
            if pattern.search(norm_path):
                return Passport.ML.value

        # 4. Cloud infrastructure
        for pattern in _CLOUD_PATTERNS:
            if pattern.search(norm_path):
                return Passport.CLOUD.value

        return Passport.ALL.value

    @classmethod
    def resolve_dynamic(cls, path_str: str, content: str = "") -> str:
        """Dynamically infer passport tag for new or ambiguous content.

        First checks path heuristics, then uses text keyword scoring.
        Maintains controlled taxonomy without creating unchecked new tags.
        """
        tag = cls.resolve_from_path(path_str)
        if tag != Passport.ALL.value:
            return tag

        if not content:
            return Passport.ALL.value

        sample = content[:3000].lower()

        scores: Dict[str, int] = {
            Passport.SKILL.value: 0,
            Passport.KUBERNETES.value: 0,
            Passport.ML.value: 0,
            Passport.CLOUD.value: 0,
        }

        # Skill indicators
        if "skill" in sample or "instructions" in sample or "workflow" in sample:
            scores[Passport.SKILL.value] += 2
        if "frontmatter" in sample or "disable-model-invocation" in sample:
            scores[Passport.SKILL.value] += 3

        # Kubernetes indicators
        if "kubernetes" in sample or "k8s" in sample or "kubectl" in sample:
            scores[Passport.KUBERNETES.value] += 3
        if "kind cluster" in sample or "daemonset" in sample or "crd" in sample:
            scores[Passport.KUBERNETES.value] += 2

        # ML indicators
        if "ray" in sample or "flyte" in sample or "surrogate" in sample or "pytorch" in sample:
            scores[Passport.ML.value] += 3
        if "distributed actor" in sample or "tensor" in sample or "flytekit" in sample:
            scores[Passport.ML.value] += 2

        # Cloud indicators
        if "aws" in sample or "terraform" in sample or "iam role" in sample or "s3" in sample:
            scores[Passport.CLOUD.value] += 3
        if "cloudformation" in sample or "ec2" in sample or "vpc" in sample:
            scores[Passport.CLOUD.value] += 2

        best_tag = max(scores, key=scores.get)
        if scores[best_tag] >= 2:
            return best_tag

        return Passport.ALL.value

    @classmethod
    def filter_results(
        cls,
        results: List[Any],
        passport: Optional[str],
        path_attr: str = "path",
    ) -> List[Any]:
        """Filter a list of search result objects by passport partition tag.

        If passport is None or 'all', returns results untouched (zero overhead).
        """
        target = cls.normalize_passport(passport)
        if target is None:
            return results

        filtered = []
        for r in results:
            path_val = getattr(r, path_attr, None)
            if path_val is None and isinstance(r, dict):
                path_val = r.get(path_attr) or r.get("filePath") or r.get("id") or ""
            if not path_val:
                continue

            item_passport = cls.resolve_from_path(str(path_val))
            if item_passport == target:
                filtered.append(r)

        return filtered
