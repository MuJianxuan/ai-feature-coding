#!/usr/bin/env python3
"""Check whether a ship feature may advance to a target stage."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from feature_meta_runtime import load_meta  # noqa: E402
from validate_feature_artifacts import ARTIFACTS_BY_STAGE, REVIEW_STAGES, validate_feature  # noqa: E402
from workflow_stage_map import CANONICAL_STAGE_ORDER  # noqa: E402


FAST_TRACK_REQUIRED_STAGES: tuple[str, ...] = (
    "ship-discover",
    "ship-define",
    "ship-define-review",
    "ship-build",
    "ship-verify",
    "ship-handoff",
)


def _issue(level: str, code: str, message: str, path: str | None = None) -> dict[str, str]:
    payload = {"level": level, "code": code, "message": message}
    if path:
        payload["path"] = path
    return payload


def _stage_meta(meta: dict[str, Any], stage: str) -> dict[str, Any]:
    stages = meta.get("stages")
    if not isinstance(stages, dict):
        return {}
    value = stages.get(stage)
    return value if isinstance(value, dict) else {}


def _artifact_for_stage(validation: dict[str, Any], stage: str, *, prefer_role: str | None = None) -> dict[str, Any] | None:
    specs = ARTIFACTS_BY_STAGE.get(stage, ())
    artifacts = validation.get("artifacts", {})
    for spec in specs:
        if prefer_role and spec.role != prefer_role:
            continue
        artifact = artifacts.get(spec.path)
        if artifact:
            return artifact
    return None


def _is_stage_complete_enough(meta: dict[str, Any], validation: dict[str, Any], stage: str) -> tuple[bool, list[dict[str, str]]]:
    stage_meta = _stage_meta(meta, stage)
    if stage_meta.get("status") == "skipped":
        return True, []

    if stage == "ship-build":
        tasks_done = stage_meta.get("tasks_done")
        tasks_total = stage_meta.get("tasks_total")
        if isinstance(tasks_done, int) and isinstance(tasks_total, int) and tasks_total > 0 and tasks_done >= tasks_total:
            return True, []
        if stage_meta.get("status") == "completed":
            return True, []
        return False, [_issue("error", "build_not_complete", "ship-build requires all tasks done before advancing")]

    artifacts = [
        validation.get("artifacts", {}).get(spec.path)
        for spec in ARTIFACTS_BY_STAGE.get(stage, ())
    ]
    artifacts = [artifact for artifact in artifacts if artifact]
    if not artifacts:
        return False, [_issue("error", "missing_stage_artifact", f"{stage} has no required artifact")]

    if stage in REVIEW_STAGES:
        artifact = artifacts[0]
        fm = artifact["frontmatter"]
        if fm.get("review_status") == "approved" and fm.get("user_sign_off") and fm.get("signed_at"):
            return True, []
        return False, [_issue("error", "gate_not_approved", f"{stage} requires approved review_status plus user_sign_off and signed_at")]

    not_ready = []
    for artifact in artifacts:
        fm = artifact["frontmatter"]
        status = fm.get("stage_status")
        if status not in ("ready", "complete"):
            not_ready.append(artifact["stage"])
    if not_ready:
        return False, [_issue("error", "stage_not_ready", f"{stage} artifact stage_status must be ready or complete")]
    return True, []


def _required_previous_stages(meta: dict[str, Any], target_stage: str) -> list[str]:
    pipeline_mode = meta.get("pipeline_mode", "standard")
    stage_order = FAST_TRACK_REQUIRED_STAGES if pipeline_mode == "fast-track" else CANONICAL_STAGE_ORDER
    if target_stage not in stage_order:
        target_index = CANONICAL_STAGE_ORDER.index(target_stage)
        stages = list(CANONICAL_STAGE_ORDER[:target_index])
    else:
        target_index = stage_order.index(target_stage)
        stages = list(stage_order[:target_index])
    project_scope = meta.get("project_scope", "fullstack")
    scenario = meta.get("scenario", "")

    if scenario in ("product_provided", "prd_direct", "technical_plan_provided"):
        stages = [stage for stage in stages if stage not in ("ship-discover", "ship-shape")]
    if scenario == "technical_plan_provided":
        stages = [stage for stage in stages if stage not in ("ship-define", "ship-define-review")]
    if project_scope == "backend_only":
        stages = [stage for stage in stages if stage not in ("ship-shape", "ship-frontend-design")]
    if project_scope == "frontend_only":
        stages = [stage for stage in stages if stage != "ship-backend-design"]
    return stages


def check_transition(feature_dir: Path, target_stage: str) -> dict[str, Any]:
    feature_dir = feature_dir.resolve()
    if target_stage not in CANONICAL_STAGE_ORDER:
        return {
            "feature_dir": str(feature_dir),
            "target_stage": target_stage,
            "allowed": False,
            "issues": [_issue("error", "invalid_target_stage", f"unknown target_stage: {target_stage}")],
        }

    meta_path = feature_dir / "meta.yml"
    try:
        meta = load_meta(meta_path)
    except Exception as exc:
        return {
            "feature_dir": str(feature_dir),
            "target_stage": target_stage,
            "allowed": False,
            "issues": [_issue("error", "invalid_meta", str(exc), "meta.yml")],
        }

    validation = validate_feature(feature_dir)
    issues = [issue for issue in validation["issues"] if issue["level"] == "error"]
    required_stages = _required_previous_stages(meta, target_stage)
    for stage in required_stages:
        ok, stage_issues = _is_stage_complete_enough(meta, validation, stage)
        if not ok:
            issues.extend(stage_issues)

    current_stage = meta.get("current_stage")
    if current_stage in CANONICAL_STAGE_ORDER:
        if CANONICAL_STAGE_ORDER.index(target_stage) < CANONICAL_STAGE_ORDER.index(current_stage):
            issues.append(_issue("warning", "target_before_current", "target_stage is before current_stage; this is a rollback-style transition"))

    return {
        "feature_dir": str(feature_dir),
        "current_stage": current_stage,
        "target_stage": target_stage,
        "allowed": not any(issue["level"] == "error" for issue in issues),
        "checked_previous_stages": required_stages,
        "issues": issues,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check ship workflow stage transition readiness")
    parser.add_argument("feature_dir", help="Feature directory containing meta.yml")
    parser.add_argument("--target-stage", required=True, choices=CANONICAL_STAGE_ORDER)
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    return parser


def main(argv: list[str]) -> int:
    args = build_parser().parse_args(argv[1:])
    result = check_transition(Path(args.feature_dir), args.target_stage)
    if args.json:
        print(json.dumps(result, ensure_ascii=True, indent=2))
    else:
        print(f"feature_dir: {result['feature_dir']}")
        print(f"current_stage: {result.get('current_stage', '')}")
        print(f"target_stage: {result['target_stage']}")
        print(f"allowed: {str(result['allowed']).lower()}")
        for issue in result["issues"]:
            path = f" [{issue['path']}]" if "path" in issue else ""
            print(f"{issue['level'].upper()} {issue['code']}{path}: {issue['message']}")
    return 0 if result["allowed"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
