#!/usr/bin/env python3
"""Validate workflow documentation consistency.

This checks that the executable stage mapping, protocol docs, meta template,
and primary workflow docs all describe the same 5-stage default view with
conditional Discover, plus the shared runtime/schema invariants.
"""

from __future__ import annotations
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from workflow_stage_map import CANONICAL_STAGE_ORDER, macro_stage_for  # noqa: E402
from feature_meta_runtime import CANONICAL_DELEGATION_NODES  # noqa: E402


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
        'target_project_id: ""',
        'target_project_root: "."',
        'spec_root: ""',
        'feature_root: ""',
        'resolution_source: ""',
        "index_status: missing",
        "referenced_spec_ids: []",
        "pending_proposals: []",
        "lifecycle_status: active",
        "skip_log: []",
        "delegation:",
        "default_mode: current_context",
        "ask_on_parallel_stage: true",
        "ask_on_assistive_node: true",
        "node_overrides: {}",
        "warnings: []",
        "parallel_subagent",
        "gate_check_subagent",
        "ship-verify.backend-contract: assistive_subagent",
        "scenario: \"\"",
        "project_scope: fullstack",
    ):
        require(snippet in text, f"{path}: missing `{snippet}`")


def validate_protocol_doc() -> None:
    path = ROOT / "skills/ship-orchestrator/_templates/protocol/workflow-protocol.md"
    text = read_text(path)
    require("## 2. Macro Stage View" in text, f"{path}: missing macro stage section")
    require("## 7. Delegation Contract" in text, f"{path}: missing delegation section")
    require("## 8. Spec Hook Contract" in text, f"{path}: missing spec hook section")
    require(
        "macro_stage.next_user_decision" in text,
        f"{path}: missing next_user_decision references",
    )
    require("`ship-spec` 是 workflow utility" in text, f"{path}: missing ship-spec utility wording")
    require("Project Resolution Contract" in text, f"{path}: missing project resolution section")
    require(".docs/ship/project.yml" in text, f"{path}: missing project config contract")
    require("spec_context" in text, f"{path}: missing spec_context references")
    require("target_project_id" in text, f"{path}: missing target_project_id references")
    require("target_project_root" in text, f"{path}: missing target_project_root references")
    require("feature_root" in text, f"{path}: missing feature_root references")
    require("resolution_source" in text, f"{path}: missing resolution_source references")
    require("skip_log" in text, f"{path}: missing skip_log references")
    require("lifecycle_status" in text, f"{path}: missing lifecycle_status references")
    require("scenario" in text, f"{path}: missing scenario references")
    require("parallel_owned_outputs" in text, f"{path}: missing delegation mode wording")
    require("parallel_subagent" in text, f"{path}: missing parallel_subagent wording")
    require("gate_check_switchable" in text, f"{path}: missing hard-gate execution mode wording")
    require("gate_check_subagent" in text, f"{path}: missing gate_check_subagent wording")
    require("Delegation Modes` 是节点能力分类" in text or "Delegation Modes` 是节点能力分类，不是 `node_overrides` 的直接取值" in text, f"{path}: missing node_overrides semantics wording")
    for snippet in (
        "先读取 `node_overrides[stage]`",
        "若 override 缺失或不适用，再读取 `delegation.default_mode`",
        "`assistive_subagent` -> `gate_check_subagent`",
        "`parallel_subagent` -> 对 hard gate 无效",
        "记录 warning 后回退到 `default_mode`",
        "在三个 hard gate 节点，映射为 `gate_check_subagent`",
        "只有 `node_overrides[node_id] = parallel_subagent` 时才自动启动子代理",
        "`ask_on_assistive_node = false`",
        "delegation.warnings",
        "canonical `node_id`",
        "ship-build.read-next-task",
        "ship-verify.backend-contract",
        "只有无法确定 `target project` 时才阻塞",
        "target project `spec_root`",
        "归一化到 `target_project_root` 相对路径",
    ):
        require(snippet in text, f"{path}: missing `{snippet}`")
    for node_id in CANONICAL_DELEGATION_NODES:
        require(node_id in text, f"{path}: missing canonical node_id `{node_id}` from runtime registry")
    require("单 `DOING`" in text, f"{path}: missing build delegation constraint")
    for stage in CANONICAL_STAGE_ORDER:
        macro = macro_stage_for(stage)
        row = f"| `{macro.current}` | `{macro.label}` |"
        require(row in text, f"{path}: missing macro row for {macro.current}/{macro.label}")
    require("5 个大阶段" in text or "五个大阶段" in text, f"{path}: missing 5-stage wording")
    require("4 个大阶段" not in text and "4 大阶段" not in text, f"{path}: contains legacy 4-stage wording")


def validate_readmes() -> None:
    workflow_readme_paths = [
        ROOT / "README.md",
        ROOT / "skills/README.md",
    ]
    for path in workflow_readme_paths:
        text = read_text(path)
        require("Discover" in text and "Define" in text and "Design" in text and "Build" in text and "Close" in text, f"{path}: missing 5-stage view")
        require("ship-spec" in text, f"{path}: missing ship-spec mention")
        require(".docs/ship/project.yml" in text or "project.yml.template" in text, f"{path}: missing project-local spec config wording")
        require("4 个大阶段" not in text and "4 大阶段" not in text, f"{path}: contains legacy 4-stage wording")

    templates_readme = ROOT / "skills/ship-orchestrator/_templates/README.md"
    templates_text = read_text(templates_readme)
    for snippet in ("meta.yml.template", "review.md.template", "workflow-protocol.md", "spec_context", "delegation", "project.yml.template", "project_root", "spec_root", "feature_root", "project_level_only"):
        require(snippet in templates_text, f"{templates_readme}: missing `{snippet}`")
    require((ROOT / "skills/ship-orchestrator/_templates/project/project.yml.template").exists(), "missing _templates/project/project.yml.template")

    agents_meta = ROOT / "skills/agents/openai.yaml"
    agents_text = read_text(agents_meta)
    for snippet in (
        "entrypoint: ship-orchestrator",
        "validate_workflow_docs.py",
        "workflow_doctor.py",
        "build_task_preflight.py",
    ):
        require(snippet in agents_text, f"{agents_meta}: missing `{snippet}`")

    regression_prompts = ROOT / "skills/ship-orchestrator/tests/regression-prompts.md"
    regression_text = read_text(regression_prompts)
    for snippet in (
        "Unsigned Gate",
        "Requirements Quality",
        "Delivery Plan DAG",
        "Build Preflight",
        "Handoff Evidence",
    ):
        require(snippet in regression_text, f"{regression_prompts}: missing `{snippet}`")


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


def validate_stage_delegation_boundaries() -> None:
    stage_skill_paths = [
        ROOT / "skills/ship-define/SKILL.md",
        ROOT / "skills/ship-define-review/SKILL.md",
        ROOT / "skills/ship-tech-discovery/SKILL.md",
        ROOT / "skills/ship-contract/SKILL.md",
        ROOT / "skills/ship-frontend-design/SKILL.md",
        ROOT / "skills/ship-backend-design/SKILL.md",
        ROOT / "skills/ship-design-review/SKILL.md",
        ROOT / "skills/ship-delivery-plan/SKILL.md",
        ROOT / "skills/ship-plan-review/SKILL.md",
        ROOT / "skills/ship-build/SKILL.md",
        ROOT / "skills/ship-verify/SKILL.md",
        ROOT / "skills/ship-handoff/SKILL.md",
    ]
    for path in stage_skill_paths:
        text = read_text(path)
        require("## Delegation Boundary" in text, f"{path}: missing `## Delegation Boundary`")

    forbidden_stage_expectations = {
        ROOT / "skills/ship-contract/SKILL.md": "禁止启动任何子代理",
        ROOT / "skills/ship-delivery-plan/SKILL.md": "禁止启动任何子代理",
    }
    for path, snippet in forbidden_stage_expectations.items():
        text = read_text(path)
        require(snippet in text, f"{path}: missing `{snippet}`")

    assistive_only_expectations = {
        ROOT / "skills/ship-define/SKILL.md": "不直接编辑 `requirements.md` 正文或 frontmatter",
        ROOT / "skills/ship-tech-discovery/SKILL.md": "不直接编辑 `tech-research.md` / `tech-selection.md` 正文或 frontmatter",
        ROOT / "skills/ship-build/SKILL.md": "不直接编辑正式 plan / 代码任务记录的 canonical 状态或正文",
        ROOT / "skills/ship-verify/SKILL.md": "不直接编辑 `verification.md` 正文或 frontmatter",
        ROOT / "skills/ship-handoff/SKILL.md": "不直接编辑 `handoff.md` / `verification.md` 正文或 frontmatter",
    }
    for path, snippet in assistive_only_expectations.items():
        text = read_text(path)
        require(snippet in text, f"{path}: missing `{snippet}`")

    parallel_owned_expectations = {
        ROOT / "skills/ship-frontend-design/SKILL.md": "`assistive_subagent` 在本阶段无效",
        ROOT / "skills/ship-backend-design/SKILL.md": "`assistive_subagent` 在本阶段无效",
    }
    for path, snippet in parallel_owned_expectations.items():
        text = read_text(path)
        require(snippet in text, f"{path}: missing `{snippet}`")

    build_text = read_text(ROOT / "skills/ship-build/SKILL.md")
    for node_id in sorted(node_id for node_id in CANONICAL_DELEGATION_NODES if node_id.startswith("ship-build.")):
        require(node_id in build_text, f"ship-build/SKILL.md: missing runtime node_id `{node_id}`")

    verify_text = read_text(ROOT / "skills/ship-verify/SKILL.md")
    for node_id in sorted(node_id for node_id in CANONICAL_DELEGATION_NODES if node_id.startswith("ship-verify.")):
        require(node_id in verify_text, f"ship-verify/SKILL.md: missing runtime node_id `{node_id}`")

    handoff_text = read_text(ROOT / "skills/ship-handoff/SKILL.md")
    for node_id in sorted(node_id for node_id in CANONICAL_DELEGATION_NODES if node_id.startswith("ship-handoff.")):
        require(node_id in handoff_text, f"ship-handoff/SKILL.md: missing runtime node_id `{node_id}`")

    gate_skill_paths = [
        ROOT / "skills/ship-define-review/SKILL.md",
        ROOT / "skills/ship-design-review/SKILL.md",
        ROOT / "skills/ship-plan-review/SKILL.md",
    ]
    for path in gate_skill_paths:
        text = read_text(path)
        for snippet in (
            "由 orchestrator 基于 delegation 配置决定",
            "gate_check_subagent",
            "`node_overrides[",
            "`assistive_subagent` 在本阶段解释为 `gate_check_subagent`",
            "`parallel_subagent` 在本阶段无效",
            "`review_status` 必须保持 `pending`",
            "`user_sign_off`、`signed_at` 必须保持为空",
            "主代理必须重新读取正式草案",
            "只有主代理可以把 `review_status` 改成",
        ):
            require(snippet in text, f"{path}: missing `{snippet}`")

    # Scope-aware adapters must exist for the stages that vary by project_scope.
    scope_adapted_paths = {
        ROOT / "skills/ship-design-review/SKILL.md",
        ROOT / "skills/ship-delivery-plan/SKILL.md",
        ROOT / "skills/ship-plan-review/SKILL.md",
        ROOT / "skills/ship-verify/SKILL.md",
    }
    for path in scope_adapted_paths:
        require("## Scope Adaptation" in read_text(path), f"{path}: missing `## Scope Adaptation`")


def validate_review_template_delegation() -> None:
    path = ROOT / "skills/ship-orchestrator/_templates/review/review.md.template"
    text = read_text(path)
    for snippet in (
        "子代理起草正式草案时必须保持 pending",
        "子代理起草时必须为空",
        "由主代理填写",
        "frontmatter 中的 `review_status` 必须仍为 `pending`",
        "子代理起草正式 gate 草案时",
        "required_changes",
        "fix_owner",
    ):
        require(snippet in text, f"{path}: missing `{snippet}`")

    reference_path = ROOT / "skills/ship-orchestrator/_templates/review/review-gate-reference.md"
    reference_text = read_text(reference_path)
    for snippet in (
        "Review Gate Reference",
        "required_changes",
        "fix_owner",
        "Decision Rules",
        "user_sign_off",
        "signed_at",
    ):
        require(snippet in reference_text, f"{reference_path}: missing `{snippet}`")


def validate_orchestrator_doc() -> None:
    path = ROOT / "skills/ship-orchestrator/SKILL.md"
    text = read_text(path)
    require("meta.yml.macro_stage" in text, f"{path}: missing meta.yml.macro_stage")
    require("macro_stage.next_user_decision" in text, f"{path}: missing next_user_decision sync")
    require("Define → Design → Build → Close" in text, f"{path}: missing default stage sequence")
    require("ship-spec" in text, f"{path}: missing ship-spec utility references")
    require("spec_context" in text, f"{path}: missing spec_context references")
    require(".docs/ship/project.yml" in text, f"{path}: missing target project config references")
    require("target project" in text, f"{path}: missing target project wording")
    require("delegation" in text, f"{path}: missing delegation references")
    require("ship-build 正式任务保持单 `DOING`" in text, f"{path}: missing build delegation wording")
    require("parallel_subagent" in text, f"{path}: missing parallel_subagent wording")
    require("gate_check_switchable" in text, f"{path}: missing gate_check_switchable wording")
    require("gate_check_subagent" in text, f"{path}: missing gate_check_subagent wording")
    for snippet in (
        "先读 `node_overrides[stage]`，再读 `default_mode`，最后回退 `current_context`",
        "`assistive_subagent` 解释为 `gate_check_subagent`",
        "`parallel_subagent` 是无效值；记录 warning 后回退",
        "三个 hard gate 的执行方式复用 `node_overrides` 与 `default_mode`",
        "canonical `node_id`",
        "`assistive_subagent` 不得在 `parallel_owned_outputs` 节点上被解释成 `parallel_subagent`",
        "ask_on_assistive_node",
        "delegation.warnings",
        "ship-verify.backend-contract",
        "负责 project resolution",
        "NEW_FEATURE / CONTINUE_FEATURE / `sync-spec` 都以 target project 为边界",
        "feature_root",
    ):
        require(snippet in text, f"{path}: missing `{snippet}`")
    require("5 个大阶段" in text or "五个大阶段" in text, f"{path}: missing 5-stage wording")
    require("14 个内部阶段名" in text, f"{path}: missing 14-stage wording")


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
        ".docs/ship/project.yml",
        "--project-config",
        "target project",
        "project_level_only",
    ):
        require(snippet in text, f"{path}: missing `{snippet}`")
    require("不是 canonical stage" in text, f"{path}: missing non-stage wording")
    require("ship-handoff" in text, f"{path}: missing handoff proposal wording")


def validate_project_local_stage_docs() -> None:
    expectations = {
        ROOT / "skills/ship-tech-discovery/SKILL.md": (
            "target project `spec_root`",
            "target project 未明确，不允许进入 `selection`",
        ),
        ROOT / "skills/ship-frontend-design/SKILL.md": (
            "target project `spec_root`",
            "不读取父目录或其他项目 spec",
        ),
        ROOT / "skills/ship-backend-design/SKILL.md": (
            "target project `spec_root`",
            "不读取父目录或其他项目 spec",
        ),
        ROOT / "skills/ship-build/SKILL.md": (
            "target project `spec_root`",
            "相对 `target_project_root` 的路径",
        ),
        ROOT / "skills/ship-handoff/SKILL.md": (
            "target project `spec_root`",
            "spec_context.warnings",
        ),
    }
    for path, snippets in expectations.items():
        text = read_text(path)
        for snippet in snippets:
            require(snippet in text, f"{path}: missing `{snippet}`")


def validate_stage_map_script() -> None:
    require(len(CANONICAL_STAGE_ORDER) == 14, "stage map: expected 14 canonical stages (incl. ship-discover / ship-shape)")
    for stage in CANONICAL_STAGE_ORDER:
        macro = macro_stage_for(stage)
        require(macro.current in {"discover", "define", "design", "build", "close"}, f"invalid macro current for {stage}")
        require(macro.label in {"Discover", "Define", "Design", "Build", "Close"}, f"invalid macro label for {stage}")


def validate_root_readme_commands() -> None:
    path = ROOT / "README.md"
    text = read_text(path)
    require("ship-orchestrator" in text, f"{path}: missing ship-orchestrator entry")
    require("5 大阶段" in text or "五个大阶段" in text, f"{path}: missing 5-stage wording")
    require("feature_meta_runtime.py" in text, f"{path}: missing feature_meta_runtime helper command")
    require("spec_runtime.py" in text, f"{path}: missing spec_runtime helper command")
    require("--project-config" in text, f"{path}: missing project-config helper examples")
    require(".docs/ship/project.yml" in text, f"{path}: missing project config example")
    require("14 个 canonical" in text or "14 个内部阶段名" in text or "14 个阶段" in text, f"{path}: missing 14-stage wording")


def main() -> int:
    validators = [
        validate_stage_map_script,
        validate_meta_template,
        validate_protocol_doc,
        validate_readmes,
        validate_stage_reference_templates,
        validate_stage_delegation_boundaries,
        validate_review_template_delegation,
        validate_orchestrator_doc,
        validate_ship_spec_doc,
        validate_project_local_stage_docs,
        validate_root_readme_commands,
    ]
    for validator in validators:
        validator()
    print("workflow docs validation: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
