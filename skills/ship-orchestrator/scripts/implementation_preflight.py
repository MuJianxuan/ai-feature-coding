#!/usr/bin/env python3
"""Unified preflight check before any implementation code edit.

Wraps stage_transition_check.py and build_task_preflight.py to provide
a single machine-readable gate for Source Code Edit Barrier.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from build_task_preflight import build_task_preflight  # noqa: E402
from feature_meta_runtime import load_meta  # noqa: E402
from stage_transition_check import check_transition  # noqa: E402


def _issue(level: str, code: str, message: str, path: str | None = None) -> dict[str, str]:
    payload = {"level": level, "code": code, "message": message}
    if path:
        payload["path"] = path
    return payload


def implementation_preflight(feature_dir: Path, project_scope: str = "fullstack") -> dict[str, Any]:
    """Check all preconditions for entering ship-build and editing implementation code.

    Returns a dict with:
      - allowed: bool - whether implementation is allowed
      - current_stage: str - current stage from meta.yml
      - required_stage: str - always "ship-build"
      - issues: list of dicts with level, code, message, optional path
    """
    feature_dir = feature_dir.resolve()
    issues: list[dict[str, str]] = []

    # 1. Check meta.yml exists and current_stage is valid
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

    # 2. Check stage_transition_check.py --target-stage ship-build allows
    transition_result = check_transition(feature_dir, "ship-build")
    if not transition_result["allowed"]:
        for issue in transition_result["issues"]:
            if issue["level"] == "error":
                issues.append(issue)

    # 3. Check review-plan.md review_status, user_sign_off, signed_at
    review_plan_path = feature_dir / "review-plan.md"
    if not review_plan_path.exists():
        issues.append(_issue("error", "missing_review_plan", "review-plan.md does not exist", "review-plan.md"))
    else:
        # Parse frontmatter
        text = review_plan_path.read_text(encoding="utf-8")
        lines = text.split("\n")
        if lines and lines[0].strip() == "---":
            fm_end = None
            for i in range(1, len(lines)):
                if lines[i].strip() == "---":
                    fm_end = i
                    break
            if fm_end:
                fm_lines = lines[1:fm_end]
                fm_dict = {}
                for line in fm_lines:
                    if ":" in line:
                        key, _, value = line.partition(":")
                        fm_dict[key.strip()] = value.strip()

                review_status = fm_dict.get("review_status", "")
                user_sign_off = fm_dict.get("user_sign_off", "")
                signed_at = fm_dict.get("signed_at", "")

                if review_status != "approved":
                    issues.append(_issue("error", "plan_not_approved", f"review-plan.md review_status is {review_status!r}, not 'approved'", "review-plan.md"))
                if not user_sign_off or user_sign_off in ("null", "~", ""):
                    issues.append(_issue("error", "plan_missing_user_sign_off", "review-plan.md user_sign_off is empty", "review-plan.md"))
                if not signed_at or signed_at in ("null", "~", ""):
                    issues.append(_issue("error", "plan_missing_signed_at", "review-plan.md signed_at is empty", "review-plan.md"))

    # 4. Check build_task_preflight.py passes
    build_result = build_task_preflight(feature_dir, project_scope)
    if not build_result["ok"]:
        for issue in build_result["issues"]:
            if issue["level"] == "error":
                issues.append(issue)

    # 5. Summary issue if not allowed
    if issues and not any(issue["code"] == "implementation_before_plan_review" for issue in issues):
        # Add a summary issue
        issues.insert(0, _issue(
            "error",
            "implementation_before_plan_review",
            "ship-build requires approved review-plan.md with user sign-off and all build preconditions met"
        ))

    return {
        "allowed": not any(issue["level"] == "error" for issue in issues),
        "current_stage": current_stage,
        "required_stage": "ship-build",
        "issues": issues,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Unified preflight check before implementation code edit"
    )
    parser.add_argument("feature_dir", help="Feature directory containing meta.yml")
    parser.add_argument(
        "--project-scope",
        choices=("fullstack", "backend_only", "frontend_only"),
        default="fullstack",
        help="Project scope (default: fullstack)"
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = implementation_preflight(Path(args.feature_dir), args.project_scope)

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
