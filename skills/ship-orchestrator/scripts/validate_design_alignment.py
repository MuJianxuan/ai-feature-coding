#!/usr/bin/env python3
"""Validate coarse contract/frontend/backend design alignment."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ENDPOINT_RE = re.compile(r"\b(GET|POST|PUT|PATCH|DELETE)\s+(/[A-Za-z0-9_./:{}-]+)")
ERROR_RE = re.compile(r"\b(?:ERR_[A-Z0-9_]+|\d{4,5})\b")


def _issue(level: str, code: str, message: str, path: str | None = None) -> dict[str, str]:
    payload = {"level": level, "code": code, "message": message}
    if path:
        payload["path"] = path
    return payload


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _endpoint_set(text: str) -> set[str]:
    return {f"{method} {path}" for method, path in ENDPOINT_RE.findall(text)}


def validate_design_alignment(feature_dir: Path, project_scope: str = "fullstack") -> dict:
    feature_dir = feature_dir.resolve()
    issues = []
    contract = _read(feature_dir / "api-contract.md")
    frontend = _read(feature_dir / "frontend-design.md")
    backend = _read(feature_dir / "backend-design.md")
    contract_eps = _endpoint_set(contract)
    frontend_eps = _endpoint_set(frontend)
    backend_eps = _endpoint_set(backend)
    if contract_eps:
        if project_scope in ("fullstack", "frontend_only"):
            missing = sorted(contract_eps - frontend_eps)
            ghost = sorted(frontend_eps - contract_eps)
            if missing:
                issues.append(_issue("warning", "contract_endpoint_not_consumed_by_frontend", ", ".join(missing), "frontend-design.md"))
            if ghost:
                issues.append(_issue("error", "frontend_unknown_endpoint", ", ".join(ghost), "frontend-design.md"))
        if project_scope in ("fullstack", "backend_only"):
            missing = sorted(contract_eps - backend_eps)
            ghost = sorted(backend_eps - contract_eps)
            if missing:
                issues.append(_issue("warning", "contract_endpoint_not_implemented_by_backend", ", ".join(missing), "backend-design.md"))
            if ghost:
                issues.append(_issue("error", "backend_unknown_endpoint", ", ".join(ghost), "backend-design.md"))
    contract_errors = set(ERROR_RE.findall(contract))
    if contract_errors and project_scope in ("fullstack", "frontend_only"):
        missing_errors = sorted(error for error in contract_errors if error not in frontend)
        if missing_errors:
            issues.append(_issue("warning", "frontend_missing_error_handling", ", ".join(missing_errors), "frontend-design.md"))
    return {"feature_dir": str(feature_dir), "ok": not any(i["level"] == "error" for i in issues), "issues": issues}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("feature_dir")
    parser.add_argument("--project-scope", choices=("fullstack", "backend_only", "frontend_only"), default="fullstack")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    result = validate_design_alignment(Path(args.feature_dir), args.project_scope)
    if args.json:
        print(json.dumps(result, ensure_ascii=True, indent=2))
    else:
        print(f"ok: {str(result['ok']).lower()}")
        for issue in result["issues"]:
            path = f" [{issue['path']}]" if "path" in issue else ""
            print(f"{issue['level'].upper()} {issue['code']}{path}: {issue['message']}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
