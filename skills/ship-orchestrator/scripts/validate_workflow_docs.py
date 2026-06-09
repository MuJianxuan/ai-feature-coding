#!/usr/bin/env python3
"""Validate Ship Solo workflow documentation consistency."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from workflow_stage_map import CANONICAL_STAGE_ORDER, SUPPORT_SKILLS, macro_stage_for  # noqa: E402


REQUIRED_STAGE_LABELS = (
    "Discover",
    "Define",
    "Understand",
    "Design",
    "Plan",
    "Build",
    "Verify",
    "Close",
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def validate_stage_map() -> None:
    require(len(CANONICAL_STAGE_ORDER) == 8, "workflow_stage_map.py: expected 8 lightweight runtime stages")
    require(CANONICAL_STAGE_ORDER[0] == "ship-discover", "workflow_stage_map.py: first stage must be ship-discover")
    require(CANONICAL_STAGE_ORDER[-1] == "ship-handoff", "workflow_stage_map.py: last stage must be ship-handoff")
    for stage in CANONICAL_STAGE_ORDER:
        view = macro_stage_for(stage)
        require(view.label in REQUIRED_STAGE_LABELS, f"workflow_stage_map.py: unexpected label {view.label}")
    for support_skill in ("ship-define-review", "ship-design-review", "ship-plan-review", "ship-shape", "ship-spec"):
        require(support_skill in SUPPORT_SKILLS, f"workflow_stage_map.py: missing support skill {support_skill}")
        require(support_skill not in CANONICAL_STAGE_ORDER, f"workflow_stage_map.py: support skill must not be canonical {support_skill}")


def validate_protocol_doc() -> None:
    path = ROOT / "skills/ship-orchestrator/_templates/protocol/workflow-protocol.md"
    text = read_text(path)
    for snippet in (
        "Ship Solo Workflow Protocol",
        "个人开发者",
        "默认运行时阶段只有 8 个",
        "review 类 skill 保留为可选检查工具",
        "Source Discipline",
        "implementation_preflight.py",
        "不再要求 `review-plan.md` 签字",
    ):
        require(snippet in text, f"{path}: missing `{snippet}`")
    for stage in CANONICAL_STAGE_ORDER:
        require(f"`{stage}`" in text, f"{path}: missing canonical stage `{stage}`")
    for label in REQUIRED_STAGE_LABELS:
        require(label in text, f"{path}: missing macro label {label}")
    for legacy in (
        "三道 hard gate",
        "必须用户签字才能放行",
        "14 个 canonical",
    ):
        require(legacy not in text, f"{path}: contains legacy heavy-gate wording `{legacy}`")


def validate_meta_template() -> None:
    path = ROOT / "skills/ship-orchestrator/_templates/meta/meta.yml.template"
    text = read_text(path)
    for snippet in (
        "schema_version: 3",
        "work_mode: feature",
        "strictness: lightweight",
        "review_skills_are_optional: true",
        "support_skills:",
        "slices:",
        "verification_command",
    ):
        require(snippet in text, f"{path}: missing `{snippet}`")
    for stage in CANONICAL_STAGE_ORDER:
        require(f"{stage}:" in text or f"{stage} |" in text or stage in text, f"{path}: missing stage {stage}")


def validate_readmes() -> None:
    for relative in ("README.md", "skills/README.md"):
        path = ROOT / relative
        text = read_text(path)
        for snippet in (
            "ship-orchestrator",
            "Discover → Define → Understand → Design → Plan → Build → Verify → Close",
            "个人开发者",
            "轻量",
        ):
            require(snippet in text, f"{path}: missing `{snippet}`")
        require("hard gate" not in text.lower() or "不再" in text or "不是" in text, f"{path}: hard gate wording must be clearly deprecated")


def validate_skill_frontmatter() -> None:
    for skill_dir in (ROOT / "skills").glob("ship-*"):
        skill_path = skill_dir / "SKILL.md"
        if not skill_path.exists():
            continue
        text = read_text(skill_path)
        require(text.startswith("---\n"), f"{skill_path}: missing YAML frontmatter")
        require("name:" in text.split("---", 2)[1], f"{skill_path}: missing name frontmatter")
        require("description:" in text.split("---", 2)[1], f"{skill_path}: missing description frontmatter")


def validate_regression_prompts() -> None:
    path = ROOT / "skills/ship-orchestrator/tests/regression-prompts.md"
    text = read_text(path)
    for snippet in (
        "Small Bugfix Starts From Understand",
        "Review Skills Are Optional",
        "Build Preflight Is Lightweight",
        "Support Skill Not Runtime Stage",
    ):
        require(snippet in text, f"{path}: missing `{snippet}`")


def validate_grill_hook_docs() -> None:
    """Compatibility wrapper for older tests.

    In the solo workflow, ship-grill-me is a support skill. It may ask one
    blocking question, but it must not become a canonical runtime stage or
    approve/sign review gates.
    """
    validate_stage_map()
    skill_path = ROOT / "skills/ship-grill-me/SKILL.md"
    text = read_text(skill_path)
    for snippet in (
        "一次只问一个真正阻塞的问题",
        "不修改 `meta.yml`",
        "不替用户批准 review",
    ):
        require(snippet in text, f"{skill_path}: missing `{snippet}`")


def main() -> int:
    checks = (
        validate_stage_map,
        validate_protocol_doc,
        validate_meta_template,
        validate_readmes,
        validate_skill_frontmatter,
        validate_regression_prompts,
    )
    failures: list[str] = []
    for check in checks:
        try:
            check()
        except AssertionError as exc:
            failures.append(str(exc))
    if failures:
        for failure in failures:
            print(f"ERROR {failure}", file=sys.stderr)
        return 1
    print("workflow docs ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
