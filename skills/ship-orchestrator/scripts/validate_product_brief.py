#!/usr/bin/env python3
"""Validate product-brief.md discovery quality signals."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from validate_feature_artifacts import read_frontmatter  # noqa: E402


def _issue(level: str, code: str, message: str, path: str = "product-brief.md") -> dict[str, str]:
    return {"level": level, "code": code, "message": message, "path": path}


def validate_product_brief(path: Path) -> dict:
    path = (path / "product-brief.md" if path.is_dir() else path).resolve()
    issues = []
    if not path.exists():
        return {"path": str(path), "ok": False, "issues": [_issue("error", "missing_product_brief", "product-brief.md missing")]}
    try:
        fm, body = read_frontmatter(path)
    except ValueError as exc:
        return {"path": str(path), "ok": False, "issues": [_issue("error", "invalid_frontmatter", str(exc))]}
    ready = fm.get("stage_status") == "ready"
    if fm.get("stage") != "ship-discover":
        issues.append(_issue("error", "invalid_stage", "product-brief.md must use stage: ship-discover"))
    for code, signal in (
        ("missing_problem_clarity", "问题"),
        ("missing_user_clarity", "用户"),
        ("missing_scope_clarity", "Must Have"),
        ("missing_success_metric", "成功标准"),
        ("missing_risk_or_assumption", "假设"),
        ("missing_evidence_index", "evidence_index"),
    ):
        if signal not in body and signal not in str(fm):
            issues.append(_issue("error" if ready else "warning", code, f"missing discovery signal: {signal}"))
    alternatives = body.count("备选") + body.lower().count("alternative")
    if ready and alternatives < 1:
        issues.append(_issue("error", "missing_real_alternative", "ready product brief must record at least one rejected alternative"))
    if ready and not fm.get("user_direction_sign_off"):
        level = "error" if fm.get("discovery_mode") == "greenfield" and fm.get("approach_selected") else "warning"
        issues.append(_issue(level, "missing_product_direction_sign_off", "ready product brief should record user_direction_sign_off"))
    if "scope" not in body.lower() and "architecture" not in body.lower() and "workflow" not in body.lower() and "risk" not in body.lower():
        issues.append(_issue("warning", "weak_option_differentiation", "alternatives should differ in scope, architecture, workflow, or delivery risk"))
    return {"path": str(path), "ok": not any(i["level"] == "error" for i in issues), "issues": issues}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    result = validate_product_brief(Path(args.path))
    if args.json:
        print(json.dumps(result, ensure_ascii=True, indent=2))
    else:
        print(f"ok: {str(result['ok']).lower()}")
        for issue in result["issues"]:
            print(f"{issue['level'].upper()} {issue['code']}: {issue['message']}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
