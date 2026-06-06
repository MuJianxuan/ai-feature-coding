#!/usr/bin/env python3
"""Validate tech research and selection evidence links."""

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
from feature_meta_runtime import load_meta  # noqa: E402
from validate_requirements import validate_requirements_file  # noqa: E402

SOURCE_RE = re.compile(r"\bSRC-[A-Z0-9]+-\d{3}\b|source_id\s*:", re.IGNORECASE)
PATH_RE = re.compile(
    r"\b(?:src|app|apps|packages|lib|server|client|pages|components|routes|api|db|migrations|prisma|orm|tests?|docs|\.docs|resource)/[A-Za-z0-9_./@{}:$*?=-]+\b"
)
SURFACE_SIGNAL_RE = re.compile(
    r"\b(?:GET|POST|PUT|PATCH|DELETE)\s+/|/api/|\b(?:DB|API|Frontend|Backend Service|Repository|DAO|Worker|MQ|Cron|Config|Auth|Permission|Observability|Test)\b|"
    r"\b(?:table|migration|schema|route|endpoint|service|component|store|client|topic|queue|worker|cron|metric|log)s?\b",
    re.IGNORECASE,
)
NA_RE = re.compile(r"不适用|N/A|not applicable|无既有代码基线|new_project", re.IGNORECASE)


def _has_heading(body: str, heading: str) -> bool:
    return bool(re.search(rf"^##+\s+.*{re.escape(heading)}", body, re.MULTILINE | re.IGNORECASE))


def _has_any_heading(body: str, headings: tuple[str, ...]) -> bool:
    return any(_has_heading(body, heading) for heading in headings)


def _section_text(body: str, heading: str) -> str:
    match = re.search(rf"^##\s+.*{re.escape(heading)}.*$", body, re.MULTILINE | re.IGNORECASE)
    if not match:
        return ""
    next_match = re.search(r"^##\s+", body[match.end() :], re.MULTILINE)
    end = match.end() + next_match.start() if next_match else len(body)
    return body[match.end() : end].strip()


def _load_meta(feature_dir: Path) -> dict[str, Any]:
    meta_path = feature_dir / "meta.yml"
    if not meta_path.exists():
        return {}
    try:
        return load_meta(meta_path)
    except Exception:
        return {}


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


def _validate_technical_plan_requirements_index(feature_dir: Path) -> list[dict[str, str]]:
    requirements_path = feature_dir / "requirements.md"
    if not requirements_path.exists():
        return [
            _issue(
                "error",
                "missing_derived_requirements_index",
                "technical_plan_provided ready tech discovery requires derived requirements.md with minimal Domain/AC index",
                "requirements.md",
            )
        ]

    try:
        frontmatter, _body = read_frontmatter(requirements_path)
    except ValueError as exc:
        return [_issue("error", "invalid_derived_requirements_frontmatter", str(exc), "requirements.md")]

    issues: list[dict[str, str]] = []
    if frontmatter.get("generation_mode") != "technical_plan":
        issues.append(
            _issue(
                "error",
                "derived_requirements_not_technical_plan",
                "technical_plan_provided derived requirements.md must set generation_mode: technical_plan",
                "requirements.md",
            )
        )
    if frontmatter.get("stage_status") != "ready":
        issues.append(
            _issue(
                "error",
                "derived_requirements_not_ready",
                "technical_plan_provided derived requirements.md must be stage_status: ready before tech discovery is ready",
                "requirements.md",
            )
        )

    requirements_result = validate_requirements_file(requirements_path)
    issues.extend(requirements_result["issues"])
    return issues


def validate_tech_discovery(feature_dir: Path) -> dict:
    feature_dir = feature_dir.resolve()
    meta = _load_meta(feature_dir)
    project_context = str(meta.get("project_context") or "unknown")
    issues, research_body, research_fm = _read_artifact(feature_dir / "tech-research.md", "research")
    selection_issues, selection_body, selection_fm = _read_artifact(feature_dir / "tech-selection.md", "selection")
    issues.extend(selection_issues)
    ready = research_fm.get("stage_status") == "ready" and selection_fm.get("stage_status") == "ready"
    if ready and meta.get("scenario") == "technical_plan_provided":
        issues.extend(_validate_technical_plan_requirements_index(feature_dir))
    if ready and not SOURCE_RE.search(research_body):
        issues.append(_issue("error", "research_missing_source_ids", "tech-research ready requires source_id entries", "tech-research.md"))
    if ready and not SOURCE_RE.search(selection_body):
        issues.append(_issue("error", "selection_missing_source_refs", "tech-selection decisions must cite source_id", "tech-selection.md"))
    if ready:
        required_research_headings = {
            "missing_project_reality_scan": ("Project Reality Scan", "项目现状发现"),
            "missing_requirement_reality_mapping": ("Requirement-to-Reality Mapping", "需求与已有系统映射"),
            "missing_existing_surface_inventory": ("Existing Surface Inventory", "现有表面清单"),
            "missing_evidence_uncertainty": ("Evidence and Uncertainty", "证据与不确定项"),
            "missing_research_alignment_check": ("Research Alignment Check", "产出前对齐记录"),
            "missing_technical_research": ("Technical Research", "技术调研"),
            "missing_selection_inputs": ("Selection Inputs", "给 tech-selection.md 的输入"),
        }
        for code, headings in required_research_headings.items():
            if not _has_any_heading(research_body, headings):
                issues.append(_issue("error", code, f"tech-research ready requires heading: {headings[0]}", "tech-research.md"))

        project_scan = _section_text(research_body, "Project Reality Scan") or _section_text(research_body, "项目现状发现")
        mapping = _section_text(research_body, "Requirement-to-Reality Mapping") or _section_text(research_body, "需求与已有系统映射")
        alignment = _section_text(research_body, "Research Alignment Check") or _section_text(research_body, "产出前对齐记录")

        if len(alignment) < 80:
            issues.append(_issue("error", "alignment_check_too_thin", "Research Alignment Check must record presented summary, feedback/assumptions, and final baseline", "tech-research.md"))

        if project_context == "existing_project":
            if NA_RE.search(project_scan):
                issues.append(_issue("error", "existing_project_reality_scan_na", "existing_project Project Reality Scan cannot be marked not applicable", "tech-research.md"))
            if not (PATH_RE.search(project_scan) or PATH_RE.search(mapping) or SURFACE_SIGNAL_RE.search(project_scan) or SURFACE_SIGNAL_RE.search(mapping)):
                issues.append(_issue("error", "missing_project_reality_evidence", "existing_project ready research requires concrete path/API/DB/frontend/service evidence", "tech-research.md"))
            if len(mapping) < 80 or "unknown" not in mapping.lower() and not re.search(r"\b(reuse|extend|replace|new|avoid)\b", mapping, re.IGNORECASE):
                issues.append(_issue("error", "empty_requirement_reality_mapping", "existing_project ready research requires non-empty Requirement-to-Reality Mapping with relation types", "tech-research.md"))
        elif project_context == "new_project":
            if not NA_RE.search(project_scan):
                issues.append(_issue("error", "new_project_reality_scan_missing_na_reason", "new_project Project Reality Scan must explain no existing code baseline", "tech-research.md"))
        elif project_context == "unknown":
            issues.append(_issue("warning", "unknown_project_context", "meta.yml project_context is unknown; ready research should record assumptions explicitly", "meta.yml"))
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
