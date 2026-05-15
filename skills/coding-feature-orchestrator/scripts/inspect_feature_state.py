#!/usr/bin/env python3
"""Inspect a Coding Feature Workflow directory and infer the next stage.

The script is intentionally stdlib-only so it can run in any AI agent
environment without extra dependencies. It implements the same ordered stage rules described in
coding-feature-orchestrator/SKILL.md and WORKFLOW_CONTRACT.md.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any

ORCHESTRATOR_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_DIR = ORCHESTRATOR_ROOT / "assets" / "feature-template"

STAGE_DOCS = {
    "discovery": "discovery.md",
    "requirements": "requirements.md",
    "design": "design.md",
    "tasks": "tasks.md",
    "verification": "verification.md",
    "handoff": "handoff.md",
}

STAGE_SKILLS = {
    "discovery": "coding-feature-discovery",
    "requirements": "coding-requirement-intake",
    "design": "coding-technical-design",
    "tasks": "coding-task-planning",
    "verification": "coding-verification-closeout",
    "handoff": "coding-verification-closeout",
}

VALID_TASK_STATUSES = {"TODO", "DOING", "DONE", "BLOCKED"}
VALID_STAGE_STATUSES = {"draft", "ready", "blocked", "complete"}
VALID_PROJECT_CONTEXTS = {"unknown", "existing_project", "empty_project"}
STAGE_ALLOWED_STATUSES = {
    "discovery": {"draft", "ready", "blocked"},
    "requirements": {"draft", "ready", "blocked"},
    "design": {"draft", "ready", "blocked"},
    "tasks": {"draft", "ready", "blocked"},
    "verification": {"draft", "blocked", "complete"},
    "handoff": {"draft", "blocked", "complete"},
}
ISO_WITH_TZ = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|[+-]\d{2}:\d{2})$")
PLACEHOLDER_TOKENS = {"UNSET", "<...>", "当前无真实任务。"}
TASK_FIELD_RE = re.compile(r"^-\s*([^:：]+?)\s*[:：]\s*(.*)$")
DELIVERY_RECORD_REQUIREMENTS = {
    "改动文件": ("改动文件", "变更文件", "修改文件", "文件：", "文件:"),
    "验证命令或证据": ("验证命令", "验证证据", "验证：", "验证:", "命令：", "命令:"),
    "结果": ("结果", "PASS", "FAIL", "BLOCKED"),
    "残余风险": ("残余风险", "剩余风险", "风险：", "风险:"),
}
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
    "发现",
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
    "domain id",
    "业务域",
    "业务能力",
    "actor / role",
    "核心 entity",
    "业务规则 / 边界",
    "关联 ac",
    "任务边界",
    "cross-domain 依赖",
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
    "来源",
    "适用范围",
    "方向",
    "适用条件",
    "具体实现差异",
    "风险 / 取舍",
    "影响范围",
    "当前状态",
    "问题 id",
    "用户回答",
    "更新位置",
    "版本",
    "来源 / 路径",
    "关键位置 / 版本",
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


def has_placeholder_marker(value: str) -> bool:
    if "UNSET" in value:
        return True
    return bool(re.search(r"<[^>\n]+>", value))


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


def section_text_any(body: str, headings: list[str]) -> str:
    for heading in headings:
        section = section_text(body, heading)
        if section.strip():
            return section
    return ""


def section_has_real_content_any(body: str, headings: list[str]) -> bool:
    section = section_text_any(body, headings)
    return any(is_real_line(line) for line in section.splitlines())


def section_has_no_placeholder_markers_any(body: str, headings: list[str]) -> bool:
    return not has_placeholder_marker(section_text_any(body, headings))


def section_has_real_content(body: str, heading: str) -> bool:
    return any(is_real_line(line) for line in section_text(body, heading).splitlines())


def section_has_no_placeholder_markers(body: str, heading: str) -> bool:
    return not has_placeholder_marker(section_text(body, heading))


def section_complete(body: str, heading: str) -> bool:
    section = section_text(body, heading)
    return bool(section.strip()) and section_has_real_content(body, heading) and not has_placeholder_marker(section)


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


def is_blocking_marker(value: str) -> bool:
    return value.strip().upper() == "BLOCKING"


def contains_standalone_blocking(value: str) -> bool:
    normalized = value.upper().replace("NON-BLOCKING", "NON_BLOCKING")
    return "NON_BLOCKING" not in normalized and bool(re.search(r"\bBLOCKING\b", normalized))


def has_blocking_questions(body: str, heading: str) -> bool:
    questions = section_text(body, heading)
    blocking_index: int | None = None
    for line in questions.splitlines():
        cells = table_cells(line)
        if cells:
            if is_table_separator(line):
                continue
            if "阻塞级别" in cells:
                blocking_index = cells.index("阻塞级别")
                continue
            if blocking_index is not None and len(cells) > blocking_index:
                if is_blocking_marker(cells[blocking_index]):
                    return True
                continue
            if any(is_blocking_marker(cell) for cell in cells):
                return True
            continue
        if contains_standalone_blocking(line):
            return True
    return False


def has_blocking_requirement(body: str) -> bool:
    return has_blocking_questions(body, "待确认问题")


def has_blocking_discovery_question(body: str) -> bool:
    return has_blocking_questions(body, "模糊点清单")


def project_context(metadata: dict[str, str]) -> str:
    return metadata.get("project_context", "unknown").strip().lower() or "unknown"


def project_context_issue(metadata: dict[str, str], status: str) -> str | None:
    context = project_context(metadata)
    if context not in VALID_PROJECT_CONTEXTS:
        return f"project_context is invalid: {context}; allowed: empty_project, existing_project, unknown"
    if status in {"ready", "complete"}:
        if context == "unknown":
            return "project_context must be existing_project or empty_project before ready/complete"
        if is_placeholder_text(metadata.get("project_context_evidence", "")):
            return "project_context_evidence must explain how project_context was determined"
    return None


def context_label(metadata: dict[str, str]) -> str:
    context = project_context(metadata)
    if context == "empty_project":
        return "empty project"
    if context == "existing_project":
        return "existing project"
    return "unknown project context"


def discovery_complete(metadata: dict[str, str], body: str) -> bool:
    context_section = section_text_any(body, ["项目上下文调研", "仓库广扫"])
    context_ok = (
        has_real_table_row(context_section)
        and not has_placeholder_marker(context_section)
    )
    return (
        section_complete(body, "原始需求摘要")
        and project_context(metadata) in {"existing_project", "empty_project"}
        and context_ok
        and section_complete(body, "外部调研")
        and has_real_table_row(section_text(body, "方案方向"))
        and section_has_no_placeholder_markers(body, "方案方向")
        and has_real_table_row(section_text(body, "模糊点清单"))
        and not has_blocking_discovery_question(body)
        and has_real_table_row(section_text(body, "逐问逐答记录"))
        and section_complete(body, "进入 Requirements 的完成判定")
    )


def requirements_complete(body: str) -> bool:
    return (
        section_complete(body, "背景")
        and section_complete(body, "目标")
        and section_complete(body, "In Scope")
        and section_complete(body, "Out of Scope")
        and section_complete(body, "用户路径 / 业务流程")
        and has_real_table_row(section_text(body, "Acceptance Criteria"), id_prefix="AC")
        and section_has_no_placeholder_markers(body, "Acceptance Criteria")
        and section_complete(body, "非功能要求")
        and section_complete(body, "约束与假设")
    )


def requirement_ac_ids(body: str) -> list[str]:
    section = section_text(body, "Acceptance Criteria")
    ids: list[str] = []
    seen: set[str] = set()
    for line in section.splitlines():
        cells = table_cells(line)
        if not cells or is_table_separator(line) or is_header_row(line):
            continue
        ac_id = cells[0].strip()
        if is_placeholder_text(ac_id) or not ac_id.upper().startswith("AC"):
            continue
        normalized = ac_id.upper()
        if normalized in seen:
            continue
        seen.add(normalized)
        ids.append(normalized)
    return ids


def duplicate_requirement_ac_ids(body: str) -> list[str]:
    section = section_text(body, "Acceptance Criteria")
    seen: set[str] = set()
    duplicates: set[str] = set()
    for line in section.splitlines():
        cells = table_cells(line)
        if not cells or is_table_separator(line) or is_header_row(line):
            continue
        ac_id = cells[0].strip()
        if is_placeholder_text(ac_id) or not ac_id.upper().startswith("AC"):
            continue
        normalized = ac_id.upper()
        if normalized in seen:
            duplicates.add(normalized)
        seen.add(normalized)
    return sorted(duplicates)


def requirement_domain_ids(body: str) -> list[str]:
    section = section_text(body, "业务域建模")
    ids: list[str] = []
    seen: set[str] = set()
    domain_id_index: int | None = None

    for line in section.splitlines():
        cells = table_cells(line)
        if not cells or is_table_separator(line):
            continue
        normalized_cells = [cell.strip().lower() for cell in cells]
        if "domain id" in normalized_cells:
            domain_id_index = normalized_cells.index("domain id")
            continue
        if is_header_row(line):
            continue
        if domain_id_index is None or len(cells) <= domain_id_index:
            continue
        domain_id = cells[domain_id_index].strip()
        if is_placeholder_text(domain_id):
            continue
        normalized = domain_id.upper()
        if normalized in seen:
            continue
        seen.add(normalized)
        ids.append(normalized)

    return ids


def requirements_domain_complete(body: str) -> bool:
    section = section_text(body, "业务域建模")
    return (
        bool(requirement_domain_ids(body))
        and has_real_table_row(section)
        and not has_placeholder_marker(section)
    )


def acceptance_criteria_domain_issue(body: str, domain_ids: list[str]) -> str | None:
    section = section_text(body, "Acceptance Criteria")
    domain_set = set(domain_ids)
    ac_id_index: int | None = None
    domain_index: int | None = None
    real_ac_count = 0
    saw_ac_row = False

    for line in section.splitlines():
        cells = table_cells(line)
        if not cells or is_table_separator(line):
            continue
        normalized_cells = [cell.strip().lower() for cell in cells]
        if "id" in normalized_cells and "业务域" in normalized_cells:
            ac_id_index = normalized_cells.index("id")
            domain_index = normalized_cells.index("业务域")
            continue
        if is_header_row(line):
            continue
        if cells and cells[0].strip().upper().startswith("AC"):
            saw_ac_row = True
        if ac_id_index is None or domain_index is None:
            continue
        if len(cells) <= max(ac_id_index, domain_index):
            continue

        ac_id = cells[ac_id_index].strip().upper()
        if is_placeholder_text(ac_id) or not ac_id.startswith("AC"):
            continue
        real_ac_count += 1
        domain_id = cells[domain_index].strip().upper()
        if is_placeholder_text(domain_id):
            return f"{ac_id} is missing business domain"
        if domain_id not in domain_set:
            return f"{ac_id} references unknown business domain {domain_id}"

    if (real_ac_count or saw_ac_row) and domain_index is None:
        return "Acceptance Criteria table is missing 业务域 column"
    return None


def design_complete(metadata: dict[str, str], body: str) -> bool:
    context_section = section_text_any(body, ["技术上下文与架构依据", "仓库勘探"])
    target_chain_complete = (
        section_complete(body, "目标链路与数据来源")
        or section_complete(body, "真实链路与数据来源")
    )
    return (
        section_complete(body, "方案摘要")
        and project_context(metadata) in {"existing_project", "empty_project"}
        and has_real_table_row(context_section)
        and not has_placeholder_marker(context_section)
        and target_chain_complete
        and section_complete(body, "澄清问题")
        and has_real_table_row(section_text(body, "方案比较"))
        and section_has_no_placeholder_markers(body, "方案比较")
        and has_real_table_row(section_text(body, "影响范围"))
        and section_has_no_placeholder_markers(body, "影响范围")
        and section_complete(body, "目标链路")
        and section_complete(body, "API 变更")
        and section_complete(body, "数据变更")
        and section_complete(body, "状态、事务与并发")
        and section_complete(body, "错误处理与日志")
        and section_has_real_content(body, "风险与回滚")
        and section_has_no_placeholder_markers(body, "风险与回滚")
        and section_complete(body, "验证策略")
    )


def metadata_true(metadata: dict[str, str], field: str) -> bool:
    return metadata.get(field, "").strip().lower() == "true"


def has_iso_timestamp(metadata: dict[str, str], field: str = "updated_at") -> bool:
    return bool(ISO_WITH_TZ.match(metadata.get(field, "").strip()))


def stage_metadata_issue(stage: str, metadata: dict[str, str]) -> str | None:
    declared_stage = metadata.get("feature_stage", "").strip()
    if declared_stage != stage:
        if not declared_stage:
            return f"{stage} document is missing feature_stage"
        return f"{stage} document feature_stage is {declared_stage}, expected {stage}"

    status = stage_status(metadata)
    if status not in VALID_STAGE_STATUSES:
        if not status:
            return f"{stage} document is missing stage_status"
        return f"{stage} document has invalid stage_status: {status}"
    allowed_statuses = STAGE_ALLOWED_STATUSES.get(stage, VALID_STAGE_STATUSES)
    if status not in allowed_statuses:
        return (
            f"{stage} document has invalid stage_status for this stage: "
            f"{status}; allowed: {', '.join(sorted(allowed_statuses))}"
        )

    evidence_value = metadata.get("evidence_complete", "").strip().lower()
    if evidence_value not in {"true", "false"}:
        if not evidence_value:
            return f"{stage} document is missing evidence_complete"
        return f"{stage} evidence_complete must be true or false"

    if status in {"ready", "complete"}:
        if evidence_value != "true":
            return f"{stage} stage_status is {status} but evidence_complete is not true"
        if not has_iso_timestamp(metadata):
            return f"{stage} stage_status is {status} but updated_at is missing or not ISO 8601 with timezone"
    elif status == "blocked":
        if evidence_value != "false":
            return f"{stage} stage_status is blocked but evidence_complete is not false"
        if not has_iso_timestamp(metadata):
            return f"{stage} stage_status is blocked but updated_at is missing or not ISO 8601 with timezone"
    elif status == "draft":
        if evidence_value == "true":
            return f"{stage} stage_status is draft but evidence_complete is true"

    context_issue = project_context_issue(metadata, status)
    if context_issue:
        return f"{stage} {context_issue}"

    return None


def design_approval_issue(metadata: dict[str, str]) -> str | None:
    if metadata.get("approval_status", "").strip().lower() != "approved":
        return None

    if is_placeholder_text(metadata.get("approved_by", "")):
        return "approval_status is approved but approved_by is empty"
    if not has_iso_timestamp(metadata, "approved_at"):
        return "approval_status is approved but approved_at is missing or not ISO 8601 with timezone"
    if is_placeholder_text(metadata.get("approval_evidence", "")):
        return "approval_status is approved but approval_evidence is empty"
    return None


def parse_task_count(metadata: dict[str, str]) -> int | None:
    raw = metadata.get("task_count", "").strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def delivery_record_issue(status: str, delivery_record: str) -> str | None:
    if status != "DONE":
        return None

    if (
        is_placeholder_text(delivery_record)
        or delivery_record.strip() in {"待执行", "待补充", "暂无", "无"}
    ):
        return "交付记录为空或仍是占位内容"

    missing = [
        label
        for label, keywords in DELIVERY_RECORD_REQUIREMENTS.items()
        if not any(keyword in delivery_record for keyword in keywords)
    ]
    if missing:
        return "交付记录缺少：" + "、".join(missing)
    return None


def extract_task_field(block: str, field: str) -> str:
    lines = block.splitlines()
    for index, line in enumerate(lines):
        match = TASK_FIELD_RE.match(line)
        if not match or match.group(1).strip() != field:
            continue

        value_parts: list[str] = []
        first_value = match.group(2).strip()
        if first_value:
            value_parts.append(first_value)

        for continuation in lines[index + 1 :]:
            if TASK_FIELD_RE.match(continuation):
                break
            stripped = continuation.strip()
            if stripped:
                value_parts.append(stripped)
        return "\n".join(value_parts).strip()
    return ""


def parse_tasks(body: str) -> list[dict[str, Any]]:
    matches = list(re.finditer(r"^###\s+(T\d+)\s+-\s+(.+?)\s*$", body, re.MULTILINE))
    tasks: list[dict[str, Any]] = []
    required_fields = ["业务域", "输入", "输出", "完成判定", "关联模块/文件", "执行要点", "风险"]

    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        block = body[start:end]
        status_match = re.search(r"^-\s*status\s*[:：]\s*(\w+)\s*$", block, re.MULTILINE | re.IGNORECASE)
        status = status_match.group(1).upper() if status_match else ""
        fields: dict[str, str] = {}
        missing_fields: list[str] = []

        for field in required_fields:
            value = extract_task_field(block, field)
            fields[field] = value
            if is_placeholder_text(value):
                missing_fields.append(field)

        delivery_record = extract_task_field(block, "交付记录")
        delivery_issue = delivery_record_issue(status, delivery_record)
        is_real = status in VALID_TASK_STATUSES and not missing_fields
        tasks.append(
            {
                "id": match.group(1),
                "title": match.group(2).strip(),
                "status": status,
                "is_real": is_real,
                "missing_fields": missing_fields,
                "fields": fields,
                "delivery_record": delivery_record,
                "delivery_record_issue": delivery_issue,
                "delivery_record_incomplete": delivery_issue is not None,
            }
        )

    return tasks


def task_domain_issue(tasks: list[dict[str, Any]], domain_ids: list[str], expected_ac_ids: list[str]) -> str | None:
    domain_set = set(domain_ids)
    ac_set = set(expected_ac_ids)
    for task in tasks:
        domain_value = task["fields"].get("业务域", "")
        task_domains = {
            item.upper()
            for item in re.findall(r"\bD[A-Z0-9_-]*\b", domain_value, flags=re.IGNORECASE)
        }
        if not task_domains:
            return f"{task['id']} is missing business domain"
        unknown_domains = sorted(task_domains - domain_set)
        if unknown_domains:
            return f"{task['id']} references unknown business domain(s): {', '.join(unknown_domains)}"

        input_value = task["fields"].get("输入", "")
        task_ac_ids = {
            item.upper()
            for item in re.findall(r"\bAC[-_]?\d+\b", input_value, flags=re.IGNORECASE)
        }
        if not task_ac_ids:
            return f"{task['id']} is missing acceptance-criteria reference"
        unknown_ac_ids = sorted(task_ac_ids - ac_set)
        if unknown_ac_ids:
            return f"{task['id']} references unknown acceptance criteria: {', '.join(unknown_ac_ids)}"
    return None


def verification_rows(body: str) -> list[dict[str, str]]:
    section = section_text(body, "验收标准映射")
    result_index: int | None = None
    evidence_index: int | None = None
    rows: list[dict[str, str]] = []

    for line in section.splitlines():
        cells = table_cells(line)
        if not cells or is_table_separator(line):
            continue
        if "结果" in cells:
            result_index = cells.index("结果")
            evidence_index = cells.index("验证证据") if "验证证据" in cells else None
            continue
        if is_header_row(line):
            continue
        if result_index is None or len(cells) <= result_index:
            continue
        ac_id = cells[0].strip() if cells else ""
        result = cells[result_index].strip()
        if is_placeholder_text(ac_id) or is_placeholder_text(result):
            continue
        evidence_value = cells[evidence_index].strip() if evidence_index is not None and len(cells) > evidence_index else ""
        rows.append(
            {
                "ac_id": ac_id.upper(),
                "result": result.upper(),
                "evidence": evidence_value,
            }
        )

    return rows


def normalize_verification_result(value: str) -> str:
    return value.strip().upper().split()[0].strip("。；;,.，")


def verification_complete(metadata: dict[str, str], body: str, expected_ac_ids: list[str]) -> tuple[bool, list[str]]:
    diagnostics: list[str] = []
    if stage_status(metadata) != "complete" or not metadata_true(metadata, "evidence_complete"):
        return False, diagnostics
    rows = verification_rows(body)
    if not rows:
        diagnostics.append("verification.md has complete metadata but no real acceptance-criteria result rows")
        return False, diagnostics
    rows_by_ac = {row["ac_id"]: row for row in rows}
    missing_ac_ids = [ac_id for ac_id in expected_ac_ids if ac_id not in rows_by_ac]
    if missing_ac_ids:
        diagnostics.append("verification.md complete metadata is missing acceptance criteria: " + ", ".join(missing_ac_ids))
        return False, diagnostics
    missing_evidence = [
        ac_id
        for ac_id in expected_ac_ids
        if is_placeholder_text(rows_by_ac.get(ac_id, {}).get("evidence", ""))
    ]
    if missing_evidence:
        diagnostics.append("verification.md complete metadata has acceptance criteria without real evidence: " + ", ".join(missing_evidence))
        return False, diagnostics
    non_pass_results = [
        row["ac_id"]
        for row in rows
        if normalize_verification_result(row["result"]) != "PASS"
    ]
    if non_pass_results:
        diagnostics.append("verification.md complete metadata requires all acceptance-criteria results to be PASS")
        return False, diagnostics
    return True, diagnostics


def handoff_complete(metadata: dict[str, str], body: str) -> bool:
    ops_section = section_text(body, "配置 / SQL / 部署事项")
    required_ops_labels = ("配置", "SQL", "部署", "数据修复")
    return (
        stage_status(metadata) == "complete"
        and metadata_true(metadata, "evidence_complete")
        and "UNSET" not in body
        and section_has_real_content(body, "交付摘要")
        and has_real_table_row(section_text(body, "变更范围"))
        and section_has_real_content(body, "配置 / SQL / 部署事项")
        and all(label in ops_section for label in required_ops_labels)
        and section_has_real_content(body, "用户复核入口")
        and section_has_real_content(body, "验证结论")
        and section_has_real_content(body, "残余风险与后续建议")
    )


def load_stage(feature_dir: Path, stage: str) -> tuple[Path, dict[str, str], str] | None:
    path = feature_dir / STAGE_DOCS[stage]
    if not path.is_file():
        return None
    metadata, body = parse_frontmatter(path)
    return path, metadata, body


def metadata_inconsistent_result(feature_dir: Path, stage: str, path: Path, issue: str) -> dict[str, Any]:
    return make_result(
        feature_dir=feature_dir,
        state=f"{stage}_metadata_inconsistent",
        next_skill=STAGE_SKILLS.get(stage),
        blocking=True,
        reason=issue,
        evidence_items=[evidence(path, issue)],
    )


def project_context_mismatch_result(
    feature_dir: Path,
    *,
    stage: str,
    path: Path,
    discovery_context: str,
    stage_context: str,
) -> dict[str, Any]:
    issue = (
        f"{stage} project_context is {stage_context}, "
        f"but discovery project_context is {discovery_context}"
    )
    return metadata_inconsistent_result(feature_dir, stage, path, issue)


def inspect_feature_state(feature_dir: Path) -> dict[str, Any]:
    feature_dir = feature_dir.resolve()
    if feature_dir == TEMPLATE_DIR.resolve():
        return make_result(
            feature_dir=feature_dir,
            state="template_dir_rejected",
            reason="feature_dir points to the bundled feature template, not a real feature directory",
            blocking=True,
            evidence_items=[evidence(feature_dir, "bundled template directory is not a feature workspace")],
        )

    if not feature_dir.is_dir():
        return make_result(
            feature_dir=feature_dir,
            state="missing_feature_dir",
            reason="feature_dir does not exist",
            blocking=True,
            evidence_items=[evidence(feature_dir, "directory not found")],
        )

    discovery = load_stage(feature_dir, "discovery")
    if discovery is None:
        discovery_path = feature_dir / STAGE_DOCS["discovery"]
        return make_result(
            feature_dir=feature_dir,
            state="discovery_missing",
            next_skill="coding-feature-discovery",
            reason="discovery.md missing",
            evidence_items=[evidence(discovery_path, "missing")],
        )
    discovery_path, discovery_meta, discovery_body = discovery
    discovery_status = stage_status(discovery_meta)
    discovery_metadata_issue = stage_metadata_issue("discovery", discovery_meta)
    if discovery_metadata_issue:
        return metadata_inconsistent_result(feature_dir, "discovery", discovery_path, discovery_metadata_issue)
    if discovery_status == "draft":
        return make_result(
            feature_dir=feature_dir,
            state="discovery_draft",
            next_skill="coding-feature-discovery",
            reason="discovery.md stage_status is draft",
            evidence_items=[evidence(discovery_path, "stage_status: draft")],
        )
    if discovery_status == "blocked" or has_blocking_discovery_question(discovery_body):
        return make_result(
            feature_dir=feature_dir,
            state="discovery_blocked",
            next_skill="coding-feature-discovery",
            blocking=True,
            reason="discovery.md has blocking ambiguity questions",
            evidence_items=[
                evidence(discovery_path, f"stage_status: {discovery_status or 'unset'}; blocking ambiguity detected")
            ],
        )
    if not discovery_complete(discovery_meta, discovery_body):
        return make_result(
            feature_dir=feature_dir,
            state="discovery_incomplete",
            next_skill="coding-feature-discovery",
            reason=(
                "discovery.md lacks required project-context research, external research, "
                "options, ambiguity, Q&A, or handoff evidence"
            ),
            evidence_items=[evidence(discovery_path, "missing real discovery sections or placeholder markers remain")],
        )

    req = load_stage(feature_dir, "requirements")
    if req is None:
        req_path = feature_dir / STAGE_DOCS["requirements"]
        return make_result(
            feature_dir=feature_dir,
            state="requirements_missing",
            next_skill="coding-requirement-intake",
            reason="requirements.md missing",
            evidence_items=[evidence(req_path, "missing")],
        )
    req_path, req_meta, req_body = req
    req_status = stage_status(req_meta)
    req_metadata_issue = stage_metadata_issue("requirements", req_meta)
    if req_metadata_issue:
        return metadata_inconsistent_result(feature_dir, "requirements", req_path, req_metadata_issue)
    if req_status == "draft":
        return make_result(
            feature_dir=feature_dir,
            state="requirements_draft",
            next_skill="coding-requirement-intake",
            reason="requirements.md stage_status is draft",
            evidence_items=[evidence(req_path, "stage_status: draft")],
        )
    if req_status == "blocked" or has_blocking_requirement(req_body):
        return make_result(
            feature_dir=feature_dir,
            state="requirements_blocked",
            next_skill="coding-requirement-intake",
            blocking=True,
            reason="requirements.md has blocking requirement questions",
            evidence_items=[evidence(req_path, f"stage_status: {req_status or 'unset'}; blocking question detected")],
        )
    if project_context(req_meta) != project_context(discovery_meta):
        return project_context_mismatch_result(
            feature_dir,
            stage="requirements",
            path=req_path,
            discovery_context=project_context(discovery_meta),
            stage_context=project_context(req_meta),
        )
    if not requirements_complete(req_body):
        return make_result(
            feature_dir=feature_dir,
            state="requirements_incomplete",
            next_skill="coding-requirement-intake",
            reason="requirements.md lacks required real content or still contains placeholder markers",
            evidence_items=[evidence(req_path, "missing real requirements sections or placeholder markers remain")],
        )
    domain_ids = requirement_domain_ids(req_body)
    if not requirements_domain_complete(req_body):
        return make_result(
            feature_dir=feature_dir,
            state="requirements_domain_incomplete",
            next_skill="coding-requirement-intake",
            blocking=True,
            reason="requirements.md lacks required business-domain model",
            evidence_items=[evidence(req_path, "missing real 业务域建模 rows or placeholder markers remain")],
        )
    ac_domain_issue = acceptance_criteria_domain_issue(req_body, domain_ids)
    if ac_domain_issue:
        return make_result(
            feature_dir=feature_dir,
            state="requirements_ac_domain_invalid",
            next_skill="coding-requirement-intake",
            blocking=True,
            reason=ac_domain_issue,
            evidence_items=[evidence(req_path, ac_domain_issue)],
        )
    duplicate_ac_ids = duplicate_requirement_ac_ids(req_body)
    if duplicate_ac_ids:
        return make_result(
            feature_dir=feature_dir,
            state="requirement_duplicate_ac_id",
            next_skill="coding-requirement-intake",
            blocking=True,
            reason="requirements.md has duplicate acceptance-criteria IDs",
            evidence_items=[evidence(req_path, "duplicate_ac_ids: " + ", ".join(duplicate_ac_ids))],
        )
    expected_ac_ids = requirement_ac_ids(req_body)

    design = load_stage(feature_dir, "design")
    if design is None:
        design_path = feature_dir / STAGE_DOCS["design"]
        return make_result(
            feature_dir=feature_dir,
            state="design_missing",
            next_skill="coding-technical-design",
            reason="design.md missing",
            evidence_items=[evidence(design_path, "missing")],
        )
    design_path, design_meta, design_body = design
    design_status = stage_status(design_meta)
    design_metadata_issue = stage_metadata_issue("design", design_meta)
    if design_metadata_issue:
        return metadata_inconsistent_result(feature_dir, "design", design_path, design_metadata_issue)
    if design_status == "blocked" or "DESIGN_BLOCKED" in design_body:
        return make_result(
            feature_dir=feature_dir,
            state="design_blocked",
            blocking=True,
            reason="design.md is blocked",
            evidence_items=[evidence(design_path, f"stage_status: {design_status or 'unset'}; DESIGN_BLOCKED marker checked")],
        )
    if design_status == "draft" or not design_complete(design_meta, design_body):
        return make_result(
            feature_dir=feature_dir,
            state="design_draft_or_incomplete",
            next_skill="coding-technical-design",
            reason=(
                "design.md is draft or lacks project-context architecture evidence, "
                "target chain, rollback risk, or verification strategy"
            ),
            evidence_items=[evidence(design_path, f"stage_status: {design_status or 'unset'}; design content incomplete")],
        )
    if project_context(design_meta) != project_context(discovery_meta):
        return project_context_mismatch_result(
            feature_dir,
            stage="design",
            path=design_path,
            discovery_context=project_context(discovery_meta),
            stage_context=project_context(design_meta),
        )
    if design_meta.get("approval_status", "").strip().lower() != "approved":
        return make_result(
            feature_dir=feature_dir,
            state="waiting_design_approval",
            next_skill="coding-task-planning",
            blocking=True,
            reason="design.md is ready but approval_status is not approved",
            evidence_items=[evidence(design_path, f"approval_status: {design_meta.get('approval_status', 'unset')}")],
        )
    approval_issue = design_approval_issue(design_meta)
    if approval_issue:
        return make_result(
            feature_dir=feature_dir,
            state="design_approval_incomplete",
            next_skill="coding-task-planning",
            blocking=True,
            reason=approval_issue,
            evidence_items=[evidence(design_path, approval_issue)],
        )

    tasks_stage = load_stage(feature_dir, "tasks")
    if tasks_stage is None:
        tasks_path = feature_dir / STAGE_DOCS["tasks"]
        return make_result(
            feature_dir=feature_dir,
            state="tasks_missing",
            next_skill="coding-task-planning",
            reason="tasks.md missing",
            evidence_items=[evidence(tasks_path, "missing")],
        )
    tasks_path, tasks_meta, tasks_body = tasks_stage
    tasks_status = stage_status(tasks_meta)
    tasks_metadata_issue = stage_metadata_issue("tasks", tasks_meta)
    if tasks_metadata_issue:
        return metadata_inconsistent_result(feature_dir, "tasks", tasks_path, tasks_metadata_issue)
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
    if "task_count" not in tasks_meta:
        return make_result(
            feature_dir=feature_dir,
            state="task_count_missing",
            next_skill="coding-task-planning",
            blocking=True,
            reason="tasks.md frontmatter is missing task_count",
            evidence_items=[evidence(tasks_path, "task_count missing")],
        )
    if expected_task_count is None:
        return make_result(
            feature_dir=feature_dir,
            state="task_count_invalid",
            next_skill="coding-task-planning",
            blocking=True,
            reason="tasks.md task_count is not an integer",
            evidence_items=[evidence(tasks_path, f"task_count: {tasks_meta.get('task_count', 'unset')}")],
        )
    if expected_task_count is not None and expected_task_count != len(real_tasks):
        return make_result(
            feature_dir=feature_dir,
            state="task_count_mismatch",
            next_skill="coding-task-planning",
            blocking=True,
            reason="tasks.md task_count does not match real task count",
            evidence_items=[evidence(tasks_path, f"task_count: {expected_task_count}; real_tasks: {len(real_tasks)}")],
        )
    task_ids = [task["id"] for task in real_tasks]
    duplicate_task_ids = sorted({task_id for task_id in task_ids if task_ids.count(task_id) > 1})
    if duplicate_task_ids:
        return make_result(
            feature_dir=feature_dir,
            state="task_duplicate_id",
            next_skill="coding-task-planning",
            blocking=True,
            reason="tasks.md has duplicate real task IDs",
            evidence_items=[evidence(tasks_path, "duplicate_task_ids: " + ", ".join(duplicate_task_ids))],
        )
    task_domain_invalid = task_domain_issue(real_tasks, domain_ids, expected_ac_ids)
    if task_domain_invalid:
        return make_result(
            feature_dir=feature_dir,
            state="task_domain_invalid",
            next_skill="coding-task-planning",
            blocking=True,
            reason=task_domain_invalid,
            evidence_items=[evidence(tasks_path, task_domain_invalid)],
        )
    if tasks_status == "draft" or not real_tasks:
        return make_result(
            feature_dir=feature_dir,
            state="tasks_draft_or_empty",
            next_skill="coding-task-planning",
            reason="tasks.md is draft or has no real tasks",
            evidence_items=[evidence(tasks_path, f"stage_status: {tasks_status or 'unset'}; real_tasks: {len(real_tasks)}")],
        )
    if project_context(tasks_meta) != project_context(discovery_meta):
        return project_context_mismatch_result(
            feature_dir,
            stage="tasks",
            path=tasks_path,
            discovery_context=project_context(discovery_meta),
            stage_context=project_context(tasks_meta),
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
    done_delivery_incomplete_tasks = [
        task for task in real_tasks if task["delivery_record_incomplete"]
    ]
    if done_delivery_incomplete_tasks:
        return make_result(
            feature_dir=feature_dir,
            state="task_done_delivery_incomplete",
            next_skill="coding-implementation-execution",
            blocking=True,
            reason="DONE task(s) lack real delivery records",
            evidence_items=[
                evidence(
                    tasks_path,
                    "done_delivery_incomplete_tasks: "
                    + ", ".join(
                        f"{task['id']} ({task['delivery_record_issue']})"
                        for task in done_delivery_incomplete_tasks
                    ),
                )
            ],
        )
    doing_tasks = [task for task in real_tasks if task["status"] == "DOING"]
    if len(doing_tasks) > 1:
        return make_result(
            feature_dir=feature_dir,
            state="task_doing_ambiguous",
            next_skill="coding-implementation-execution",
            blocking=True,
            reason="tasks.md has multiple DOING tasks; resume target is ambiguous",
            evidence_items=[evidence(tasks_path, "doing_tasks: " + ", ".join(task["id"] for task in doing_tasks))],
        )
    if doing_tasks:
        return make_result(
            feature_dir=feature_dir,
            state="task_doing",
            next_skill="coding-implementation-execution",
            reason="tasks.md has DOING task(s); resume first DOING task",
            evidence_items=[evidence(tasks_path, "doing_tasks: " + ", ".join(task["id"] for task in doing_tasks))],
        )
    todo_tasks = [task for task in real_tasks if task["status"] == "TODO"]
    if todo_tasks:
        return make_result(
            feature_dir=feature_dir,
            state="task_todo",
            next_skill="coding-implementation-execution",
            reason="tasks.md has TODO task(s)",
            evidence_items=[evidence(tasks_path, "todo_tasks: " + ", ".join(task["id"] for task in todo_tasks))],
        )

    verification = load_stage(feature_dir, "verification")
    if verification is None:
        verification_path = feature_dir / STAGE_DOCS["verification"]
        return make_result(
            feature_dir=feature_dir,
            state="verification_missing",
            next_skill="coding-verification-closeout",
            reason="verification.md missing",
            evidence_items=[evidence(verification_path, "missing")],
        )
    verification_path, verification_meta, verification_body = verification
    verification_metadata_issue = stage_metadata_issue("verification", verification_meta)
    if verification_metadata_issue:
        return metadata_inconsistent_result(
            feature_dir,
            "verification",
            verification_path,
            verification_metadata_issue,
        )
    verification_is_complete, verification_diagnostics = verification_complete(
        verification_meta,
        verification_body,
        expected_ac_ids,
    )
    if not verification_is_complete:
        return make_result(
            feature_dir=feature_dir,
            state="verification_incomplete",
            next_skill="coding-verification-closeout",
            reason="all real tasks are DONE but verification.md is incomplete or has failed evidence",
            evidence_items=[
                evidence(
                    verification_path,
                    f"stage_status: {stage_status(verification_meta) or 'unset'}; evidence_complete: {verification_meta.get('evidence_complete', 'unset')}",
                )
            ],
            diagnostics=verification_diagnostics,
        )
    if project_context(verification_meta) != project_context(discovery_meta):
        return project_context_mismatch_result(
            feature_dir,
            stage="verification",
            path=verification_path,
            discovery_context=project_context(discovery_meta),
            stage_context=project_context(verification_meta),
        )

    handoff = load_stage(feature_dir, "handoff")
    if handoff is None:
        handoff_path = feature_dir / STAGE_DOCS["handoff"]
        return make_result(
            feature_dir=feature_dir,
            state="handoff_missing",
            next_skill="coding-verification-closeout",
            reason="handoff.md missing",
            evidence_items=[evidence(handoff_path, "missing")],
        )
    handoff_path, handoff_meta, handoff_body = handoff
    handoff_metadata_issue = stage_metadata_issue("handoff", handoff_meta)
    if handoff_metadata_issue:
        return metadata_inconsistent_result(feature_dir, "handoff", handoff_path, handoff_metadata_issue)
    if not handoff_complete(handoff_meta, handoff_body):
        return make_result(
            feature_dir=feature_dir,
            state="handoff_incomplete",
            next_skill="coding-verification-closeout",
            reason="verification.md is complete but handoff.md lacks complete closeout metadata/content",
            evidence_items=[
                evidence(
                    handoff_path,
                    f"stage_status: {stage_status(handoff_meta) or 'unset'}; evidence_complete: {handoff_meta.get('evidence_complete', 'unset')}",
                )
            ],
        )
    if project_context(handoff_meta) != project_context(discovery_meta):
        return project_context_mismatch_result(
            feature_dir,
            stage="handoff",
            path=handoff_path,
            discovery_context=project_context(discovery_meta),
            stage_context=project_context(handoff_meta),
        )

    return make_result(
        feature_dir=feature_dir,
        state="complete",
        complete=True,
        reason="all Coding Feature Workflow stage documents are complete",
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
    parser = argparse.ArgumentParser(description="Inspect Coding Feature Workflow state")
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
