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


@dataclass(frozen=True)
class ProjectSpecContext:
    target_project_id: str
    target_project_root: str
    spec_root: str
    feature_root: str
    resolution_source: str
    resolved_project_root: Path
    resolved_spec_root: Path
    resolved_feature_root: Path


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


def _normalize_required_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"`{field_name}` must be a non-empty string")
    return value.strip()


def _normalize_relative_path(value: Any, field_name: str, default: str) -> str:
    raw = default if value in (None, "") else value
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError(f"`{field_name}` must be a non-empty string")
    normalized = Path(raw.strip())
    if normalized.is_absolute():
        raise ValueError(f"`{field_name}` must be a project-relative path")
    return normalized.as_posix()


def _relative_to_project(path: Path, project_root: Path) -> str:
    try:
        return str(path.relative_to(project_root))
    except ValueError:
        return str(path)


def _resolve_project_relative(project_root: Path, raw_path: str) -> Path:
    return (project_root / Path(raw_path)).resolve()


def locate_project_config(search_from: Path) -> Path | None:
    anchor = search_from.resolve()
    if search_from.suffix:
        anchor = anchor.parent
    for candidate_root in (anchor, *anchor.parents):
        candidate = candidate_root / ".docs/ship/project.yml"
        if candidate.exists():
            return candidate
    return None


def build_explicit_project_context(
    spec_root: Path,
    project_root: Path,
    *,
    feature_root: Path | str = Path(".docs"),
    target_project_id: str = "",
    resolution_source: str = "explicit_paths",
) -> ProjectSpecContext:
    resolved_project_root = project_root.resolve()
    feature_root_path = Path(feature_root)
    resolved_spec_root = (
        spec_root.resolve()
        if spec_root.is_absolute()
        else _resolve_project_relative(resolved_project_root, spec_root.as_posix())
    )
    resolved_feature_root = (
        feature_root_path.resolve()
        if feature_root_path.is_absolute()
        else _resolve_project_relative(resolved_project_root, feature_root_path.as_posix())
    )
    return ProjectSpecContext(
        target_project_id=target_project_id,
        target_project_root=".",
        spec_root=_relative_to_project(resolved_spec_root, resolved_project_root),
        feature_root=_relative_to_project(resolved_feature_root, resolved_project_root),
        resolution_source=resolution_source,
        resolved_project_root=resolved_project_root,
        resolved_spec_root=resolved_spec_root,
        resolved_feature_root=resolved_feature_root,
    )


def load_project_context(project_config: Path) -> ProjectSpecContext:
    resolved_config = project_config.resolve()
    config_data = yaml.safe_load(resolved_config.read_text(encoding="utf-8")) or {}
    if not isinstance(config_data, dict):
        raise ValueError(f"{resolved_config}: project config must be a YAML mapping")

    target_project_id = _normalize_required_string(config_data.get("project_id"), "project_id")
    project_root_raw = _normalize_relative_path(config_data.get("project_root"), "project_root", ".")
    spec_root_raw = _normalize_relative_path(config_data.get("spec_root"), "spec_root", ".docs/spec")
    feature_root_raw = _normalize_relative_path(
        config_data.get("feature_root"),
        "feature_root",
        ".docs",
    )

    module_layout = config_data.get("module_layout") or {}
    if not isinstance(module_layout, dict):
        raise ValueError("`module_layout` must be a mapping when provided")
    if module_layout.get("mode", "project_level_only") != "project_level_only":
        raise ValueError("only `project_level_only` module_layout.mode is supported")

    config_project_root = resolved_config.parents[2]
    resolved_project_root = _resolve_project_relative(config_project_root, project_root_raw)
    resolved_spec_root = _resolve_project_relative(resolved_project_root, spec_root_raw)
    resolved_feature_root = _resolve_project_relative(resolved_project_root, feature_root_raw)

    return ProjectSpecContext(
        target_project_id=target_project_id,
        target_project_root=".",
        spec_root=spec_root_raw,
        feature_root=feature_root_raw,
        resolution_source="project_config",
        resolved_project_root=resolved_project_root,
        resolved_spec_root=resolved_spec_root,
        resolved_feature_root=resolved_feature_root,
    )


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


def _scan_specs_with_context(project_context: ProjectSpecContext) -> dict[str, Any]:
    warnings: list[str] = []
    records: list[SpecRecord] = []
    spec_root = project_context.resolved_spec_root
    project_root = project_context.resolved_project_root

    if not spec_root.exists():
        return {
            "target_project_id": project_context.target_project_id,
            "target_project_root": project_context.target_project_root,
            "spec_root": project_context.spec_root,
            "feature_root": project_context.feature_root,
            "resolution_source": project_context.resolution_source,
            "index_status": "missing",
            "warnings": [f"{project_context.spec_root}: spec directory does not exist"],
            "specs": [],
        }

    index_path = spec_root / "INDEX.md"
    index_status = "ready" if index_path.exists() else "missing"
    if not index_path.exists():
        warnings.append(f"{_relative_to_project(index_path, project_root)}: missing INDEX.md registry")

    seen_ids: dict[str, str] = {}
    for path in sorted(spec_root.rglob("*.md")):
        if path.name == "INDEX.md":
            continue
        try:
            record = _parse_spec(path, spec_root, project_root)
        except ValueError as exc:
            warnings.append(f"{_relative_to_project(path, project_root)}: invalid spec frontmatter: {exc}")
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
        "target_project_id": project_context.target_project_id,
        "target_project_root": project_context.target_project_root,
        "spec_root": project_context.spec_root,
        "feature_root": project_context.feature_root,
        "resolution_source": project_context.resolution_source,
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


def scan_specs(
    spec_root: Path | None = None,
    project_root: Path | None = None,
    *,
    project_context: ProjectSpecContext | None = None,
    feature_root: Path | str = Path(".docs"),
    target_project_id: str = "",
    resolution_source: str = "explicit_paths",
) -> dict[str, Any]:
    if project_context is None:
        if spec_root is None:
            raise ValueError("scan_specs requires spec_root when project_context is not provided")
        project_context = build_explicit_project_context(
            spec_root=spec_root,
            project_root=project_root or Path.cwd(),
            feature_root=feature_root,
            target_project_id=target_project_id,
            resolution_source=resolution_source,
        )
    return _scan_specs_with_context(project_context)


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


def _normalize_requested_files(files: list[str], project_root: Path) -> list[str]:
    normalized: list[str] = []
    cwd = Path.cwd().resolve()
    for raw_path in files:
        candidate = Path(raw_path)
        if candidate.is_absolute():
            normalized.append(_relative_to_project(candidate.resolve(), project_root))
            continue
        resolved_from_cwd = (cwd / candidate).resolve()
        if str(resolved_from_cwd).startswith(str(project_root)):
            normalized.append(_relative_to_project(resolved_from_cwd, project_root))
            continue
        normalized.append(candidate.as_posix())
    return normalized


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
    spec_root: Path | None,
    stage_hook: str,
    stack_tags: list[str] | None = None,
    domains: list[str] | None = None,
    files: list[str] | None = None,
    project_root: Path | None = None,
    *,
    project_context: ProjectSpecContext | None = None,
    feature_root: Path | str = Path(".docs"),
    target_project_id: str = "",
    resolution_source: str = "explicit_paths",
) -> dict[str, Any]:
    if stage_hook not in VALID_STAGE_HOOKS:
        raise ValueError(f"invalid stage hook: {stage_hook}")

    if project_context is None:
        if spec_root is None:
            raise ValueError("resolve_specs requires spec_root when project_context is not provided")
        project_context = build_explicit_project_context(
            spec_root=spec_root,
            project_root=project_root or Path.cwd(),
            feature_root=feature_root,
            target_project_id=target_project_id,
            resolution_source=resolution_source,
        )

    scan_result = scan_specs(project_context=project_context)
    stack_tag_set = _normalize_requested_tags(stack_tags)
    domain_set = _normalize_requested_tags(domains)
    file_list = _normalize_requested_files(
        [value for value in (files or []) if value],
        project_context.resolved_project_root,
    )

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
        "target_project_id": project_context.target_project_id,
        "target_project_root": project_context.target_project_root,
        "spec_root": project_context.spec_root,
        "feature_root": project_context.feature_root,
        "resolution_source": project_context.resolution_source,
        "stage_hook": stage_hook,
        "index_status": scan_result["index_status"],
        "matched_spec_ids": [spec["spec_id"] for spec in matched_specs],
        "matched_specs": matched_specs,
        "normalized_files": file_list,
        "warnings": warnings,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ship spec runtime helper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan_parser = subparsers.add_parser("scan", help="Validate and list project specs")
    scan_parser.add_argument(
        "spec_root",
        nargs="?",
        help="Spec root directory",
    )
    scan_parser.add_argument(
        "--project-config",
        help="Path to target project .docs/ship/project.yml",
    )
    scan_parser.add_argument(
        "--project-root",
        help="Project root used for low-level explicit path resolution",
    )
    scan_parser.add_argument(
        "--feature-root",
        default=".docs",
        help="Feature root used for low-level explicit path resolution",
    )

    resolve_parser = subparsers.add_parser("resolve", help="Resolve matching specs for a stage hook")
    resolve_parser.add_argument("stage_hook", choices=VALID_STAGE_HOOKS)
    resolve_parser.add_argument(
        "--project-config",
        help="Path to target project .docs/ship/project.yml",
    )
    resolve_parser.add_argument(
        "--spec-root",
        help="Spec root directory",
    )
    resolve_parser.add_argument(
        "--project-root",
        help="Project root used for low-level explicit path resolution",
    )
    resolve_parser.add_argument(
        "--feature-root",
        default=".docs",
        help="Feature root used for low-level explicit path resolution",
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
        if args.project_config:
            project_context = load_project_context(Path(args.project_config))
            payload = scan_specs(project_context=project_context)
        else:
            if not args.spec_root or not args.project_root:
                parser.error("scan requires --project-config or both spec_root and --project-root")
            payload = scan_specs(
                Path(args.spec_root),
                project_root=Path(args.project_root),
                feature_root=Path(args.feature_root),
            )
        print(json.dumps(payload, ensure_ascii=True, indent=2))
        return 0

    if args.command == "resolve":
        if args.project_config:
            project_context = load_project_context(Path(args.project_config))
            payload = resolve_specs(
                spec_root=None,
                project_context=project_context,
                stage_hook=args.stage_hook,
                stack_tags=args.stack_tag,
                domains=args.domain,
                files=args.file,
            )
        else:
            if not args.spec_root or not args.project_root:
                parser.error(
                    "resolve requires --project-config or both --spec-root and --project-root"
                )
            payload = resolve_specs(
                spec_root=Path(args.spec_root),
                stage_hook=args.stage_hook,
                stack_tags=args.stack_tag,
                domains=args.domain,
                files=args.file,
                project_root=Path(args.project_root),
                feature_root=Path(args.feature_root),
            )
        print(json.dumps(payload, ensure_ascii=True, indent=2))
        return 0

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
