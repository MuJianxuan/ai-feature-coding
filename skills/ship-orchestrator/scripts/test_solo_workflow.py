#!/usr/bin/env python3
"""Regression tests for the lightweight Ship solo workflow."""

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
from workflow_stage_map import CANONICAL_STAGE_ORDER, SUPPORT_SKILLS, stage_view_for


class SoloWorkflowTest(unittest.TestCase):
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

    def write_meta(self, current_stage: str = "ship-build") -> None:
        stages = {
            "ship-discover": {"status": "skipped", "artifact": "intent.md"},
            "ship-define": {"status": "ready", "artifact": "brief.md"},
            "ship-tech-discovery": {"status": "ready", "artifact": "context-map.md"},
            "ship-contract": {"status": "ready", "artifact": "contract.md"},
            "ship-delivery-plan": {"status": "ready", "artifact": "plan.md"},
            "ship-build": {"status": "in_progress", "artifact": "build-log.md"},
            "ship-verify": {"status": "pending", "artifact": "verification.md"},
            "ship-handoff": {"status": "pending", "artifact": "handoff.md"},
        }
        view = stage_view_for(current_stage)
        self.write_text("meta.yml", yaml.safe_dump({
            "schema_version": 3,
            "work_id": "demo",
            "work_title": "Demo",
            "work_mode": "bugfix",
            "current_stage": current_stage,
            "macro_stage": {
                "current": view.macro.current,
                "label": view.macro.label,
                "summary": view.summary,
                "next_user_decision": view.next_user_decision,
            },
            "lifecycle_status": "active",
            "stages": stages,
            "slices": [],
        }, sort_keys=False))

    def write_plan(self, *, status: str = "DOING", allowed_file: str = "src/a.ts") -> None:
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
- verification_command: pnpm test src/a.test.ts

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

    def test_runtime_stage_map_is_lightweight(self) -> None:
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
        self.assertIn("ship-plan-review", SUPPORT_SKILLS)
        self.assertNotIn("ship-plan-review", CANONICAL_STAGE_ORDER)

    def test_build_task_preflight_accepts_single_doing_slice(self) -> None:
        self.write_plan()
        result = build_task_preflight(self.feature_dir)
        self.assertTrue(result["ok"], result["issues"])
        self.assertEqual(result["doing_tasks"][0]["task_id"], "S-001")

    def test_implementation_preflight_allows_planned_file_without_review_signoff(self) -> None:
        self.write_meta()
        self.write_plan()
        result = implementation_preflight(self.feature_dir, files=["src/a.ts"])
        self.assertTrue(result["allowed"], result["issues"])

    def test_implementation_preflight_rejects_unplanned_file(self) -> None:
        self.write_meta()
        self.write_plan()
        result = implementation_preflight(self.feature_dir, files=["src/b.ts"])
        self.assertFalse(result["allowed"])
        self.assertTrue(any(issue["code"] == "file_not_allowed_by_doing_task" for issue in result["issues"]))


if __name__ == "__main__":
    unittest.main()
