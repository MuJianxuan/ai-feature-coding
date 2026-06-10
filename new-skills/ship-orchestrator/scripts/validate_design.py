#!/usr/bin/env python3
"""Design Validator - 验证 design.md 完整性、AC 覆盖和参考模板结构。"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

from _lib import (
    Check,
    extract_ac_ids,
    feature_path,
    has_section,
    has_top_section,
    parse_frontmatter,
    parse_loose_yaml,
    read_text,
    require_frontmatter,
    section_text,
    summarize,
)

BASE_SECTIONS = [
    "AC 覆盖映射",
    "API 契约",
    "数据模型",
    "前端设计",
    "后端设计",
    "性能考量",
    "风险和回滚",
]

TEMPLATE_REQUIRED_SCENARIOS = {"full_flow", "prd_direct", "split_first"}
FORBIDDEN_READY_PATTERNS = [
    ("{{", "存在未替换占位符 '{{'"),
    ("}}", "存在未替换占位符 '}}'"),
    ("{功能名称}", "存在未替换模板变量 {功能名称}"),
    ("待补充", "存在待补充内容"),
    ("后续再说", "存在未决内容：后续再说"),
    ("视情况而定", "存在无解释的“视情况而定”"),
]


def script_root() -> Path:
    return Path(__file__).resolve().parents[3]


def builtin_template_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "templates" / "design-reference"


def parse_template_ref(ref: str) -> tuple[str, str]:
    if ref.startswith("builtin:"):
        rest = ref[len("builtin:") :]
        template_id = rest.split("@", 1)[0]
        return "builtin", template_id
    if ref.startswith("project:"):
        rest = ref[len("project:") :]
        path = rest.split("#", 1)[0]
        return "project", path
    return "unknown", ref


def load_builtin_template(template_id: str) -> tuple[Path, dict[str, Any]]:
    path = builtin_template_dir() / f"{template_id}.md"
    if not path.exists():
        return path, {}
    fm, _ = parse_frontmatter(read_text(path))
    return path, fm


def index_contains_template(template_id: str) -> bool:
    index = builtin_template_dir() / "INDEX.md"
    if not index.exists():
        return False
    content = read_text(index)
    return bool(re.search(rf"^\|\s*{re.escape(template_id)}\s*\|", content, flags=re.MULTILINE))


def project_template_exists(raw_path: str) -> bool:
    path = Path(raw_path)
    if path.is_absolute():
        return path.exists()
    return (script_root() / path).exists()


def check_template_ref(ref: str) -> tuple[bool, str, dict[str, Any]]:
    kind, value = parse_template_ref(ref)
    if kind == "builtin":
        path, fm = load_builtin_template(value)
        if not path.exists():
            return False, f"内置模板不存在: {value}", {}
        if not index_contains_template(value):
            return False, f"内置模板未登记到 design-reference/INDEX.md: {value}", {}
        return True, "", fm
    if kind == "project":
        if not project_template_exists(value):
            return False, f"项目模板路径不存在: {value}", {}
        return True, "", {}
    return False, f"模板引用格式非法: {ref}", {}


def has_explicit_not_applicable(text: str) -> bool:
    return "不涉及" in text and ("原因" in text or "因为" in text or "无需" in text or "无变更" in text)


def subsection_satisfied(body: str, item: str) -> bool:
    if "/" not in item:
        return item in body
    section_name, subsection = item.split("/", 1)
    content = section_text(body, [section_name])
    if not content:
        return False
    if subsection.lower() in content.lower():
        return True
    return has_explicit_not_applicable(content)


def validate_template_deviation(body: str) -> Check:
    if "偏离" not in body:
        return Check("模板偏离格式", True)
    required = ["偏离项", "原因", "影响", "替代设计"]
    missing = [name for name in required if name not in body]
    return Check(
        "模板偏离格式",
        not missing,
        "模板偏离缺少字段: " + ", ".join(missing) if missing else "",
    )


def validate_ready_placeholders(status: str, body: str) -> list[Check]:
    if status != "ready":
        return []
    checks: list[Check] = []
    for pattern, message in FORBIDDEN_READY_PATTERNS:
        checks.append(Check(f"ready 禁止内容: {pattern}", pattern not in body, message))
    checks.append(Check("ready 禁止内容: TBD", re.search(r"\bTBD\b", body, flags=re.IGNORECASE) is None, "存在 TBD"))
    return checks


def validate_design(feature_dir: Path) -> list[Check]:
    design_file = feature_dir / "design.md"
    requirements_file = feature_dir / "requirements.md"
    checks, fm, body = require_frontmatter(design_file)

    meta = parse_loose_yaml(feature_dir / "meta.yml")
    scenario = str(meta.get("scenario") or "")
    template_ref = str(meta.get("design_template_ref") or "").strip()
    template_fm: dict[str, Any] = {}
    must_have_template = scenario in TEMPLATE_REQUIRED_SCENARIOS

    if template_ref:
        ok, message, template_fm = check_template_ref(template_ref)
        checks.append(Check("模板存在性", ok, message))
    elif must_have_template:
        checks.append(Check("模板引用", False, f"{scenario} 必须在 meta.yml 记录 design_template_ref"))
    else:
        checks.append(Check("模板引用", True, "quick_start 缺少模板引用可接受", warning=True))

    template_section = section_text(body, ["方案模板引用"])
    if template_ref or must_have_template:
        checks.append(Check("方案模板引用章节", bool(template_section), "非 quick_start 或已选模板时必须包含 ## 方案模板引用"))
    elif not template_section:
        checks.append(Check("方案模板引用章节", True, "quick_start 缺少 ## 方案模板引用可接受", warning=True))

    if template_ref and template_section:
        checks.append(Check("正文模板引用一致", template_ref in template_section, f"design.md 方案模板引用未包含 meta.yml.design_template_ref: {template_ref}"))

    top_sections = list(BASE_SECTIONS)
    if template_ref or must_have_template:
        top_sections = ["方案模板引用"] + top_sections
    for section in top_sections:
        checks.append(Check(f"顶层章节: {section}", has_top_section(body, [section]), f"design.md 缺少顶层章节 ## {section}"))

    req_content = read_text(requirements_file) if requirements_file.exists() else ""
    ac_ids = extract_ac_ids(req_content)

    api = section_text(body, ["API 契约", "API Contract"])
    no_api = "不涉及 API" in api or "无 API" in api
    checks.append(Check("API 契约章节", bool(api), "design.md 必须包含 API 契约章节"))
    if api and not no_api:
        checks.append(Check("API Request", "Request" in api or "请求" in api, "API 契约缺少 Request"))
        checks.append(Check("API Response", "Response" in api or "响应" in api, "API 契约缺少 Response"))
        checks.append(Check("API Error", "Error" in api or "错误" in api or "4" in api, "API 契约缺少错误响应"))

    data_model = section_text(body, ["数据模型", "Data Model"])
    no_data = "不涉及数据" in data_model or "无数据" in data_model
    checks.append(Check("数据模型", bool(data_model) and (no_data or len(data_model.strip()) > 5), "需要数据模型，或明确说明不涉及数据变更"))

    checks.append(Check("前端设计章节", has_section(body, ["前端设计", "Frontend"]), "缺少前端设计章节；纯后端也应说明不涉及前端"))
    checks.append(Check("后端设计章节", has_section(body, ["后端设计", "Backend"]), "缺少后端设计章节；纯前端也应说明不涉及后端"))

    uncovered = [ac for ac in ac_ids if ac not in body]
    checks.append(Check("AC 覆盖", not uncovered, f"设计未覆盖 AC: {', '.join(uncovered)}" if uncovered else ""))

    required_sections = template_fm.get("required_sections") or []
    if isinstance(required_sections, list):
        for section in required_sections:
            checks.append(Check(f"模板必填章节: {section}", has_top_section(body, [section]), f"模板要求缺少章节: ## {section}"))

    required_subsections = template_fm.get("required_subsections") or []
    if isinstance(required_subsections, list):
        for item in required_subsections:
            checks.append(Check(f"模板必填子章节: {item}", subsection_satisfied(body, item), f"模板要求缺少子章节或不涉及说明: {item}"))

    checks.append(validate_template_deviation(body))
    checks.extend(validate_ready_placeholders(str(fm.get("status") or ""), body))

    spec_refs = fm.get("spec_refs") or meta.get("spec_refs") or []
    if not spec_refs:
        checks.append(Check("规范引用", True, "未引用任何 spec，quick_start 可接受但 full_flow 应补充", warning=True))
    else:
        checks.append(Check("规范引用", True))

    if template_ref:
        spec_priority_declared = "spec" in template_section.lower() and ("优先" in template_section or "冲突" in template_section)
        checks.append(Check("模板与 spec 优先声明", spec_priority_declared, "有模板但未声明模板与 spec 冲突时以 spec 为准", warning=not spec_priority_declared))

    perf = section_text(body, ["性能考量", "性能"])
    checks.append(Check("性能考量", bool(perf), "缺少性能考量；小功能可接受", warning=not bool(perf)))

    return checks


def main() -> int:
    feature_dir = feature_path(sys.argv)
    return summarize(validate_design(feature_dir), "Design Validation")


if __name__ == "__main__":
    raise SystemExit(main())
