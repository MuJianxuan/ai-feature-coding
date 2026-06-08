#!/usr/bin/env python3
"""Validate frontend-design.md page/API/state coverage signals."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from validate_feature_artifacts import read_frontmatter  # noqa: E402

AC_RE = re.compile(r"\bAC-[A-Z0-9]+-\d{3}\b")
ENDPOINT_RE = re.compile(r"\b(GET|POST|PUT|PATCH|DELETE)\s+/[A-Za-z0-9_./:{}-]+")


def _issue(level: str, code: str, message: str, path: str = "frontend-design.md") -> dict[str, str]:
    return {"level": level, "code": code, "message": message, "path": path}


def validate_frontend_design(path: Path) -> dict:
    path = (path / "frontend-design.md" if path.is_dir() else path).resolve()
    issues = []
    if not path.exists():
        return {"path": str(path), "ok": False, "issues": [_issue("error", "missing_frontend_design", "frontend-design.md missing")]}
    try:
        fm, body = read_frontmatter(path)
    except ValueError as exc:
        return {"path": str(path), "ok": False, "issues": [_issue("error", "invalid_frontmatter", str(exc))]}
    ready = fm.get("stage_status") == "ready"
    if fm.get("stage") != "ship-frontend-design":
        issues.append(_issue("error", "invalid_stage", "expected ship-frontend-design"))
    for signal in ("Page Tree", "页面", "route", "component", "页面-接口", "状态", "权限"):
        if ready and signal not in body:
            issues.append(_issue("error", "missing_frontend_design_signal", f"missing signal: {signal}"))
    for state in ("loading", "empty", "error", "success", "permission"):
        if ready and state not in body.lower():
            issues.append(_issue("warning", "page_state_gap", f"page_state_matrix missing state: {state}"))
    if ready and not ENDPOINT_RE.search(body):
        issues.append(_issue("error", "missing_api_refs", "ready frontend design must reference API endpoints or local component API"))
    if ready and not AC_RE.search(body):
        issues.append(_issue("error", "missing_ac_refs", "ready frontend design must reference AC IDs"))
    for field in ("AC ID", "Source", "Evidence", "Owner"):
        if ready and field.lower() not in body.lower():
            issues.append(_issue("warning", "missing_structured_design_field", f"frontend design should include structured field: {field}"))
    for field in ("metrics", "logs"):
        if ready and field not in body.lower():
            issues.append(_issue("warning", "missing_observability_field", f"frontend observability should mention {field}"))
    for field in ("traces", "alerts"):
        if ready and field not in body.lower() and "n/a reason" not in body.lower():
            issues.append(_issue("warning", "missing_observability_field", f"frontend observability should mention {field} or N/A reason"))
    return {"path": str(path), "ok": not any(i["level"] == "error" for i in issues), "issues": issues}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    result = validate_frontend_design(Path(args.path))
    if args.json:
        print(json.dumps(result, ensure_ascii=True, indent=2))
    else:
        print(f"ok: {str(result['ok']).lower()}")
        for issue in result["issues"]:
            print(f"{issue['level'].upper()} {issue['code']}: {issue['message']}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
