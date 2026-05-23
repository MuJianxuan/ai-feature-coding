#!/usr/bin/env python3
"""Validate workflow documentation consistency.

This checks that the executable stage mapping, protocol docs, meta template,
and primary workflow docs all describe the same 4-stage default view.
"""

from __future__ import annotations
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from workflow_stage_map import CANONICAL_STAGE_ORDER, macro_stage_for  # noqa: E402


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate_meta_template() -> None:
    path = ROOT / "skills/ship-orchestrator/_templates/meta/meta.yml.template"
    text = read_text(path)
    for snippet in (
        "macro_stage:",
        'current: ""',
        'label: ""',
        'summary: ""',
        'next_user_decision: ""',
        "ship-tech-discovery:",
        "current_part: research",
        "ship-delivery-plan:",
        "current_part: frontend",
        "spec_context:",
        "index_status: missing",
        "referenced_spec_ids: []",
        "pending_proposals: []",
    ):
        require(snippet in text, f"{path}: missing `{snippet}`")


def validate_protocol_doc() -> None:
    path = ROOT / "skills/ship-orchestrator/_templates/protocol/workflow-protocol.md"
    text = read_text(path)
    require("## 2. Macro Stage View" in text, f"{path}: missing macro stage section")
    require("## 7. Spec Hook Contract" in text, f"{path}: missing spec hook section")
    require(
        "macro_stage.next_user_decision" in text,
        f"{path}: missing next_user_decision references",
    )
    require("`ship-spec` 是 workflow utility" in text, f"{path}: missing ship-spec utility wording")
    require("spec_context" in text, f"{path}: missing spec_context references")
    for stage in CANONICAL_STAGE_ORDER:
        macro = macro_stage_for(stage)
        row = f"| `{macro.current}` | `{macro.label}` |"
        require(row in text, f"{path}: missing macro row for {macro.current}/{macro.label}")


def validate_readmes() -> None:
    workflow_readme_paths = [
        ROOT / "README.md",
        ROOT / "skills/README.md",
    ]
    for path in workflow_readme_paths:
        text = read_text(path)
        require("Define" in text and "Design" in text and "Build" in text and "Close" in text, f"{path}: missing 4-stage view")
        require("ship-spec" in text, f"{path}: missing ship-spec mention")

    templates_readme = ROOT / "skills/ship-orchestrator/_templates/README.md"
    templates_text = read_text(templates_readme)
    for snippet in ("meta.yml.template", "review.md.template", "workflow-protocol.md", "spec_context"):
        require(snippet in templates_text, f"{templates_readme}: missing `{snippet}`")


def validate_stage_reference_templates() -> None:
    skill_templates = {
        ROOT / "skills/ship-contract/SKILL.md": (
            ROOT / "skills/ship-contract/references/api-contract-template.md",
            "references/api-contract-template.md",
        ),
        ROOT / "skills/ship-frontend-design/SKILL.md": (
            ROOT / "skills/ship-frontend-design/references/frontend-design-template.md",
            "references/frontend-design-template.md",
        ),
        ROOT / "skills/ship-backend-design/SKILL.md": (
            ROOT / "skills/ship-backend-design/references/backend-design-template.md",
            "references/backend-design-template.md",
        ),
    }
    for skill_path, (template_path, relative_ref) in skill_templates.items():
        require(template_path.exists(), f"{template_path}: missing stage reference template")
        skill_text = read_text(skill_path)
        require(relative_ref in skill_text, f"{skill_path}: missing template reference `{relative_ref}`")
        template_text = read_text(template_path)
        for snippet in ("这是一份写作引导模板，不是固定格式。", "## 必答问题", "## 推荐写法", "## 常见空话警报"):
            require(snippet in template_text, f"{template_path}: missing `{snippet}`")


def validate_orchestrator_doc() -> None:
    path = ROOT / "skills/ship-orchestrator/SKILL.md"
    text = read_text(path)
    require("meta.yml.macro_stage" in text, f"{path}: missing meta.yml.macro_stage")
    require("macro_stage.next_user_decision" in text, f"{path}: missing next_user_decision sync")
    require("Define → Design → Build → Close" in text, f"{path}: missing default stage sequence")
    require("ship-spec" in text, f"{path}: missing ship-spec utility references")
    require("spec_context" in text, f"{path}: missing spec_context references")


def validate_ship_spec_doc() -> None:
    path = ROOT / "skills/ship-spec/SKILL.md"
    text = read_text(path)
    for snippet in (
        "stage_hooks",
        "stack_tags",
        "domains",
        "Proposal-First",
        "spec_runtime.py",
        "feature_meta_runtime.py sync-spec",
    ):
        require(snippet in text, f"{path}: missing `{snippet}`")
    require("不是 canonical stage" in text, f"{path}: missing non-stage wording")


def validate_stage_map_script() -> None:
    require(len(CANONICAL_STAGE_ORDER) == 12, "stage map: expected 12 canonical stages")
    for stage in CANONICAL_STAGE_ORDER:
        macro = macro_stage_for(stage)
        require(macro.current in {"define", "design", "build", "close"}, f"invalid macro current for {stage}")
        require(macro.label in {"Define", "Design", "Build", "Close"}, f"invalid macro label for {stage}")


def validate_root_readme_commands() -> None:
    path = ROOT / "README.md"
    text = read_text(path)
    require("ship-orchestrator" in text, f"{path}: missing ship-orchestrator entry")
    require("4 大阶段" in text or "4 个大阶段" in text or "4 个大阶段" in text, f"{path}: missing 4-stage wording")
    require("feature_meta_runtime.py" in text, f"{path}: missing feature_meta_runtime helper command")
    require("spec_runtime.py" in text, f"{path}: missing spec_runtime helper command")


def main() -> int:
    validators = [
        validate_stage_map_script,
        validate_meta_template,
        validate_protocol_doc,
        validate_readmes,
        validate_stage_reference_templates,
        validate_orchestrator_doc,
        validate_ship_spec_doc,
        validate_root_readme_commands,
    ]
    for validator in validators:
        validator()
    print("workflow docs validation: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
