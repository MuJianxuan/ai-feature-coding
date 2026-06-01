#!/usr/bin/env python3
"""Heuristic validator for ship-define requirements.md quality gates."""

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

DOMAIN_RE = re.compile(r"\bD-[A-Z0-9]+-\d{3}\b")
AC_RE = re.compile(r"\bAC-[A-Z0-9]+-\d{3}\b")
FUZZY_TERMS = ("尽量", "合理", "完善", "优化", "快速", "支持", "友好", "等等")
NFR_KEYWORDS = {
    "performance": ("性能", "响应", "延迟", "吞吐", "并发", "P95", "p95", "load", "latency", "performance"),
    "security": ("安全", "认证", "授权", "加密", "权限", "auth", "security", "permission"),
    "availability": ("可用", "容错", "恢复", "降级", "备份", "availability", "recovery", "rollback"),
    "accessibility": ("可访问", "无障碍", "键盘", "屏幕阅读器", "accessibility", "a11y"),
}


def _issue(level: str, code: str, message: str, path: str = "requirements.md") -> dict[str, str]:
    return {"level": level, "code": code, "message": message, "path": path}


def _section_present(text: str, names: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(name.lower() in lowered for name in names)


def _technical_plan_source_present(frontmatter: dict[str, Any], body: str) -> bool:
    source_documents = frontmatter.get("source_documents")
    if isinstance(source_documents, list) and source_documents:
        return True
    if isinstance(source_documents, str) and source_documents.strip():
        return True
    selected_scope = frontmatter.get("selected_scope")
    if isinstance(selected_scope, list) and selected_scope:
        return True
    if isinstance(selected_scope, str) and selected_scope.strip():
        return True
    lowered = body.lower()
    return (
        "technical_plan_source" in lowered
        or "selected scope" in lowered
        or "selected_scope" in lowered
        or "技术方案选区" in body
        or "选中范围" in body
    )


def _lines_with(pattern: re.Pattern[str], text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if pattern.search(line)]


def _ac_lines(text: str) -> list[str]:
    return _lines_with(AC_RE, text)


def _blocking_question_lines(text: str) -> list[str]:
    lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        lowered = stripped.lower()
        if not stripped:
            continue
        unresolved = stripped.startswith("- [ ]") or stripped.startswith("* [ ]") or "[gap]" in lowered or "[GAP]" in stripped
        blocking = "阻塞: 是" in stripped or "阻塞：是" in stripped or "blocking: yes" in lowered or "blocker: yes" in lowered
        if unresolved and blocking:
            lines.append(stripped)
    return lines


def _nfr_coverage(text: str) -> dict[str, bool]:
    return {
        category: any(keyword in text for keyword in keywords)
        for category, keywords in NFR_KEYWORDS.items()
    }


def validate_requirements_file(requirements_path: Path) -> dict[str, Any]:
    requirements_path = requirements_path.resolve()
    issues: list[dict[str, str]] = []
    if not requirements_path.exists():
        return {
            "requirements_path": str(requirements_path),
            "ok": False,
            "issues": [_issue("error", "missing_requirements", "requirements.md does not exist")],
            "summary": {},
        }

    try:
        frontmatter, body = read_frontmatter(requirements_path)
    except ValueError as exc:
        return {
            "requirements_path": str(requirements_path),
            "ok": False,
            "issues": [_issue("error", "invalid_frontmatter", str(exc))],
            "summary": {},
        }

    stage_status = frontmatter.get("stage_status")
    generation_mode = frontmatter.get("generation_mode")
    ready = stage_status == "ready"

    if frontmatter.get("stage") != "ship-define":
        issues.append(_issue("error", "invalid_stage", f"expected stage ship-define, found {frontmatter.get('stage')!r}"))
    if stage_status not in ("draft", "ready", "complete"):
        issues.append(_issue("error", "invalid_stage_status", f"invalid stage_status: {stage_status!r}"))
    if generation_mode in ("raw_prd_input", "raw_prd") and ready:
        issues.append(_issue("error", "raw_prd_marked_ready", "raw PRD inbox cannot be marked ready before normalize"))
    if generation_mode == "technical_plan" and not _technical_plan_source_present(frontmatter, body):
        issues.append(
            _issue(
                "error" if ready else "warning",
                "technical_plan_missing_source_index",
                "technical_plan requirements must reference selected scope source_documents or equivalent source index",
            )
        )

    domain_ids = sorted(set(DOMAIN_RE.findall(body)))
    ac_ids = sorted(set(AC_RE.findall(body)))
    ac_lines = _ac_lines(body)

    if not domain_ids:
        issues.append(_issue("error" if ready else "warning", "missing_domain_ids", "no Domain ID found"))
    if not ac_ids:
        issues.append(_issue("error" if ready else "warning", "missing_acceptance_criteria", "no AC ID found"))

    ac_without_domain = [line for line in ac_lines if not DOMAIN_RE.search(line)]
    if ac_without_domain:
        issues.append(_issue("error" if ready else "warning", "ac_missing_domain_ref", f"{len(ac_without_domain)} AC lines do not reference a Domain ID"))

    domains_without_ac = [
        domain_id
        for domain_id in domain_ids
        if not any(domain_id in line for line in ac_lines)
    ]
    if domains_without_ac:
        issues.append(_issue("error" if ready else "warning", "domain_without_ac", f"Domain IDs without AC coverage: {', '.join(domains_without_ac)}"))

    ac_without_gwt = [
        line
        for line in ac_lines
        if not all(token in line for token in ("Given", "When", "Then"))
    ]
    if ac_without_gwt:
        issues.append(_issue("warning", "ac_not_given_when_then", f"{len(ac_without_gwt)} AC lines do not contain Given/When/Then"))

    for section_code, names in (
        ("missing_in_scope", ("In Scope", "本次必须实现", "范围")),
        ("missing_out_of_scope", ("Out of Scope", "明确不做", "不做")),
        ("missing_open_questions", ("待确认问题", "Open Questions", "Questions")),
        ("missing_source_index", ("需求资料索引", "source_documents", "Source Index")),
    ):
        if not _section_present(body, names):
            issues.append(_issue("error" if ready else "warning", section_code, f"missing section signal: {names[0]}"))

    blocking_questions = _blocking_question_lines(body)
    if ready and blocking_questions:
        issues.append(_issue("error", "ready_with_blocking_questions", f"{len(blocking_questions)} unresolved blocking questions or GAPs found"))
    elif blocking_questions:
        issues.append(_issue("warning", "blocking_questions_present", f"{len(blocking_questions)} unresolved blocking questions or GAPs found"))

    nfr_coverage = _nfr_coverage(body)
    if not _section_present(body, ("非功能需求", "NFR", "Non-functional")):
        issues.append(_issue("error" if ready else "warning", "missing_nfr_section", "missing NFR / non-functional requirements section"))
    missing_nfr = [category for category, covered in nfr_coverage.items() if not covered]
    if missing_nfr:
        issues.append(_issue("warning", "nfr_category_gap", f"NFR category not explicitly covered: {', '.join(missing_nfr)}"))

    fuzzy_hits = [
        term
        for term in FUZZY_TERMS
        if term in body
    ]
    if fuzzy_hits:
        issues.append(_issue("warning", "fuzzy_terms", f"fuzzy terms found: {', '.join(fuzzy_hits)}"))

    return {
        "requirements_path": str(requirements_path),
        "ok": not any(issue["level"] == "error" for issue in issues),
        "issues": issues,
        "summary": {
            "stage_status": stage_status,
            "generation_mode": generation_mode,
            "domain_ids": domain_ids,
            "ac_ids": ac_ids,
            "nfr_coverage": nfr_coverage,
            "blocking_question_count": len(blocking_questions),
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate requirements.md readiness heuristics")
    parser.add_argument("path", help="Path to requirements.md or a feature directory containing requirements.md")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    return parser


def main(argv: list[str]) -> int:
    args = build_parser().parse_args(argv[1:])
    path = Path(args.path)
    requirements_path = path / "requirements.md" if path.is_dir() else path
    result = validate_requirements_file(requirements_path)
    if args.json:
        print(json.dumps(result, ensure_ascii=True, indent=2))
    else:
        print(f"requirements_path: {result['requirements_path']}")
        print(f"ok: {str(result['ok']).lower()}")
        for issue in result["issues"]:
            print(f"{issue['level'].upper()} {issue['code']} [{issue['path']}]: {issue['message']}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
