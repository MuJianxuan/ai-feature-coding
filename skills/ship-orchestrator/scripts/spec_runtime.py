#!/usr/bin/env python3
"""Runtime helpers for ship-spec discovery and matching."""

from __future__ import annotations

import argparse
import fnmatch
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


VALID_STAGE_HOOKS: tuple[str, ...] = (
    "ship-tech-discovery",
    "ship-frontend-design",
    "ship-backend-design",
    "ship-build",
    "ship-handoff",
)

VALID_SCOPES: tuple[str, ...] = (
    "project",
    "module",
    "file",
)


@dataclass(frozen=True)
class SpecRecord:
    spec_id: str
    path: str
    scope: str
    stage_hooks: tuple[str, ...]
    stack_tags: tuple[str, ...]
    domains: tuple[str, ...]
    applies_to: tuple[str, ...]
    last_updated: str


def _load_frontmatter(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError("missing YAML frontmatter start")

    try:
        _, rest = text.split("---\n", 1)
        raw_frontmatter, _ = rest.split("\n---\n", 1)
    except ValueError as exc:
        raise ValueError("frontmatter closing delimiter not found") from exc

    data = yaml.safe_load(raw_frontmatter) or {}
    if not isinstance(data, dict):
        raise ValueError("frontmatter is not a YAML mapping")
    return data


def _normalize_string_list(value: Any, field_name: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise ValueError(f"`{field_name}` must be a list")
    result: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"`{field_name}` entries must be non-empty strings")
        result.append(item.strip())
    return tuple(result)


def _relative_to_project(path: Path, project_root: Path) -> str:
    try:
        return str(path.relative_to(project_root))
    except ValueError:
        return str(path)


def _parse_spec(path: Path, spec_root: Path, project_root: Path) -> SpecRecord:
    data = _load_frontmatter(path)

    spec_id = data.get("spec_id")
    if not isinstance(spec_id, str) or not spec_id.strip():
        raise ValueError("missing `spec_id`")

    scope = data.get("scope")
    if scope not in VALID_SCOPES:
        raise ValueError(f"`scope` must be one of {VALID_SCOPES}")

    stage_hooks = _normalize_string_list(data.get("stage_hooks"), "stage_hooks")
    if not stage_hooks:
        raise ValueError("`stage_hooks` must not be empty")
    invalid_hooks = sorted({hook for hook in stage_hooks if hook not in VALID_STAGE_HOOKS})
    if invalid_hooks:
        raise ValueError(f"`stage_hooks` contains invalid values: {', '.join(invalid_hooks)}")

    stack_tags = _normalize_string_list(data.get("stack_tags"), "stack_tags")
    domains = _normalize_string_list(data.get("domains"), "domains")
    applies_to = _normalize_string_list(data.get("applies_to"), "applies_to")

    last_updated = data.get("last_updated")
    if not isinstance(last_updated, str):
        raise ValueError("`last_updated` must be a string")

    return SpecRecord(
        spec_id=spec_id.strip(),
        path=_relative_to_project(path, project_root),
        scope=scope,
        stage_hooks=stage_hooks,
        stack_tags=stack_tags,
        domains=domains,
        applies_to=applies_to,
        last_updated=last_updated,
    )


def scan_specs(spec_root: Path, project_root: Path | None = None) -> dict[str, Any]:
    warnings: list[str] = []
    records: list[SpecRecord] = []
    spec_root = spec_root.resolve()
    project_root = (project_root or Path.cwd()).resolve()

    if not spec_root.exists():
        return {
            "spec_root": str(spec_root),
            "index_status": "missing",
            "warnings": [f"{spec_root}: spec directory does not exist"],
            "specs": [],
        }

    index_path = spec_root / "INDEX.md"
    index_status = "ready" if index_path.exists() else "missing"
    if not index_path.exists():
        warnings.append(f"{index_path}: missing INDEX.md registry")

    seen_ids: dict[str, str] = {}
    for path in sorted(spec_root.rglob("*.md")):
        if path.name == "INDEX.md":
            continue
        try:
            record = _parse_spec(path, spec_root, project_root)
        except ValueError as exc:
            warnings.append(f"{path}: invalid spec frontmatter: {exc}")
            continue

        duplicate_path = seen_ids.get(record.spec_id)
        if duplicate_path:
            warnings.append(
                f"duplicate spec_id `{record.spec_id}` in {duplicate_path} and {record.path}"
            )
            continue

        seen_ids[record.spec_id] = record.path
        records.append(record)

    if warnings and index_status == "ready":
        index_status = "invalid"

    return {
        "spec_root": str(spec_root),
        "index_status": index_status,
        "warnings": warnings,
        "specs": [
            {
                "spec_id": record.spec_id,
                "path": record.path,
                "scope": record.scope,
                "stage_hooks": list(record.stage_hooks),
                "stack_tags": list(record.stack_tags),
                "domains": list(record.domains),
                "applies_to": list(record.applies_to),
                "last_updated": record.last_updated,
            }
            for record in records
        ],
    }


def _normalize_requested_tags(values: list[str] | None) -> set[str]:
    return {value.strip() for value in (values or []) if value.strip()}


def _matches_stack(record: SpecRecord, stack_tags: set[str]) -> bool:
    if not stack_tags:
        return True
    if not record.stack_tags:
        return True
    return bool(stack_tags.intersection(record.stack_tags))


def _matches_domains(record: SpecRecord, domains: set[str]) -> bool:
    if not domains:
        return True
    if not record.domains:
        return True
    return bool(domains.intersection(record.domains))


def _matches_files(record: SpecRecord, files: list[str]) -> bool:
    if not record.applies_to:
        return True
    if not files:
        return False
    return any(
        fnmatch.fnmatch(file_path, pattern)
        or fnmatch.fnmatch(Path(file_path).name, pattern)
        for file_path in files
        for pattern in record.applies_to
    )


def resolve_specs(
    spec_root: Path,
    stage_hook: str,
    stack_tags: list[str] | None = None,
    domains: list[str] | None = None,
    files: list[str] | None = None,
    project_root: Path | None = None,
) -> dict[str, Any]:
    if stage_hook not in VALID_STAGE_HOOKS:
        raise ValueError(f"invalid stage hook: {stage_hook}")

    scan_result = scan_specs(spec_root, project_root=project_root)
    stack_tag_set = _normalize_requested_tags(stack_tags)
    domain_set = _normalize_requested_tags(domains)
    file_list = [value for value in (files or []) if value]

    matched_specs: list[dict[str, Any]] = []
    for spec in scan_result["specs"]:
        record = SpecRecord(
            spec_id=spec["spec_id"],
            path=spec["path"],
            scope=spec["scope"],
            stage_hooks=tuple(spec["stage_hooks"]),
            stack_tags=tuple(spec["stack_tags"]),
            domains=tuple(spec["domains"]),
            applies_to=tuple(spec["applies_to"]),
            last_updated=spec["last_updated"],
        )

        if stage_hook not in record.stage_hooks:
            continue
        if not _matches_stack(record, stack_tag_set):
            continue
        if not _matches_domains(record, domain_set):
            continue
        if stage_hook == "ship-build" and not _matches_files(record, file_list):
            continue

        matched_specs.append(spec)

    warnings = list(scan_result["warnings"])
    if not matched_specs:
        warnings.append(f"{stage_hook}: no matching specs found")

    return {
        "stage_hook": stage_hook,
        "index_status": scan_result["index_status"],
        "matched_spec_ids": [spec["spec_id"] for spec in matched_specs],
        "matched_specs": matched_specs,
        "warnings": warnings,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ship spec runtime helper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan_parser = subparsers.add_parser("scan", help="Validate and list project specs")
    scan_parser.add_argument(
        "spec_root",
        nargs="?",
        default=".docs/spec",
        help="Spec root directory",
    )
    scan_parser.add_argument(
        "--project-root",
        default=".",
        help="Project root used for stable relative paths",
    )

    resolve_parser = subparsers.add_parser("resolve", help="Resolve matching specs for a stage hook")
    resolve_parser.add_argument("stage_hook", choices=VALID_STAGE_HOOKS)
    resolve_parser.add_argument(
        "--spec-root",
        default=".docs/spec",
        help="Spec root directory",
    )
    resolve_parser.add_argument(
        "--project-root",
        default=".",
        help="Project root used for stable relative paths",
    )
    resolve_parser.add_argument(
        "--stack-tag",
        action="append",
        default=[],
        help="Stack tag used for spec matching",
    )
    resolve_parser.add_argument(
        "--domain",
        action="append",
        default=[],
        help="Domain tag used for spec matching",
    )
    resolve_parser.add_argument(
        "--file",
        action="append",
        default=[],
        help="File path used for ship-build applies_to matching",
    )

    return parser


def main(argv: list[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv[1:])

    if args.command == "scan":
        payload = scan_specs(Path(args.spec_root), project_root=Path(args.project_root))
        print(json.dumps(payload, ensure_ascii=True, indent=2))
        return 0

    if args.command == "resolve":
        payload = resolve_specs(
            spec_root=Path(args.spec_root),
            stage_hook=args.stage_hook,
            stack_tags=args.stack_tag,
            domains=args.domain,
            files=args.file,
            project_root=Path(args.project_root),
        )
        print(json.dumps(payload, ensure_ascii=True, indent=2))
        return 0

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
