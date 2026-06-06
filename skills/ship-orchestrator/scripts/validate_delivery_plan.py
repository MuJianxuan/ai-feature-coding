#!/usr/bin/env python3
"""Validate delivery plan task schema and dependency graph."""

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
from feature_meta_runtime import load_meta  # noqa: E402

TASK_ID_RE = re.compile(r"\b(?:FE|BE|FS|TASK)-[A-Z0-9]+-\d{3}\b")
TASK_HEADING_RE = re.compile(r"(?m)^(?:#{2,6}\s+|[-*]\s+)?((?:FE|BE|FS|TASK)-[A-Z0-9]+-\d{3})\b")
AC_RE = re.compile(r"\bAC-[A-Z0-9]+-\d{3}\b")
CONTRACT_REF_RE = re.compile(r"\b(?:GET|POST|PUT|PATCH|DELETE)\s+/[A-Za-z0-9_./:{}-]+|\bapi-contract\.md\b|\bcontract\b", re.IGNORECASE)

REQUIRED_TASK_FIELDS = {
    "project": ("project:", "project：", "目标项目"),
    "scope": ("scope", "范围"),
    "allowed_files": ("allowed_files", "allowed files", "允许文件"),
    "depends_on": ("depends_on", "depends on", "依赖"),
    "verification_command": ("verification command", "verification_command", "验证命令"),
    "done_evidence": ("done evidence", "done_evidence", "完成证据"),
}

REQUIRED_TASK_BRIEF_SECTIONS = ("任务目标", "上下文", "约束", "验收", "输出")


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


def _has_field(block: str, aliases: tuple[str, ...]) -> bool:
    lowered = block.lower()
    return any(alias.lower() in lowered for alias in aliases)


def _depends_on(task_id: str, block: str) -> list[str]:
    deps: set[str] = set()
    for line in block.splitlines():
        lowered = line.lower()
        if "depends_on" in lowered or "depends on" in lowered or "依赖" in line:
            deps.update(match for match in TASK_ID_RE.findall(line) if match != task_id)
    return sorted(deps)


def _find_cycle(graph: dict[str, list[str]]) -> list[str]:
    visiting: set[str] = set()
    visited: set[str] = set()
    stack: list[str] = []

    def visit(node: str) -> list[str]:
        if node in visiting:
            try:
                return stack[stack.index(node) :] + [node]
            except ValueError:
                return [node, node]
        if node in visited:
            return []
        visiting.add(node)
        stack.append(node)
        for dep in graph.get(node, []):
            cycle = visit(dep)
            if cycle:
                return cycle
        stack.pop()
        visiting.remove(node)
        visited.add(node)
        return []

    for node in graph:
        cycle = visit(node)
        if cycle:
            return cycle
    return []


def _selected_scope_terms(meta: dict[str, Any]) -> list[str]:
    technical_plan_source = meta.get("technical_plan_source")
    if not isinstance(technical_plan_source, dict):
        return []
    terms: list[str] = []
    for item in technical_plan_source.get("selected_scope") or []:
        if isinstance(item, dict):
            for key in ("label", "source_file"):
                value = str(item.get(key, "")).strip()
                if value:
                    terms.append(value)
        elif isinstance(item, str) and item.strip():
            terms.append(item.strip())
    for source_file in technical_plan_source.get("source_files") or []:
        value = str(source_file).strip()
        if value:
            terms.append(value)
    pasted = str(technical_plan_source.get("pasted_excerpt_file", "")).strip()
    if pasted:
        terms.append(pasted)
    return terms


def _technical_plan_task_issues(blocks: list[tuple[str, str]], terms: list[str], path_name: str) -> list[dict[str, str]]:
    if not terms:
        return []
    issues: list[dict[str, str]] = []
    lowered_terms = [term.lower() for term in terms]
    for task_id, block in blocks:
        lowered_block = block.lower()
        if not any(term in lowered_block for term in lowered_terms):
            issues.append(
                _issue(
                    "error",
                    "task_missing_selected_scope_ref",
                    f"{task_id} must reference selected scope or technical source",
                    path_name,
                )
            )
    return issues


def validate_plan_file(path: Path, expected_role: str, selected_scope_terms: list[str] | None = None) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    if not path.exists():
        return {
            "path": str(path),
            "ok": False,
            "issues": [_issue("error", "missing_plan", f"{path.name} does not exist", path.name)],
            "tasks": [],
        }
    try:
        frontmatter, body = read_frontmatter(path)
    except ValueError as exc:
        return {
            "path": str(path),
            "ok": False,
            "issues": [_issue("error", "invalid_frontmatter", str(exc), path.name)],
            "tasks": [],
        }

    ready = frontmatter.get("stage_status") == "ready"
    if frontmatter.get("stage") != "ship-delivery-plan":
        issues.append(_issue("error", "invalid_stage", f"expected ship-delivery-plan, found {frontmatter.get('stage')!r}", path.name))
    if frontmatter.get("artifact_role") != expected_role:
        issues.append(_issue("error", "invalid_artifact_role", f"expected {expected_role}, found {frontmatter.get('artifact_role')!r}", path.name))
    if frontmatter.get("stage_status") not in ("draft", "ready", "complete"):
        issues.append(_issue("error", "invalid_stage_status", f"invalid stage_status: {frontmatter.get('stage_status')!r}", path.name))

    blocks = _task_blocks(body)
    task_ids = [task_id for task_id, _block in blocks]
    if not task_ids:
        issues.append(_issue("error" if ready else "warning", "missing_tasks", "plan contains no task IDs", path.name))

    graph: dict[str, list[str]] = {}
    task_rows: list[dict[str, Any]] = []
    for task_id, block in blocks:
        deps = _depends_on(task_id, block)
        graph[task_id] = deps
        row = {
            "task_id": task_id,
            "depends_on": deps,
            "ac_refs": sorted(set(AC_RE.findall(block))),
            "contract_refs": bool(CONTRACT_REF_RE.search(block)),
        }
        task_rows.append(row)
        for field_name, aliases in REQUIRED_TASK_FIELDS.items():
            if not _has_field(block, aliases):
                issues.append(_issue("error" if ready else "warning", "task_missing_field", f"{task_id} missing {field_name}", path.name))
        for section in REQUIRED_TASK_BRIEF_SECTIONS:
            if section not in block:
                issues.append(_issue("error" if ready else "warning", "task_missing_brief_section", f"{task_id} missing {section}", path.name))
        if not row["ac_refs"]:
            issues.append(_issue("error" if ready else "warning", "task_missing_ac_refs", f"{task_id} missing AC refs", path.name))

    unknown_deps = sorted({dep for deps in graph.values() for dep in deps if dep not in graph})
    if unknown_deps:
        issues.append(_issue("error", "unknown_task_dependency", f"depends_on references unknown tasks: {', '.join(unknown_deps)}", path.name))
    cycle = _find_cycle(graph)
    if cycle:
        issues.append(_issue("error", "task_dependency_cycle", f"dependency cycle: {' -> '.join(cycle)}", path.name))

    if ready and not any(row["contract_refs"] for row in task_rows):
        issues.append(_issue("warning", "missing_contract_task_refs", "ready plan has no explicit contract refs", path.name))
    issues.extend(_technical_plan_task_issues(blocks, selected_scope_terms or [], path.name))

    return {
        "path": str(path),
        "ok": not any(issue["level"] == "error" for issue in issues),
        "issues": issues,
        "tasks": task_rows,
    }


def validate_delivery_plan(feature_dir: Path, project_scope: str = "fullstack") -> dict[str, Any]:
    feature_dir = feature_dir.resolve()
    issues: list[dict[str, str]] = []
    plan_results: list[dict[str, Any]] = []
    selected_scope_terms: list[str] = []
    meta_path = feature_dir / "meta.yml"
    if meta_path.exists():
        try:
            meta = load_meta(meta_path)
        except Exception:
            meta = {}
        if meta.get("scenario") == "technical_plan_provided":
            selected_scope_terms = _selected_scope_terms(meta)
    expected = []
    if project_scope in ("fullstack", "frontend_only"):
        expected.append(("frontend-plan.md", "frontend-plan"))
    if project_scope in ("fullstack", "backend_only"):
        expected.append(("backend-plan.md", "backend-plan"))

    for relative_path, role in expected:
        result = validate_plan_file(feature_dir / relative_path, role, selected_scope_terms)
        plan_results.append(result)
        issues.extend(result["issues"])

    all_ac_refs = sorted({ac for result in plan_results for task in result["tasks"] for ac in task["ac_refs"]})
    if not all_ac_refs:
        issues.append(_issue("warning", "missing_plan_ac_coverage", "no AC refs found across delivery plans"))

    if project_scope == "fullstack":
        frontend_tasks = {task["task_id"] for result in plan_results if result["path"].endswith("frontend-plan.md") for task in result["tasks"]}
        backend_tasks = {task["task_id"] for result in plan_results if result["path"].endswith("backend-plan.md") for task in result["tasks"]}
        if frontend_tasks and backend_tasks:
            has_cross_dep = False
            for result in plan_results:
                for task in result["tasks"]:
                    deps = set(task["depends_on"])
                    if task["task_id"] in frontend_tasks and deps & backend_tasks:
                        has_cross_dep = True
                    if task["task_id"] in backend_tasks and deps & frontend_tasks:
                        has_cross_dep = True
            if not has_cross_dep:
                issues.append(_issue("warning", "missing_sync_dependency", "fullstack plans do not show cross-side sync dependencies"))

    return {
        "feature_dir": str(feature_dir),
        "project_scope": project_scope,
        "ok": not any(issue["level"] == "error" for issue in issues),
        "issues": issues,
        "plans": plan_results,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate delivery plan task schema and DAG")
    parser.add_argument("feature_dir", help="Feature directory containing frontend-plan.md/backend-plan.md")
    parser.add_argument("--project-scope", choices=("fullstack", "backend_only", "frontend_only"), default="fullstack")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    return parser


def main(argv: list[str]) -> int:
    args = build_parser().parse_args(argv[1:])
    result = validate_delivery_plan(Path(args.feature_dir), args.project_scope)
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
    raise SystemExit(main(sys.argv))
