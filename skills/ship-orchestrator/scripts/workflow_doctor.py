#!/usr/bin/env python3
"""Diagnose a ship feature workflow state and suggest the next action."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from feature_meta_runtime import load_meta  # noqa: E402
from stage_transition_check import check_transition  # noqa: E402
from validate_feature_artifacts import ARTIFACTS_BY_STAGE, REVIEW_STAGES, validate_feature  # noqa: E402
from workflow_stage_map import CANONICAL_STAGE_ORDER, stage_view_for  # noqa: E402


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


def _artifact_statuses(validation: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    artifacts = validation.get("artifacts", {})
    for stage in CANONICAL_STAGE_ORDER:
        for spec in ARTIFACTS_BY_STAGE.get(stage, ()):
            artifact = artifacts.get(spec.path)
            if not artifact:
                rows.append(
                    {
                        "stage": stage,
                        "path": spec.path,
                        "kind": spec.kind,
                        "exists": False,
                    }
                )
                continue
            fm = artifact["frontmatter"]
            rows.append(
                {
                    "stage": stage,
                    "path": spec.path,
                    "kind": spec.kind,
                    "exists": True,
                    "stage_status": fm.get("stage_status"),
                    "review_status": fm.get("review_status"),
                    "user_sign_off": bool(fm.get("user_sign_off")),
                    "signed_at": bool(fm.get("signed_at")),
                    "artifact_role": fm.get("artifact_role"),
                }
            )
    return rows


def _gate_statuses(validation: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    artifacts = validation.get("artifacts", {})
    for stage in REVIEW_STAGES:
        specs = ARTIFACTS_BY_STAGE.get(stage, ())
        artifact = artifacts.get(specs[0].path) if specs else None
        if not artifact:
            rows.append({"stage": stage, "exists": False, "approved_for_transition": False})
            continue
        fm = artifact["frontmatter"]
        approved = fm.get("review_status") == "approved" and bool(fm.get("user_sign_off")) and bool(fm.get("signed_at"))
        rows.append(
            {
                "stage": stage,
                "exists": True,
                "review_status": fm.get("review_status"),
                "user_sign_off": bool(fm.get("user_sign_off")),
                "signed_at": bool(fm.get("signed_at")),
                "approved_for_transition": approved,
            }
        )
    return rows


def _next_stage(current_stage: str) -> str | None:
    try:
        index = CANONICAL_STAGE_ORDER.index(current_stage)
    except ValueError:
        return None
    if index + 1 >= len(CANONICAL_STAGE_ORDER):
        return None
    return CANONICAL_STAGE_ORDER[index + 1]


def _next_action(meta: dict[str, Any], validation: dict[str, Any], current_stage: str) -> dict[str, Any]:
    if any(issue["level"] == "error" for issue in validation["issues"]):
        return {
            "action": "fix_blocking_issues",
            "detail": "Fix validation errors before advancing; artifact frontmatter is the source of truth.",
        }

    target_stage = _next_stage(current_stage)
    if not target_stage:
        return {"action": "close_or_archive", "detail": "No next canonical stage exists."}

    transition = check_transition(Path(validation["feature_dir"]), target_stage)
    if transition["allowed"]:
        return {
            "action": "advance_stage",
            "target_stage": target_stage,
            "detail": f"Allowed to advance from {current_stage} to {target_stage}.",
        }

    stage_meta = _stage_meta(meta, current_stage)
    if current_stage in REVIEW_STAGES:
        return {
            "action": "complete_hard_gate",
            "target_stage": target_stage,
            "detail": "Hard gate must be approved by the user; review_status, user_sign_off, and signed_at are required.",
            "transition_issues": transition["issues"],
        }

    if stage_meta.get("status") == "blocked":
        return {
            "action": "resolve_blocker",
            "detail": stage_meta.get("block_reason") or "Current stage is marked blocked in meta.yml.",
            "transition_issues": transition["issues"],
        }

    return {
        "action": "finish_current_stage",
        "target_stage": target_stage,
        "detail": f"Current stage {current_stage} is not ready for {target_stage}.",
        "transition_issues": transition["issues"],
    }


def diagnose_feature(feature_dir: Path) -> dict[str, Any]:
    feature_dir = feature_dir.resolve()
    meta_path = feature_dir / "meta.yml"
    if not meta_path.exists():
        return {
            "feature_dir": str(feature_dir),
            "ok": False,
            "issues": [_issue("error", "missing_meta", "feature dir missing meta.yml", "meta.yml")],
        }

    try:
        meta = load_meta(meta_path)
    except Exception as exc:
        return {
            "feature_dir": str(feature_dir),
            "ok": False,
            "issues": [_issue("error", "invalid_meta", str(exc), "meta.yml")],
        }

    current_stage = meta.get("current_stage", "")
    validation = validate_feature(feature_dir)
    issues = list(validation["issues"])
    if current_stage not in CANONICAL_STAGE_ORDER:
        issues.append(_issue("error", "invalid_current_stage", f"invalid current_stage: {current_stage!r}", "meta.yml"))
        macro_stage = {}
        next_action = {"action": "fix_meta", "detail": "Set current_stage to a canonical stage id."}
    else:
        view = stage_view_for(current_stage)
        macro_stage = {
            "current": view.macro.current,
            "label": view.macro.label,
            "summary": view.summary,
            "next_user_decision": view.next_user_decision,
        }
        next_action = _next_action(meta, validation, current_stage)

    return {
        "feature_dir": str(feature_dir),
        "ok": not any(issue["level"] == "error" for issue in issues),
        "current_stage": current_stage,
        "macro_stage": macro_stage,
        "lifecycle_status": meta.get("lifecycle_status"),
        "project_scope": meta.get("project_scope"),
        "scenario": meta.get("scenario"),
        "artifact_status": _artifact_statuses(validation),
        "gate_status": _gate_statuses(validation),
        "issues": issues,
        "next_action": next_action,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Diagnose ship workflow feature state")
    parser.add_argument("feature_dir", help="Feature directory containing meta.yml")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    return parser


def main(argv: list[str]) -> int:
    args = build_parser().parse_args(argv[1:])
    result = diagnose_feature(Path(args.feature_dir))
    if args.json:
        print(json.dumps(result, ensure_ascii=True, indent=2))
    else:
        print(f"feature_dir: {result['feature_dir']}")
        print(f"ok: {str(result.get('ok', False)).lower()}")
        print(f"current_stage: {result.get('current_stage', '')}")
        macro = result.get("macro_stage") or {}
        print(f"macro_stage: {macro.get('label', '')} ({macro.get('current', '')})")
        next_action = result.get("next_action") or {}
        print(f"next_action: {next_action.get('action', '')}")
        if next_action.get("detail"):
            print(f"next_action.detail: {next_action['detail']}")
        for issue in result.get("issues", []):
            path = f" [{issue['path']}]" if "path" in issue else ""
            print(f"{issue['level'].upper()} {issue['code']}{path}: {issue['message']}")
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
