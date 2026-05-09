#!/usr/bin/env python3
"""Inspect an AI Feature Workflow directory and infer the next stage.

The script is intentionally stdlib-only so it can run in minimal Codex
workspaces. It implements the same ordered stage rules described in
ai-feature-orchestrator/SKILL.md and WORKFLOW_CONTRACT.md.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any

STAGE_DOCS = {
    "requirements": "requirements.md",
    "investigation": "investigation.md",
    "design": "design.md",
    "tasks": "tasks.md",
    "verification": "verification.md",
    "handoff": "handoff.md",
}

VALID_TASK_STATUSES = {"TODO", "DOING", "DONE", "BLOCKED"}
PLACEHOLDER_TOKENS = {"UNSET", "<...>", "当前无真实任务。"}
HEADER_CELLS = {
    "id",
    "ac id",
    "问题",
    "阻塞级别",
    "已查证据",
    "需要用户确认",
    "验收标准",
    "验证方式",
    "状态",
    "路径",
    "关键位置",
    "结论",
    "位置",
    "可复用点",
    "限制",
    "类型",
    "内容",
    "证据",
    "处理方式",
    "模块 / 文件",
    "模块/文件",
    "影响说明",
    "风险",
    "影响",
    "缓解方案",
    "回滚方式",
    "任务",
    "完成判定",
    "交付记录",
    "验证证据",
    "结果",
    "备注",
    "命令",
    "目的",
    "输出摘要",
    "步骤",
    "预期",
    "实际",
    "文件 / 模块",
    "变更说明",
}


def parse_frontmatter(path: Path) -> tuple[dict[str, str], str]:
    text = path.read_text()
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---", 4)
    if end == -1:
        return {}, text
    metadata: dict[str, str] = {}
    for line in text[4:end].splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"').strip("'")
    return metadata, text[end + 4 :]


def stage_status(metadata: dict[str, str]) -> str:
    return metadata.get("stage_status", "").strip().lower()


def evidence(path: Path, finding: str) -> dict[str, str]:
    return {"path": path.as_posix(), "finding": finding}


def make_result(
    *,
    feature_dir: Path,
    state: str,
    reason: str,
    next_skill: str | None = None,
    blocking: bool = False,
    complete: bool = False,
    evidence_items: list[dict[str, str]] | None = None,
    diagnostics: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "feature_dir": feature_dir.as_posix(),
        "state": state,
        "next_skill": next_skill,
        "blocking": blocking,
        "complete": complete,
        "reason": reason,
        "evidence": evidence_items or [],
        "diagnostics": diagnostics or [],
    }


def is_placeholder_text(value: str) -> bool:
    stripped = value.strip()
    if not stripped:
        return True
    if stripped in {"-", "—", "N/A", "n/a"}:
        return True
    if stripped in PLACEHOLDER_TOKENS:
        return True
    if "UNSET" in stripped:
        return True
    if re.fullmatch(r"<[^>]+>", stripped):
        return True
    return False


def is_table_separator(line: str) -> bool:
    return bool(re.fullmatch(r"\|\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)+\|?", line.strip()))


def table_cells(line: str) -> list[str]:
    if "|" not in line:
        return []
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def is_header_row(line: str) -> bool:
    cells = table_cells(line)
    if not cells:
        return False
    normalized = {cell.lower() for cell in cells if cell.strip()}
    return bool(normalized) and normalized.issubset(HEADER_CELLS)


def is_real_line(line: str) -> bool:
    stripped = line.strip()
    if is_placeholder_text(stripped):
        return False
    if stripped.startswith("#"):
        return False
    if stripped.startswith("```"):
        return False
    if is_table_separator(stripped) or is_header_row(stripped):
        return False
    if stripped.startswith("|"):
        cells = table_cells(stripped)
        return any(not is_placeholder_text(cell) and cell.lower() not in HEADER_CELLS for cell in cells)
    return True


def section_text(body: str, heading: str) -> str:
    pattern = re.compile(rf"^###?\s+(?:\d+\.\s+)?{re.escape(heading)}\s*$", re.MULTILINE)
    match = pattern.search(body)
    if not match:
        return ""
    tail = body[match.end() :]
    next_heading = re.search(r"^###?\s+", tail, re.MULTILINE)
    if not next_heading:
        return tail
    return tail[: next_heading.start()]


def section_has_real_content(body: str, heading: str) -> bool:
    return any(is_real_line(line) for line in section_text(body, heading).splitlines())


def has_real_table_row(body: str, *, id_prefix: str | None = None) -> bool:
    for line in body.splitlines():
        cells = table_cells(line)
        if not cells or is_table_separator(line) or is_header_row(line):
            continue
        if any(is_placeholder_text(cell) for cell in cells):
            continue
        if id_prefix and not cells[0].upper().startswith(id_prefix.upper()):
            continue
        if any(cell.lower() not in HEADER_CELLS for cell in cells):
            return True
    return False


def has_blocking_requirement(body: str) -> bool:
    questions = section_text(body, "待确认问题")
    for line in questions.splitlines():
        cells = table_cells(line)
        if cells and not is_table_separator(line) and not is_header_row(line):
            if any(cell.upper() == "BLOCKING" for cell in cells):
                return True
        if "BLOCKING" in line.upper():
            return True
    return False


def requirements_complete(body: str) -> bool:
    return (
        section_has_real_content(body, "In Scope")
        and section_has_real_content(body, "Out of Scope")
        and has_real_table_row(section_text(body, "Acceptance Criteria"), id_prefix="AC")
    )


def investigation_complete(body: str) -> bool:
    return (
        has_real_table_row(section_text(body, "已查文件"))
        and section_has_real_content(body, "真实调用链 / 数据流")
        and section_has_real_content(body, "数据来源")
    )


def design_complete(body: str) -> bool:
    return (
        has_real_table_row(section_text(body, "影响范围"))
        and section_has_real_content(body, "目标链路")
        and section_has_real_content(body, "风险与回滚")
        and section_has_real_content(body, "验证策略")
    )


def metadata_true(metadata: dict[str, str], field: str) -> bool:
    return metadata.get(field, "").strip().lower() == "true"


def parse_task_count(metadata: dict[str, str]) -> int | None:
    raw = metadata.get("task_count", "").strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def parse_tasks(body: str) -> list[dict[str, Any]]:
    matches = list(re.finditer(r"^###\s+(T\d+)\s+-\s+(.+?)\s*$", body, re.MULTILINE))
    tasks: list[dict[str, Any]] = []
    required_fields = ["输入", "输出", "完成判定", "关联模块/文件"]

    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        block = body[start:end]
        status_match = re.search(r"^-\s*status\s*[:：]\s*(\w+)\s*$", block, re.MULTILINE | re.IGNORECASE)
        status = status_match.group(1).upper() if status_match else ""
        fields: dict[str, str] = {}
        missing_fields: list[str] = []

        for field in required_fields:
            field_match = re.search(rf"^-\s*{re.escape(field)}\s*[:：]\s*(.+?)\s*$", block, re.MULTILINE)
            value = field_match.group(1).strip() if field_match else ""
            fields[field] = value
            if is_placeholder_text(value):
                missing_fields.append(field)

        is_real = status in VALID_TASK_STATUSES and not missing_fields
        tasks.append(
            {
                "id": match.group(1),
                "title": match.group(2).strip(),
                "status": status,
                "is_real": is_real,
                "missing_fields": missing_fields,
                "fields": fields,
            }
        )

    return tasks


def verification_complete(metadata: dict[str, str], body: str) -> tuple[bool, list[str]]:
    diagnostics: list[str] = []
    if stage_status(metadata) != "complete" or not metadata_true(metadata, "evidence_complete"):
        return False, diagnostics
    if "FAIL" in body.upper() or "BLOCKED" in body.upper():
        diagnostics.append("verification.md contains FAIL or BLOCKED while metadata says complete")
        return False, diagnostics
    return True, diagnostics


def handoff_complete(metadata: dict[str, str], body: str) -> bool:
    return (
        stage_status(metadata) == "complete"
        and metadata_true(metadata, "evidence_complete")
        and "UNSET" not in body
    )


def load_stage(feature_dir: Path, stage: str) -> tuple[Path, dict[str, str], str] | None:
    path = feature_dir / STAGE_DOCS[stage]
    if not path.is_file():
        return None
    metadata, body = parse_frontmatter(path)
    return path, metadata, body


def inspect_feature_state(feature_dir: Path) -> dict[str, Any]:
    feature_dir = feature_dir.resolve()
    if not feature_dir.is_dir():
        return make_result(
            feature_dir=feature_dir,
            state="missing_feature_dir",
            reason="feature_dir does not exist",
            blocking=True,
            evidence_items=[evidence(feature_dir, "directory not found")],
        )

    req = load_stage(feature_dir, "requirements")
    if req is None:
        req_path = feature_dir / STAGE_DOCS["requirements"]
        return make_result(
            feature_dir=feature_dir,
            state="requirements_missing",
            next_skill="ai-requirement-intake",
            reason="requirements.md missing",
            evidence_items=[evidence(req_path, "missing")],
        )
    req_path, req_meta, req_body = req
    req_status = stage_status(req_meta)
    if req_status == "draft":
        return make_result(
            feature_dir=feature_dir,
            state="requirements_draft",
            next_skill="ai-requirement-intake",
            reason="requirements.md stage_status is draft",
            evidence_items=[evidence(req_path, "stage_status: draft")],
        )
    if req_status == "blocked" or has_blocking_requirement(req_body):
        return make_result(
            feature_dir=feature_dir,
            state="requirements_blocked",
            next_skill="ai-requirement-intake",
            blocking=True,
            reason="requirements.md has blocking requirement questions",
            evidence_items=[evidence(req_path, f"stage_status: {req_status or 'unset'}; blocking question detected")],
        )
    if not requirements_complete(req_body):
        return make_result(
            feature_dir=feature_dir,
            state="requirements_incomplete",
            next_skill="ai-requirement-intake",
            reason="requirements.md lacks real in-scope, out-of-scope, or acceptance criteria content",
            evidence_items=[evidence(req_path, "missing real scope or acceptance criteria")],
        )

    inv = load_stage(feature_dir, "investigation")
    if inv is None:
        inv_path = feature_dir / STAGE_DOCS["investigation"]
        return make_result(
            feature_dir=feature_dir,
            state="investigation_missing",
            next_skill="ai-repo-investigation",
            reason="investigation.md missing",
            evidence_items=[evidence(inv_path, "missing")],
        )
    inv_path, inv_meta, inv_body = inv
    inv_status = stage_status(inv_meta)
    if inv_status == "blocked":
        return make_result(
            feature_dir=feature_dir,
            state="investigation_blocked",
            blocking=True,
            reason="investigation.md stage_status is blocked",
            evidence_items=[evidence(inv_path, "stage_status: blocked")],
        )
    if inv_status == "draft" or not investigation_complete(inv_body):
        return make_result(
            feature_dir=feature_dir,
            state="investigation_draft_or_incomplete",
            next_skill="ai-repo-investigation",
            reason="investigation.md is draft or lacks real call chain/data-source evidence",
            evidence_items=[evidence(inv_path, f"stage_status: {inv_status or 'unset'}; evidence incomplete")],
        )

    design = load_stage(feature_dir, "design")
    if design is None:
        design_path = feature_dir / STAGE_DOCS["design"]
        return make_result(
            feature_dir=feature_dir,
            state="design_missing",
            next_skill="ai-technical-design",
            reason="design.md missing",
            evidence_items=[evidence(design_path, "missing")],
        )
    design_path, design_meta, design_body = design
    design_status = stage_status(design_meta)
    if design_status == "blocked" or "DESIGN_BLOCKED" in design_body:
        return make_result(
            feature_dir=feature_dir,
            state="design_blocked",
            blocking=True,
            reason="design.md is blocked",
            evidence_items=[evidence(design_path, f"stage_status: {design_status or 'unset'}; DESIGN_BLOCKED marker checked")],
        )
    if design_status == "draft" or not design_complete(design_body):
        return make_result(
            feature_dir=feature_dir,
            state="design_draft_or_incomplete",
            next_skill="ai-technical-design",
            reason="design.md is draft or lacks impact scope, target chain, rollback risk, or verification strategy",
            evidence_items=[evidence(design_path, f"stage_status: {design_status or 'unset'}; design content incomplete")],
        )
    if design_meta.get("approval_status", "").strip().lower() != "approved":
        return make_result(
            feature_dir=feature_dir,
            state="waiting_design_approval",
            next_skill="ai-task-planning",
            blocking=True,
            reason="design.md is ready but approval_status is not approved",
            evidence_items=[evidence(design_path, f"approval_status: {design_meta.get('approval_status', 'unset')}")],
        )

    tasks_stage = load_stage(feature_dir, "tasks")
    if tasks_stage is None:
        tasks_path = feature_dir / STAGE_DOCS["tasks"]
        return make_result(
            feature_dir=feature_dir,
            state="tasks_missing",
            next_skill="ai-task-planning",
            reason="tasks.md missing",
            evidence_items=[evidence(tasks_path, "missing")],
        )
    tasks_path, tasks_meta, tasks_body = tasks_stage
    tasks_status = stage_status(tasks_meta)
    real_tasks = [task for task in parse_tasks(tasks_body) if task["is_real"]]
    expected_task_count = parse_task_count(tasks_meta)
    if tasks_status == "blocked":
        return make_result(
            feature_dir=feature_dir,
            state="tasks_blocked",
            blocking=True,
            reason="tasks.md stage_status is blocked",
            evidence_items=[evidence(tasks_path, "stage_status: blocked")],
        )
    if expected_task_count is not None and expected_task_count != len(real_tasks):
        return make_result(
            feature_dir=feature_dir,
            state="task_count_mismatch",
            next_skill="ai-task-planning",
            blocking=True,
            reason="tasks.md task_count does not match real task count",
            evidence_items=[evidence(tasks_path, f"task_count: {expected_task_count}; real_tasks: {len(real_tasks)}")],
        )
    if tasks_status == "draft" or not real_tasks:
        return make_result(
            feature_dir=feature_dir,
            state="tasks_draft_or_empty",
            next_skill="ai-task-planning",
            reason="tasks.md is draft or has no real tasks",
            evidence_items=[evidence(tasks_path, f"stage_status: {tasks_status or 'unset'}; real_tasks: {len(real_tasks)}")],
        )
    blocked_tasks = [task for task in real_tasks if task["status"] == "BLOCKED"]
    if blocked_tasks:
        return make_result(
            feature_dir=feature_dir,
            state="task_blocked",
            blocking=True,
            reason="tasks.md has BLOCKED task(s)",
            evidence_items=[evidence(tasks_path, "blocked_tasks: " + ", ".join(task["id"] for task in blocked_tasks))],
        )
    doing_tasks = [task for task in real_tasks if task["status"] == "DOING"]
    if doing_tasks:
        return make_result(
            feature_dir=feature_dir,
            state="task_doing",
            next_skill="ai-implementation-execution",
            reason="tasks.md has DOING task(s); resume first DOING task",
            evidence_items=[evidence(tasks_path, "doing_tasks: " + ", ".join(task["id"] for task in doing_tasks))],
        )
    todo_tasks = [task for task in real_tasks if task["status"] == "TODO"]
    if todo_tasks:
        return make_result(
            feature_dir=feature_dir,
            state="task_todo",
            next_skill="ai-implementation-execution",
            reason="tasks.md has TODO task(s)",
            evidence_items=[evidence(tasks_path, "todo_tasks: " + ", ".join(task["id"] for task in todo_tasks))],
        )

    verification = load_stage(feature_dir, "verification")
    if verification is None:
        verification_path = feature_dir / STAGE_DOCS["verification"]
        return make_result(
            feature_dir=feature_dir,
            state="verification_missing",
            next_skill="ai-verification-closeout",
            reason="verification.md missing",
            evidence_items=[evidence(verification_path, "missing")],
        )
    verification_path, verification_meta, verification_body = verification
    verification_is_complete, verification_diagnostics = verification_complete(verification_meta, verification_body)
    if not verification_is_complete:
        return make_result(
            feature_dir=feature_dir,
            state="verification_incomplete",
            next_skill="ai-verification-closeout",
            reason="all real tasks are DONE but verification.md is incomplete or has failed evidence",
            evidence_items=[
                evidence(
                    verification_path,
                    f"stage_status: {stage_status(verification_meta) or 'unset'}; evidence_complete: {verification_meta.get('evidence_complete', 'unset')}",
                )
            ],
            diagnostics=verification_diagnostics,
        )

    handoff = load_stage(feature_dir, "handoff")
    if handoff is None:
        handoff_path = feature_dir / STAGE_DOCS["handoff"]
        return make_result(
            feature_dir=feature_dir,
            state="handoff_missing",
            next_skill="ai-verification-closeout",
            reason="handoff.md missing",
            evidence_items=[evidence(handoff_path, "missing")],
        )
    handoff_path, handoff_meta, handoff_body = handoff
    if not handoff_complete(handoff_meta, handoff_body):
        return make_result(
            feature_dir=feature_dir,
            state="handoff_incomplete",
            next_skill="ai-verification-closeout",
            reason="verification.md is complete but handoff.md lacks complete closeout metadata/content",
            evidence_items=[
                evidence(
                    handoff_path,
                    f"stage_status: {stage_status(handoff_meta) or 'unset'}; evidence_complete: {handoff_meta.get('evidence_complete', 'unset')}",
                )
            ],
        )

    return make_result(
        feature_dir=feature_dir,
        state="complete",
        complete=True,
        reason="all AI Feature Workflow stage documents are complete",
        evidence_items=[
            evidence(verification_path, "stage_status: complete"),
            evidence(handoff_path, "stage_status: complete"),
        ],
    )


def print_yamlish(result: dict[str, Any]) -> None:
    print(f"feature_dir: {result['feature_dir']}")
    print(f"state: {result['state']}")
    print(f"next_skill: {result['next_skill'] or ''}")
    print(f"blocking: {str(result['blocking']).lower()}")
    print(f"complete: {str(result['complete']).lower()}")
    print(f"reason: {result['reason']}")
    print("evidence:")
    for item in result["evidence"]:
        print(f"  - path: {item['path']}")
        print(f"    finding: {item['finding']}")
    if result["diagnostics"]:
        print("diagnostics:")
        for diagnostic in result["diagnostics"]:
            print(f"  - {diagnostic}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect AI Feature Workflow state")
    parser.add_argument("feature_dir", help="Path to .docs/feature-YYYYMMDD-short-name")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of yaml-like text")
    args = parser.parse_args(argv)

    result = inspect_feature_state(Path(args.feature_dir))
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_yamlish(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
