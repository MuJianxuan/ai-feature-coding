#!/usr/bin/env python3
"""Validate workflow documentation consistency.

This checks that the executable stage mapping, protocol docs, meta template,
and example docs all describe the same 4-stage default view.
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
    ):
        require(snippet in text, f"{path}: missing `{snippet}`")


def validate_protocol_doc() -> None:
    path = ROOT / "skills/ship-orchestrator/_templates/protocol/workflow-protocol.md"
    text = read_text(path)
    require("## 2. Macro Stage View" in text, f"{path}: missing macro stage section")
    require(
        "macro_stage.next_user_decision" in text,
        f"{path}: missing next_user_decision references",
    )
    for stage in CANONICAL_STAGE_ORDER:
        macro = macro_stage_for(stage)
        row = f"| `{macro.current}` | `{macro.label}` |"
        require(row in text, f"{path}: missing macro row for {macro.current}/{macro.label}")


def validate_macro_view_example() -> None:
    path = ROOT / "skills/ship-orchestrator/_templates/todo-app-example/meta-view-example.md"
    text = read_text(path)
    require("current_stage: \"ship-design-review\"" in text, f"{path}: missing example current_stage")
    require("macro_stage:" in text, f"{path}: missing macro_stage example")
    for stage in CANONICAL_STAGE_ORDER:
        macro = macro_stage_for(stage)
        row = f"| `{stage}` | `{macro.current}` | `{macro.label}` |"
        require(row in text, f"{path}: missing mapping row for {stage}")


def validate_readmes() -> None:
    readme_paths = [
        ROOT / "README.md",
        ROOT / "skills/README.md",
        ROOT / "skills/ship-orchestrator/_templates/todo-app-example/README.md",
    ]
    for path in readme_paths:
        text = read_text(path)
        require("Define" in text and "Design" in text and "Build" in text and "Close" in text, f"{path}: missing 4-stage view")


def validate_orchestrator_doc() -> None:
    path = ROOT / "skills/ship-orchestrator/SKILL.md"
    text = read_text(path)
    require("meta.yml.macro_stage" in text, f"{path}: missing meta.yml.macro_stage")
    require("macro_stage.next_user_decision" in text, f"{path}: missing next_user_decision sync")
    require("Define → Design → Build → Close" in text, f"{path}: missing default stage sequence")


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


def main() -> int:
    validators = [
        validate_stage_map_script,
        validate_meta_template,
        validate_protocol_doc,
        validate_macro_view_example,
        validate_readmes,
        validate_orchestrator_doc,
        validate_root_readme_commands,
    ]
    for validator in validators:
        validator()
    print("workflow docs validation: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
