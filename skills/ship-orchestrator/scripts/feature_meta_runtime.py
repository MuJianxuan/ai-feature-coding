#!/usr/bin/env python3
"""Runtime helpers for ship feature meta files.

This script provides the minimum executable behavior needed to keep
`macro_stage` in sync during feature creation and resume flows.
"""

from __future__ import annotations

import argparse
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


def iso_now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def load_meta(meta_path: Path) -> dict:
    with meta_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{meta_path} does not contain a YAML mapping")
    return data


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
    delegation.setdefault("default_mode", "current_context")
    delegation.setdefault("ask_on_parallel_stage", True)
    delegation.setdefault("ask_on_assistive_node", True)
    delegation.setdefault("node_overrides", {})
    delegation.setdefault("warnings", [])
    return data


def feature_dir_for(feature_name: str) -> Path:
    return FEATURES_ROOT / feature_name


def create_feature_meta(
    feature_dir: Path,
    feature_name: str,
    feature_id: str,
    pipeline_mode: str,
    project_context: str,
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
    data["current_stage"] = "ship-intake"
    data["pipeline_mode"] = pipeline_mode
    data["project_context"] = project_context
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
