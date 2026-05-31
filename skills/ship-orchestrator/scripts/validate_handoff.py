#!/usr/bin/env python3
"""Validate handoff AC evidence and risk acceptance closure."""

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
RESULT_RE = re.compile(r"\b(PASS|FAIL|BLOCKED|N/A|NA)\b", re.IGNORECASE)


def _issue(level: str, code: str, message: str, path: str | None = None) -> dict[str, str]:
    payload = {"level": level, "code": code, "message": message}
    if path:
        payload["path"] = path
    return payload


def _ac_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if AC_RE.search(line)]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def validate_handoff(feature_dir: Path) -> dict[str, Any]:
    feature_dir = feature_dir.resolve()
    issues: list[dict[str, str]] = []
    requirements_acs = set(AC_RE.findall(_read(feature_dir / "requirements.md")))

    verification_path = feature_dir / "verification.md"
    if not verification_path.exists():
        return {"feature_dir": str(feature_dir), "ok": False, "issues": [_issue("error", "missing_verification", "verification.md missing", "verification.md")], "summary": {}}
    try:
        verification_fm, verification_body = read_frontmatter(verification_path)
    except ValueError as exc:
        return {"feature_dir": str(feature_dir), "ok": False, "issues": [_issue("error", "invalid_verification_frontmatter", str(exc), "verification.md")], "summary": {}}

    verification_acs = set(AC_RE.findall(verification_body))
    missing_acs = sorted(requirements_acs - verification_acs)
    if missing_acs:
        issues.append(_issue("error", "missing_ac_mapping", f"AC missing from verification.md: {', '.join(missing_acs)}", "verification.md"))

    for line in _ac_lines(verification_body):
        ac_id = AC_RE.search(line).group(0)  # type: ignore[union-attr]
        result_match = RESULT_RE.search(line)
        if not result_match:
            issues.append(_issue("error", "ac_missing_result", f"{ac_id} missing PASS/FAIL/BLOCKED/N/A result", "verification.md"))
            continue
        result = result_match.group(1).upper()
        if result == "NA":
            result = "N/A"
        if result == "PASS" and not ("`" in line or "evidence" in line.lower() or "证据" in line):
            issues.append(_issue("error", "pass_ac_missing_evidence", f"{ac_id} PASS has no traceable evidence", "verification.md"))
        if result == "N/A" and not ("原因" in line or "reason" in line.lower()):
            issues.append(_issue("error", "na_missing_reason", f"{ac_id} N/A has no reason", "verification.md"))
        if result in ("FAIL", "BLOCKED") and not ("risk" in verification_body.lower() or "风险" in verification_body):
            issues.append(_issue("error", "failed_ac_missing_risk", f"{ac_id} {result} has no risk record", "verification.md"))

    if verification_fm.get("stage_status") == "complete" and verification_fm.get("all_ac_verified") is not True:
        issues.append(_issue("error", "complete_without_all_ac_verified", "complete verification requires all_ac_verified: true", "verification.md"))
    if any(token in verification_body.upper() for token in ("FAIL", "BLOCKED")):
        if not ("accepted_risks_sign_off" in verification_body or "user_sign_off" in verification_body or "风险接受" in verification_body):
            issues.append(_issue("error", "risk_acceptance_missing_signoff", "FAIL/BLOCKED closure requires accepted_risks_sign_off or user sign-off", "verification.md"))

    handoff_path = feature_dir / "handoff.md"
    if not handoff_path.exists():
        issues.append(_issue("error", "missing_handoff", "handoff.md missing", "handoff.md"))
        handoff_body = ""
    else:
        try:
            _handoff_fm, handoff_body = read_frontmatter(handoff_path)
        except ValueError as exc:
            issues.append(_issue("error", "invalid_handoff_frontmatter", str(exc), "handoff.md"))
            handoff_body = _read(handoff_path)
        for section in ("交付摘要", "变更范围", "部署事项", "后续建议", "Spec Proposals"):
            if section not in handoff_body:
                issues.append(_issue("warning", "handoff_section_missing", f"handoff.md missing section signal: {section}", "handoff.md"))
        for deploy_item in ("环境变量", "数据库迁移", "配置变更", "第三方依赖"):
            if deploy_item not in handoff_body:
                issues.append(_issue("warning", "deploy_item_missing", f"handoff.md missing deploy item: {deploy_item}", "handoff.md"))

    return {
        "feature_dir": str(feature_dir),
        "ok": not any(issue["level"] == "error" for issue in issues),
        "issues": issues,
        "summary": {
            "requirements_ac_count": len(requirements_acs),
            "verification_ac_count": len(verification_acs),
            "verification_stage_status": verification_fm.get("stage_status"),
            "all_ac_verified": verification_fm.get("all_ac_verified"),
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate handoff AC evidence closure")
    parser.add_argument("feature_dir")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = validate_handoff(Path(args.feature_dir))
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
    raise SystemExit(main())
