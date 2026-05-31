#!/usr/bin/env python3
"""Validate backend-design.md implementation and operations coverage signals."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from validate_feature_artifacts import read_frontmatter  # noqa: E402

DOMAIN_RE = re.compile(r"\bD-[A-Z0-9]+-\d{3}\b")
ENDPOINT_RE = re.compile(r"\b(GET|POST|PUT|PATCH|DELETE)\s+/[A-Za-z0-9_./:{}-]+")


def _issue(level: str, code: str, message: str, path: str = "backend-design.md") -> dict[str, str]:
    return {"level": level, "code": code, "message": message, "path": path}


def validate_backend_design(path: Path) -> dict:
    path = (path / "backend-design.md" if path.is_dir() else path).resolve()
    issues = []
    if not path.exists():
        return {"path": str(path), "ok": False, "issues": [_issue("error", "missing_backend_design", "backend-design.md missing")]}
    try:
        fm, body = read_frontmatter(path)
    except ValueError as exc:
        return {"path": str(path), "ok": False, "issues": [_issue("error", "invalid_frontmatter", str(exc))]}
    ready = fm.get("stage_status") == "ready"
    if fm.get("stage") != "ship-backend-design":
        issues.append(_issue("error", "invalid_stage", "expected ship-backend-design"))
    if ready and not DOMAIN_RE.search(body):
        issues.append(_issue("error", "missing_domain_refs", "ready backend design must map Domain IDs"))
    if ready and not ENDPOINT_RE.search(body):
        issues.append(_issue("error", "missing_endpoint_mapping", "ready backend design must map contract endpoints"))
    for signal in ("Controller", "Service", "Repository"):
        if ready and signal not in body:
            issues.append(_issue("warning", "implementation_mapping_gap", f"endpoint mapping missing signal: {signal}"))
    for signal in ("migration", "rollback", "backfill", "迁移", "回滚"):
        if ready and signal not in body.lower():
            issues.append(_issue("warning", "migration_strategy_gap", f"missing migration/rollback signal: {signal}"))
            break
    for signal in ("auth", "rate", "logging", "metrics", "error", "认证", "限流", "日志", "监控", "错误"):
        if ready and signal not in body.lower():
            issues.append(_issue("warning", "nfr_strategy_gap", f"missing backend NFR signal: {signal}"))
            break
    return {"path": str(path), "ok": not any(i["level"] == "error" for i in issues), "issues": issues}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    result = validate_backend_design(Path(args.path))
    if args.json:
        print(json.dumps(result, ensure_ascii=True, indent=2))
    else:
        print(f"ok: {str(result['ok']).lower()}")
        for issue in result["issues"]:
            print(f"{issue['level'].upper()} {issue['code']}: {issue['message']}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
