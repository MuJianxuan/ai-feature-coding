#!/usr/bin/env python3
"""Preflight checks for the single DOING ship-build task."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

TASK_HEADING_RE = re.compile(r"(?m)^(?:#{2,6}\s+|[-*]\s+)?(?:Task\s+)?((?:FE|BE|FS|FT|TASK)-[A-Z0-9]+-\d{3}|(?:FE|BE|FS|FT)?-\d{3})\b")
AC_RE = re.compile(r"\bAC-[A-Z0-9]+-\d{3}\b")


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


def _task_source_paths(feature_dir: Path, project_scope: str, pipeline_mode: str) -> list[Path]:
    if pipeline_mode == "fast-track":
        return [feature_dir / "fast-track-tasks.md"]
    return _plan_paths(feature_dir, project_scope)


def build_task_preflight(feature_dir: Path, project_scope: str = "fullstack", pipeline_mode: str = "standard") -> dict[str, Any]:
    feature_dir = feature_dir.resolve()
    issues: list[dict[str, str]] = []
    doing: list[dict[str, Any]] = []
    tasks: list[dict[str, Any]] = []

    for path in _task_source_paths(feature_dir, project_scope, pipeline_mode):
        if not path.exists():
            code = "missing_fast_track_tasks" if pipeline_mode == "fast-track" else "missing_plan"
            issues.append(_issue("error", code, f"{path.name} does not exist", path.name))
            continue
        text = path.read_text(encoding="utf-8")
        for task_id, block in _task_blocks(text):
            status = _status(block)
            task = {
                "task_id": task_id,
                "path": path.name,
                "status": status,
                "ac_refs": sorted(set(AC_RE.findall(block))),
                "has_allowed_files": _has(block, "allowed_files", "allowed files", "允许文件"),
                "has_verification_command": _has(block, "verification command", "verification_command", "验证命令"),
                "has_evidence": _has(block, "evidence", "done evidence", "完成证据"),
                "has_spec_refs": _has(block, "spec_refs", "spec refs", "spec context"),
            }
            tasks.append(task)
            if status == "DOING":
                doing.append(task)

    if len(doing) != 1:
        issues.append(_issue("error", "doing_count_invalid", f"expected exactly one DOING task, found {len(doing)}"))
    elif doing:
        task = doing[0]
        if not task["has_allowed_files"]:
            issues.append(_issue("error", "doing_missing_allowed_files", f"{task['task_id']} missing allowed_files", task["path"]))
        if not task["ac_refs"]:
            issues.append(_issue("error", "doing_missing_ac_refs", f"{task['task_id']} missing AC refs", task["path"]))
        if not task["has_verification_command"]:
            issues.append(_issue("error", "doing_missing_verification_command", f"{task['task_id']} missing verification command", task["path"]))

    return {
        "feature_dir": str(feature_dir),
        "project_scope": project_scope,
        "pipeline_mode": pipeline_mode,
        "ok": not any(issue["level"] == "error" for issue in issues),
        "issues": issues,
        "doing_tasks": doing,
        "tasks": tasks,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Preflight the current ship-build DOING task")
    parser.add_argument("feature_dir")
    parser.add_argument("--project-scope", choices=("fullstack", "backend_only", "frontend_only"), default="fullstack")
    parser.add_argument("--pipeline-mode", choices=("standard", "fast-track"), default="standard")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = build_task_preflight(Path(args.feature_dir), args.project_scope, args.pipeline_mode)
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
