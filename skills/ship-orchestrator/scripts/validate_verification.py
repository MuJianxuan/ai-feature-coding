#!/usr/bin/env python3
"""Validate verification.md test run schema and required tracks."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from validate_feature_artifacts import read_frontmatter  # noqa: E402

AC_RE = re.compile(r"\bAC-[A-Z0-9]+-\d{3}\b")
AC_RESULT_RE = re.compile(r"\bAC-[A-Z0-9]+-\d{3}\b.*\b(PASS|FAIL|BLOCKED|NOT_TESTED)\b", re.IGNORECASE)
TRACKS = ("backend-unit", "backend-integration", "backend-contract", "frontend-component", "frontend-e2e")


def _issue(level: str, code: str, message: str, path: str = "verification.md") -> dict[str, str]:
    return {"level": level, "code": code, "message": message, "path": path}


def _required_tracks(project_scope: str) -> set[str]:
    if project_scope == "backend_only":
        return {"backend-unit", "backend-integration", "backend-contract"}
    if project_scope == "frontend_only":
        return {"frontend-component", "frontend-e2e"}
    return set(TRACKS)


def _has_track(text: str, track: str) -> bool:
    return track in text or track.replace("-", " ") in text.lower()


def validate_verification_file(path: Path, project_scope: str = "fullstack") -> dict[str, Any]:
    path = path.resolve()
    issues: list[dict[str, str]] = []
    if not path.exists():
        return {"path": str(path), "ok": False, "issues": [_issue("error", "missing_verification", "verification.md does not exist")], "summary": {}}
    try:
        frontmatter, body = read_frontmatter(path)
    except ValueError as exc:
        return {"path": str(path), "ok": False, "issues": [_issue("error", "invalid_frontmatter", str(exc))], "summary": {}}

    ready = frontmatter.get("stage_status") in ("ready", "complete")
    if frontmatter.get("stage") != "ship-handoff":
        issues.append(_issue("error", "invalid_stage", f"expected stage ship-handoff, found {frontmatter.get('stage')!r}"))
    stage_status = frontmatter.get("stage_status")
    if stage_status not in ("draft", "ready", "complete"):
        issues.append(_issue("error", "invalid_stage_status", f"invalid stage_status: {stage_status!r}"))
    if stage_status in ("ready", "complete"):
        produced_by = frontmatter.get("produced_by")
        if not isinstance(produced_by, list) or "ship-verify" not in produced_by:
            issues.append(_issue("error", "missing_verification_produced_by", "ready/complete verification.md requires produced_by including ship-verify"))
        if frontmatter.get("accepted_by") != "ship-handoff":
            issues.append(_issue("error", "invalid_verification_accepted_by", "verification.md requires accepted_by: ship-handoff"))
        phase = frontmatter.get("artifact_phase")
        if stage_status == "ready" and phase not in {"testing", "acceptance"}:
            issues.append(_issue("error", "invalid_verification_artifact_phase", "ready verification.md requires artifact_phase testing or acceptance"))
        if stage_status == "complete" and phase != "acceptance":
            issues.append(_issue("error", "verification_complete_not_acceptance", "complete verification.md requires artifact_phase: acceptance"))

    required = _required_tracks(project_scope)
    present = {track for track in TRACKS if _has_track(body, track)}
    missing = sorted(required - present)
    if missing:
        issues.append(_issue("error" if ready else "warning", "missing_required_test_tracks", f"missing required test tracks: {', '.join(missing)}"))
    skipped = sorted(set(TRACKS) - required)
    for track in skipped:
        if track not in present and "N/A" not in body and "na" not in body.lower():
            issues.append(_issue("warning", "missing_na_track_explanation", f"{track} should be marked N/A with reason for {project_scope}"))

    for field, aliases in (
        ("command", ("command", "命令")),
        ("status", ("status", "状态", "PASS", "FAIL")),
        ("evidence", ("evidence", "证据", "output", "输出")),
        ("failure_class", ("failure_class", "failure class", "失败分类", "真 bug", "环境")),
        ("linked_ac", ("linked_ac", "linked ac", "AC-")),
    ):
        if not any(alias in body for alias in aliases):
            issues.append(_issue("error" if ready else "warning", "missing_test_run_field", f"missing test run field signal: {field}"))

    ac_ids = sorted(set(AC_RE.findall(body)))
    if ready:
        for line in body.splitlines():
            match = AC_RESULT_RE.search(line)
            if not match:
                continue
            result = match.group(1).upper()
            if result == "NOT_TESTED" and "reason" not in line.lower() and "原因" not in line:
                issues.append(_issue("error", "not_tested_missing_reason", "NOT_TESTED AC result requires reason"))
    if ready and not ac_ids:
        issues.append(_issue("error", "missing_linked_ac", "ready verification must link test runs to AC IDs"))

    return {
        "path": str(path),
        "ok": not any(issue["level"] == "error" for issue in issues),
        "issues": issues,
        "summary": {
            "stage_status": frontmatter.get("stage_status"),
            "project_scope": project_scope,
            "required_tracks": sorted(required),
            "present_tracks": sorted(present),
            "ac_ids": ac_ids,
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate verification.md test track schema")
    parser.add_argument("path", help="Path to verification.md or feature dir")
    parser.add_argument("--project-scope", choices=("fullstack", "backend_only", "frontend_only"), default="fullstack")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    path = Path(args.path)
    verification_path = path / "verification.md" if path.is_dir() else path
    result = validate_verification_file(verification_path, args.project_scope)
    if args.json:
        print(json.dumps(result, ensure_ascii=True, indent=2))
    else:
        print(f"path: {result['path']}")
        print(f"ok: {str(result['ok']).lower()}")
        for issue in result["issues"]:
            print(f"{issue['level'].upper()} {issue['code']} [{issue['path']}]: {issue['message']}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
