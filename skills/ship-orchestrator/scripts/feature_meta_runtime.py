#!/usr/bin/env python3
"""Runtime helpers for ship feature meta files.

This script provides the minimum executable behavior needed to keep
`macro_stage` and delegation metadata in sync during feature creation
and resume flows.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[2]
sys.path.insert(0, str(SCRIPT_DIR))

from spec_runtime import (  # noqa: E402
    VALID_STAGE_HOOKS,
    VALID_WORKSPACE_MODES,
    WorkspaceSpecContext,
    build_explicit_workspace_context,
    load_project_context,
    locate_project_config,
    resolve_specs,
)
from workflow_stage_map import CANONICAL_STAGE_ORDER, stage_view_for  # noqa: E402


META_TEMPLATE_PATH = ROOT / "skills/ship-orchestrator/_templates/meta/meta.yml.template"
RAW_PRD_INBOX_TEMPLATE_PATH = (
    ROOT / "skills/ship-orchestrator/_templates/requirements/raw-prd-inbox.md.template"
)
RESOURCE_README_TEMPLATE_PATH = (
    ROOT / "skills/ship-orchestrator/_templates/resource/README.md.template"
)

CURRENT_CONTEXT = "current_context"
ASSISTIVE_SUBAGENT = "assistive_subagent"
PARALLEL_SUBAGENT = "parallel_subagent"
GATE_CHECK_SUBAGENT = "gate_check_subagent"

FORBIDDEN = "forbidden"
GATE_CHECK_SWITCHABLE = "gate_check_switchable"
PARALLEL_OWNED_OUTPUTS = "parallel_owned_outputs"
ASSISTIVE_ONLY = "assistive_only"

ASK_ON_PARALLEL_STAGE = "ask_on_parallel_stage"
ASK_ON_ASSISTIVE_NODE = "ask_on_assistive_node"

VALID_EXECUTION_MODES: tuple[str, ...] = (
    CURRENT_CONTEXT,
    ASSISTIVE_SUBAGENT,
    PARALLEL_SUBAGENT,
    GATE_CHECK_SUBAGENT,
)
VALID_DEFAULT_MODES: tuple[str, ...] = (
    CURRENT_CONTEXT,
    ASSISTIVE_SUBAGENT,
)
VALID_DELEGATION_MODES: tuple[str, ...] = (
    FORBIDDEN,
    GATE_CHECK_SWITCHABLE,
    PARALLEL_OWNED_OUTPUTS,
    ASSISTIVE_ONLY,
)

VALID_PROJECT_SCOPES: tuple[str, ...] = ("fullstack", "backend_only", "frontend_only")
VALID_SCENARIOS: tuple[str, ...] = (
    "greenfield",
    "product_provided",
    "prd_direct",
    "evolve",
    "technical_plan_provided",
)
DISCOVER_SCENARIOS: frozenset[str] = frozenset({"greenfield", "evolve"})
DEFINE_SCENARIOS: frozenset[str] = frozenset({"product_provided", "prd_direct"})
TECHNICAL_PLAN_SCENARIOS: frozenset[str] = frozenset({"technical_plan_provided"})
VALID_LIFECYCLE_STATUSES: tuple[str, ...] = ("active", "blocked", "completed", "abandoned")
AWAITING_MATERIALS = "awaiting_materials"
IGNORED_PROJECT_CANDIDATE_DIRS: frozenset[str] = frozenset(
    {
        ".docs",
        ".git",
        ".idea",
        ".vscode",
        "__pycache__",
        "build",
        "coverage",
        "dist",
        "node_modules",
        "target",
        "tmp",
        "vendor",
    }
)

SCOPE_SKIP_MAP: dict[str, list[str]] = {
    "fullstack": [],
    "backend_only": ["ship-shape", "ship-frontend-design"],
    "frontend_only": ["ship-backend-design"],
}


@dataclass(frozen=True)
class DelegationNodeSpec:
    node_id: str
    delegation_mode: str
    ask_flag: str | None
    allowed_execution_modes: tuple[str, ...]


CANONICAL_DELEGATION_NODES: dict[str, DelegationNodeSpec] = {
    "ship-discover": DelegationNodeSpec(
        node_id="ship-discover",
        delegation_mode=ASSISTIVE_ONLY,
        ask_flag=ASK_ON_ASSISTIVE_NODE,
        allowed_execution_modes=(CURRENT_CONTEXT, ASSISTIVE_SUBAGENT),
    ),
    "ship-shape": DelegationNodeSpec(
        node_id="ship-shape",
        delegation_mode=ASSISTIVE_ONLY,
        ask_flag=ASK_ON_ASSISTIVE_NODE,
        allowed_execution_modes=(CURRENT_CONTEXT, ASSISTIVE_SUBAGENT),
    ),
    "ship-define": DelegationNodeSpec(
        node_id="ship-define",
        delegation_mode=ASSISTIVE_ONLY,
        ask_flag=ASK_ON_ASSISTIVE_NODE,
        allowed_execution_modes=(CURRENT_CONTEXT, ASSISTIVE_SUBAGENT),
    ),
    "ship-define-review": DelegationNodeSpec(
        node_id="ship-define-review",
        delegation_mode=GATE_CHECK_SWITCHABLE,
        ask_flag=None,
        allowed_execution_modes=(CURRENT_CONTEXT, GATE_CHECK_SUBAGENT),
    ),
    "ship-tech-discovery.research": DelegationNodeSpec(
        node_id="ship-tech-discovery.research",
        delegation_mode=ASSISTIVE_ONLY,
        ask_flag=ASK_ON_ASSISTIVE_NODE,
        allowed_execution_modes=(CURRENT_CONTEXT, ASSISTIVE_SUBAGENT),
    ),
    "ship-tech-discovery.selection": DelegationNodeSpec(
        node_id="ship-tech-discovery.selection",
        delegation_mode=FORBIDDEN,
        ask_flag=None,
        allowed_execution_modes=(CURRENT_CONTEXT,),
    ),
    "ship-contract": DelegationNodeSpec(
        node_id="ship-contract",
        delegation_mode=FORBIDDEN,
        ask_flag=None,
        allowed_execution_modes=(CURRENT_CONTEXT,),
    ),
    "ship-frontend-design": DelegationNodeSpec(
        node_id="ship-frontend-design",
        delegation_mode=PARALLEL_OWNED_OUTPUTS,
        ask_flag=ASK_ON_PARALLEL_STAGE,
        allowed_execution_modes=(CURRENT_CONTEXT, PARALLEL_SUBAGENT),
    ),
    "ship-backend-design": DelegationNodeSpec(
        node_id="ship-backend-design",
        delegation_mode=PARALLEL_OWNED_OUTPUTS,
        ask_flag=ASK_ON_PARALLEL_STAGE,
        allowed_execution_modes=(CURRENT_CONTEXT, PARALLEL_SUBAGENT),
    ),
    "ship-design-review": DelegationNodeSpec(
        node_id="ship-design-review",
        delegation_mode=GATE_CHECK_SWITCHABLE,
        ask_flag=None,
        allowed_execution_modes=(CURRENT_CONTEXT, GATE_CHECK_SUBAGENT),
    ),
    "ship-delivery-plan": DelegationNodeSpec(
        node_id="ship-delivery-plan",
        delegation_mode=FORBIDDEN,
        ask_flag=None,
        allowed_execution_modes=(CURRENT_CONTEXT,),
    ),
    "ship-plan-review": DelegationNodeSpec(
        node_id="ship-plan-review",
        delegation_mode=GATE_CHECK_SWITCHABLE,
        ask_flag=None,
        allowed_execution_modes=(CURRENT_CONTEXT, GATE_CHECK_SUBAGENT),
    ),
    "ship-build.read-next-task": DelegationNodeSpec(
        node_id="ship-build.read-next-task",
        delegation_mode=ASSISTIVE_ONLY,
        ask_flag=ASK_ON_ASSISTIVE_NODE,
        allowed_execution_modes=(CURRENT_CONTEXT, ASSISTIVE_SUBAGENT),
    ),
    "ship-build.spec-scan": DelegationNodeSpec(
        node_id="ship-build.spec-scan",
        delegation_mode=ASSISTIVE_ONLY,
        ask_flag=ASK_ON_ASSISTIVE_NODE,
        allowed_execution_modes=(CURRENT_CONTEXT, ASSISTIVE_SUBAGENT),
    ),
    "ship-build.env-precheck": DelegationNodeSpec(
        node_id="ship-build.env-precheck",
        delegation_mode=ASSISTIVE_ONLY,
        ask_flag=ASK_ON_ASSISTIVE_NODE,
        allowed_execution_modes=(CURRENT_CONTEXT, ASSISTIVE_SUBAGENT),
    ),
    "ship-build.evidence-pack": DelegationNodeSpec(
        node_id="ship-build.evidence-pack",
        delegation_mode=ASSISTIVE_ONLY,
        ask_flag=ASK_ON_ASSISTIVE_NODE,
        allowed_execution_modes=(CURRENT_CONTEXT, ASSISTIVE_SUBAGENT),
    ),
    "ship-verify.backend-unit": DelegationNodeSpec(
        node_id="ship-verify.backend-unit",
        delegation_mode=ASSISTIVE_ONLY,
        ask_flag=ASK_ON_ASSISTIVE_NODE,
        allowed_execution_modes=(CURRENT_CONTEXT, ASSISTIVE_SUBAGENT),
    ),
    "ship-verify.backend-integration": DelegationNodeSpec(
        node_id="ship-verify.backend-integration",
        delegation_mode=ASSISTIVE_ONLY,
        ask_flag=ASK_ON_ASSISTIVE_NODE,
        allowed_execution_modes=(CURRENT_CONTEXT, ASSISTIVE_SUBAGENT),
    ),
    "ship-verify.backend-contract": DelegationNodeSpec(
        node_id="ship-verify.backend-contract",
        delegation_mode=ASSISTIVE_ONLY,
        ask_flag=ASK_ON_ASSISTIVE_NODE,
        allowed_execution_modes=(CURRENT_CONTEXT, ASSISTIVE_SUBAGENT),
    ),
    "ship-verify.frontend-component": DelegationNodeSpec(
        node_id="ship-verify.frontend-component",
        delegation_mode=ASSISTIVE_ONLY,
        ask_flag=ASK_ON_ASSISTIVE_NODE,
        allowed_execution_modes=(CURRENT_CONTEXT, ASSISTIVE_SUBAGENT),
    ),
    "ship-verify.frontend-e2e": DelegationNodeSpec(
        node_id="ship-verify.frontend-e2e",
        delegation_mode=ASSISTIVE_ONLY,
        ask_flag=ASK_ON_ASSISTIVE_NODE,
        allowed_execution_modes=(CURRENT_CONTEXT, ASSISTIVE_SUBAGENT),
    ),
    "ship-handoff.ac-evidence": DelegationNodeSpec(
        node_id="ship-handoff.ac-evidence",
        delegation_mode=ASSISTIVE_ONLY,
        ask_flag=ASK_ON_ASSISTIVE_NODE,
        allowed_execution_modes=(CURRENT_CONTEXT, ASSISTIVE_SUBAGENT),
    ),
    "ship-handoff.deploy-materials": DelegationNodeSpec(
        node_id="ship-handoff.deploy-materials",
        delegation_mode=ASSISTIVE_ONLY,
        ask_flag=ASK_ON_ASSISTIVE_NODE,
        allowed_execution_modes=(CURRENT_CONTEXT, ASSISTIVE_SUBAGENT),
    ),
    "ship-handoff.spec-proposals": DelegationNodeSpec(
        node_id="ship-handoff.spec-proposals",
        delegation_mode=ASSISTIVE_ONLY,
        ask_flag=ASK_ON_ASSISTIVE_NODE,
        allowed_execution_modes=(CURRENT_CONTEXT, ASSISTIVE_SUBAGENT),
    ),
}

PARALLEL_OWNED_NODE_IDS = frozenset(
    node_id
    for node_id, spec in CANONICAL_DELEGATION_NODES.items()
    if spec.delegation_mode == PARALLEL_OWNED_OUTPUTS
)
ASSISTIVE_ONLY_NODE_IDS = frozenset(
    node_id
    for node_id, spec in CANONICAL_DELEGATION_NODES.items()
    if spec.delegation_mode == ASSISTIVE_ONLY
)
HARD_GATE_NODE_IDS = frozenset(
    node_id
    for node_id, spec in CANONICAL_DELEGATION_NODES.items()
    if spec.delegation_mode == GATE_CHECK_SWITCHABLE
)


def iso_now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def load_meta(meta_path: Path) -> dict:
    with meta_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{meta_path} does not contain a YAML mapping")
    migrate_legacy_stage_names(data)
    return data


# ship-intake / ship-intake-review 已于改名为 ship-define / ship-define-review。
# 旧 feature 目录的 meta.yml 仍可能写着旧 stage id，这里做读时迁移以保持兼容。
LEGACY_STAGE_RENAMES: dict[str, str] = {
    "ship-intake": "ship-define",
    "ship-intake-review": "ship-define-review",
}


def migrate_legacy_stage_names(data: dict) -> bool:
    changed = False

    current_stage = data.get("current_stage")
    if isinstance(current_stage, str) and current_stage in LEGACY_STAGE_RENAMES:
        data["current_stage"] = LEGACY_STAGE_RENAMES[current_stage]
        changed = True

    stages = data.get("stages")
    if isinstance(stages, dict):
        for legacy_id, new_id in LEGACY_STAGE_RENAMES.items():
            if legacy_id in stages and new_id not in stages:
                stages[new_id] = stages.pop(legacy_id)
                changed = True
            elif legacy_id in stages:
                # 已有新键时舍弃旧键，避免重复
                stages.pop(legacy_id)
                changed = True

    delegation = data.get("delegation")
    if isinstance(delegation, dict):
        node_overrides = delegation.get("node_overrides")
        if isinstance(node_overrides, dict):
            for legacy_id, new_id in LEGACY_STAGE_RENAMES.items():
                if legacy_id in node_overrides and new_id not in node_overrides:
                    node_overrides[new_id] = node_overrides.pop(legacy_id)
                    changed = True
                elif legacy_id in node_overrides:
                    node_overrides.pop(legacy_id)
                    changed = True

    return changed


def save_meta(meta_path: Path, data: dict) -> None:
    with meta_path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(data, handle, allow_unicode=False, sort_keys=False)


def ensure_macro_stage(data: dict) -> dict:
    current_stage = data.get("current_stage")
    if not current_stage:
        raise ValueError("meta.yml missing current_stage")

    stage_view = stage_view_for(current_stage)
    macro_stage = data.setdefault("macro_stage", {})
    macro_stage["current"] = stage_view.macro.current
    macro_stage["label"] = stage_view.macro.label
    macro_stage["summary"] = stage_view.summary
    macro_stage["next_user_decision"] = stage_view.next_user_decision
    data["updated_at"] = iso_now()
    return data


def ensure_spec_context(data: dict) -> dict:
    spec_context = data.setdefault("spec_context", {})
    spec_context.setdefault("workspace_mode", "")
    spec_context.setdefault("workspace_name", "")
    spec_context.setdefault("spec_root", "")
    spec_context.setdefault("feature_root", "")
    spec_context.setdefault("resolution_source", "")
    spec_context.setdefault("index_status", "missing")
    spec_context.setdefault("last_checked_at", "")
    spec_context.setdefault("last_checked_stage", "")
    spec_context.setdefault("referenced_spec_ids", [])
    spec_context.setdefault("warnings", [])
    spec_context.setdefault("pending_proposals", [])
    return data


def ensure_delegation(data: dict) -> dict:
    delegation = data.setdefault("delegation", {})
    delegation.setdefault("default_mode", CURRENT_CONTEXT)
    delegation.setdefault("ask_on_parallel_stage", True)
    delegation.setdefault("ask_on_assistive_node", True)
    delegation.setdefault("node_overrides", {})
    delegation.setdefault("warnings", [])
    return data


def ensure_skip_log(data: dict) -> dict:
    skip_log = data.setdefault("skip_log", [])
    if not isinstance(skip_log, list):
        raise ValueError("skip_log must be a list")
    return data


def ensure_lifecycle_status(data: dict) -> dict:
    lifecycle_status = data.setdefault("lifecycle_status", "active")
    if lifecycle_status not in VALID_LIFECYCLE_STATUSES:
        raise ValueError(f"invalid lifecycle_status: {lifecycle_status}")
    return data


def delegation_node_spec(node_id: str) -> DelegationNodeSpec:
    try:
        return CANONICAL_DELEGATION_NODES[node_id]
    except KeyError as exc:
        raise ValueError(f"unknown delegation node_id: {node_id}") from exc


def _normalize_delegation_config(delegation: dict | None) -> dict:
    if delegation is None:
        raw: dict = {}
    elif isinstance(delegation, dict):
        raw = delegation
    else:
        raise ValueError("delegation config must be a mapping")

    node_overrides = raw.get("node_overrides") or {}
    warnings = raw.get("warnings") or []
    if not isinstance(node_overrides, dict):
        raise ValueError("delegation.node_overrides must be a mapping")
    if not isinstance(warnings, list):
        raise ValueError("delegation.warnings must be a list")

    return {
        "default_mode": raw.get("default_mode", CURRENT_CONTEXT),
        ASK_ON_PARALLEL_STAGE: bool(raw.get(ASK_ON_PARALLEL_STAGE, True)),
        ASK_ON_ASSISTIVE_NODE: bool(raw.get(ASK_ON_ASSISTIVE_NODE, True)),
        "node_overrides": dict(node_overrides),
        "warnings": list(warnings),
    }


def _resolution_payload(
    node_id: str,
    requested_mode: str | None,
    resolved_mode: str | None,
    used_override: bool,
    should_ask_user: bool,
    warning_reason: str | None,
) -> dict:
    return {
        "node_id": node_id,
        "requested_mode": requested_mode,
        "resolved_mode": resolved_mode,
        "used_override": used_override,
        "should_ask_user": should_ask_user,
        "warning_reason": warning_reason,
    }


def _resolve_forbidden(node_id: str, requested_mode: str | None, used_override: bool) -> dict:
    if requested_mode is None:
        return _resolution_payload(
            node_id=node_id,
            requested_mode=None,
            resolved_mode=CURRENT_CONTEXT,
            used_override=False,
            should_ask_user=False,
            warning_reason=None,
        )
    return _resolution_payload(
        node_id=node_id,
        requested_mode=requested_mode,
        resolved_mode=CURRENT_CONTEXT,
        used_override=used_override,
        should_ask_user=False,
        warning_reason=f"{node_id} forbids delegation and always falls back to current_context",
    )


def _resolve_parallel_owned(node_id: str, config: dict, override_mode: str | None) -> dict:
    if override_mode is not None:
        if override_mode in (CURRENT_CONTEXT, PARALLEL_SUBAGENT):
            return _resolution_payload(
                node_id=node_id,
                requested_mode=override_mode,
                resolved_mode=override_mode,
                used_override=True,
                should_ask_user=False,
                warning_reason=None,
            )
        return _resolution_payload(
            node_id=node_id,
            requested_mode=override_mode,
            resolved_mode=CURRENT_CONTEXT,
            used_override=True,
            should_ask_user=False,
            warning_reason=(
                f"{node_id} only accepts current_context or parallel_subagent overrides"
            ),
        )

    if config[ASK_ON_PARALLEL_STAGE]:
        return _resolution_payload(
            node_id=node_id,
            requested_mode=None,
            resolved_mode=None,
            used_override=False,
            should_ask_user=True,
            warning_reason=None,
        )

    default_mode = config["default_mode"]
    if default_mode == CURRENT_CONTEXT:
        return _resolution_payload(
            node_id=node_id,
            requested_mode=CURRENT_CONTEXT,
            resolved_mode=CURRENT_CONTEXT,
            used_override=False,
            should_ask_user=False,
            warning_reason=None,
        )

    if default_mode == ASSISTIVE_SUBAGENT:
        return _resolution_payload(
            node_id=node_id,
            requested_mode=ASSISTIVE_SUBAGENT,
            resolved_mode=CURRENT_CONTEXT,
            used_override=False,
            should_ask_user=False,
            warning_reason=(
                f"{node_id} requires an explicit parallel_subagent override when ask_on_parallel_stage is false"
            ),
        )

    return _resolution_payload(
        node_id=node_id,
        requested_mode=str(default_mode),
        resolved_mode=CURRENT_CONTEXT,
        used_override=False,
        should_ask_user=False,
        warning_reason=f"invalid default_mode `{default_mode}` for {node_id}",
    )


def _resolve_assistive_only(node_id: str, config: dict, override_mode: str | None) -> dict:
    if override_mode is not None:
        if override_mode in (CURRENT_CONTEXT, ASSISTIVE_SUBAGENT):
            return _resolution_payload(
                node_id=node_id,
                requested_mode=override_mode,
                resolved_mode=override_mode,
                used_override=True,
                should_ask_user=False,
                warning_reason=None,
            )
        return _resolution_payload(
            node_id=node_id,
            requested_mode=override_mode,
            resolved_mode=CURRENT_CONTEXT,
            used_override=True,
            should_ask_user=False,
            warning_reason=(
                f"{node_id} only accepts current_context or assistive_subagent overrides"
            ),
        )

    if config[ASK_ON_ASSISTIVE_NODE]:
        return _resolution_payload(
            node_id=node_id,
            requested_mode=None,
            resolved_mode=None,
            used_override=False,
            should_ask_user=True,
            warning_reason=None,
        )

    default_mode = config["default_mode"]
    if default_mode in (CURRENT_CONTEXT, ASSISTIVE_SUBAGENT):
        return _resolution_payload(
            node_id=node_id,
            requested_mode=default_mode,
            resolved_mode=default_mode,
            used_override=False,
            should_ask_user=False,
            warning_reason=None,
        )

    return _resolution_payload(
        node_id=node_id,
        requested_mode=str(default_mode),
        resolved_mode=CURRENT_CONTEXT,
        used_override=False,
        should_ask_user=False,
        warning_reason=f"invalid default_mode `{default_mode}` for {node_id}",
    )


def _resolve_gate_check(node_id: str, config: dict, override_mode: str | None) -> dict:
    requested_mode = override_mode if override_mode is not None else config["default_mode"]
    used_override = override_mode is not None

    if requested_mode == CURRENT_CONTEXT:
        resolved_mode = CURRENT_CONTEXT
        warning_reason = None
    elif requested_mode == GATE_CHECK_SUBAGENT:
        resolved_mode = GATE_CHECK_SUBAGENT
        warning_reason = None
    elif requested_mode == ASSISTIVE_SUBAGENT:
        resolved_mode = GATE_CHECK_SUBAGENT
        warning_reason = None
    elif used_override:
        fallback = _resolve_gate_check(node_id, config, None)
        fallback["requested_mode"] = requested_mode
        fallback["used_override"] = True
        fallback["warning_reason"] = (
            f"{node_id} does not accept override `{requested_mode}` and fell back to default_mode"
        )
        return fallback
    else:
        return _resolution_payload(
            node_id=node_id,
            requested_mode=str(requested_mode),
            resolved_mode=CURRENT_CONTEXT,
            used_override=False,
            should_ask_user=False,
            warning_reason=f"invalid default_mode `{requested_mode}` for {node_id}",
        )

    return _resolution_payload(
        node_id=node_id,
        requested_mode=requested_mode,
        resolved_mode=resolved_mode,
        used_override=used_override,
        should_ask_user=False,
        warning_reason=warning_reason,
    )


def resolve_delegation(node_id: str, delegation: dict | None) -> dict:
    spec = delegation_node_spec(node_id)
    config = _normalize_delegation_config(delegation)
    override_mode = config["node_overrides"].get(node_id)

    if spec.delegation_mode == FORBIDDEN:
        return _resolve_forbidden(node_id, override_mode, override_mode is not None)
    if spec.delegation_mode == PARALLEL_OWNED_OUTPUTS:
        return _resolve_parallel_owned(node_id, config, override_mode)
    if spec.delegation_mode == ASSISTIVE_ONLY:
        return _resolve_assistive_only(node_id, config, override_mode)
    if spec.delegation_mode == GATE_CHECK_SWITCHABLE:
        return _resolve_gate_check(node_id, config, override_mode)
    raise ValueError(f"unsupported delegation mode `{spec.delegation_mode}` for {node_id}")


def _ensure_execution_mode_value(execution_mode: str, *, allow_default_only: bool = False) -> None:
    valid_modes = VALID_DEFAULT_MODES if allow_default_only else VALID_EXECUTION_MODES
    if execution_mode not in valid_modes:
        raise ValueError(f"invalid execution mode: {execution_mode}")


def _save_meta_with_updated_at(meta_path: Path, data: dict) -> None:
    data["updated_at"] = iso_now()
    save_meta(meta_path, data)


def record_delegation_warning(
    meta_path: Path,
    node_id: str,
    requested_mode: str | None,
    resolved_mode: str | None,
    reason: str,
) -> dict:
    delegation_node_spec(node_id)
    if not reason:
        raise ValueError("delegation warning reason must be non-empty")

    data = load_meta(meta_path)
    ensure_delegation(data)
    warning = {
        "at": iso_now(),
        "node_id": node_id,
        "requested_mode": requested_mode or "",
        "resolved_mode": resolved_mode or "",
        "reason": reason,
    }
    data["delegation"]["warnings"].append(warning)
    _save_meta_with_updated_at(meta_path, data)
    return warning


def set_node_override(meta_path: Path, node_id: str, execution_mode: str) -> dict:
    delegation_node_spec(node_id)
    _ensure_execution_mode_value(execution_mode)

    data = load_meta(meta_path)
    ensure_delegation(data)
    data["delegation"]["node_overrides"][node_id] = execution_mode
    _save_meta_with_updated_at(meta_path, data)
    return {"node_id": node_id, "execution_mode": execution_mode}


def set_default_delegation_mode(meta_path: Path, default_mode: str) -> dict:
    _ensure_execution_mode_value(default_mode, allow_default_only=True)

    data = load_meta(meta_path)
    ensure_delegation(data)
    data["delegation"]["default_mode"] = default_mode
    _save_meta_with_updated_at(meta_path, data)
    return {"default_mode": default_mode}


def clear_delegation_warning_log(meta_path: Path) -> None:
    data = load_meta(meta_path)
    ensure_delegation(data)
    data["delegation"]["warnings"] = []
    _save_meta_with_updated_at(meta_path, data)


def _feature_root_parts(feature_root: str) -> tuple[str, ...]:
    return tuple(part for part in Path(feature_root).parts if part not in ("", "."))


def feature_dir_for(feature_name: str, workspace_context: WorkspaceSpecContext) -> Path:
    return workspace_context.resolved_feature_root / feature_name


def _sync_workspace_spec_context(spec_context: dict, workspace_context: WorkspaceSpecContext) -> None:
    spec_context["workspace_mode"] = workspace_context.workspace_mode
    spec_context["workspace_name"] = workspace_context.workspace_name
    spec_context["spec_root"] = workspace_context.spec_root
    spec_context["feature_root"] = workspace_context.feature_root
    spec_context["resolution_source"] = workspace_context.resolution_source


def _normalize_feature_projects(
    projects: list[str] | tuple[str, ...] | None,
    workspace_context: WorkspaceSpecContext,
) -> list[str]:
    normalized: list[str] = []
    for project in projects or []:
        if not isinstance(project, str) or not project.strip():
            raise ValueError("projects entries must be non-empty strings")
        name = project.strip()
        if "/" in name or "\\" in name or name in {".", ".."}:
            raise ValueError("projects entries must be first-level directory names")
        if name not in normalized:
            normalized.append(name)

    if workspace_context.workspace_mode == "single_project":
        if normalized:
            raise ValueError("single_project workspace does not accept feature projects")
        return []

    if not normalized:
        raise ValueError(
            "workspace_mode=project_group requires at least one --project before creating feature meta"
        )

    unknown = [project for project in normalized if project not in workspace_context.projects]
    if unknown:
        raise ValueError(
            "feature projects must be declared in .docs/ship/project.yml first: "
            + ", ".join(unknown)
        )
    return normalized


def _resolve_project_context_from_meta(meta_path: Path, data: dict) -> WorkspaceSpecContext:
    spec_context = data.get("spec_context") or {}
    workspace_mode = str(spec_context.get("workspace_mode", "")).strip()
    workspace_name = str(spec_context.get("workspace_name", "")).strip()
    spec_root = str(spec_context.get("spec_root", "")).strip()
    feature_root = str(spec_context.get("feature_root", "")).strip()
    if not workspace_mode or not workspace_name or not spec_root or not feature_root:
        raise ValueError(
            "unable to determine workspace from meta.yml; initialize .docs/ship/project.yml first"
        )

    parts = _feature_root_parts(feature_root)
    feature_dir = meta_path.parent.resolve()
    workspace_root = feature_dir.parent if not parts else feature_dir.parents[len(parts)]
    return build_explicit_workspace_context(
        spec_root=Path(spec_root),
        workspace_root=workspace_root,
        feature_root=Path(feature_root),
        workspace_mode=workspace_mode,
        workspace_name=workspace_name,
        projects=tuple(data.get("projects") or ()),
        resolution_source="meta_spec_context",
    )


def resolve_project_context(
    *,
    project_config: Path | None = None,
    search_from: Path | None = None,
    meta_path: Path | None = None,
    data: dict | None = None,
) -> WorkspaceSpecContext:
    if project_config is not None:
        return load_project_context(project_config)
    if search_from is not None:
        discovered = locate_project_config(search_from)
        if discovered is not None:
            return load_project_context(discovered)
    if meta_path is not None and data is not None:
        return _resolve_project_context_from_meta(meta_path, data)
    raise ValueError("unable to determine workspace; initialize .docs/ship/project.yml first")


def resolve_feature_dir(feature_arg: str, workspace_context: WorkspaceSpecContext) -> Path:
    raw = Path(feature_arg)
    if raw.is_absolute():
        feature_dir = raw.resolve()
    elif raw.parent == Path("."):
        feature_dir = feature_dir_for(raw.name, workspace_context)
    else:
        feature_dir = raw.resolve()

    try:
        feature_dir.relative_to(workspace_context.resolved_feature_root)
    except ValueError as exc:
        raise ValueError(
            f"feature_dir must be inside workspace feature_root `{workspace_context.feature_root}`"
        ) from exc
    return feature_dir


def apply_scope_skips(data: dict) -> None:
    scope = data.get("project_scope", "fullstack")
    stages = data.get("stages", {})
    for stage_id in SCOPE_SKIP_MAP.get(scope, []):
        if stage_id in stages:
            stages[stage_id]["status"] = "skipped"
    delivery_plan = stages.get("ship-delivery-plan")
    if isinstance(delivery_plan, dict):
        if scope == "backend_only":
            delivery_plan["current_part"] = "backend"
        elif scope in {"fullstack", "frontend_only"}:
            delivery_plan["current_part"] = "frontend"


def apply_scenario_initial_state(data: dict, scenario: str) -> None:
    if scenario not in VALID_SCENARIOS:
        raise ValueError(f"invalid scenario: {scenario}")

    stages = data.setdefault("stages", {})
    data["scenario"] = scenario

    discover = stages.setdefault("ship-discover", {})
    shape = stages.setdefault("ship-shape", {})
    define = stages.setdefault("ship-define", {})

    if scenario in DISCOVER_SCENARIOS:
        data["current_stage"] = "ship-discover"
        discover["status"] = "pending"
        discover["discovery_mode"] = scenario
        shape.setdefault("status", "pending")
        define["block_reason"] = ""
        define["generation_mode"] = "interview"
    elif scenario in TECHNICAL_PLAN_SCENARIOS:
        data["current_stage"] = "ship-tech-discovery"
        discover["status"] = "skipped"
        shape["status"] = "skipped"
        define["status"] = "skipped"
        define["block_reason"] = ""
        define["evidence_complete"] = False
        define["generation_mode"] = "technical_plan"
        define_review = stages.setdefault("ship-define-review", {})
        define_review["status"] = "skipped"
        define_review["approved"] = False
        tech_discovery = stages.setdefault("ship-tech-discovery", {})
        tech_discovery["status"] = "pending"
        tech_discovery.setdefault("current_part", "research")
        tech_discovery.setdefault("evidence_complete", False)
        technical_plan_source = data.setdefault("technical_plan_source", {})
        technical_plan_source.setdefault("source_files", [])
        technical_plan_source.setdefault("selection_mode", "")
        technical_plan_source.setdefault("selected_scope", [])
        technical_plan_source.setdefault("pasted_excerpt_file", "")
        technical_plan_source["ignored_source_policy"] = "out_of_scope"
        technical_plan_source["repository_scan_required"] = True
        technical_plan_source.setdefault("repository_scan_status", "pending")
    else:
        data["current_stage"] = "ship-define"
        discover["status"] = "skipped"
        shape["status"] = "skipped"
        define["status"] = "blocked"
        define["block_reason"] = AWAITING_MATERIALS
        define["evidence_complete"] = False
        define["generation_mode"] = "prd_direct" if scenario == "prd_direct" else "interview"


def create_material_intake_files(feature_dir: Path, scenario: str) -> None:
    resource_dir = feature_dir / "resource"
    resource_dir.mkdir(parents=True, exist_ok=True)

    resource_readme_path = resource_dir / "README.md"
    if not resource_readme_path.exists():
        shutil.copyfile(RESOURCE_README_TEMPLATE_PATH, resource_readme_path)

    if scenario in DEFINE_SCENARIOS:
        requirements_path = feature_dir / "requirements.md"
        if not requirements_path.exists():
            shutil.copyfile(RAW_PRD_INBOX_TEMPLATE_PATH, requirements_path)


def _selected_scope_items(
    selected_scopes: list[str] | tuple[str, ...] | None,
    source_files: list[str],
) -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    default_source = source_files[0] if source_files else ""
    for raw_scope in selected_scopes or []:
        if not isinstance(raw_scope, str) or not raw_scope.strip():
            raise ValueError("technical selected scope entries must be non-empty strings")
        label = raw_scope.strip()
        scope_type = "api" if "/" in label and any(method in label.upper() for method in ("GET", "POST", "PUT", "PATCH", "DELETE")) else "section"
        items.append(
            {
                "type": scope_type,
                "label": label,
                "source_file": default_source,
                "locator": "heading" if scope_type == "section" else "api",
            }
        )
    return items


def build_technical_plan_source(
    *,
    source_files: list[str] | tuple[str, ...] | None = None,
    selection_mode: str = "",
    selected_scopes: list[str] | tuple[str, ...] | None = None,
    pasted_excerpt_file: str = "",
) -> dict:
    normalized_source_files = [str(path).strip() for path in source_files or [] if str(path).strip()]
    normalized_selection_mode = selection_mode.strip()
    normalized_pasted_excerpt_file = pasted_excerpt_file.strip()
    if normalized_selection_mode not in ("referenced_sections", "pasted_excerpt"):
        raise ValueError("technical selection mode must be referenced_sections or pasted_excerpt")

    selected_scope = _selected_scope_items(selected_scopes, normalized_source_files)
    return {
        "source_files": normalized_source_files,
        "selection_mode": normalized_selection_mode,
        "selected_scope": selected_scope,
        "pasted_excerpt_file": normalized_pasted_excerpt_file,
        "ignored_source_policy": "out_of_scope",
        "repository_scan_required": True,
        "repository_scan_status": "pending",
    }


def _is_raw_prd_inbox_empty(requirements_path: Path) -> bool:
    if not requirements_path.exists():
        return True

    content = requirements_path.read_text(encoding="utf-8").strip()
    template = RAW_PRD_INBOX_TEMPLATE_PATH.read_text(encoding="utf-8").strip()
    return not content or content == template


def _has_resource_materials(resource_dir: Path) -> bool:
    if not resource_dir.exists():
        return False

    for path in resource_dir.rglob("*"):
        if not path.is_file():
            continue
        if path.relative_to(resource_dir).as_posix() == "README.md":
            continue
        return True
    return False


def has_materials_ready(feature_dir: Path) -> bool:
    return (
        not _is_raw_prd_inbox_empty(feature_dir / "requirements.md")
        or _has_resource_materials(feature_dir / "resource")
    )


def create_feature_meta(
    feature_dir: Path,
    feature_name: str,
    feature_id: str,
    project_context: str,
    project_scope: str = "fullstack",
    project_scope_evidence: str = "",
    scenario: str = "",
    workspace_context: WorkspaceSpecContext | None = None,
    projects: list[str] | tuple[str, ...] | None = None,
    technical_source_files: list[str] | tuple[str, ...] | None = None,
    technical_selection_mode: str = "",
    technical_selected_scopes: list[str] | tuple[str, ...] | None = None,
    technical_pasted_excerpt_file: str = "",
) -> Path:
    if scenario not in VALID_SCENARIOS:
        raise ValueError(f"invalid scenario: {scenario}")
    if project_scope not in VALID_PROJECT_SCOPES:
        raise ValueError(f"invalid project_scope: {project_scope}")
    if project_scope in {"backend_only", "frontend_only"} and not project_scope_evidence.strip():
        raise ValueError(
            "project_scope_evidence is required when project_scope is backend_only or frontend_only"
        )
    if scenario in TECHNICAL_PLAN_SCENARIOS and project_context != "existing_project":
        raise ValueError("technical_plan_provided requires project_context=existing_project")

    technical_plan_source = None
    if scenario in TECHNICAL_PLAN_SCENARIOS:
        technical_plan_source = build_technical_plan_source(
            source_files=technical_source_files,
            selection_mode=technical_selection_mode,
            selected_scopes=technical_selected_scopes,
            pasted_excerpt_file=technical_pasted_excerpt_file,
        )

    feature_projects = (
        _normalize_feature_projects(projects, workspace_context)
        if workspace_context is not None
        else list(projects or [])
    )

    feature_dir.mkdir(parents=True, exist_ok=True)
    create_material_intake_files(feature_dir, scenario)

    meta_path = feature_dir / "meta.yml"
    if not meta_path.exists():
        shutil.copyfile(META_TEMPLATE_PATH, meta_path)

    data = load_meta(meta_path)
    now = iso_now()
    data["feature_name"] = feature_name
    data["feature_id"] = feature_id
    data["created_at"] = data.get("created_at") or now
    data["updated_at"] = now
    data["project_context"] = project_context
    data["project_scope"] = project_scope
    data["project_scope_evidence"] = project_scope_evidence.strip()
    if workspace_context is not None:
        data["workspace_mode"] = workspace_context.workspace_mode
    data["projects"] = feature_projects
    data["lifecycle_status"] = "active"
    if technical_plan_source is not None:
        data["technical_plan_source"] = technical_plan_source
    apply_scenario_initial_state(data, scenario)
    apply_scope_skips(data)
    ensure_macro_stage(data)
    ensure_spec_context(data)
    if workspace_context is not None:
        _sync_workspace_spec_context(data["spec_context"], workspace_context)
    ensure_delegation(data)
    ensure_skip_log(data)
    ensure_lifecycle_status(data)
    save_meta(meta_path, data)
    return meta_path


def mark_materials_ready(meta_path: Path) -> dict:
    feature_dir = meta_path.parent
    data = load_meta(meta_path)
    if data.get("current_stage") != "ship-define":
        raise ValueError("materials can only be marked ready while current_stage is ship-define")

    stages = data.setdefault("stages", {})
    define = stages.setdefault("ship-define", {})
    if define.get("block_reason") != AWAITING_MATERIALS:
        raise ValueError("ship-define is not waiting for materials")

    materials_ready = has_materials_ready(feature_dir)
    if not materials_ready:
        return {
            "materials_ready": False,
            "status": define.get("status", ""),
            "block_reason": define.get("block_reason", ""),
            "message": "requirements.md is still the empty raw PRD template and resource/ has no materials",
        }

    define["status"] = "pending"
    define["block_reason"] = ""
    _save_meta_with_updated_at(meta_path, data)
    return {
        "materials_ready": True,
        "status": define["status"],
        "block_reason": define["block_reason"],
        "message": "materials detected; ship-define can start",
    }


def refresh_feature_meta(meta_path: Path) -> None:
    data = load_meta(meta_path)
    ensure_macro_stage(data)
    ensure_spec_context(data)
    ensure_delegation(data)
    ensure_skip_log(data)
    ensure_lifecycle_status(data)
    save_meta(meta_path, data)


def sync_spec_context(
    meta_path: Path,
    stage_hook: str,
    stack_tags: list[str],
    domains: list[str],
    files: list[str],
    project_config: Path | None = None,
    spec_root: Path | None = None,
) -> dict:
    data = load_meta(meta_path)
    ensure_spec_context(data)
    ensure_delegation(data)
    ensure_skip_log(data)
    ensure_lifecycle_status(data)
    workspace_context = resolve_project_context(
        project_config=project_config,
        meta_path=meta_path,
        data=data,
    )
    if spec_root is not None:
        workspace_context = build_explicit_workspace_context(
            spec_root=spec_root,
            workspace_root=workspace_context.resolved_workspace_root,
            feature_root=Path(workspace_context.feature_root),
            workspace_mode=workspace_context.workspace_mode,
            workspace_name=workspace_context.workspace_name,
            projects=workspace_context.projects,
            resolution_source=workspace_context.resolution_source,
        )
    result = resolve_specs(
        spec_root=None,
        workspace_context=workspace_context,
        stage_hook=stage_hook,
        stack_tags=stack_tags,
        domains=domains,
        files=files,
    )

    spec_context = data["spec_context"]
    existing_spec_ids = set(spec_context.get("referenced_spec_ids", []))
    existing_spec_ids.update(result["matched_spec_ids"])

    _sync_workspace_spec_context(spec_context, workspace_context)
    spec_context["index_status"] = result["index_status"]
    spec_context["last_checked_at"] = iso_now()
    spec_context["last_checked_stage"] = stage_hook
    spec_context["referenced_spec_ids"] = sorted(existing_spec_ids)
    spec_context["warnings"] = result["warnings"]
    data["updated_at"] = iso_now()
    save_meta(meta_path, data)
    return result


def record_spec_proposal(
    meta_path: Path,
    proposal_id: str,
    title: str,
    source_stage: str,
    target_spec_id: str,
    summary: str,
) -> dict:
    if source_stage != "ship-handoff":
        raise ValueError("spec proposals must be recorded from ship-handoff")

    data = load_meta(meta_path)
    ensure_spec_context(data)
    ensure_delegation(data)
    ensure_skip_log(data)
    ensure_lifecycle_status(data)
    pending_proposals = [
        proposal
        for proposal in data["spec_context"].get("pending_proposals", [])
        if proposal.get("proposal_id") != proposal_id
    ]
    pending_proposals.append(
        {
            "proposal_id": proposal_id,
            "title": title,
            "source_stage": source_stage,
            "target_spec_id": target_spec_id,
            "summary": summary,
        }
    )
    data["spec_context"]["pending_proposals"] = pending_proposals
    data["updated_at"] = iso_now()
    save_meta(meta_path, data)
    return pending_proposals[-1]


def record_skip(
    meta_path: Path,
    from_stage: str,
    to_stage: str,
    gate_type: str,
    reason: str,
    user_sign_off: str,
) -> dict:
    if from_stage not in CANONICAL_STAGE_ORDER:
        raise ValueError(f"invalid from_stage: {from_stage}")
    if to_stage not in CANONICAL_STAGE_ORDER:
        raise ValueError(f"invalid to_stage: {to_stage}")
    if not reason.strip():
        raise ValueError("skip reason must be non-empty")
    if not user_sign_off.strip():
        raise ValueError("user_sign_off must be non-empty")

    data = load_meta(meta_path)
    ensure_skip_log(data)
    ensure_lifecycle_status(data)
    entry = {
        "at": iso_now(),
        "from_stage": from_stage,
        "to_stage": to_stage,
        "gate_type": gate_type,
        "reason": reason,
        "user_sign_off": user_sign_off,
    }
    data["skip_log"].append(entry)
    _save_meta_with_updated_at(meta_path, data)
    return entry


def set_lifecycle_status(meta_path: Path, lifecycle_status: str) -> dict:
    if lifecycle_status not in VALID_LIFECYCLE_STATUSES:
        raise ValueError(f"invalid lifecycle_status: {lifecycle_status}")

    data = load_meta(meta_path)
    data["lifecycle_status"] = lifecycle_status
    _save_meta_with_updated_at(meta_path, data)
    return {"lifecycle_status": lifecycle_status}


def list_project_candidates(workspace_root: Path) -> list[str]:
    candidates: list[str] = []
    for child in sorted(workspace_root.iterdir(), key=lambda path: path.name):
        name = child.name
        if not child.is_dir():
            continue
        if name.startswith(".") or name in IGNORED_PROJECT_CANDIDATE_DIRS:
            continue
        candidates.append(name)
    return candidates


def write_workspace_config(
    workspace_root: Path,
    *,
    workspace_mode: str,
    workspace_name: str,
    feature_root: str = ".docs",
    projects: list[str] | tuple[str, ...] | None = None,
) -> Path:
    if workspace_mode not in VALID_WORKSPACE_MODES:
        raise ValueError(f"invalid workspace_mode: {workspace_mode}")
    config_path = workspace_root / ".docs/ship/project.yml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 2,
        "workspace_mode": workspace_mode,
        "workspace_name": workspace_name,
        "feature_root": feature_root,
        "projects": list(projects or []),
    }
    config_path.write_text(yaml.safe_dump(payload, allow_unicode=False, sort_keys=False), encoding="utf-8")
    return config_path


def append_workspace_project(project_config: Path, project: str, *, allow_missing: bool = False) -> dict:
    data = yaml.safe_load(project_config.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{project_config}: workspace config must be a YAML mapping")
    if data.get("workspace_mode") != "project_group":
        raise ValueError("projects can only be appended when workspace_mode=project_group")
    if not isinstance(project, str) or not project.strip():
        raise ValueError("project must be a non-empty string")
    workspace_project = project.strip()
    if "/" in workspace_project or "\\" in workspace_project or workspace_project in {".", ".."}:
        raise ValueError("project must be a first-level directory name")

    workspace_root = project_config.resolve().parents[2]
    project_dir = workspace_root / workspace_project
    if not project_dir.is_dir() and not allow_missing:
        raise ValueError(
            f"{workspace_project}: first-level directory does not exist; pass --allow-missing to register it anyway"
        )

    projects = data.setdefault("projects", [])
    if not isinstance(projects, list):
        raise ValueError("`projects` must be a list")
    if workspace_project not in projects:
        projects.append(workspace_project)
    project_config.write_text(yaml.safe_dump(data, allow_unicode=False, sort_keys=False), encoding="utf-8")
    return {"project": workspace_project, "projects": projects}


def advance_stage(
    meta_path: Path,
    from_stage: str,
    to_stage: str,
    completed_status: str = "completed",
) -> dict:
    if from_stage not in CANONICAL_STAGE_ORDER:
        raise ValueError(f"invalid from_stage: {from_stage}")
    if to_stage not in CANONICAL_STAGE_ORDER:
        raise ValueError(f"invalid to_stage: {to_stage}")

    data = load_meta(meta_path)
    if data.get("current_stage") != from_stage:
        raise ValueError(f"current_stage is {data.get('current_stage')}, expected {from_stage}")

    stages = data.setdefault("stages", {})
    stages.setdefault(from_stage, {})["status"] = completed_status
    stages.setdefault(to_stage, {})["status"] = "pending"
    data["current_stage"] = to_stage
    ensure_macro_stage(data)
    ensure_spec_context(data)
    ensure_delegation(data)
    ensure_skip_log(data)
    ensure_lifecycle_status(data)
    save_meta(meta_path, data)
    return {
        "from_stage": from_stage,
        "to_stage": to_stage,
        "current_stage": data["current_stage"],
        "macro_stage": data["macro_stage"],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ship feature meta runtime helper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Initialize a feature meta.yml")
    init_parser.add_argument("feature_dir", help="Feature directory path")
    init_parser.add_argument(
        "--project-config",
        help="Path to workspace .docs/ship/project.yml",
    )
    init_parser.add_argument(
        "--project",
        action="append",
        default=[],
        help="Default associated project for project_group workspaces; repeatable",
    )
    init_parser.add_argument("--feature-name", required=True, help="Human-readable feature name")
    init_parser.add_argument("--feature-id", required=True, help="Stable feature id")
    init_parser.add_argument(
        "--scenario",
        required=True,
        choices=VALID_SCENARIOS,
        help="Entry scenario: greenfield, product_provided, prd_direct, evolve, or technical_plan_provided",
    )
    init_parser.add_argument(
        "--project-context",
        default="unknown",
        choices=("unknown", "new_project", "existing_project"),
        help="Project context to write into meta.yml",
    )
    init_parser.add_argument(
        "--project-scope",
        default="fullstack",
        choices=VALID_PROJECT_SCOPES,
        help="Project scope: fullstack, backend_only, or frontend_only",
    )
    init_parser.add_argument(
        "--project-scope-evidence",
        default="",
        help="Required evidence when project_scope is backend_only or frontend_only",
    )
    init_parser.add_argument(
        "--technical-source-file",
        action="append",
        default=[],
        help="Technical plan source file path for technical_plan_provided; repeatable",
    )
    init_parser.add_argument(
        "--technical-selected-scope",
        action="append",
        default=[],
        help="Selected technical plan section/API/module label; repeatable",
    )
    init_parser.add_argument(
        "--technical-selection-mode",
        default="",
        choices=("", "referenced_sections", "pasted_excerpt"),
        help="Selection mode for technical_plan_provided",
    )
    init_parser.add_argument(
        "--technical-pasted-excerpt-file",
        default="",
        help="Archived pasted excerpt path, e.g. resource/technical-plan-excerpt.md",
    )

    refresh_parser = subparsers.add_parser("refresh", help="Refresh macro_stage from current_stage")
    refresh_parser.add_argument("meta_path", help="Path to meta.yml")

    sync_parser = subparsers.add_parser("sync-spec", help="Resolve specs and sync spec_context")
    sync_parser.add_argument("meta_path", help="Path to meta.yml")
    sync_parser.add_argument("--stage", required=True, choices=VALID_STAGE_HOOKS)
    sync_parser.add_argument(
        "--project-config",
        help="Path to workspace .docs/ship/project.yml",
    )
    sync_parser.add_argument("--spec-root", help="Low-level override for spec root directory")
    sync_parser.add_argument("--stack-tag", action="append", default=[], help="Stack tag used for spec matching")
    sync_parser.add_argument("--domain", action="append", default=[], help="Domain tag used for spec matching")
    sync_parser.add_argument("--file", action="append", default=[], help="File path used for ship-build matching")

    proposal_parser = subparsers.add_parser("record-spec-proposal", help="Append a pending spec proposal")
    proposal_parser.add_argument("meta_path", help="Path to meta.yml")
    proposal_parser.add_argument("--proposal-id", required=True, help="Stable proposal identifier")
    proposal_parser.add_argument("--title", required=True, help="Proposal title")
    proposal_parser.add_argument("--source-stage", required=True, choices=("ship-handoff",))
    proposal_parser.add_argument("--target-spec-id", required=True, help="Target spec id")
    proposal_parser.add_argument("--summary", required=True, help="Proposal summary")

    skip_parser = subparsers.add_parser("record-skip", help="Record a user-approved skip")
    skip_parser.add_argument("meta_path", help="Path to meta.yml")
    skip_parser.add_argument("--from-stage", required=True, choices=CANONICAL_STAGE_ORDER)
    skip_parser.add_argument("--to-stage", required=True, choices=CANONICAL_STAGE_ORDER)
    skip_parser.add_argument("--gate-type", required=True, help="Gate type or skip category")
    skip_parser.add_argument("--reason", required=True, help="Reason for the skip")
    skip_parser.add_argument("--user-sign-off", required=True, help="User sign-off text")

    lifecycle_parser = subparsers.add_parser("set-lifecycle", help="Set feature lifecycle status")
    lifecycle_parser.add_argument("meta_path", help="Path to meta.yml")
    lifecycle_parser.add_argument("--status", required=True, choices=VALID_LIFECYCLE_STATUSES)

    materials_parser = subparsers.add_parser(
        "mark-materials-ready",
        help="Release ship-define from awaiting_materials when raw PRD or resource files exist",
    )
    materials_parser.add_argument("meta_path", help="Path to meta.yml")

    workspace_parser = subparsers.add_parser(
        "workspace-candidates",
        help="List first-level project candidates for workspace config initialization",
    )
    workspace_parser.add_argument("workspace_root", help="Workspace root path")

    init_workspace_parser = subparsers.add_parser(
        "init-workspace",
        help="Initialize .docs/ship/project.yml for a workspace",
    )
    init_workspace_parser.add_argument("workspace_root", help="Workspace root path")
    init_workspace_parser.add_argument("--workspace-mode", required=True, choices=VALID_WORKSPACE_MODES)
    init_workspace_parser.add_argument("--workspace-name", required=True)
    init_workspace_parser.add_argument("--feature-root", default=".docs")
    init_workspace_parser.add_argument("--project", action="append", default=[])

    append_project_parser = subparsers.add_parser(
        "append-project",
        help="Append a project name to workspace config projects",
    )
    append_project_parser.add_argument("project_config", help="Path to .docs/ship/project.yml")
    append_project_parser.add_argument("--project", required=True)
    append_project_parser.add_argument("--allow-missing", action="store_true")

    advance_parser = subparsers.add_parser("advance-stage", help="Advance current_stage")
    advance_parser.add_argument("meta_path", help="Path to meta.yml")
    advance_parser.add_argument("--from-stage", required=True, choices=CANONICAL_STAGE_ORDER)
    advance_parser.add_argument("--to-stage", required=True, choices=CANONICAL_STAGE_ORDER)
    advance_parser.add_argument("--completed-status", default="completed", help="Status to set on from-stage")

    return parser


def main(argv: list[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv[1:])

    if args.command == "init":
        workspace_context = resolve_project_context(
            project_config=Path(args.project_config) if args.project_config else None,
            search_from=Path(args.feature_dir),
        )
        feature_dir = resolve_feature_dir(args.feature_dir, workspace_context)
        meta_path = create_feature_meta(
            feature_dir=feature_dir,
            feature_name=args.feature_name,
            feature_id=args.feature_id,
            project_context=args.project_context,
            project_scope=args.project_scope,
            project_scope_evidence=args.project_scope_evidence,
            scenario=args.scenario,
            workspace_context=workspace_context,
            projects=args.project,
            technical_source_files=args.technical_source_file,
            technical_selection_mode=args.technical_selection_mode,
            technical_selected_scopes=args.technical_selected_scope,
            technical_pasted_excerpt_file=args.technical_pasted_excerpt_file,
        )
        print(meta_path)
        return 0

    if args.command == "refresh":
        refresh_feature_meta(Path(args.meta_path))
        print(args.meta_path)
        return 0

    if args.command == "sync-spec":
        payload = sync_spec_context(
            meta_path=Path(args.meta_path),
            stage_hook=args.stage,
            stack_tags=args.stack_tag,
            domains=args.domain,
            files=args.file,
            project_config=Path(args.project_config) if args.project_config else None,
            spec_root=Path(args.spec_root) if args.spec_root else None,
        )
        print(json.dumps(payload, ensure_ascii=True, indent=2))
        return 0

    if args.command == "record-skip":
        payload = record_skip(
            meta_path=Path(args.meta_path),
            from_stage=args.from_stage,
            to_stage=args.to_stage,
            gate_type=args.gate_type,
            reason=args.reason,
            user_sign_off=args.user_sign_off,
        )
        print(json.dumps(payload, ensure_ascii=True, indent=2))
        return 0

    if args.command == "set-lifecycle":
        payload = set_lifecycle_status(Path(args.meta_path), args.status)
        print(json.dumps(payload, ensure_ascii=True, indent=2))
        return 0

    if args.command == "mark-materials-ready":
        payload = mark_materials_ready(Path(args.meta_path))
        print(json.dumps(payload, ensure_ascii=True, indent=2))
        return 0

    if args.command == "workspace-candidates":
        payload = {"projects": list_project_candidates(Path(args.workspace_root))}
        print(json.dumps(payload, ensure_ascii=True, indent=2))
        return 0

    if args.command == "init-workspace":
        config_path = write_workspace_config(
            Path(args.workspace_root),
            workspace_mode=args.workspace_mode,
            workspace_name=args.workspace_name,
            feature_root=args.feature_root,
            projects=args.project,
        )
        print(config_path)
        return 0

    if args.command == "append-project":
        payload = append_workspace_project(
            Path(args.project_config),
            args.project,
            allow_missing=args.allow_missing,
        )
        print(json.dumps(payload, ensure_ascii=True, indent=2))
        return 0

    if args.command == "advance-stage":
        payload = advance_stage(
            meta_path=Path(args.meta_path),
            from_stage=args.from_stage,
            to_stage=args.to_stage,
            completed_status=args.completed_status,
        )
        print(json.dumps(payload, ensure_ascii=True, indent=2))
        return 0

    if args.command == "record-spec-proposal":
        payload = record_spec_proposal(
            meta_path=Path(args.meta_path),
            proposal_id=args.proposal_id,
            title=args.title,
            source_stage=args.source_stage,
            target_spec_id=args.target_spec_id,
            summary=args.summary,
        )
        print(json.dumps(payload, ensure_ascii=True, indent=2))
        return 0

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
