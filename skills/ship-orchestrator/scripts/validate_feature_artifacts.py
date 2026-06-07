#!/usr/bin/env python3
"""Validate ship feature artifacts against workflow frontmatter contracts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from feature_meta_runtime import is_raw_prd_inbox_frontmatter, load_meta, validate_evolve_source  # noqa: E402
from workflow_stage_map import CANONICAL_STAGE_ORDER, stage_view_for  # noqa: E402
from workflow_invariants import (  # noqa: E402
    TECHNICAL_PLAN_SCENARIO,
    backend_contract_material_present,
    design_review_meta_approved,
    normalize_project_scope,
    scope_forbidden_artifacts,
    scope_freeze,
    scope_freeze_is_valid,
    stage_meta as _stage_meta,
)

NON_REVIEW_STATUSES = frozenset({"draft", "ready", "complete"})
REVIEW_STATUSES = frozenset({"pending", "approved", "rejected", "revision_needed"})
META_NON_REVIEW_STATUSES = frozenset({"pending", "in_progress", "ready", "blocked", "completed", "skipped"})
META_REVIEW_STATUSES = frozenset({"pending", "in_progress", "approved", "rejected", "revision_needed", "skipped"})
REVIEW_STAGES = frozenset({"ship-define-review", "ship-design-review", "ship-plan-review"})
TECHNICAL_PLAN_SCAN_STATUSES = frozenset({"pending", "in_progress", "ready", "blocked"})
AC_RE = re.compile(r"\bAC-[A-Z0-9]+-\d{3}\b")
SOFT_BLOCKING_STAGES = frozenset({"ship-define", "ship-tech-discovery", "ship-contract", "ship-frontend-design", "ship-backend-design", "ship-delivery-plan", "ship-verify", "ship-handoff"})


@dataclass(frozen=True)
class ArtifactSpec:
    stage: str
    path: str
    kind: str
    role: str | None = None
    frontmatter_stage: str | None = None


ARTIFACT_SPECS: tuple[ArtifactSpec, ...] = (
    ArtifactSpec("ship-discover", "product-brief.md", "artifact"),
    ArtifactSpec("ship-shape", "design-brief.md", "artifact"),
    ArtifactSpec("ship-define", "requirements.md", "artifact"),
    ArtifactSpec("ship-define-review", "review-define.md", "review"),
    ArtifactSpec("ship-tech-discovery", "tech-research.md", "artifact", "research"),
    ArtifactSpec("ship-tech-discovery", "tech-selection.md", "artifact", "selection"),
    ArtifactSpec("ship-contract", "api-contract.md", "artifact"),
    ArtifactSpec("ship-frontend-design", "frontend-design.md", "artifact"),
    ArtifactSpec("ship-backend-design", "backend-design.md", "artifact"),
    ArtifactSpec("ship-design-review", "review-design.md", "review"),
    ArtifactSpec("ship-delivery-plan", "frontend-plan.md", "artifact", "frontend-plan"),
    ArtifactSpec("ship-delivery-plan", "backend-plan.md", "artifact", "backend-plan"),
    ArtifactSpec("ship-plan-review", "review-plan.md", "review"),
    ArtifactSpec("ship-verify", "verification.md", "artifact", frontmatter_stage="ship-handoff"),
    ArtifactSpec("ship-handoff", "handoff.md", "artifact"),
)

ARTIFACTS_BY_STAGE: dict[str, tuple[ArtifactSpec, ...]] = {
    stage: tuple(spec for spec in ARTIFACT_SPECS if spec.stage == stage)
    for stage in CANONICAL_STAGE_ORDER
}


def _issue(level: str, code: str, message: str, path: str | None = None) -> dict[str, str]:
    payload = {"level": level, "code": code, "message": message}
    if path:
        payload["path"] = path
    return payload


def read_frontmatter(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError("missing YAML frontmatter")
    end = text.find("\n---", 4)
    if end == -1:
        raise ValueError("unterminated YAML frontmatter")
    raw = text[4:end]
    data = yaml.safe_load(raw) or {}
    if not isinstance(data, dict):
        raise ValueError("frontmatter must be a YAML mapping")
    return data, text[end + 4 :]


def _stage_is_active_enough(meta: dict[str, Any], stage: str) -> bool:
    stage_meta = _stage_meta(meta, stage)
    status = stage_meta.get("status")
    if status and status not in ("pending", "skipped"):
        return True
    current_stage = meta.get("current_stage")
    if current_stage not in CANONICAL_STAGE_ORDER:
        return False
    return CANONICAL_STAGE_ORDER.index(stage) <= CANONICAL_STAGE_ORDER.index(current_stage)


def _artifact_required(meta: dict[str, Any], spec: ArtifactSpec) -> bool:
    project_scope = meta.get("project_scope", "fullstack")
    if project_scope == "backend_only" and (
        spec.stage in ("ship-shape", "ship-frontend-design")
        or spec.path == "frontend-plan.md"
    ):
        return False
    if project_scope == "frontend_only" and (
        spec.stage == "ship-backend-design"
        or spec.path == "backend-plan.md"
    ):
        return False

    return _stage_is_active_enough(meta, spec.stage)


def _scope_forbidden_artifacts(project_scope: str) -> tuple[str, ...]:
    return scope_forbidden_artifacts(project_scope)


def _validate_meta(feature_dir: Path, meta: dict[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    current_stage = meta.get("current_stage")
    if current_stage not in CANONICAL_STAGE_ORDER:
        issues.append(_issue("error", "invalid_current_stage", f"invalid current_stage: {current_stage!r}", "meta.yml"))
    else:
        expected = stage_view_for(str(current_stage)).macro
        macro_stage = meta.get("macro_stage")
        if isinstance(macro_stage, dict):
            if macro_stage.get("current") and macro_stage.get("current") != expected.current:
                issues.append(_issue("error", "macro_stage_conflict", "meta.yml macro_stage.current conflicts with current_stage", "meta.yml"))
            if macro_stage.get("label") and macro_stage.get("label") != expected.label:
                issues.append(_issue("error", "macro_stage_conflict", "meta.yml macro_stage.label conflicts with current_stage", "meta.yml"))

    stages = meta.get("stages")
    if not isinstance(stages, dict):
        issues.append(_issue("error", "missing_stages", "meta.yml missing stages mapping", "meta.yml"))
        return issues

    for stage, value in stages.items():
        if stage not in CANONICAL_STAGE_ORDER:
            issues.append(_issue("error", "unknown_stage", f"unknown meta stage: {stage}", "meta.yml"))
            continue
        if not isinstance(value, dict):
            issues.append(_issue("error", "invalid_stage_summary", f"meta.yml stages.{stage} must be a mapping", "meta.yml"))
            continue
        status = value.get("status")
        allowed = META_REVIEW_STATUSES if stage in REVIEW_STAGES else META_NON_REVIEW_STATUSES
        if status not in allowed:
            issues.append(_issue("error", "invalid_meta_status", f"invalid meta status for {stage}: {status!r}", "meta.yml"))

    issues.extend(_validate_ship_shape_meta(meta))
    issues.extend(_validate_scope_freeze_meta(meta))
    issues.extend(_validate_evolve_meta(meta))
    if meta.get("scenario") == TECHNICAL_PLAN_SCENARIO:
        issues.extend(_validate_technical_plan_meta(feature_dir, meta))
    if meta.get("scenario") == "evolve":
        issues.extend(_validate_evolve_product_brief(feature_dir, meta))

    return issues


def _validate_ship_shape_meta(meta: dict[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    scenario = meta.get("scenario")
    project_scope = meta.get("project_scope")
    shape = _stage_meta(meta, "ship-shape")
    status = shape.get("status")
    if scenario in {"product_provided", "prd_direct"} and not status == "skipped":
        if not shape.get("activation_mode") == "uiux_material_gate_insert":
            issues.append(_issue("error", "invalid_shape_activation_mode", "B/D ship-shape requires activation_mode=uiux_material_gate_insert", "meta.yml"))
        if not shape.get("uiux_gate_user_sign_off") or not shape.get("uiux_gate_signed_at"):
            issues.append(_issue("error", "missing_uiux_gate_sign_off", "B/D inserted ship-shape requires user sign-off and signed_at", "meta.yml"))
        if status in ("pending", "in_progress", "ready", "completed"):
            issues.append(
                _issue(
                    "warning",
                    "inserted_shape_transition_required",
                    "B/D inserted ship-shape must be checked by transition through design-brief.md.stage_status before downstream stages",
                    "meta.yml",
                )
            )
    if scenario == TECHNICAL_PLAN_SCENARIO and not status == "skipped":
        issues.append(_issue("error", "technical_plan_shape_forbidden", "technical_plan_provided must keep ship-shape skipped", "meta.yml"))
    if project_scope == "backend_only" and not status == "skipped":
        issues.append(_issue("error", "backend_only_shape_forbidden", "backend_only must keep ship-shape skipped", "meta.yml"))
    return issues


def _validate_scope_freeze_meta(meta: dict[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    freeze = scope_freeze(meta)
    if design_review_meta_approved(meta) and not scope_freeze_is_valid(meta):
        if not freeze:
            issues.append(_issue("error", "scope_freeze_missing", "approved ship-design-review requires scope_freeze", "meta.yml"))
        else:
            issues.append(
                _issue(
                    "error",
                    "scope_freeze_mismatch",
                    "approved ship-design-review requires scope_freeze.status=frozen and frozen_scope equal to project_scope",
                    "meta.yml",
                )
            )
    elif freeze.get("status") == "frozen" and not scope_freeze_is_valid(meta):
        issues.append(
            _issue(
                "error",
                "scope_freeze_mismatch",
                "scope_freeze.status=frozen must keep project_scope equal to frozen_scope",
                "meta.yml",
            )
        )
    return issues


def _validate_evolve_meta(meta: dict[str, Any]) -> list[dict[str, str]]:
    # validate_evolve_source emits evolve_source_missing when no baseline exists.
    return [_issue("error", code, "scenario=evolve requires meta.yml.evolve_source baseline", "meta.yml") for code in validate_evolve_source(meta)]


def _evolve_source_tokens(meta: dict[str, Any]) -> set[str]:
    source = meta.get("evolve_source") if isinstance(meta.get("evolve_source"), dict) else {}
    tokens: set[str] = set()
    for key in ("feature_dirs", "code_paths"):
        values = source.get(key)
        if isinstance(values, list):
            tokens.update(str(item).strip() for item in values if str(item).strip())
    summary = str(source.get("existing_behavior_summary", "")).strip()
    if summary:
        tokens.add(summary)
    return tokens


def _validate_evolve_product_brief(feature_dir: Path, meta: dict[str, Any]) -> list[dict[str, str]]:
    product_brief_path = feature_dir / "product-brief.md"
    if not product_brief_path.exists():
        return []
    try:
        frontmatter, _body = read_frontmatter(product_brief_path)
    except ValueError as exc:
        return [_issue("error", "invalid_product_brief_frontmatter", str(exc), "product-brief.md")]

    base_feature = str(frontmatter.get("base_feature", "")).strip()
    if not base_feature:
        if frontmatter.get("stage_status") == "ready":
            return [
                _issue(
                    "error",
                    "evolve_base_feature_missing",
                    "ready evolve product-brief.md must set base_feature that points back to meta.yml evolve_source",
                    "product-brief.md",
                )
            ]
        return []
    if base_feature in _evolve_source_tokens(meta):
        return []
    level = "error" if frontmatter.get("stage_status") == "ready" else "warning"
    return [
        _issue(
            level,
            "evolve_base_feature_mismatch",
            "product-brief.md base_feature must match meta.yml evolve_source feature_dirs/code_paths/existing_behavior_summary",
            "product-brief.md",
        )
    ]


def _validate_technical_plan_meta(feature_dir: Path, meta: dict[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    technical_plan_source = meta.get("technical_plan_source")
    if not isinstance(technical_plan_source, dict):
        return [_issue("error", "missing_technical_plan_source", "technical_plan_provided requires technical_plan_source", "meta.yml")]

    source_files = technical_plan_source.get("source_files")
    selection_mode = technical_plan_source.get("selection_mode")
    pasted_excerpt_file = technical_plan_source.get("pasted_excerpt_file")
    selected_scope = technical_plan_source.get("selected_scope")
    repository_scan_status = technical_plan_source.get("repository_scan_status")

    if meta.get("project_context") != "existing_project":
        issues.append(_issue("error", "technical_plan_requires_existing_project", "technical_plan_provided requires project_context=existing_project", "meta.yml"))
    if not isinstance(source_files, list):
        issues.append(_issue("error", "invalid_technical_source_files", "technical_plan_source.source_files must be a list", "meta.yml"))
        source_files = []
    if selection_mode not in ("referenced_sections", "pasted_excerpt"):
        issues.append(_issue("error", "invalid_technical_selection_mode", f"invalid technical selection_mode: {selection_mode!r}", "meta.yml"))
    if not any(str(item).strip() for item in source_files) and not str(pasted_excerpt_file or "").strip():
        issues.append(_issue("error", "missing_technical_source", "technical_plan_source requires source_files or pasted_excerpt_file", "meta.yml"))
    if not isinstance(selected_scope, list) or not selected_scope:
        issues.append(_issue("error", "missing_selected_scope", "technical_plan_source.selected_scope must be non-empty", "meta.yml"))
    if selection_mode == "pasted_excerpt":
        if not str(pasted_excerpt_file or "").strip():
            issues.append(_issue("error", "missing_pasted_excerpt_file", "selection_mode=pasted_excerpt requires pasted_excerpt_file", "meta.yml"))
        else:
            pasted_path = Path(str(pasted_excerpt_file))
            if not pasted_path.is_absolute() and not (feature_dir / pasted_path).exists():
                issues.append(_issue("error", "missing_pasted_excerpt_archive", "pasted_excerpt_file must exist relative to feature_dir", "meta.yml"))
    if technical_plan_source.get("ignored_source_policy") != "out_of_scope":
        issues.append(_issue("error", "invalid_ignored_source_policy", "technical_plan_source.ignored_source_policy must be out_of_scope", "meta.yml"))
    if technical_plan_source.get("repository_scan_required") is not True:
        issues.append(_issue("error", "repository_scan_required", "technical_plan_source.repository_scan_required must be true", "meta.yml"))
    if repository_scan_status not in TECHNICAL_PLAN_SCAN_STATUSES:
        issues.append(_issue("error", "invalid_repository_scan_status", f"invalid repository_scan_status: {repository_scan_status!r}", "meta.yml"))

    stages = meta.get("stages") if isinstance(meta.get("stages"), dict) else {}
    tech_discovery = stages.get("ship-tech-discovery") if isinstance(stages.get("ship-tech-discovery"), dict) else {}
    if tech_discovery.get("status") in ("ready", "completed"):
        if not repository_scan_status == "ready":
            issues.append(_issue("error", "repository_scan_not_ready", "repository_scan_status must be ready after ship-tech-discovery is ready", "meta.yml"))
        confirmation = technical_plan_source.get("selected_scope_ac_confirmation")
        if not isinstance(confirmation, dict):
            issues.append(_issue("error", "missing_selected_scope_ac_confirmation", "technical_plan_source.selected_scope_ac_confirmation is required", "meta.yml"))
        else:
            if not confirmation.get("status") == "confirmed":
                issues.append(_issue("error", "selected_scope_ac_not_confirmed", "selected_scope_ac_confirmation.status must be confirmed before contract", "meta.yml"))
            if not confirmation.get("user_sign_off") or not confirmation.get("confirmed_at"):
                issues.append(_issue("error", "selected_scope_ac_unsigned", "selected_scope_ac_confirmation requires user_sign_off and confirmed_at", "meta.yml"))
            confirmed_ac_ids = confirmation.get("confirmed_ac_ids")
            if not isinstance(confirmed_ac_ids, list) or not confirmed_ac_ids:
                issues.append(_issue("error", "selected_scope_ac_ids_missing", "selected_scope_ac_confirmation.confirmed_ac_ids must be non-empty", "meta.yml"))
            else:
                requirements_path = feature_dir / "requirements.md"
                if requirements_path.exists():
                    _fm, requirements_body = read_frontmatter(requirements_path)
                    body_ac_ids = set(AC_RE.findall(requirements_body))
                    if not body_ac_ids:
                        issues.append(_issue("error", "technical_plan_requirements_ac_ids_missing", "technical_plan requirements body must contain AC IDs", "requirements.md"))
                    missing = sorted(body_ac_ids - set(str(item) for item in confirmed_ac_ids))
                    if missing:
                        issues.append(_issue("error", "selected_scope_ac_confirmation_incomplete", "confirmed_ac_ids do not cover requirements AC IDs: " + ", ".join(missing), "meta.yml"))

    return issues


def _validate_artifact_spec(feature_dir: Path, meta: dict[str, Any], spec: ArtifactSpec) -> tuple[dict[str, Any] | None, list[dict[str, str]]]:
    path = feature_dir / spec.path
    issues: list[dict[str, str]] = []
    if not path.exists():
        if _artifact_required(meta, spec) and _stage_meta(meta, spec.stage).get("status") != "skipped":
            issues.append(_issue("error", "missing_artifact", f"required artifact missing for {spec.stage}", spec.path))
        return None, issues

    try:
        frontmatter, _body = read_frontmatter(path)
    except ValueError as exc:
        return None, [_issue("error", "invalid_frontmatter", str(exc), spec.path)]

    expected_stage = spec.frontmatter_stage or spec.stage
    if frontmatter.get("stage") != expected_stage:
        issues.append(_issue("error", "stage_frontmatter_mismatch", f"expected stage {expected_stage}, found {frontmatter.get('stage')!r}", spec.path))

    if spec.role and frontmatter.get("artifact_role") != spec.role:
        issues.append(_issue("error", "artifact_role_mismatch", f"expected artifact_role {spec.role}, found {frontmatter.get('artifact_role')!r}", spec.path))

    if spec.kind == "review":
        if frontmatter.get("gate_type") != "hard":
            issues.append(_issue("error", "invalid_gate_type", "review gate artifact must set gate_type: hard", spec.path))
        review_status = frontmatter.get("review_status")
        if review_status not in REVIEW_STATUSES:
            issues.append(_issue("error", "invalid_review_status", f"invalid review_status: {review_status!r}", spec.path))
        if review_status == "approved" and (not frontmatter.get("user_sign_off") or not frontmatter.get("signed_at")):
            issues.append(_issue("error", "unsigned_approved_gate", "approved hard gate requires user_sign_off and signed_at", spec.path))
    else:
        stage_status = frontmatter.get("stage_status")
        if stage_status not in NON_REVIEW_STATUSES:
            issues.append(_issue("error", "invalid_stage_status", f"invalid stage_status: {stage_status!r}", spec.path))
        if "evidence_complete" not in frontmatter:
            issues.append(_issue("warning", "missing_evidence_complete", "artifact frontmatter should include evidence_complete", spec.path))
        blocking_gaps = frontmatter.get("blocking_gaps")
        if stage_status == "ready" and isinstance(blocking_gaps, list) and blocking_gaps:
            issues.append(_issue("error", "ready_with_blocking_gaps", "artifact ready cannot contain blocking_gaps", spec.path))
        if spec.path == "design-brief.md":
            if frontmatter.get("activation_mode") == "uiux_material_gate_insert" and (not frontmatter.get("uiux_gate_user_sign_off") or not frontmatter.get("uiux_gate_signed_at")):
                issues.append(_issue("error", "missing_uiux_gate_sign_off", "inserted design-brief requires UIUX gate sign-off", spec.path))
            if stage_status == "ready" and frontmatter.get("browser_verified") is not True:
                issues.append(_issue("error", "design_brief_browser_not_verified", "ready design-brief requires browser_verified: true", spec.path))
        if spec.path == "product-brief.md" and stage_status == "ready" and not frontmatter.get("user_direction_sign_off"):
            level = "error" if frontmatter.get("discovery_mode") == "greenfield" and frontmatter.get("approach_selected") else "warning"
            issues.append(_issue(level, "missing_product_direction_sign_off", "ready product-brief should record user_direction_sign_off", spec.path))
        if spec.path == "verification.md" and stage_status in ("ready", "complete"):
            produced_by = frontmatter.get("produced_by")
            if not isinstance(produced_by, list) or "ship-verify" not in produced_by:
                issues.append(_issue("error", "missing_verification_produced_by", "ready/complete verification.md requires produced_by including ship-verify", spec.path))
            if not frontmatter.get("accepted_by") == "ship-handoff":
                issues.append(_issue("error", "invalid_verification_accepted_by", "verification.md requires accepted_by: ship-handoff", spec.path))
            phase = frontmatter.get("artifact_phase")
            if stage_status == "ready" and phase not in {"testing", "acceptance"}:
                issues.append(_issue("error", "invalid_verification_artifact_phase", "ready verification.md requires artifact_phase testing or acceptance", spec.path))
            if stage_status == "complete" and not phase == "acceptance":
                issues.append(_issue("error", "verification_complete_not_acceptance", "complete verification.md requires artifact_phase: acceptance", spec.path))

    stage_meta = _stage_meta(meta, spec.stage)
    meta_status = stage_meta.get("status")
    if spec.kind == "review":
        review_status = frontmatter.get("review_status")
        if meta_status in REVIEW_STATUSES and review_status in REVIEW_STATUSES and meta_status != review_status:
            issues.append(_issue("error", "meta_artifact_status_conflict", f"meta status {meta_status!r} conflicts with review_status {review_status!r}", spec.path))
        approved = stage_meta.get("approved")
        if isinstance(approved, bool) and review_status == "approved" and not approved:
            issues.append(_issue("error", "meta_artifact_status_conflict", "meta approved=false conflicts with approved review artifact", spec.path))
    else:
        stage_status = frontmatter.get("stage_status")
        if meta_status in ("ready", "completed") and stage_status in NON_REVIEW_STATUSES:
            expected = "ready" if meta_status == "ready" else "complete"
            if meta_status == "completed" and stage_status == "ready":
                pass
            elif not stage_status == expected:
                issues.append(_issue("error", "meta_artifact_status_conflict", f"meta status {meta_status!r} conflicts with stage_status {stage_status!r}", spec.path))
        blocking_gaps = frontmatter.get("blocking_gaps")
        if meta_status in ("ready", "completed") and isinstance(blocking_gaps, list) and blocking_gaps:
            issues.append(_issue("error", "meta_ready_with_blocking_gaps", "meta ready/completed conflicts with artifact blocking_gaps", spec.path))

    return frontmatter, issues


def _review_artifact_approved(artifacts: dict[str, dict[str, Any]], path: str) -> bool:
    artifact = artifacts.get(path)
    if not artifact:
        return False
    fm = artifact["frontmatter"]
    return fm.get("review_status") == "approved" and bool(fm.get("user_sign_off")) and bool(fm.get("signed_at"))


def _validate_scope_freeze_artifacts(meta: dict[str, Any], artifacts: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    if not _review_artifact_approved(artifacts, "review-design.md"):
        return []
    if not scope_freeze(meta):
        return [_issue("error", "scope_freeze_missing", "approved review-design.md requires scope_freeze", "meta.yml")]
    if not scope_freeze_is_valid(meta):
        return [_issue("error", "scope_freeze_mismatch", "project_scope conflicts with frozen_scope after design review", "meta.yml")]
    return []


def _validate_backend_contract_material(meta: dict[str, Any], requirements_fm: dict[str, Any], requirements_body: str) -> list[dict[str, str]]:
    if meta.get("scenario") != "prd_direct":
        return []
    if normalize_project_scope(meta.get("project_scope")) != "backend_only":
        return []
    if requirements_fm.get("stage_status") != "ready":
        return []
    if requirements_fm.get("generation_mode") not in ("prd_direct", None):
        return []
    material_text = yaml.safe_dump(requirements_fm, allow_unicode=True, sort_keys=False) + "\n" + requirements_body
    if backend_contract_material_present(material_text):
        return []
    return [
        _issue(
            "error",
            "backend_contract_material_missing",
            "D + backend_only requires contract-level material such as OpenAPI, endpoint list, API spec, message protocol, CLI spec, SDK, or request/response source index",
            "requirements.md",
        )
    ]


def validate_feature(feature_dir: Path) -> dict[str, Any]:
    feature_dir = feature_dir.resolve()
    meta_path = feature_dir / "meta.yml"
    issues: list[dict[str, str]] = []
    artifacts: dict[str, dict[str, Any]] = {}

    if not meta_path.exists():
        return {
            "feature_dir": str(feature_dir),
            "ok": False,
            "issues": [_issue("error", "missing_meta", "feature dir missing meta.yml", "meta.yml")],
            "artifacts": {},
        }

    try:
        meta = load_meta(meta_path)
    except Exception as exc:
        return {
            "feature_dir": str(feature_dir),
            "ok": False,
            "issues": [_issue("error", "invalid_meta", str(exc), "meta.yml")],
            "artifacts": {},
        }

    issues.extend(_validate_meta(feature_dir, meta))
    project_scope = normalize_project_scope(meta.get("project_scope", "fullstack"))
    if project_scope in ("backend_only", "frontend_only"):
        if not str(meta.get("project_scope_evidence", "")).strip():
            issues.append(
                _issue(
                    "error",
                    "missing_project_scope_evidence",
                    f"{project_scope} scope requires project_scope_evidence",
                    "meta.yml",
                )
            )
    for spec in ARTIFACT_SPECS:
        frontmatter, spec_issues = _validate_artifact_spec(feature_dir, meta, spec)
        issues.extend(spec_issues)
        if frontmatter is not None:
            artifacts[spec.path] = {
                "stage": spec.stage,
                "kind": spec.kind,
                "artifact_role": spec.role,
                "frontmatter": frontmatter,
            }

    for relative_path in _scope_forbidden_artifacts(str(project_scope)):
        if (feature_dir / relative_path).exists():
            issues.append(
                _issue(
                    "error",
                    "scope_forbidden_artifact",
                    f"{project_scope} scope must not include {relative_path}",
                    relative_path,
                )
            )

    requirements_path = feature_dir / "requirements.md"
    if requirements_path.exists():
        from validate_requirements import validate_requirements_file  # noqa: WPS433

        requirements_result = validate_requirements_file(requirements_path)
        issues.extend(requirements_result["issues"])
        try:
            requirements_fm, _requirements_body = read_frontmatter(requirements_path)
            issues.extend(_validate_backend_contract_material(meta, requirements_fm, _requirements_body))
            if is_raw_prd_inbox_frontmatter(requirements_fm):
                current_stage = meta.get("current_stage")
                if current_stage in CANONICAL_STAGE_ORDER and CANONICAL_STAGE_ORDER.index(str(current_stage)) > CANONICAL_STAGE_ORDER.index("ship-define"):
                    issues.append(_issue("error", "raw_inbox_past_define", "raw requirements.md inbox cannot advance past ship-define", "requirements.md"))
                if _stage_meta(meta, "ship-define").get("status") in ("ready", "completed"):
                    issues.append(_issue("error", "raw_inbox_marked_structured", "raw requirements.md inbox cannot be marked as structured/ready", "requirements.md"))
                review_path = feature_dir / "review-define.md"
                if review_path.exists():
                    review_fm, _review_body = read_frontmatter(review_path)
                    if review_fm.get("review_status") == "approved":
                        issues.append(_issue("error", "raw_inbox_approved_gate", "raw requirements.md inbox cannot have approved define review", "requirements.md"))
        except ValueError as exc:
            issues.append(_issue("error", "invalid_requirements_frontmatter", str(exc), "requirements.md"))

    if (feature_dir / "product-brief.md").exists():
        from validate_product_brief import validate_product_brief  # noqa: WPS433

        product_brief_result = validate_product_brief(feature_dir / "product-brief.md")
        issues.extend(product_brief_result["issues"])

    if (feature_dir / "design-brief.md").exists():
        from validate_ui_artifacts import validate_ui_artifacts  # noqa: WPS433

        ui_result = validate_ui_artifacts(feature_dir)
        issues.extend(ui_result["issues"])

    issues.extend(_validate_scope_freeze_artifacts(meta, artifacts))

    if (feature_dir / "tech-research.md").exists() or (feature_dir / "tech-selection.md").exists():
        from validate_tech_discovery import validate_tech_discovery  # noqa: WPS433

        tech_result = validate_tech_discovery(feature_dir)
        issues.extend(tech_result["issues"])

    contract_path = feature_dir / "api-contract.md"
    if contract_path.exists():
        from validate_contract import validate_contract_file  # noqa: WPS433

        contract_result = validate_contract_file(contract_path)
        issues.extend(contract_result["issues"])

    if (feature_dir / "frontend-design.md").exists():
        from validate_frontend_design import validate_frontend_design  # noqa: WPS433

        frontend_result = validate_frontend_design(feature_dir / "frontend-design.md")
        issues.extend(frontend_result["issues"])

    if (feature_dir / "backend-design.md").exists():
        from validate_backend_design import validate_backend_design  # noqa: WPS433

        backend_result = validate_backend_design(feature_dir / "backend-design.md")
        issues.extend(backend_result["issues"])

    if (feature_dir / "api-contract.md").exists() and (
        (feature_dir / "frontend-design.md").exists() or (feature_dir / "backend-design.md").exists()
    ):
        from validate_design_alignment import validate_design_alignment  # noqa: WPS433

        project_scope = normalize_project_scope(meta.get("project_scope", "fullstack"))
        design_alignment_result = validate_design_alignment(feature_dir, project_scope)
        issues.extend(design_alignment_result["issues"])

    if (feature_dir / "frontend-plan.md").exists() or (feature_dir / "backend-plan.md").exists():
        from validate_delivery_plan import validate_delivery_plan  # noqa: WPS433

        project_scope = normalize_project_scope(meta.get("project_scope", "fullstack"))
        delivery_plan_result = validate_delivery_plan(feature_dir, project_scope)
        issues.extend(delivery_plan_result["issues"])

    verification_path = feature_dir / "verification.md"
    if verification_path.exists():
        from validate_verification import validate_verification_file  # noqa: WPS433

        project_scope = normalize_project_scope(meta.get("project_scope", "fullstack"))
        verification_result = validate_verification_file(verification_path, project_scope)
        issues.extend(verification_result["issues"])

    if (feature_dir / "handoff.md").exists():
        from validate_handoff import validate_handoff  # noqa: WPS433

        handoff_result = validate_handoff(feature_dir)
        issues.extend(handoff_result["issues"])

    for entry in meta.get("skip_log", []) if isinstance(meta.get("skip_log"), list) else []:
        if isinstance(entry, dict):
            gate_type = str(entry.get("gate_type", "")).lower()
            from_stage = str(entry.get("from_stage", ""))
            reason = str(entry.get("reason", "")).lower()
            if gate_type == "hard":
                issues.append(_issue("error", "hard_gate_skip_not_allowed", "hard gates cannot be skipped via skip_log", "meta.yml"))
            if gate_type == "soft" and (from_stage in SOFT_BLOCKING_STAGES or "soft_blocking" in reason):
                issues.append(_issue("error", "soft_blocking_skip_not_allowed", "soft_blocking gates cannot be bypassed by skip_log", "meta.yml"))

    return {
        "feature_dir": str(feature_dir),
        "ok": not any(issue["level"] == "error" for issue in issues),
        "issues": issues,
        "artifacts": artifacts,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate ship feature artifact frontmatter")
    parser.add_argument("feature_dir", help="Feature directory containing meta.yml")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    return parser


def main(argv: list[str]) -> int:
    args = build_parser().parse_args(argv[1:])
    result = validate_feature(Path(args.feature_dir))
    if args.json:
        print(json.dumps(result, ensure_ascii=True, indent=2))
    else:
        print(f"feature_dir: {result['feature_dir']}")
        print(f"ok: {str(result['ok']).lower()}")
        for issue in result["issues"]:
            path = f" [{issue['path']}]" if "path" in issue else ""
            print(f"{issue['level'].upper()} {issue['code']}{path}: {issue['message']}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
