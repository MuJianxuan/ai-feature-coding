#!/usr/bin/env python3
"""Smoke tests for the explicit-only AI feature workflow skills."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
SKILLS = ROOT / "skills"
ORCHESTRATOR = SKILLS / "ai-feature-orchestrator"
TEMPLATE = ORCHESTRATOR / "assets" / "feature-template"
CHILD_SKILLS = [
    "ai-requirement-intake",
    "ai-repo-investigation",
    "ai-technical-design",
    "ai-task-planning",
    "ai-implementation-execution",
    "ai-verification-closeout",
]
ROUTE_FIELDS = ["activation_source", "feature_dir", "stage_evidence"]
BAD_TEMPLATE_PATTERNS = [
    "BLOCKING / NON_BLOCKING",
    "TODO / PASS / FAIL / BLOCKED",
    "<任务名>",
    "| Q-01 |",
    "| AC-01 |",
    "| T01 |  | TODO |",
    "- status: TODO",
]


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def main() -> int:
    errors: list[str] = []

    for yaml_path in sorted(SKILLS.glob("*/agents/openai.yaml")):
        text = yaml_path.read_text()
        if "allow_implicit_invocation: false" not in text:
            fail(errors, f"{yaml_path}: allow_implicit_invocation must be false")
        if "allow_implicit_invocation: true" in text:
            fail(errors, f"{yaml_path}: implicit invocation is still true")

    orchestrator_skill = ORCHESTRATOR / "SKILL.md"
    orch_text = orchestrator_skill.read_text()
    for required in ["Workflow contract", "阶段停止点", "Safety policy", "WORKFLOW_CONTRACT.md"]:
        if required not in orch_text:
            fail(errors, f"{orchestrator_skill}: missing {required}")
    for field in ROUTE_FIELDS:
        if field not in orch_text:
            fail(errors, f"{orchestrator_skill}: missing route field {field}")

    contract = ORCHESTRATOR / "WORKFLOW_CONTRACT.md"
    if not contract.exists():
        fail(errors, "missing WORKFLOW_CONTRACT.md")
    else:
        contract_text = contract.read_text()
        for required in ["Activation contract", "Route contract", "Document metadata contract", "Gate policy", "Safety policy", "Resume protocol"]:
            if required not in contract_text:
                fail(errors, f"{contract}: missing {required}")

    for name in CHILD_SKILLS:
        path = SKILLS / name / "SKILL.md"
        text = path.read_text()
        for required in ["Activation policy", "启动模式与 route contract", "Safety policy"]:
            if required not in text:
                fail(errors, f"{path}: missing {required}")
        for field in ROUTE_FIELDS:
            if field not in text:
                fail(errors, f"{path}: missing route field {field}")
        if "自行猜目录" not in text:
            fail(errors, f"{path}: missing no-guess-directory guard")

    for md_path in sorted(TEMPLATE.rglob("*.md")):
        text = md_path.read_text()
        if not text.startswith("---\n"):
            fail(errors, f"{md_path}: missing YAML frontmatter")
        if "stage_status:" not in text:
            fail(errors, f"{md_path}: missing stage_status metadata")
        for pattern in BAD_TEMPLATE_PATTERNS:
            if pattern in text:
                fail(errors, f"{md_path}: contains misleading placeholder pattern {pattern!r}")

    tasks_text = (TEMPLATE / "tasks.md").read_text()
    if "task_count: 0" not in tasks_text:
        fail(errors, "template tasks.md should start with task_count: 0")
    if "当前无真实任务" not in tasks_text:
        fail(errors, "template tasks.md should explicitly state no real tasks")

    if errors:
        print("AI skill smoke test failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("AI skill smoke test passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
