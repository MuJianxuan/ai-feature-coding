#!/usr/bin/env python3
"""Heuristic validator for ship-contract api-contract.md artifacts."""

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
DOMAIN_RE = re.compile(r"\bD-[A-Z0-9]+-\d{3}\b")
HTTP_ENDPOINT_RE = re.compile(r"\b(GET|POST|PUT|PATCH|DELETE)\s+(/[A-Za-z0-9_./:{}-]+)")
ERROR_CODE_RE = re.compile(r"\b(?:ERR_[A-Z0-9_]+|\d{4,5}|[1-5]\d{2})\b")
VALID_CONTRACT_FORMS = frozenset({"rest", "grpc", "message", "cron", "cli", "sdk"})


def _issue(level: str, code: str, message: str, path: str = "api-contract.md") -> dict[str, str]:
    return {"level": level, "code": code, "message": message, "path": path}


def _has_any(text: str, needles: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(needle.lower() in lowered for needle in needles)


def _endpoint_blocks(text: str) -> list[str]:
    lines = text.splitlines()
    blocks: list[str] = []
    current: list[str] = []
    for line in lines:
        if HTTP_ENDPOINT_RE.search(line):
            if current:
                blocks.append("\n".join(current))
            current = [line]
            continue
        if current:
            if line.startswith("#") and not HTTP_ENDPOINT_RE.search(line):
                blocks.append("\n".join(current))
                current = []
            else:
                current.append(line)
    if current:
        blocks.append("\n".join(current))
    return blocks


def validate_contract_file(contract_path: Path) -> dict[str, Any]:
    contract_path = contract_path.resolve()
    issues: list[dict[str, str]] = []
    if not contract_path.exists():
        return {
            "contract_path": str(contract_path),
            "ok": False,
            "issues": [_issue("error", "missing_contract", "api-contract.md does not exist")],
            "summary": {},
        }

    try:
        frontmatter, body = read_frontmatter(contract_path)
    except ValueError as exc:
        return {
            "contract_path": str(contract_path),
            "ok": False,
            "issues": [_issue("error", "invalid_frontmatter", str(exc))],
            "summary": {},
        }

    ready = frontmatter.get("stage_status") == "ready"
    contract_forms = frontmatter.get("contract_forms")
    if frontmatter.get("stage") != "ship-contract":
        issues.append(_issue("error", "invalid_stage", f"expected stage ship-contract, found {frontmatter.get('stage')!r}"))
    if frontmatter.get("stage_status") not in ("draft", "ready", "complete"):
        issues.append(_issue("error", "invalid_stage_status", f"invalid stage_status: {frontmatter.get('stage_status')!r}"))
    if not isinstance(contract_forms, list) or not contract_forms:
        issues.append(_issue("error" if ready else "warning", "missing_contract_forms", "contract_forms must list at least one contract form"))
        contract_forms = []
    else:
        invalid_forms = sorted(str(form) for form in contract_forms if form not in VALID_CONTRACT_FORMS)
        if invalid_forms:
            issues.append(_issue("error", "invalid_contract_forms", f"invalid contract_forms: {', '.join(invalid_forms)}"))

    ac_ids = sorted(set(AC_RE.findall(body)))
    domain_ids = sorted(set(DOMAIN_RE.findall(body)))
    endpoints = HTTP_ENDPOINT_RE.findall(body)
    endpoint_blocks = _endpoint_blocks(body)
    error_codes = sorted(set(ERROR_CODE_RE.findall(body)))

    if not ac_ids:
        issues.append(_issue("error" if ready else "warning", "missing_ac_refs", "contract contains no AC refs"))
    if not domain_ids:
        issues.append(_issue("warning", "missing_domain_refs", "contract contains no Domain ID refs"))

    if "rest" in contract_forms and not endpoints:
        issues.append(_issue("error" if ready else "warning", "missing_rest_endpoints", "REST contract form requires endpoint definitions"))
    if "grpc" in contract_forms and not _has_any(body, ("proto", ".proto", "rpc ", "service ")):
        issues.append(_issue("error" if ready else "warning", "missing_grpc_proto_ref", "gRPC contract form requires proto/service/method references"))
    if "message" in contract_forms and not _has_any(body, ("topic", "queue", "payload schema", "schema", "dlq")):
        issues.append(_issue("error" if ready else "warning", "missing_message_contract_refs", "message contract form requires topic/queue and payload schema references"))
    if "cli" in contract_forms and not _has_any(body, ("stdout", "stderr", "exit code", "退出码", "command", "命令")):
        issues.append(_issue("error" if ready else "warning", "missing_cli_contract_refs", "CLI contract form requires command/input/output/exit code semantics"))
    if "sdk" in contract_forms and not _has_any(body, ("public api", "公开", "signature", "semver", "breaking change")):
        issues.append(_issue("error" if ready else "warning", "missing_sdk_contract_refs", "SDK contract form requires public API and versioning semantics"))

    endpoint_blocks_without_ac = [block for block in endpoint_blocks if not AC_RE.search(block)]
    if endpoint_blocks_without_ac:
        issues.append(_issue("error" if ready else "warning", "endpoint_missing_ac_refs", f"{len(endpoint_blocks_without_ac)} endpoint blocks do not reference AC IDs"))
    endpoint_blocks_without_error = [
        block
        for block in endpoint_blocks
        if not _has_any(block, ("错误", "error", "HTTP Status", "status")) or not ERROR_CODE_RE.search(block)
    ]
    if endpoint_blocks_without_error:
        issues.append(_issue("warning", "endpoint_missing_error_mapping", f"{len(endpoint_blocks_without_error)} endpoint blocks may lack error mapping"))

    if not _has_any(body, ("数据模型", "Data Model", "JSON Schema", "Zod", "interface", "schema", "proto")):
        issues.append(_issue("error" if ready else "warning", "missing_schema_section", "contract should define or reference shared schemas/data models"))
    if not error_codes:
        issues.append(_issue("error" if ready else "warning", "missing_error_codes", "contract contains no error code/status definitions"))
    if not _has_any(body, ("breaking", "non-breaking", "additive", "破坏", "兼容", "新增", "修改", "废弃", "删除", "变更日志")):
        issues.append(_issue("warning", "missing_change_classification", "contract changelog should classify breaking/non-breaking/additive changes"))
    if "rest" in contract_forms and not _has_any(body, ("OpenAPI", "JSON Schema", "Zod", ".yaml", ".json", "schema")):
        issues.append(_issue("warning", "missing_machine_readable_contract_ref", "REST contracts should reference OpenAPI, JSON Schema, or Zod artifacts when applicable"))

    return {
        "contract_path": str(contract_path),
        "ok": not any(issue["level"] == "error" for issue in issues),
        "issues": issues,
        "summary": {
            "stage_status": frontmatter.get("stage_status"),
            "contract_forms": contract_forms,
            "ac_ids": ac_ids,
            "domain_ids": domain_ids,
            "endpoint_count": len(endpoints),
            "error_codes": error_codes,
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate api-contract.md readiness heuristics")
    parser.add_argument("path", help="Path to api-contract.md or a feature directory containing api-contract.md")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    return parser


def main(argv: list[str]) -> int:
    args = build_parser().parse_args(argv[1:])
    path = Path(args.path)
    contract_path = path / "api-contract.md" if path.is_dir() else path
    result = validate_contract_file(contract_path)
    if args.json:
        print(json.dumps(result, ensure_ascii=True, indent=2))
    else:
        print(f"contract_path: {result['contract_path']}")
        print(f"ok: {str(result['ok']).lower()}")
        for issue in result["issues"]:
            print(f"{issue['level'].upper()} {issue['code']} [{issue['path']}]: {issue['message']}")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
