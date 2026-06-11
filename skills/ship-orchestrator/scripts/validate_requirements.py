#!/usr/bin/env python3
"""Requirements Validator - 验证 requirements.md 质量。"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from _lib import Check, extract_ac_sections, feature_path, has_section, parse_meta_yaml, require_frontmatter, section_text, summarize



def normalize_project_names(raw: object) -> list[str]:
    if not isinstance(raw, list):
        return []
    names: list[str] = []
    for item in raw:
        if isinstance(item, dict):
            value = item.get("name") or item.get("id") or item.get("project")
        else:
            value = item
        if value:
            names.append(str(value))
    return names


def workspace_project_config(feature_dir: Path) -> Path | None:
    candidates = [
        feature_dir.parent / "ship" / "project.yml",
        feature_dir.parent.parent / ".docs" / "ship" / "project.yml" if feature_dir.parent.parent else feature_dir / "__missing__",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def validate_meta_contract(feature_dir: Path) -> list[Check]:
    checks: list[Check] = []
    meta_path = feature_dir / "meta.yml"
    meta = parse_meta_yaml(meta_path)

    source_refs = meta.get("source_refs")
    has_sources = isinstance(source_refs, list) and bool(source_refs)
    checks.append(Check("source_refs 存在", has_sources, "meta.yml 必须登记至少一个 source_refs"))

    primary_available = False
    if has_sources:
        for source in source_refs:
            if not isinstance(source, dict):
                continue
            role = str(source.get("role") or "")
            status = str(source.get("status") or "")
            if role == "primary" and status == "available":
                primary_available = True
                break
    checks.append(Check("primary source 可用", primary_available, "至少一个 primary source_ref 的 status 必须是 available"))

    workspace_mode = str(meta.get("workspace_mode") or "")
    projects = normalize_project_names(meta.get("projects"))
    if workspace_mode == "project_group":
        checks.append(Check("project_group projects", bool(projects), "workspace_mode: project_group 时 meta.yml.projects 必须至少包含 1 个项目名"))
    elif workspace_mode:
        checks.append(Check("workspace_mode", workspace_mode in {"single_project", "project_group"}, "workspace_mode 必须是 single_project 或 project_group"))
    else:
        checks.append(Check("workspace_mode", False, "meta.yml 必须包含 workspace_mode"))

    project_config = workspace_project_config(feature_dir)
    if project_config and projects:
        configured = set(normalize_project_names(parse_meta_yaml(project_config).get("projects")))
        unknown = [project for project in projects if project not in configured]
        checks.append(Check("projects 属于 project.yml", not unknown, "meta.yml.projects 不属于 .docs/ship/project.yml: " + ", ".join(unknown) if unknown else ""))

    return checks
def validate_requirements(feature_dir: Path) -> list[Check]:
    req_file = feature_dir / "requirements.md"
    checks, _fm, body = require_frontmatter(req_file)

    checks.extend(validate_meta_contract(feature_dir))
    ac_sections = extract_ac_sections(body)
    checks.append(Check("至少 1 个 AC", bool(ac_sections), "requirements.md 必须包含 ### AC-1 形式的验收标准"))

    for ac_id, section in ac_sections.items():
        ok = all(token in section for token in ("Given", "When", "Then"))
        checks.append(Check(f"{ac_id} Given/When/Then", ok, f"{ac_id} 缺少 Given/When/Then 结构"))

    domain_ok = has_section(body, ["Domain 模型", "领域模型"])
    no_domain = "不涉及业务域" in body or "无 Domain" in body or "不涉及 Domain" in body
    checks.append(Check("Domain 模型", domain_ok or no_domain, "需要 Domain 模型，或明确说明不涉及业务域"))

    nfr = section_text(body, ["非功能需求", "NFR"])
    if not nfr:
        checks.append(Check("非功能需求", True, "小功能可接受未定义非功能需求", warning=True))
    else:
        has_metric = bool(re.search(r"(<|>|<=|>=|P95|P99|QPS|ms|秒|分钟|%)", nfr, flags=re.IGNORECASE))
        checks.append(Check("非功能需求量化", has_metric, "非功能需求存在但缺少量化指标", warning=not has_metric))

    return checks


def main() -> int:
    feature_dir = feature_path(sys.argv)
    return summarize(validate_requirements(feature_dir), "Requirements Validation")


if __name__ == "__main__":
    raise SystemExit(main())
