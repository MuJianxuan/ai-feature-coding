#!/usr/bin/env python3
"""Validate ship feature artifacts against workflow frontmatter contracts."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from feature_meta_runtime import load_meta  # noqa: E402
from workflow_stage_map import CANONICAL_STAGE_ORDER, stage_view_for  # noqa: E402

NON_REVIEW_STATUSES = frozenset({"draft", "ready", "complete"})
REVIEW_STATUSES = frozenset({"pending", "approved", "rejected", "revision_needed"})
META_NON_REVIEW_STATUSES = frozenset({"pending", "in_progress", "ready", "blocked", "completed", "skipped"})
META_REVIEW_STATUSES = frozenset({"pending", "in_progress", "approved", "rejected", "revision_needed", "skipped"})
REVIEW_STAGES = frozenset({"ship-define-review", "ship-design-review", "ship-plan-review"})


@dataclass(frozen=True)
class ArtifactSpec:
    stage: str
    path: str
    kind: str
    role: str | None = None


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
    ArtifactSpec("ship-build", "fast-track-tasks.md", "artifact", "fast-track-tasks"),
    ArtifactSpec("ship-plan-review", "review-plan.md", "review"),
    ArtifactSpec("ship-verify", "verification.md", "artifact"),
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


def _stage_meta(meta: dict[str, Any], stage: str) -> dict[str, Any]:
    stages = meta.get("stages")
    if not isinstance(stages, dict):
        return {}
    value = stages.get(stage)
    return value if isinstance(value, dict) else {}


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
    pipeline_mode = meta.get("pipeline_mode", "standard")
    if pipeline_mode == "fast-track":
        if spec.stage in (
            "ship-shape",
            "ship-tech-discovery",
            "ship-contract",
            "ship-frontend-design",
            "ship-backend-design",
            "ship-design-review",
            "ship-delivery-plan",
            "ship-plan-review",
        ):
            return False
        if spec.path == "fast-track-tasks.md":
            return _stage_is_active_enough(meta, spec.stage)
    elif spec.path == "fast-track-tasks.md":
        return False

    project_scope = meta.get("project_scope", "fullstack")
    if project_scope == "backend_only" and spec.stage in ("ship-shape", "ship-frontend-design"):
        return False
    if project_scope == "frontend_only" and spec.stage == "ship-backend-design":
        return False

    return _stage_is_active_enough(meta, spec.stage)


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

    if frontmatter.get("stage") != spec.stage:
        issues.append(_issue("error", "stage_frontmatter_mismatch", f"expected stage {spec.stage}, found {frontmatter.get('stage')!r}", spec.path))

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
            elif stage_status != expected:
                issues.append(_issue("error", "meta_artifact_status_conflict", f"meta status {meta_status!r} conflicts with stage_status {stage_status!r}", spec.path))

    return frontmatter, issues


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

    requirements_path = feature_dir / "requirements.md"
    if requirements_path.exists():
        from validate_requirements import validate_requirements_file  # noqa: WPS433

        requirements_result = validate_requirements_file(requirements_path)
        issues.extend(requirements_result["issues"])

    if (feature_dir / "product-brief.md").exists():
        from validate_product_brief import validate_product_brief  # noqa: WPS433

        product_brief_result = validate_product_brief(feature_dir / "product-brief.md")
        issues.extend(product_brief_result["issues"])

    if (feature_dir / "design-brief.md").exists():
        from validate_ui_artifacts import validate_ui_artifacts  # noqa: WPS433

        ui_result = validate_ui_artifacts(feature_dir)
        issues.extend(ui_result["issues"])

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

        project_scope = meta.get("project_scope", "fullstack")
        if project_scope not in ("fullstack", "backend_only", "frontend_only"):
            project_scope = "fullstack"
        design_alignment_result = validate_design_alignment(feature_dir, project_scope)
        issues.extend(design_alignment_result["issues"])

    if (feature_dir / "frontend-plan.md").exists() or (feature_dir / "backend-plan.md").exists():
        from validate_delivery_plan import validate_delivery_plan  # noqa: WPS433

        project_scope = meta.get("project_scope", "fullstack")
        if project_scope not in ("fullstack", "backend_only", "frontend_only"):
            project_scope = "fullstack"
        delivery_plan_result = validate_delivery_plan(feature_dir, project_scope)
        issues.extend(delivery_plan_result["issues"])

    verification_path = feature_dir / "verification.md"
    if verification_path.exists():
        from validate_verification import validate_verification_file  # noqa: WPS433

        project_scope = meta.get("project_scope", "fullstack")
        if project_scope not in ("fullstack", "backend_only", "frontend_only"):
            project_scope = "fullstack"
        verification_result = validate_verification_file(verification_path, project_scope)
        issues.extend(verification_result["issues"])

    if (feature_dir / "handoff.md").exists():
        from validate_handoff import validate_handoff  # noqa: WPS433

        handoff_result = validate_handoff(feature_dir)
        issues.extend(handoff_result["issues"])

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
