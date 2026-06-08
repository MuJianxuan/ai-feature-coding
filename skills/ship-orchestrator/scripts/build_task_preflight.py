#!/usr/bin/env python3
"""Preflight checks for the single DOING ship-build task."""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
from pathlib import Path
from typing import Any

TASK_HEADING_RE = re.compile(r"(?m)^(?:#{2,6}\s+|[-*]\s+)?(?:Task\s+)?((?:FE|BE|FS|FT|TASK)-[A-Z0-9]+-\d{3}|(?:FE|BE|FS|FT)?-\d{3})\b")
AC_RE = re.compile(r"\bAC-[A-Z0-9]+-\d{3}\b")
REQUIRED_TASK_BRIEF_SECTIONS = ("任务目标", "上下文", "约束", "验收", "输出")


BROAD_ALLOWED_FILE_GLOBS = {"*", "**", "**/*", "./**/*", "."}
ALLOWED_FILES_KEY_RE = re.compile(r"(?im)^\s*[-*]?\s*(allowed_files|allowed files|允许文件)\s*:\s*(.*)$")
INLINE_LIST_RE = re.compile(r"^\[(.*)\]$")


def normalize_allowed_file_pattern(raw: str) -> str:
    value = raw.strip().strip('"\'')
    if not value:
        raise ValueError("empty_allowed_file_path")
    path = Path(value)
    if path.is_absolute():
        raise ValueError("invalid_allowed_file_path")
    if any(part == ".." for part in path.parts):
        raise ValueError("invalid_allowed_file_path")
    normalized = path.as_posix().lstrip("./")
    if not normalized or normalized in BROAD_ALLOWED_FILE_GLOBS:
        raise ValueError("allowed_file_glob_too_broad")
    if normalized.endswith("/**") and normalized.count("/") == 0:
        raise ValueError("allowed_file_glob_too_broad")
    return normalized


def _split_inline_allowed_files(value: str) -> list[str]:
    value = value.strip()
    if not value:
        return []
    match = INLINE_LIST_RE.match(value)
    if match:
        return [item.strip().strip('"\'') for item in match.group(1).split(",") if item.strip()]
    return [value]


def extract_allowed_files(block: str) -> list[str]:
    lines = block.splitlines()
    allowed: list[str] = []
    for index, line in enumerate(lines):
        match = ALLOWED_FILES_KEY_RE.match(line)
        if not match:
            continue
        inline = match.group(2).strip()
        allowed.extend(_split_inline_allowed_files(inline))
        if inline:
            continue
        base_indent = len(line) - len(line.lstrip())
        for child in lines[index + 1:]:
            if not child.strip():
                continue
            indent = len(child) - len(child.lstrip())
            if indent <= base_indent:
                break
            item = child.strip()
            if item.startswith(("- ", "* ")):
                item = item[2:].strip()
                if ":" in item:
                    _, _, item = item.partition(":")
                    item = item.strip()
                if item:
                    allowed.extend(_split_inline_allowed_files(item))
    return allowed


def validate_allowed_files(paths: list[str]) -> tuple[list[str], list[dict[str, str]]]:
    normalized: list[str] = []
    issues: list[dict[str, str]] = []
    for raw in paths:
        try:
            value = normalize_allowed_file_pattern(raw)
        except ValueError as exc:
            code = str(exc) or "invalid_allowed_file_path"
            issues.append(_issue("error", code, f"invalid allowed_files entry: {raw!r}"))
            continue
        if value not in normalized:
            normalized.append(value)
    return normalized, issues


def file_matches_allowed(path: str, allowed_pattern: str) -> bool:
    target = normalize_allowed_file_pattern(path)
    pattern = normalize_allowed_file_pattern(allowed_pattern)
    if pattern.endswith("/**"):
        prefix = pattern[:-3].rstrip("/")
        return target == prefix or target.startswith(prefix + "/")
    if any(char in pattern for char in "*?["):
        return fnmatch.fnmatch(target, pattern)
    if pattern.endswith("/"):
        return target.startswith(pattern)
    return target == pattern or target.startswith(pattern.rstrip("/") + "/")


def _issue(level: str, code: str, message: str, path: str | None = None) -> dict[str, str]:
    payload = {"level": level, "code": code, "message": message}
    if path:
        payload["path"] = path
    return payload


def _task_blocks(text: str) -> list[tuple[str, str]]:
    matches = list(TASK_HEADING_RE.finditer(text))
    blocks: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        blocks.append((match.group(1), text[start:end]))
    return blocks


def _status(block: str) -> str:
    match = re.search(r"(?im)^\s*[-*]?\s*status\s*:\s*([A-Z_]+)\b", block)
    return match.group(1) if match else ""


def _has(block: str, *needles: str) -> bool:
    lowered = block.lower()
    return any(needle.lower() in lowered for needle in needles)


def _plan_paths(feature_dir: Path, project_scope: str) -> list[Path]:
    paths = []
    if project_scope in ("fullstack", "frontend_only"):
        paths.append(feature_dir / "frontend-plan.md")
    if project_scope in ("fullstack", "backend_only"):
        paths.append(feature_dir / "backend-plan.md")
    return paths


def build_task_preflight(feature_dir: Path, project_scope: str = "fullstack") -> dict[str, Any]:
    feature_dir = feature_dir.resolve()
    issues: list[dict[str, str]] = []
    doing: list[dict[str, Any]] = []
    tasks: list[dict[str, Any]] = []

    for path in _plan_paths(feature_dir, project_scope):
        if not path.exists():
            issues.append(_issue("error", "missing_plan", f"{path.name} does not exist", path.name))
            continue
        text = path.read_text(encoding="utf-8")
        for task_id, block in _task_blocks(text):
            status = _status(block)
            task = {
                "task_id": task_id,
                "path": path.name,
                "status": status,
                "ac_refs": sorted(set(AC_RE.findall(block))),
                "allowed_files_raw": extract_allowed_files(block),
                "has_verification_command": _has(block, "verification command", "verification_command", "验证命令"),
                "has_evidence": _has(block, "evidence", "done evidence", "完成证据"),
                "has_spec_refs": _has(block, "spec_refs", "spec refs", "spec context"),
                "missing_brief_sections": [section for section in REQUIRED_TASK_BRIEF_SECTIONS if section not in block],
            }
            allowed_files, invalid_allowed_files = validate_allowed_files(task["allowed_files_raw"])
            task["allowed_files"] = allowed_files
            task["invalid_allowed_files"] = invalid_allowed_files
            task["has_allowed_files"] = bool(allowed_files)
            tasks.append(task)
            if status == "DOING":
                doing.append(task)

    if len(doing) != 1:
        issues.append(_issue("error", "doing_count_invalid", f"expected exactly one DOING task, found {len(doing)}"))
    elif doing:
        task = doing[0]
        if not task["has_allowed_files"]:
            issues.append(_issue("error", "doing_missing_allowed_files", f"{task['task_id']} missing allowed_files", task["path"]))
        for invalid in task.get("invalid_allowed_files", []):
            issue = dict(invalid)
            issue["path"] = task["path"]
            issues.append(issue)
        if not task["ac_refs"]:
            issues.append(_issue("error", "doing_missing_ac_refs", f"{task['task_id']} missing AC refs", task["path"]))
        if not task["has_verification_command"]:
            issues.append(_issue("error", "doing_missing_verification_command", f"{task['task_id']} missing verification command", task["path"]))
        for section in task["missing_brief_sections"]:
            issues.append(_issue("error", "doing_missing_task_brief_section", f"{task['task_id']} missing {section}", task["path"]))

    return {
        "feature_dir": str(feature_dir),
        "project_scope": project_scope,
        "ok": not any(issue["level"] == "error" for issue in issues),
        "issues": issues,
        "doing_tasks": doing,
        "tasks": tasks,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Preflight the current ship-build DOING task")
    parser.add_argument("feature_dir")
    parser.add_argument("--project-scope", choices=("fullstack", "backend_only", "frontend_only"), default="fullstack")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = build_task_preflight(Path(args.feature_dir), args.project_scope)
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
