#!/usr/bin/env python3
"""Validate ship-shape design brief and wireframe manifest signals."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from validate_feature_artifacts import read_frontmatter  # noqa: E402

UIUX_COVERAGE_VALUES = frozenset({"sufficient", "partial", "screenshot_only", "inaccessible", "generated"})


def _issue(level: str, code: str, message: str, path: str = "design-brief.md") -> dict[str, str]:
    return {"level": level, "code": code, "message": message, "path": path}


def validate_ui_artifacts(feature_dir: Path) -> dict:
    feature_dir = feature_dir.resolve()
    path = feature_dir / "design-brief.md"
    issues = []
    if not path.exists():
        return {"feature_dir": str(feature_dir), "ok": False, "issues": [_issue("error", "missing_design_brief", "design-brief.md missing")]}
    try:
        fm, body = read_frontmatter(path)
    except ValueError as exc:
        return {"feature_dir": str(feature_dir), "ok": False, "issues": [_issue("error", "invalid_frontmatter", str(exc))]}
    ready = fm.get("stage_status") == "ready"
    if fm.get("stage") != "ship-shape":
        issues.append(_issue("error", "invalid_stage", "design-brief.md must use stage: ship-shape"))
    variations = fm.get("variations_count", 0)
    if ready and (not isinstance(variations, int) or variations < 3):
        issues.append(_issue("error", "insufficient_variants", "ready design brief requires 3+ variants"))
    if fm.get("activation_mode") == "ui_shape_insert" and not (fm.get("ui_shape_decision") or fm.get("open_questions") or fm.get("uiux_risks")):
        issues.append(_issue("warning", "missing_ui_shape_decision", "inserted design brief should record ui_shape_decision, open_questions, or uiux_risks"))
    if ready and fm.get("browser_verified") is not True:
        issues.append(_issue("error", "design_brief_browser_not_verified", "ready design brief requires browser_verified: true"))
    coverage = fm.get("uiux_material_coverage")
    if coverage is not None and coverage not in UIUX_COVERAGE_VALUES:
        issues.append(_issue("error", "invalid_uiux_material_coverage", "uiux_material_coverage must be sufficient, partial, screenshot_only, inaccessible, or generated"))
    if ready and coverage == "inaccessible":
        issues.append(_issue("error", "uiux_material_inaccessible", "ready design brief cannot use inaccessible UIUX material coverage"))
    if ready and coverage in {"partial", "screenshot_only"}:
        risks = fm.get("uiux_risks")
        open_questions = fm.get("open_questions")
        has_risks = isinstance(risks, list) and bool(risks) or isinstance(risks, str) and bool(risks.strip())
        has_questions = isinstance(open_questions, list) and bool(open_questions) or isinstance(open_questions, str) and bool(open_questions.strip())
        if not has_risks and not has_questions:
            issues.append(_issue("error", "uiux_partial_without_risk", "partial/screenshot_only UIUX coverage requires uiux_risks or open_questions"))
    for signal in ("tokens:", "Visual System", "viewport", "wireframe", "resource/wireframes"):
        if signal not in body and signal not in str(fm):
            issues.append(_issue("error" if ready else "warning", "missing_ui_manifest_signal", f"missing UI artifact signal: {signal}"))
    index_path = feature_dir / str(fm.get("wireframe_index_path", "resource/wireframes/index.html"))
    if ready and not index_path.exists():
        issues.append(_issue("error", "missing_wireframe_index", f"wireframe index missing: {index_path.relative_to(feature_dir)}"))
    html_count = len(list((feature_dir / "resource/wireframes").glob("*.html"))) if (feature_dir / "resource/wireframes").exists() else 0
    if ready and html_count < 3:
        issues.append(_issue("error", "missing_wireframe_files", "ready shape artifact requires 3+ HTML wireframe files"))
    return {"feature_dir": str(feature_dir), "ok": not any(i["level"] == "error" for i in issues), "issues": issues}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("feature_dir")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    result = validate_ui_artifacts(Path(args.feature_dir))
    if args.json:
        print(json.dumps(result, ensure_ascii=True, indent=2))
    else:
        print(f"ok: {str(result['ok']).lower()}")
        for issue in result["issues"]:
            print(f"{issue['level'].upper()} {issue['code']}: {issue['message']}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
