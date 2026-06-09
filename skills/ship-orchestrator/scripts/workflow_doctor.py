#!/usr/bin/env python3
"""Diagnose a ship feature workflow state and suggest the next action."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from feature_meta_runtime import load_meta, read_last_workflow_events, resolve_and_validate_feature_dir  # noqa: E402
from stage_transition_check import check_transition  # noqa: E402
from build_task_preflight import build_task_preflight, file_matches_allowed, normalize_allowed_file_pattern  # noqa: E402
from validate_feature_artifacts import ARTIFACTS_BY_STAGE, REVIEW_STAGES, validate_feature  # noqa: E402
from workflow_invariants import stage_meta  # noqa: E402
from workflow_stage_map import CANONICAL_STAGE_ORDER, stage_view_for  # noqa: E402


def _issue(level: str, code: str, message: str, path: str | None = None) -> dict[str, str]:
    payload = {"level": level, "code": code, "message": message}
    if path:
        payload["path"] = path
    return payload


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
            rows.append({"stage": stage, "exists": False, "checklist_passed": False})
            continue
        fm = artifact["frontmatter"]
        passed = fm.get("review_status") in {"approved", "pass"}
        rows.append(
            {
                "stage": stage,
                "exists": True,
                "review_status": fm.get("review_status"),
                "checklist_passed": passed,
                "optional_user_confirmation": bool(fm.get("user_sign_off") and fm.get("signed_at")),
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

    current_stage_meta = stage_meta(meta, current_stage)
    if current_stage in REVIEW_STAGES:
        return {
            "action": "finish_review_checklist",
            "target_stage": target_stage,
            "detail": "Review checklists are optional support artifacts; mark pass/needs_revision/blocked and record accepted_risks if needed.",
            "transition_issues": transition["issues"],
        }

    if current_stage_meta.get("status") == "blocked":
        return {
            "action": "resolve_blocker",
            "detail": current_stage_meta.get("block_reason") or "Current stage is marked blocked in meta.yml.",
            "transition_issues": transition["issues"],
        }

    return {
        "action": "finish_current_stage",
        "target_stage": target_stage,
        "detail": f"Current stage {current_stage} is not ready for {target_stage}.",
        "transition_issues": transition["issues"],
    }


def _git_status(workspace_root: Path) -> list[str]:
    try:
        completed = subprocess.run(
            ["git", "-C", str(workspace_root), "status", "--porcelain"],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
    except OSError:
        return []
    if completed.returncode != 0:
        return []
    files: list[str] = []
    for line in completed.stdout.splitlines():
        if not line.strip():
            continue
        status_path = line[3:].strip() if len(line) > 3 else line.strip()
        candidate = workspace_root / status_path
        if status_path.endswith("/") and candidate.is_dir():
            files.extend(str(path.relative_to(workspace_root)) for path in candidate.rglob("*") if path.is_file())
        else:
            files.append(status_path)
    return sorted(set(files))


def _classify_worktree_changes(workspace_root: Path, feature_root: Path, changed_files: list[str]) -> dict[str, Any]:
    workflow_artifact_changes: list[str] = []
    implementation_changes: list[str] = []
    feature_root_rel = feature_root.relative_to(workspace_root).as_posix()
    for changed_file in changed_files:
        normalized = changed_file.strip().strip('"')
        if not normalized:
            continue
        if normalized.startswith(feature_root_rel + "/feature-"):
            workflow_artifact_changes.append(normalized)
        else:
            implementation_changes.append(normalized)
    return {
        "worktree_status": changed_files,
        "implementation_changes": implementation_changes,
        "workflow_artifact_changes": workflow_artifact_changes,
    }


def _outside_allowed_files(feature_dir: Path, project_scope: str, implementation_changes: list[str]) -> list[str]:
    if not implementation_changes:
        return []
    try:
        build_result = build_task_preflight(feature_dir, project_scope)
    except Exception:
        return implementation_changes
    doing = build_result.get("doing_tasks") or []
    if not doing:
        return implementation_changes
    allowed_files = doing[0].get("allowed_files", [])
    outside: list[str] = []
    for changed_file in implementation_changes:
        try:
            normalize_allowed_file_pattern(changed_file)
        except ValueError:
            outside.append(changed_file)
            continue
        if not any(file_matches_allowed(changed_file, allowed_file) for allowed_file in allowed_files):
            outside.append(changed_file)
    return outside


def diagnose_feature(feature_dir: Path) -> dict[str, Any]:
    feature_dir = feature_dir.resolve()
    feature_context = None
    try:
        feature_context = resolve_and_validate_feature_dir(feature_dir)
        feature_dir = feature_context.feature_dir
    except Exception as exc:
        return {
            "feature_dir": str(feature_dir),
            "ok": False,
            "issues": [_issue("error", "invalid_feature_dir", str(exc))],
        }
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
    workflow_events = read_last_workflow_events(feature_dir)
    worktree = _classify_worktree_changes(
        feature_context.workspace_root,
        feature_context.feature_root,
        _git_status(feature_context.workspace_root),
    ) if feature_context else {"worktree_status": [], "implementation_changes": [], "workflow_artifact_changes": []}
    outside_allowed_files: list[str] = []
    if current_stage in CANONICAL_STAGE_ORDER:
        if CANONICAL_STAGE_ORDER.index(current_stage) < CANONICAL_STAGE_ORDER.index("ship-build") and worktree["implementation_changes"]:
            issues.append(_issue("error", "implementation_changes_before_build_gate", "implementation changes exist before ship-build gate"))
        elif current_stage == "ship-build":
            outside_allowed_files = _outside_allowed_files(feature_dir, str(meta.get("project_scope") or "fullstack"), worktree["implementation_changes"])
            if outside_allowed_files:
                issues.append(_issue("error", "implementation_changes_outside_allowed_files", "implementation changes are outside current DOING task allowed_files"))
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
        "workspace_root": str(feature_context.workspace_root) if feature_context else None,
        "feature_root": str(feature_context.feature_root) if feature_context else None,
        "feature_dir_validated": feature_context is not None,
        "ok": not any(issue["level"] == "error" for issue in issues),
        "current_stage": current_stage,
        "macro_stage": macro_stage,
        "lifecycle_status": meta.get("lifecycle_status"),
        "project_scope": meta.get("project_scope"),
        "scenario": meta.get("scenario"),
        "artifact_status": _artifact_statuses(validation),
        "gate_status": _gate_statuses(validation),
        "worktree_status": worktree["worktree_status"],
        "implementation_changes": worktree["implementation_changes"],
        "workflow_artifact_changes": worktree["workflow_artifact_changes"],
        "outside_allowed_files": outside_allowed_files,
        "workflow_events": workflow_events,
        "last_transition_event": next((event for event in reversed(workflow_events) if event.get("type") == "stage_transition"), None),
        "last_validator_event": next((event for event in reversed(workflow_events) if event.get("type") == "validator_run"), None),
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
