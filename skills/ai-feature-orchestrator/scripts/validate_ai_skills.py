#!/usr/bin/env python3
"""Smoke tests for the explicit-only AI Feature Workflow skills."""

from __future__ import annotations

from pathlib import Path
import re
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
STAGE_TEMPLATE_FILES = {
    "requirements.md": "requirements",
    "investigation.md": "investigation",
    "design.md": "design",
    "tasks.md": "tasks",
    "verification.md": "verification",
    "handoff.md": "handoff",
}
VALID_STAGE_STATUS = {"draft", "ready", "blocked", "complete"}
ISO_WITH_TZ = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|[+-]\d{2}:\d{2})$")
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


def parse_frontmatter(path: Path, errors: list[str]) -> dict[str, str]:
    text = path.read_text()
    if not text.startswith("---\n"):
        fail(errors, f"{path}: missing YAML frontmatter")
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        fail(errors, f"{path}: unterminated YAML frontmatter")
        return {}
    metadata: dict[str, str] = {}
    for line in text[4:end].splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in stripped:
            fail(errors, f"{path}: invalid frontmatter line {line!r}")
            continue
        key, value = stripped.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"').strip("'")
    return metadata


def assert_order(text: str, first: str, second: str, errors: list[str], label: str) -> None:
    first_index = text.find(first)
    second_index = text.find(second)
    if first_index == -1:
        fail(errors, f"missing order marker {first!r} for {label}")
        return
    if second_index == -1:
        fail(errors, f"missing order marker {second!r} for {label}")
        return
    if first_index > second_index:
        fail(errors, f"{label}: blocked check must appear before draft/content check")


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
    for required in ["Workflow contract", "阶段停止点", "Safety policy", "WORKFLOW_CONTRACT.md", "approval_status", "references/golden-examples.md"]:
        if required not in orch_text:
            fail(errors, f"{orchestrator_skill}: missing {required}")
    for field in ROUTE_FIELDS:
        if field not in orch_text:
            fail(errors, f"{orchestrator_skill}: missing route field {field}")
    assert_order(
        orch_text,
        "`investigation.md` 的 `stage_status` 为 `blocked`",
        "`investigation.md` 的 `stage_status` 为 `draft`",
        errors,
        "investigation stage inference",
    )
    assert_order(
        orch_text,
        "`design.md` 的 `stage_status` 为 `blocked`",
        "`design.md` 的 `stage_status` 为 `draft`",
        errors,
        "design stage inference",
    )

    contract = ORCHESTRATOR / "WORKFLOW_CONTRACT.md"
    if not contract.exists():
        fail(errors, "missing WORKFLOW_CONTRACT.md")
    else:
        contract_text = contract.read_text()
        for required in [
            "Activation contract",
            "Route contract",
            "Document metadata contract",
            "Design approval contract",
            "Gate policy",
            "Safety policy",
            "Service startup and port-check protocol",
            "Scope change protocol",
            "Resume protocol",
        ]:
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
        if "WORKFLOW_CONTRACT.md" not in text:
            fail(errors, f"{path}: missing shared contract reference")

    required_template_dirs = [TEMPLATE / "resource", TEMPLATE / "sql"]
    for directory in required_template_dirs:
        if not directory.is_dir():
            fail(errors, f"{directory}: missing template directory")
    for sql_name in ["DDL.sql", "DML.sql", "ROLLBACK.sql"]:
        if not (TEMPLATE / "sql" / sql_name).is_file():
            fail(errors, f"{TEMPLATE / 'sql' / sql_name}: missing SQL draft file")

    for md_path in sorted(TEMPLATE.rglob("*.md")):
        text = md_path.read_text()
        metadata = parse_frontmatter(md_path, errors)
        if "stage_status" not in metadata:
            fail(errors, f"{md_path}: missing stage_status metadata")
        elif metadata["stage_status"] not in VALID_STAGE_STATUS:
            fail(errors, f"{md_path}: invalid stage_status {metadata['stage_status']!r}")
        for pattern in BAD_TEMPLATE_PATTERNS:
            if pattern in text:
                fail(errors, f"{md_path}: contains misleading placeholder pattern {pattern!r}")

        relative_name = md_path.relative_to(TEMPLATE).as_posix()
        if relative_name in STAGE_TEMPLATE_FILES:
            expected_stage = STAGE_TEMPLATE_FILES[relative_name]
            for required in ["feature_stage", "stage_status", "updated_at", "evidence_complete"]:
                if required not in metadata:
                    fail(errors, f"{md_path}: missing stage metadata {required}")
            if metadata.get("feature_stage") != expected_stage:
                fail(errors, f"{md_path}: feature_stage must be {expected_stage!r}")
            if metadata.get("evidence_complete") not in {"false", "true"}:
                fail(errors, f"{md_path}: evidence_complete must be true or false")
            updated_at = metadata.get("updated_at", "")
            if updated_at and not ISO_WITH_TZ.match(updated_at):
                fail(errors, f"{md_path}: updated_at must be ISO 8601 with timezone")
        elif relative_name in {"README.md", "resource/README.md"}:
            if metadata.get("feature_stage") in STAGE_TEMPLATE_FILES.values():
                fail(errors, f"{md_path}: auxiliary doc must not use a real feature_stage")

    tasks_text = (TEMPLATE / "tasks.md").read_text()
    if "task_count: 0" not in tasks_text:
        fail(errors, "template tasks.md should start with task_count: 0")
    if "当前无真实任务" not in tasks_text:
        fail(errors, "template tasks.md should explicitly state no real tasks")
    tasks_metadata = parse_frontmatter(TEMPLATE / "tasks.md", errors)
    if tasks_metadata.get("evidence_complete") != "false":
        fail(errors, "template tasks.md should include evidence_complete: false")

    design_metadata = parse_frontmatter(TEMPLATE / "design.md", errors)
    for field in ["approval_status", "approved_by", "approved_at", "approval_evidence"]:
        if field not in design_metadata:
            fail(errors, f"template design.md missing approval metadata {field}")
    if design_metadata.get("approval_status") != "pending":
        fail(errors, "template design.md should start with approval_status: pending")

    golden_examples = ORCHESTRATOR / "references" / "golden-examples.md"
    if not golden_examples.is_file():
        fail(errors, f"{golden_examples}: missing golden examples reference")
    else:
        examples_text = golden_examples.read_text()
        for required in ["Happy path", "Blocked requirement", "Resume DOING", "Verification failed"]:
            if required not in examples_text:
                fail(errors, f"{golden_examples}: missing {required} example")

    for doc_path in [*sorted(SKILLS.glob("*/SKILL.md")), ORCHESTRATOR / "WORKFLOW_CONTRACT.md"]:
        if "AI feature workflow" in doc_path.read_text():
            fail(errors, f"{doc_path}: use unified term AI Feature Workflow")

    if errors:
        print("AI skill smoke test failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("AI skill smoke test passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
