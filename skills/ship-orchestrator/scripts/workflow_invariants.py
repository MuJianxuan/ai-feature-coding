#!/usr/bin/env python3
"""Shared workflow invariants for ShipKit routing and validators."""

from __future__ import annotations

from typing import Any

from workflow_stage_map import CANONICAL_STAGE_ORDER

DEFINE_SCENARIOS = frozenset({"product_provided", "prd_direct"})
TECHNICAL_PLAN_SCENARIO = "technical_plan_provided"
VALID_PROJECT_SCOPES = frozenset({"fullstack", "backend_only", "frontend_only"})
BACKEND_CONTRACT_MATERIAL_KEYWORDS = (
    "OpenAPI",
    "endpoint",
    "接口文档",
    "API spec",
    "message protocol",
    "消息协议",
    "CLI spec",
    "SDK",
    "request/response",
)


def stage_meta(meta: dict[str, Any], stage: str) -> dict[str, Any]:
    stages = meta.get("stages")
    if not isinstance(stages, dict):
        return {}
    value = stages.get(stage)
    return value if isinstance(value, dict) else {}


def is_stage_skipped(meta: dict[str, Any], stage: str) -> bool:
    return stage_meta(meta, stage).get("status") == "skipped"


def is_inserted_shape_required(meta: dict[str, Any]) -> bool:
    return meta.get("scenario") in DEFINE_SCENARIOS and not is_stage_skipped(meta, "ship-shape")


def scope_forbidden_artifacts(project_scope: str) -> tuple[str, ...]:
    if project_scope == "backend_only":
        return ("design-brief.md", "frontend-design.md", "frontend-plan.md")
    if project_scope == "frontend_only":
        return ("backend-design.md", "backend-plan.md")
    return ()


def normalize_project_scope(project_scope: Any) -> str:
    value = str(project_scope or "fullstack")
    return value if value in VALID_PROJECT_SCOPES else "fullstack"


def target_requires_scope_freeze(target_stage: str) -> bool:
    if target_stage not in CANONICAL_STAGE_ORDER:
        return False
    return CANONICAL_STAGE_ORDER.index(target_stage) >= CANONICAL_STAGE_ORDER.index("ship-delivery-plan")


def design_review_meta_approved(meta: dict[str, Any]) -> bool:
    review = stage_meta(meta, "ship-design-review")
    return review.get("status") == "approved" or review.get("approved") is True


def scope_freeze(meta: dict[str, Any]) -> dict[str, Any]:
    value = meta.get("scope_freeze")
    return value if isinstance(value, dict) else {}


def scope_freeze_is_valid(meta: dict[str, Any]) -> bool:
    freeze = scope_freeze(meta)
    return freeze.get("status") == "frozen" and str(freeze.get("frozen_scope", "")).strip() == normalize_project_scope(meta.get("project_scope"))


def backend_contract_material_present(text: str) -> bool:
    return any(keyword in text for keyword in BACKEND_CONTRACT_MATERIAL_KEYWORDS)
