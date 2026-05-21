#!/usr/bin/env python3
"""Validation script for skills-new workflow assets."""

from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "skills-new"

REQUIRED_FILES = [
    BASE / "README.md",
    BASE / "workflow-orchestrator" / "SKILL.md",
    BASE / "workflow-orchestrator" / "WORKFLOW_CONTRACT.md",
    BASE / "product-requirements" / "SKILL.md",
    BASE / "technical-solution" / "SKILL.md",
    BASE / "implementation-planning" / "SKILL.md",
    BASE / "implementation-execution" / "SKILL.md",
    BASE / "verification-handoff" / "SKILL.md",
]

TEMPLATE_FILES = [
    "README.md",
    "source-index.md",
    "requirements.md",
    "requirements-gate.md",
    "tech-research.md",
    "solution.md",
    "solution-gate.md",
    "frontend-plan.md",
    "backend-plan.md",
    "plan-gate.md",
    "task-ledger.md",
    "verification.md",
    "handoff.md",
]

TODO_EXAMPLE_FILES = [
    "source-index.md",
    "requirements.md",
    "requirements-gate.md",
    "tech-research.md",
    "solution.md",
    "solution-gate.md",
    "frontend-plan.md",
    "backend-plan.md",
    "plan-gate.md",
    "task-ledger.md",
    "verification.md",
    "handoff.md",
]


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def require_exists(path: Path, errors: list[str]) -> None:
    if not path.exists():
        fail(errors, f"missing: {path}")


def require_text(path: Path, needle: str, errors: list[str]) -> None:
    text = path.read_text()
    if needle not in text:
        fail(errors, f"{path}: missing {needle!r}")


def main() -> int:
    errors: list[str] = []

    for path in REQUIRED_FILES:
        require_exists(path, errors)

    template_dir = BASE / "workflow-orchestrator" / "assets" / "workflow-template"
    for name in TEMPLATE_FILES:
        require_exists(template_dir / name, errors)

    example_dir = BASE / "workflow-orchestrator" / "assets" / "todo-web-example"
    for name in TODO_EXAMPLE_FILES:
        require_exists(example_dir / name, errors)

    require_text(BASE / "workflow-orchestrator" / "WORKFLOW_CONTRACT.md", "Requirements Gate", errors)
    require_text(BASE / "workflow-orchestrator" / "WORKFLOW_CONTRACT.md", "Solution Gate", errors)
    require_text(BASE / "workflow-orchestrator" / "WORKFLOW_CONTRACT.md", "Planning Gate", errors)
    require_text(template_dir / "frontend-plan.md", "依赖接口", errors)
    require_text(template_dir / "backend-plan.md", "数据影响", errors)
    require_text(example_dir / "requirements-gate.md", "gate_status: pass", errors)
    require_text(example_dir / "solution-gate.md", "gate_status: pass", errors)
    require_text(example_dir / "plan-gate.md", "gate_status: pass", errors)
    require_text(example_dir / "task-ledger.md", "task_count: 8", errors)
    require_text(example_dir / "handoff.md", "实施计划验收汇报", errors)
    require_text(example_dir / "requirements.md", "创建 todo", errors)
    require_text(example_dir / "requirements.md", "编辑 todo", errors)
    require_text(example_dir / "requirements.md", "删除 todo", errors)
    require_text(example_dir / "requirements.md", "筛选", errors)

    if errors:
        print("skills-new validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("skills-new validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
