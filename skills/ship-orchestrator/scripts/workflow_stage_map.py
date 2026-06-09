#!/usr/bin/env python3
"""Solo-developer Ship workflow stage mapping utilities.

This module is the executable source of truth for the default lightweight
workflow view. Review skills and design-specialist skills remain available as
utilities, but they are not blocking runtime stages by default.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class MacroStage:
    current: str
    label: str


@dataclass(frozen=True)
class StageView:
    macro: MacroStage
    summary: str
    next_user_decision: str


CANONICAL_STAGE_ORDER: tuple[str, ...] = (
    "ship-discover",
    "ship-define",
    "ship-tech-discovery",
    "ship-contract",
    "ship-delivery-plan",
    "ship-build",
    "ship-verify",
    "ship-handoff",
)

SUPPORT_SKILLS: tuple[str, ...] = (
    "ship-shape",
    "ship-frontend-design",
    "ship-backend-design",
    "ship-define-review",
    "ship-design-review",
    "ship-plan-review",
    "ship-grill-me",
    "ship-spec",
)

STAGE_VIEW_MAP: dict[str, StageView] = {
    "ship-discover": StageView(
        macro=MacroStage("discover", "Discover"),
        summary="Clarify the real goal, constraints, project context, and smallest useful scope.",
        next_user_decision="Confirm the target outcome and what is intentionally out of scope.",
    ),
    "ship-define": StageView(
        macro=MacroStage("define", "Define"),
        summary="Turn the request into a brief with acceptance criteria, assumptions, and risks.",
        next_user_decision="Confirm the brief is accurate enough to design or plan from.",
    ),
    "ship-tech-discovery": StageView(
        macro=MacroStage("understand", "Understand"),
        summary="Read the existing code and docs before proposing changes; capture evidence-backed constraints.",
        next_user_decision="Confirm any unresolved repository facts, dependency choices, or risk trade-offs.",
    ),
    "ship-contract": StageView(
        macro=MacroStage("design", "Design"),
        summary="Define the smallest stable contract: data shapes, API/event/CLI boundaries, and behavior rules.",
        next_user_decision="Confirm the contract is enough for implementation and not over-designed.",
    ),
    "ship-delivery-plan": StageView(
        macro=MacroStage("plan", "Plan"),
        summary="Break the work into atomic slices with files, verification commands, and rollback notes.",
        next_user_decision="Choose whether to start the next slice or adjust the plan.",
    ),
    "ship-build": StageView(
        macro=MacroStage("build", "Build"),
        summary="Implement one slice at a time with surgical changes and local verification.",
        next_user_decision="Review the completed slice and decide whether to continue.",
    ),
    "ship-verify": StageView(
        macro=MacroStage("verify", "Verify"),
        summary="Run targeted checks, inspect diffs, and collect evidence against the acceptance criteria.",
        next_user_decision="Decide whether failures require fixes, scope cuts, or accepted risks.",
    ),
    "ship-handoff": StageView(
        macro=MacroStage("close", "Close"),
        summary="Package the change summary, verification evidence, known risks, and next actions.",
        next_user_decision="Confirm the work is ready to stop, ship, or continue with follow-up tasks.",
    ),
}


def macro_stage_for(current_stage: str) -> MacroStage:
    try:
        return STAGE_VIEW_MAP[current_stage].macro
    except KeyError as exc:
        raise KeyError(f"unknown current_stage: {current_stage}") from exc


def stage_view_for(current_stage: str) -> StageView:
    try:
        return STAGE_VIEW_MAP[current_stage]
    except KeyError as exc:
        raise KeyError(f"unknown current_stage: {current_stage}") from exc


def mapping_rows() -> list[tuple[str, str, str]]:
    return [
        (stage, stage_view.macro.current, stage_view.macro.label)
        for stage, stage_view in STAGE_VIEW_MAP.items()
    ]


def _print_usage() -> int:
    print(
        "Usage:\n"
        "  python3 workflow_stage_map.py <current_stage>\n"
        "  python3 workflow_stage_map.py --json <current_stage>\n"
        "  python3 workflow_stage_map.py --list\n"
        "  python3 workflow_stage_map.py --support-skills",
        file=sys.stderr,
    )
    return 2


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        return _print_usage()

    if argv[1] == "--list":
        for stage in CANONICAL_STAGE_ORDER:
            stage_view = stage_view_for(stage)
            print(
                f"{stage}\t{stage_view.macro.current}\t{stage_view.macro.label}\t"
                f"{stage_view.summary}\t{stage_view.next_user_decision}"
            )
        return 0

    if argv[1] == "--support-skills":
        for skill in SUPPORT_SKILLS:
            print(skill)
        return 0

    as_json = False
    args = argv[1:]
    if args and args[0] == "--json":
        as_json = True
        args = args[1:]

    if len(args) != 1:
        return _print_usage()

    current_stage = args[0]
    try:
        stage_view = stage_view_for(current_stage)
    except KeyError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    payload = {
        "current_stage": current_stage,
        "macro_stage": {
            "current": stage_view.macro.current,
            "label": stage_view.macro.label,
            "summary": stage_view.summary,
            "next_user_decision": stage_view.next_user_decision,
        },
    }

    if as_json:
        print(json.dumps(payload, ensure_ascii=True, indent=2))
        return 0

    print(f"current_stage: {current_stage}")
    print(f"macro_stage.current: {stage_view.macro.current}")
    print(f"macro_stage.label: {stage_view.macro.label}")
    print(f"macro_stage.summary: {stage_view.summary}")
    print(f"macro_stage.next_user_decision: {stage_view.next_user_decision}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
