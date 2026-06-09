#!/usr/bin/env python3
"""Unified lightweight preflight before implementation edits.

The solo-developer workflow checks that implementation is scoped to the active
DOING slice. It no longer requires review-plan.md user sign-off by default.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from build_task_preflight import build_task_preflight, file_matches_allowed, normalize_allowed_file_pattern  # noqa: E402
from feature_meta_runtime import load_meta, resolve_and_validate_feature_dir  # noqa: E402
from workflow_stage_map import CANONICAL_STAGE_ORDER  # noqa: E402


def _issue(level: str, code: str, message: str, path: str | None = None) -> dict[str, str]:
    payload = {"level": level, "code": code, "message": message}
    if path:
        payload["path"] = path
    return payload


def _stage_ready_enough(meta: dict[str, Any], stage: str) -> bool:
    stages = meta.get("stages")
    if not isinstance(stages, dict):
        return False
    value = stages.get(stage)
    if not isinstance(value, dict):
        return False
    return value.get("status") in {"ready", "completed", "skipped"}


def _previous_runtime_issues(meta: dict[str, Any]) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    current_stage = meta.get("current_stage")
    if current_stage not in CANONICAL_STAGE_ORDER:
        return [_issue("error", "invalid_current_stage", f"invalid current_stage: {current_stage!r}", "meta.yml")]
    if current_stage != "ship-build":
        return [_issue("error", "current_stage_not_ship_build", "implementation edits require meta.yml.current_stage == ship-build", "meta.yml")]
    for stage in CANONICAL_STAGE_ORDER[:CANONICAL_STAGE_ORDER.index("ship-build")]:
        if not _stage_ready_enough(meta, stage):
            # Lightweight mode permits compressed stages, but incomplete plan is unsafe.
            if stage == "ship-delivery-plan":
                issues.append(_issue("error", "plan_stage_not_ready", "ship-delivery-plan must be ready, completed, or skipped before source edits", "meta.yml"))
            else:
                issues.append(_issue("warning", "compressed_or_incomplete_stage", f"{stage} is not marked ready/completed/skipped", "meta.yml"))
    return issues


def implementation_preflight(
    feature_dir: Path,
    project_scope: str = "fullstack",
    files: list[str] | None = None,
    strict_files: bool = True,
) -> dict[str, Any]:
    feature_dir = feature_dir.resolve()
    issues: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    feature_context = None

    try:
        feature_context = resolve_and_validate_feature_dir(feature_dir)
        feature_dir = feature_context.feature_dir
    except Exception as exc:
        warnings.append(_issue("warning", "feature_dir_context_unresolved", str(exc)))

    meta_path = feature_dir / "meta.yml"
    if not meta_path.exists():
        return {
            "allowed": False,
            "current_stage": None,
            "required_stage": "ship-build",
            "issues": [_issue("error", "missing_meta", "meta.yml does not exist", "meta.yml")],
        }

    try:
        meta = load_meta(meta_path)
    except Exception as exc:
        return {
            "allowed": False,
            "current_stage": None,
            "required_stage": "ship-build",
            "issues": [_issue("error", "invalid_meta", str(exc), "meta.yml")],
        }

    current_stage = meta.get("current_stage")
    for issue in _previous_runtime_issues(meta):
        if issue["level"] == "error":
            issues.append(issue)
        else:
            warnings.append(issue)

    build_result = build_task_preflight(feature_dir, project_scope)
    if not build_result["ok"]:
        for issue in build_result["issues"]:
            if issue["level"] == "error":
                issues.append(issue)
            else:
                warnings.append(issue)

    target_files: list[str] = []
    if files:
        workspace_root = feature_context.workspace_root if feature_context else feature_dir.parent.parent.resolve()
        for raw_file in files:
            try:
                candidate = Path(raw_file)
                if candidate.is_absolute():
                    resolved = candidate.resolve()
                    try:
                        normalized = resolved.relative_to(workspace_root).as_posix()
                    except ValueError as exc:
                        raise ValueError("target file escapes workspace_root") from exc
                else:
                    normalized = normalize_allowed_file_pattern(raw_file)
                normalize_allowed_file_pattern(normalized)
                target_files.append(normalized)
            except ValueError as exc:
                issues.append(_issue("error", "invalid_target_file_path", str(exc), raw_file))
    else:
        issues.append(_issue("error", "target_files_not_provided", "pass --files with planned implementation paths"))

    doing_tasks = build_result.get("doing_tasks") or []
    if target_files and doing_tasks:
        allowed_files = doing_tasks[0].get("allowed_files", [])
        for target_file in target_files:
            if not any(file_matches_allowed(target_file, allowed_file) for allowed_file in allowed_files):
                issues.append(_issue(
                    "error",
                    "file_not_allowed_by_doing_task",
                    f"{target_file} is not covered by current DOING slice allowed_files",
                    target_file,
                ))

    if issues and not any(issue["code"] == "implementation_scope_not_ready" for issue in issues):
        issues.insert(0, _issue(
            "error",
            "implementation_scope_not_ready",
            "ship-build requires current_stage == ship-build, one DOING slice, allowed_files, AC refs, verification_command, and matching target files",
        ))

    all_issues = issues + warnings
    return {
        "allowed": not any(issue["level"] == "error" for issue in all_issues),
        "current_stage": current_stage,
        "required_stage": "ship-build",
        "workspace_root": str(feature_context.workspace_root) if feature_context else None,
        "feature_root": str(feature_context.feature_root) if feature_context else None,
        "feature_dir_validated": feature_context is not None,
        "target_files": target_files,
        "doing_task": doing_tasks[0] if doing_tasks else None,
        "issues": all_issues,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Unified lightweight preflight before implementation code edits")
    parser.add_argument("feature_dir", help="Ship work directory containing meta.yml")
    parser.add_argument("--project-scope", choices=("fullstack", "backend_only", "frontend_only"), default="fullstack")
    parser.add_argument("--files", nargs="*", default=None, help="Workspace-relative implementation files planned for this edit")
    parser.add_argument("--strict-files", action="store_true", help="Compatibility flag; target files are always checked")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = implementation_preflight(Path(args.feature_dir), args.project_scope, args.files, args.strict_files)

    if args.json:
        print(json.dumps(result, ensure_ascii=True, indent=2))
    else:
        print(f"feature_dir: {Path(args.feature_dir).resolve()}")
        print(f"current_stage: {result.get('current_stage', '')}")
        print(f"required_stage: {result['required_stage']}")
        print(f"allowed: {str(result['allowed']).lower()}")
        if result["issues"]:
            print("\nIssues:")
            for issue in result["issues"]:
                path = f" [{issue['path']}]" if "path" in issue else ""
                print(f"  {issue['level'].upper()} {issue['code']}{path}: {issue['message']}")

    return 0 if result["allowed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
