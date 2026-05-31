#!/usr/bin/env python3
"""Validate tech research and selection evidence links."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from validate_feature_artifacts import read_frontmatter  # noqa: E402

SOURCE_RE = re.compile(r"\bSRC-[A-Z0-9]+-\d{3}\b|source_id\s*:", re.IGNORECASE)


def _issue(level: str, code: str, message: str, path: str) -> dict[str, str]:
    return {"level": level, "code": code, "message": message, "path": path}


def _read_artifact(path: Path, role: str) -> tuple[list[dict[str, str]], str, dict]:
    if not path.exists():
        return [_issue("error", "missing_tech_artifact", f"{path.name} missing", path.name)], "", {}
    try:
        fm, body = read_frontmatter(path)
    except ValueError as exc:
        return [_issue("error", "invalid_frontmatter", str(exc), path.name)], "", {}
    issues = []
    if fm.get("stage") != "ship-tech-discovery":
        issues.append(_issue("error", "invalid_stage", "expected ship-tech-discovery", path.name))
    if fm.get("artifact_role") != role:
        issues.append(_issue("error", "invalid_artifact_role", f"expected {role}", path.name))
    return issues, body, fm


def validate_tech_discovery(feature_dir: Path) -> dict:
    feature_dir = feature_dir.resolve()
    issues, research_body, research_fm = _read_artifact(feature_dir / "tech-research.md", "research")
    selection_issues, selection_body, selection_fm = _read_artifact(feature_dir / "tech-selection.md", "selection")
    issues.extend(selection_issues)
    ready = research_fm.get("stage_status") == "ready" and selection_fm.get("stage_status") == "ready"
    if ready and not SOURCE_RE.search(research_body):
        issues.append(_issue("error", "research_missing_source_ids", "tech-research ready requires source_id entries", "tech-research.md"))
    if ready and not SOURCE_RE.search(selection_body):
        issues.append(_issue("error", "selection_missing_source_refs", "tech-selection decisions must cite source_id", "tech-selection.md"))
    for signal in ("ADR", "Decision", "Rejected", "备选", "否决"):
        if ready and signal not in selection_body:
            issues.append(_issue("warning", "selection_missing_decision_signal", f"missing selection signal: {signal}", "tech-selection.md"))
    if ready and "tech_stack" not in selection_body and "技术栈" not in selection_body:
        issues.append(_issue("warning", "missing_tech_stack_freeze_signal", "tech-selection should record frozen tech_stack source", "tech-selection.md"))
    return {"feature_dir": str(feature_dir), "ok": not any(i["level"] == "error" for i in issues), "issues": issues}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("feature_dir")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    result = validate_tech_discovery(Path(args.feature_dir))
    if args.json:
        print(json.dumps(result, ensure_ascii=True, indent=2))
    else:
        print(f"ok: {str(result['ok']).lower()}")
        for issue in result["issues"]:
            print(f"{issue['level'].upper()} {issue['code']} [{issue['path']}]: {issue['message']}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
