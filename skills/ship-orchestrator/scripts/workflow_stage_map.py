#!/usr/bin/env python3
"""Ship workflow stage mapping utilities.

This module is the executable source of truth for the default 5-stage view
(Discover is conditional and only appears in scenario A / C).
It intentionally stays dependency-free so it can be used from validation
scripts, runtime helpers, and shell commands without extra setup.
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
    "ship-shape",
    "ship-define",
    "ship-define-review",
    "ship-tech-discovery",
    "ship-contract",
    "ship-frontend-design",
    "ship-backend-design",
    "ship-design-review",
    "ship-delivery-plan",
    "ship-plan-review",
    "ship-build",
    "ship-verify",
    "ship-handoff",
)

# Conditional pre-Define stages. ship-discover is A/C only; ship-shape is A/C by default and may be inserted for B/D via UIUX Material Gate.
CONDITIONAL_STAGES: frozenset[str] = frozenset({"ship-discover", "ship-shape"})

STAGE_VIEW_MAP: dict[str, StageView] = {
    "ship-discover": StageView(
        macro=MacroStage("discover", "Discover"),
        summary="Exploring requirements through structured discovery — producing a product brief from a rough idea or change request.",
        next_user_decision="Select an approach from the proposed alternatives and confirm the product brief.",
    ),
    "ship-shape": StageView(
        macro=MacroStage("discover", "Discover"),
        summary="Designing visual direction and producing HTML wireframe prototypes with multiple variants.",
        next_user_decision="Choose a design direction from the presented variants.",
    ),
    "ship-define": StageView(
        macro=MacroStage("define", "Define"),
        summary="Requirements are being structured into a verifiable feature brief.",
        next_user_decision="Review the requirements outcome before design work starts.",
    ),
    "ship-define-review": StageView(
        macro=MacroStage("define", "Define"),
        summary="Requirements are ready and waiting for the first hard-gate review.",
        next_user_decision="Approve or reject the requirement review result.",
    ),
    "ship-tech-discovery": StageView(
        macro=MacroStage("design", "Design"),
        summary="Source-backed research and stack decisions are being consolidated into a single technical discovery stage.",
        next_user_decision="Review whether research coverage and stack decisions are both ready before contract design starts.",
    ),
    "ship-contract": StageView(
        macro=MacroStage("design", "Design"),
        summary="The shared API contract is being defined for frontend and backend alignment.",
        next_user_decision="Confirm the contract once request, response, and error shapes are stable.",
    ),
    "ship-frontend-design": StageView(
        macro=MacroStage("design", "Design"),
        summary="Frontend structure is being mapped from pages and flows to components and APIs.",
        next_user_decision="Review whether the frontend design matches the intended UI and interaction model.",
    ),
    "ship-backend-design": StageView(
        macro=MacroStage("design", "Design"),
        summary="Backend domain, data, and service boundaries are being designed against the contract.",
        next_user_decision="Review whether the backend design covers domain logic, data shape, and operations.",
    ),
    "ship-design-review": StageView(
        macro=MacroStage("design", "Design"),
        summary="Contract, frontend, and backend designs are waiting for the design hard gate.",
        next_user_decision="Approve or reject the design review before planning starts.",
    ),
    "ship-delivery-plan": StageView(
        macro=MacroStage("build", "Build"),
        summary="Frontend and backend implementation plans are being decomposed and cross-checked in one delivery planning stage.",
        next_user_decision="Review whether both frontend and backend plans are ready before implementation starts.",
    ),
    "ship-plan-review": StageView(
        macro=MacroStage("build", "Build"),
        summary="Frontend and backend plans are waiting for the planning hard gate.",
        next_user_decision="Approve or reject the plan review before implementation starts.",
    ),
    "ship-build": StageView(
        macro=MacroStage("build", "Build"),
        summary="Implementation is in progress with contract-first task execution.",
        next_user_decision="Decide whether to continue with the next task after each verified slice.",
    ),
    "ship-verify": StageView(
        macro=MacroStage("build", "Build"),
        summary="Automated and contract-level verification are being consolidated for handoff.",
        next_user_decision="Review the verification outcome before final acceptance and handoff.",
    ),
    "ship-handoff": StageView(
        macro=MacroStage("close", "Close"),
        summary="Acceptance mapping and delivery notes are being finalized for handoff.",
        next_user_decision="Confirm whether the feature is acceptable to close or needs follow-up work.",
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
        "  python3 workflow_stage_map.py --list",
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
