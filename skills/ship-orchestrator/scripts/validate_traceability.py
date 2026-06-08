#!/usr/bin/env python3
"""Validate AC traceability across requirements, contract, plans, and evidence."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

AC_RE = re.compile(r"\bAC-[A-Z0-9]+-\d{3}\b")

TRACE_TARGETS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("contract", ("api-contract.md",)),
    ("plan", ("frontend-plan.md", "backend-plan.md")),
    ("test", ("verification.md",)),
    ("handoff", ("handoff.md",)),
)


def _issue(level: str, code: str, message: str, path: str | None = None) -> dict[str, str]:
    payload = {"level": level, "code": code, "message": message}
    if path:
        payload["path"] = path
    return payload


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _ac_ids_in(path: Path) -> set[str]:
    return set(AC_RE.findall(_read(path)))


def _required_links(strict: bool, stage: str) -> tuple[str, ...]:
    if strict and stage == "ship-verify":
        return ("test",)
    if strict and stage == "ship-handoff":
        return ("contract", "plan", "test", "handoff")
    return ("contract", "plan", "test")


def validate_traceability(feature_dir: Path, *, strict: bool = False, stage: str = "") -> dict[str, Any]:
    feature_dir = feature_dir.resolve()
    issues: list[dict[str, str]] = []
    requirements_path = feature_dir / "requirements.md"
    if not requirements_path.exists():
        return {
            "feature_dir": str(feature_dir),
            "ok": False,
            "issues": [_issue("error", "missing_requirements", "requirements.md is required", "requirements.md")],
            "strict": strict,
            "stage": stage,
            "matrix": [],
        }

    requirement_acs = sorted(_ac_ids_in(requirements_path))
    if not requirement_acs:
        issues.append(_issue("error", "missing_requirement_acs", "requirements.md contains no AC IDs", "requirements.md"))

    target_ac_sets: dict[str, set[str]] = {}
    missing_target_files: dict[str, list[str]] = {}
    for target_name, relative_paths in TRACE_TARGETS:
        found: set[str] = set()
        missing: list[str] = []
        for relative_path in relative_paths:
            path = feature_dir / relative_path
            if not path.exists():
                missing.append(relative_path)
                continue
            found.update(_ac_ids_in(path))
        target_ac_sets[target_name] = found
        if missing:
            missing_target_files[target_name] = missing

    matrix: list[dict[str, Any]] = []
    required_links = _required_links(strict, stage)
    for ac_id in requirement_acs:
        row = {"ac_id": ac_id}
        for target_name, _paths in TRACE_TARGETS:
            row[target_name] = ac_id in target_ac_sets[target_name]
        matrix.append(row)

        missing_links = [target_name for target_name in required_links if not row[target_name]]
        if missing_links:
            level = "error" if strict and stage in {"ship-verify", "ship-handoff"} else "warning"
            issues.append(_issue(level, "ac_trace_gap", f"{ac_id} missing trace links: {', '.join(missing_links)}"))

    for target_name, missing in missing_target_files.items():
        issues.append(_issue("warning", "missing_trace_target", f"{target_name} trace target files missing: {', '.join(missing)}"))

    orphan_refs: dict[str, list[str]] = {}
    requirement_set = set(requirement_acs)
    for target_name, ac_ids in target_ac_sets.items():
        orphans = sorted(ac_ids - requirement_set)
        if orphans:
            orphan_refs[target_name] = orphans
            issues.append(_issue("warning", "orphan_ac_ref", f"{target_name} references AC IDs not in requirements.md: {', '.join(orphans)}"))

    return {
        "feature_dir": str(feature_dir),
        "ok": not any(issue["level"] == "error" for issue in issues),
        "issues": issues,
        "strict": strict,
        "stage": stage,
        "matrix": matrix,
        "orphan_refs": orphan_refs,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate AC traceability across workflow artifacts")
    parser.add_argument("feature_dir", help="Feature directory containing requirements.md")
    parser.add_argument("--strict", action="store_true", help="Upgrade close-stage trace gaps to errors")
    parser.add_argument("--stage", choices=("ship-contract", "ship-delivery-plan", "ship-verify", "ship-handoff"), default="")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = validate_traceability(Path(args.feature_dir), strict=args.strict, stage=args.stage)
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
