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

from spec_runtime import VALID_STAGE_HOOKS, resolve_specs  # noqa: E402
from workflow_stage_map import stage_view_for  # noqa: E402


META_TEMPLATE_PATH = ROOT / "skills/ship-orchestrator/_templates/meta/meta.yml.template"
FEATURES_ROOT = ROOT / ".docs"

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

SCOPE_SKIP_MAP: dict[str, list[str]] = {
    "fullstack": [],
    "backend_only": ["ship-frontend-design"],
    "frontend_only": ["ship-backend-design"],
}


@dataclass(frozen=True)
class DelegationNodeSpec:
    node_id: str
    delegation_mode: str
    ask_flag: str | None
    allowed_execution_modes: tuple[str, ...]


CANONICAL_DELEGATION_NODES: dict[str, DelegationNodeSpec] = {
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


def feature_dir_for(feature_name: str) -> Path:
    return FEATURES_ROOT / feature_name


def apply_scope_skips(data: dict) -> None:
    scope = data.get("project_scope", "fullstack")
    stages = data.get("stages", {})
    for stage_id in SCOPE_SKIP_MAP.get(scope, []):
        if stage_id in stages:
            stages[stage_id]["status"] = "skipped"


def create_feature_meta(
    feature_dir: Path,
    feature_name: str,
    feature_id: str,
    pipeline_mode: str,
    project_context: str,
    project_scope: str = "fullstack",
) -> Path:
    feature_dir.mkdir(parents=True, exist_ok=True)
    resource_dir = feature_dir / "resource"
    resource_dir.mkdir(parents=True, exist_ok=True)

    meta_path = feature_dir / "meta.yml"
    if not meta_path.exists():
        shutil.copyfile(META_TEMPLATE_PATH, meta_path)

    data = load_meta(meta_path)
    now = iso_now()
    data["feature_name"] = feature_name
    data["feature_id"] = feature_id
    data["created_at"] = data.get("created_at") or now
    data["updated_at"] = now
    data["current_stage"] = "ship-define"
    data["pipeline_mode"] = pipeline_mode
    data["project_context"] = project_context
    data["project_scope"] = project_scope
    apply_scope_skips(data)
    ensure_macro_stage(data)
    ensure_spec_context(data)
    ensure_delegation(data)
    save_meta(meta_path, data)
    return meta_path


def refresh_feature_meta(meta_path: Path) -> None:
    data = load_meta(meta_path)
    ensure_macro_stage(data)
    ensure_spec_context(data)
    ensure_delegation(data)
    save_meta(meta_path, data)


def sync_spec_context(
    meta_path: Path,
    stage_hook: str,
    spec_root: Path,
    stack_tags: list[str],
    domains: list[str],
    files: list[str],
) -> dict:
    data = load_meta(meta_path)
    ensure_spec_context(data)
    ensure_delegation(data)
    result = resolve_specs(
        spec_root=spec_root,
        stage_hook=stage_hook,
        stack_tags=stack_tags,
        domains=domains,
        files=files,
    )

    spec_context = data["spec_context"]
    existing_spec_ids = set(spec_context.get("referenced_spec_ids", []))
    existing_spec_ids.update(result["matched_spec_ids"])

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
    data = load_meta(meta_path)
    ensure_spec_context(data)
    ensure_delegation(data)
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ship feature meta runtime helper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="Initialize a feature meta.yml")
    init_parser.add_argument("feature_dir", help="Feature directory path")
    init_parser.add_argument("--feature-name", required=True, help="Human-readable feature name")
    init_parser.add_argument("--feature-id", required=True, help="Stable feature id")
    init_parser.add_argument(
        "--pipeline-mode",
        default="standard",
        choices=("standard", "fast-track"),
        help="Pipeline mode to write into meta.yml",
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

    refresh_parser = subparsers.add_parser("refresh", help="Refresh macro_stage from current_stage")
    refresh_parser.add_argument("meta_path", help="Path to meta.yml")

    sync_parser = subparsers.add_parser("sync-spec", help="Resolve specs and sync spec_context")
    sync_parser.add_argument("meta_path", help="Path to meta.yml")
    sync_parser.add_argument("--stage", required=True, choices=VALID_STAGE_HOOKS)
    sync_parser.add_argument("--spec-root", default=".docs/spec", help="Spec root directory")
    sync_parser.add_argument("--stack-tag", action="append", default=[], help="Stack tag used for spec matching")
    sync_parser.add_argument("--domain", action="append", default=[], help="Domain tag used for spec matching")
    sync_parser.add_argument("--file", action="append", default=[], help="File path used for ship-build matching")

    proposal_parser = subparsers.add_parser("record-spec-proposal", help="Append a pending spec proposal")
    proposal_parser.add_argument("meta_path", help="Path to meta.yml")
    proposal_parser.add_argument("--proposal-id", required=True, help="Stable proposal identifier")
    proposal_parser.add_argument("--title", required=True, help="Proposal title")
    proposal_parser.add_argument("--source-stage", required=True, choices=VALID_STAGE_HOOKS)
    proposal_parser.add_argument("--target-spec-id", required=True, help="Target spec id")
    proposal_parser.add_argument("--summary", required=True, help="Proposal summary")

    return parser


def main(argv: list[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv[1:])

    if args.command == "init":
        feature_dir = Path(args.feature_dir)
        meta_path = create_feature_meta(
            feature_dir=feature_dir,
            feature_name=args.feature_name,
            feature_id=args.feature_id,
            pipeline_mode=args.pipeline_mode,
            project_context=args.project_context,
            project_scope=args.project_scope,
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
            spec_root=Path(args.spec_root),
            stack_tags=args.stack_tag,
            domains=args.domain,
            files=args.file,
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
