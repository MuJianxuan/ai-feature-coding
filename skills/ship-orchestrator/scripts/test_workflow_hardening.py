#!/usr/bin/env python3
"""Hardening tests for the Ship solo-developer workflow.

This file intentionally replaces the legacy 14-stage hard-gate test suite. The
current suite verifies the new lightweight default: support skills are optional,
implementation is scoped by one DOING slice, and review sign-off is not a
runtime requirement.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import sys

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from build_task_preflight import build_task_preflight
from implementation_preflight import implementation_preflight
from stage_transition_check import check_transition
from validate_feature_artifacts import validate_feature
from validate_workflow_docs import validate_grill_hook_docs
from workflow_stage_map import CANONICAL_STAGE_ORDER, SUPPORT_SKILLS, stage_view_for


class WorkflowHardeningTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.feature_dir = self.root / ".docs" / "ship" / "demo"
        self.feature_dir.mkdir(parents=True)
        self.write_root_text(".docs/ship/project.yml", yaml.safe_dump({
            "schema_version": 3,
            "workspace_mode": "single_project",
            "workspace_name": "test-workspace",
            "work_root": ".docs/ship",
            "feature_root": ".docs/ship",
            "spec_root": ".docs/spec",
            "projects": [],
        }, sort_keys=False))

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def write_root_text(self, relative_path: str, content: str) -> None:
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def write_text(self, relative_path: str, content: str) -> None:
        path = self.feature_dir / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def write_meta(self, *, current_stage: str = "ship-build", plan_status: str = "ready") -> None:
        view = stage_view_for(current_stage)
        stages = {
            "ship-discover": {"status": "skipped", "artifact": "intent.md"},
            "ship-define": {"status": "ready", "artifact": "brief.md"},
            "ship-tech-discovery": {"status": "ready", "artifact": "context-map.md"},
            "ship-contract": {"status": "ready", "artifact": "contract.md"},
            "ship-delivery-plan": {"status": plan_status, "artifact": "plan.md"},
            "ship-build": {"status": "in_progress", "artifact": "build-log.md"},
            "ship-verify": {"status": "pending", "artifact": "verification.md"},
            "ship-handoff": {"status": "pending", "artifact": "handoff.md"},
        }
        self.write_text("meta.yml", yaml.safe_dump({
            "schema_version": 3,
            "work_id": "demo",
            "work_title": "Demo",
            "work_mode": "feature",
            "current_stage": current_stage,
            "macro_stage": {
                "current": view.macro.current,
                "label": view.macro.label,
                "summary": view.summary,
                "next_user_decision": view.next_user_decision,
            },
            "lifecycle_status": "active",
            "stages": stages,
            "support_skills": {
                "ship-plan-review": {"used": False, "outputs": []},
                "ship-grill-me": {"used": False, "decisions": []},
            },
            "slices": [],
        }, sort_keys=False))

    def write_plan(self, *, status: str = "DOING", allowed_file: str = "src/a.ts", verification: str = "pnpm test src/a.test.ts") -> None:
        self.write_text("plan.md", f"""---
stage: ship-delivery-plan
stage_status: ready
---

# Delivery Plan

## Slice S-001: Fix demo
- status: {status}
- ac_refs: [AC-001]
- allowed_files:
  - {allowed_file}
- verification_command: {verification}

### 任务目标
Fix demo behavior.
### 上下文
Existing module src/a.ts.
### 约束
Only touch allowed files.
### 验收
AC-001 passes.
### 输出
Code and test evidence.
""")

    def write_runtime_artifacts(self) -> None:
        artifacts = {
            "brief.md": ("ship-define", "# Brief\n\n## Acceptance Criteria\n- AC-001: Demo works.\n"),
            "context-map.md": ("ship-tech-discovery", "# Context Map\n\n## Relevant Files\n- src/a.ts\n"),
            "contract.md": ("ship-contract", "# Contract\n\n## AC Mapping\n- AC-001 -> invariant\n"),
            "plan.md": ("ship-delivery-plan", "# Delivery Plan\n\n## Slice S-001\n- status: DONE\n- ac_refs: [AC-001]\n- allowed_files:\n  - src/a.ts\n- verification_command: pnpm test src/a.test.ts\n\n### 任务目标\nFix.\n### 上下文\nKnown.\n### 约束\nScoped.\n### 验收\nAC-001.\n### 输出\nPatch.\n"),
            "build-log.md": ("ship-build", "# Build Log\n\n## Slice S-001\n- changed_files: src/a.ts\n"),
            "verification.md": ("ship-verify", "# Verification\n\n## Commands\n- pnpm test src/a.test.ts: pass\n"),
            "handoff.md": ("ship-handoff", "# Handoff\n\n## Summary\nDone.\n"),
        }
        for path, (stage, body) in artifacts.items():
            self.write_text(path, f"---\nstage: {stage}\nstage_status: ready\nupdated_at: ''\nblocking_gaps: []\nevidence: []\n---\n\n{body}")

    def test_canonical_runtime_stages_are_lightweight(self) -> None:
        self.assertEqual(CANONICAL_STAGE_ORDER, (
            "ship-discover",
            "ship-define",
            "ship-tech-discovery",
            "ship-contract",
            "ship-delivery-plan",
            "ship-build",
            "ship-verify",
            "ship-handoff",
        ))
        for support_skill in ("ship-shape", "ship-define-review", "ship-design-review", "ship-plan-review", "ship-grill-me", "ship-spec"):
            self.assertIn(support_skill, SUPPORT_SKILLS)
            self.assertNotIn(support_skill, CANONICAL_STAGE_ORDER)

    def test_grill_hook_docs_remain_support_only(self) -> None:
        validate_grill_hook_docs()

    def test_build_task_preflight_requires_single_doing_slice(self) -> None:
        self.write_plan(status="TODO")
        result = build_task_preflight(self.feature_dir)
        self.assertFalse(result["ok"])
        self.assertTrue(any(issue["code"] == "doing_count_invalid" for issue in result["issues"]))

    def test_build_task_preflight_accepts_valid_slice(self) -> None:
        self.write_plan()
        result = build_task_preflight(self.feature_dir)
        self.assertTrue(result["ok"], result["issues"])

    def test_implementation_preflight_allows_planned_file_without_plan_review(self) -> None:
        self.write_meta()
        self.write_plan()
        result = implementation_preflight(self.feature_dir, files=["src/a.ts"])
        self.assertTrue(result["allowed"], result["issues"])

    def test_implementation_preflight_blocks_unplanned_file(self) -> None:
        self.write_meta()
        self.write_plan()
        result = implementation_preflight(self.feature_dir, files=["src/b.ts"])
        self.assertFalse(result["allowed"])
        self.assertTrue(any(issue["code"] == "file_not_allowed_by_doing_task" for issue in result["issues"]))

    def test_implementation_preflight_requires_build_stage(self) -> None:
        self.write_meta(current_stage="ship-delivery-plan")
        self.write_plan()
        result = implementation_preflight(self.feature_dir, files=["src/a.ts"])
        self.assertFalse(result["allowed"])
        self.assertTrue(any(issue["code"] == "current_stage_not_ship_build" for issue in result["issues"]))

    def test_implementation_preflight_requires_plan_stage_ready(self) -> None:
        self.write_meta(plan_status="pending")
        self.write_plan()
        result = implementation_preflight(self.feature_dir, files=["src/a.ts"])
        self.assertFalse(result["allowed"])
        self.assertTrue(any(issue["code"] == "plan_stage_not_ready" for issue in result["issues"]))

    def test_transition_requires_previous_runtime_artifacts(self) -> None:
        self.write_meta(current_stage="ship-contract")
        result = check_transition(self.feature_dir, "ship-delivery-plan")
        self.assertFalse(result["allowed"])
        self.assertIn("ship-contract", result["checked_previous_stages"])

    def test_transition_accepts_ready_previous_runtime_stage(self) -> None:
        self.write_meta(current_stage="ship-delivery-plan")
        self.write_text("brief.md", "---\nstage: ship-define\nstage_status: ready\n---\n# Brief\n")
        self.write_text("context-map.md", "---\nstage: ship-tech-discovery\nstage_status: ready\n---\n# Context\n")
        self.write_text("contract.md", "---\nstage: ship-contract\nstage_status: ready\n---\n# Contract\n")
        result = check_transition(self.feature_dir, "ship-delivery-plan")
        self.assertTrue(result["allowed"], result["issues"])

    def test_validate_feature_accepts_support_skill_metadata(self) -> None:
        self.write_meta(current_stage="ship-verify")
        self.write_runtime_artifacts()
        result = validate_feature(self.feature_dir)
        self.assertTrue(all(issue["code"] != "unknown_stage" for issue in result["issues"]), result["issues"])


if __name__ == "__main__":
    unittest.main()
