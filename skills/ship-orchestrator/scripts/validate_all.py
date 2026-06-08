#!/usr/bin/env python3
"""Run the common ShipKit validators for one feature directory."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from feature_meta_runtime import load_meta  # noqa: E402
from validate_backend_design import validate_backend_design  # noqa: E402
from validate_contract import validate_contract_file  # noqa: E402
from validate_delivery_plan import validate_delivery_plan  # noqa: E402
from validate_design_alignment import validate_design_alignment  # noqa: E402
from validate_feature_artifacts import validate_feature  # noqa: E402
from validate_frontend_design import validate_frontend_design  # noqa: E402
from validate_handoff import validate_handoff  # noqa: E402
from validate_requirements import validate_requirements_file  # noqa: E402
from validate_tech_discovery import validate_tech_discovery  # noqa: E402
from validate_traceability import validate_traceability  # noqa: E402
from validate_verification import validate_verification_file  # noqa: E402
from workflow_doctor import diagnose_feature  # noqa: E402


def _issue(level: str, code: str, message: str, path: str | None = None, check: str | None = None) -> dict[str, str]:
    payload = {"level": level, "code": code, "message": message}
    if path:
        payload["path"] = path
    if check:
        payload["check"] = check
    return payload


def _run_check(name: str, func: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    try:
        result = func()
    except Exception as exc:
        result = {"ok": False, "issues": [_issue("error", "validator_exception", str(exc), check=name)]}
    issues = [dict(issue, check=issue.get("check", name)) for issue in result.get("issues", [])]
    return {
        "name": name,
        "ok": not any(issue.get("level") == "error" for issue in issues),
        "issues": issues,
        "summary": result.get("summary", {}),
    }


def validate_all(feature_dir: Path, *, strict: bool = False) -> dict[str, Any]:
    feature_dir = feature_dir.resolve()
    meta = load_meta(feature_dir / "meta.yml") if (feature_dir / "meta.yml").exists() else {}
    project_scope = str(meta.get("project_scope") or "fullstack")
    current_stage = str(meta.get("current_stage") or "")
    checks = [
        _run_check("validate_feature_artifacts", lambda: validate_feature(feature_dir, strict_confirmation=strict)),
        _run_check("validate_requirements", lambda: validate_requirements_file(feature_dir / "requirements.md")),
        _run_check("validate_contract", lambda: validate_contract_file(feature_dir / "api-contract.md")),
        _run_check("validate_tech_discovery", lambda: validate_tech_discovery(feature_dir)),
        _run_check("validate_design_alignment", lambda: validate_design_alignment(feature_dir, project_scope=project_scope)),
        _run_check("validate_delivery_plan", lambda: validate_delivery_plan(feature_dir, project_scope=project_scope)),
        _run_check("validate_traceability", lambda: validate_traceability(feature_dir, strict=strict, stage=current_stage)),
        _run_check("validate_verification", lambda: validate_verification_file(feature_dir / "verification.md", project_scope=project_scope)),
        _run_check("validate_handoff", lambda: validate_handoff(feature_dir)),
        _run_check("workflow_doctor", lambda: diagnose_feature(feature_dir)),
    ]
    if project_scope in ("fullstack", "frontend_only"):
        checks.append(_run_check("validate_frontend_design", lambda: validate_frontend_design(feature_dir / "frontend-design.md")))
    if project_scope in ("fullstack", "backend_only"):
        checks.append(_run_check("validate_backend_design", lambda: validate_backend_design(feature_dir / "backend-design.md")))
    issues = [issue for check in checks for issue in check["issues"]]
    return {
        "feature_dir": str(feature_dir),
        "strict": strict,
        "ok": not any(issue.get("level") == "error" for issue in issues),
        "errors_count": sum(1 for issue in issues if issue.get("level") == "error"),
        "warnings_count": sum(1 for issue in issues if issue.get("level") == "warning"),
        "checks": checks,
        "issues": issues,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run all ShipKit workflow validators")
    parser.add_argument("feature_dir")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = validate_all(Path(args.feature_dir), strict=args.strict)
    if args.json:
        print(json.dumps(result, ensure_ascii=True, indent=2))
    else:
        print(f"feature_dir: {result['feature_dir']}")
        print(f"ok: {str(result['ok']).lower()}")
        print(f"errors: {result['errors_count']} warnings: {result['warnings_count']}")
        for issue in result["issues"]:
            path = f" [{issue['path']}]" if "path" in issue else ""
            print(f"{issue['level'].upper()} {issue.get('check', '')}:{issue['code']}{path}: {issue['message']}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
