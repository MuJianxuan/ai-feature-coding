#!/usr/bin/env python3
"""Unit tests for ship-spec runtime helpers."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from feature_meta_runtime import (
    ASSISTIVE_SUBAGENT,
    CURRENT_CONTEXT,
    GATE_CHECK_SUBAGENT,
    PARALLEL_SUBAGENT,
    clear_delegation_warning_log,
    record_delegation_warning,
    resolve_delegation,
    set_default_delegation_mode,
    set_node_override,
    sync_spec_context,
)
from spec_runtime import resolve_specs, scan_specs


class SpecRuntimeTest(unittest.TestCase):
    def write_text(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.spec_root = self.root / ".docs/spec"
        self.write_text(
            self.spec_root / "INDEX.md",
            "---\ndoc_type: spec-index\ndoc_status: active\nschema_version: 2\nupdated_at: \"\"\n---\n",
        )
        self.write_text(
            self.spec_root / "coding/frontend-data.md",
            """---
spec_id: react-query-data-fetching
scope: module
stage_hooks:
  - ship-tech-discovery
  - ship-frontend-design
  - ship-build
stack_tags:
  - react
  - tanstack-query
domains:
  - todo
applies_to:
  - "src/features/todo/**/*.tsx"
last_updated: "2026-05-23T10:00:00+08:00"
---

# Frontend data fetching
""",
        )

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_scan_specs_returns_ready_for_valid_spec(self) -> None:
        result = scan_specs(self.spec_root)
        self.assertEqual(result["index_status"], "ready")
        self.assertEqual(result["warnings"], [])
        self.assertEqual(result["specs"][0]["spec_id"], "react-query-data-fetching")
        self.assertEqual(result["specs"][0]["path"], ".docs/spec/coding/frontend-data.md")

    def test_scan_specs_marks_invalid_when_frontmatter_is_broken(self) -> None:
        self.write_text(
            self.spec_root / "coding/broken.md",
            """---
spec_id: broken
scope: project
stage_hooks: ship-build
last_updated: ""
---
""",
        )
        result = scan_specs(self.spec_root)
        self.assertEqual(result["index_status"], "invalid")
        self.assertTrue(any("invalid spec frontmatter" in warning for warning in result["warnings"]))

    def test_resolve_specs_filters_by_hook_tags_and_files(self) -> None:
        result = resolve_specs(
            spec_root=self.spec_root,
            stage_hook="ship-build",
            stack_tags=["react"],
            domains=["todo"],
            files=["src/features/todo/list/TodoList.tsx"],
        )
        self.assertEqual(result["matched_spec_ids"], ["react-query-data-fetching"])

        miss = resolve_specs(
            spec_root=self.spec_root,
            stage_hook="ship-build",
            stack_tags=["vue"],
            domains=["todo"],
            files=["src/features/todo/list/TodoList.tsx"],
        )
        self.assertEqual(miss["matched_spec_ids"], [])
        self.assertTrue(any("no matching specs found" in warning for warning in miss["warnings"]))

    def test_sync_spec_context_updates_meta_summary(self) -> None:
        meta_path = self.root / "feature/meta.yml"
        meta_path.parent.mkdir(parents=True, exist_ok=True)
        meta_path.write_text(
            yaml.safe_dump(
                {
                    "feature_name": "Demo",
                    "feature_id": "feature-demo",
                    "current_stage": "ship-build",
                    "spec_context": {},
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )

        sync_spec_context(
            meta_path=meta_path,
            stage_hook="ship-build",
            spec_root=self.spec_root,
            stack_tags=["react"],
            domains=["todo"],
            files=["src/features/todo/list/TodoList.tsx"],
        )

        saved = yaml.safe_load(meta_path.read_text(encoding="utf-8"))
        spec_context = saved["spec_context"]
        self.assertEqual(spec_context["index_status"], "ready")
        self.assertEqual(spec_context["last_checked_stage"], "ship-build")
        self.assertEqual(spec_context["referenced_spec_ids"], ["react-query-data-fetching"])
        self.assertEqual(saved["delegation"]["default_mode"], CURRENT_CONTEXT)
        self.assertEqual(saved["delegation"]["node_overrides"], {})
        self.assertEqual(saved["delegation"]["warnings"], [])


class DelegationRuntimeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.meta_path = self.root / "feature/meta.yml"
        self.meta_path.parent.mkdir(parents=True, exist_ok=True)
        self.meta_path.write_text(
            yaml.safe_dump(
                {
                    "feature_name": "Demo",
                    "feature_id": "feature-demo",
                    "current_stage": "ship-build",
                    "delegation": {},
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def load_meta(self) -> dict:
        return yaml.safe_load(self.meta_path.read_text(encoding="utf-8"))

    def test_resolve_delegation_rejects_unknown_node_id(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown delegation node_id"):
            resolve_delegation("ship-verify.unknown-track", {})

    def test_forbidden_node_override_falls_back_to_current_context(self) -> None:
        result = resolve_delegation(
            "ship-contract",
            {"node_overrides": {"ship-contract": ASSISTIVE_SUBAGENT}},
        )

        self.assertEqual(result["resolved_mode"], CURRENT_CONTEXT)
        self.assertTrue(result["used_override"])
        self.assertFalse(result["should_ask_user"])
        self.assertIn("forbids delegation", result["warning_reason"])

    def test_parallel_node_asks_user_when_flag_enabled_and_no_override(self) -> None:
        result = resolve_delegation("ship-frontend-design", {})

        self.assertIsNone(result["resolved_mode"])
        self.assertTrue(result["should_ask_user"])
        self.assertIsNone(result["warning_reason"])

    def test_parallel_node_accepts_explicit_parallel_override(self) -> None:
        result = resolve_delegation(
            "ship-frontend-design",
            {"node_overrides": {"ship-frontend-design": PARALLEL_SUBAGENT}},
        )

        self.assertEqual(result["resolved_mode"], PARALLEL_SUBAGENT)
        self.assertTrue(result["used_override"])
        self.assertFalse(result["should_ask_user"])

    def test_parallel_node_rejects_assistive_inference_when_ask_is_disabled(self) -> None:
        result = resolve_delegation(
            "ship-backend-design",
            {
                "default_mode": ASSISTIVE_SUBAGENT,
                "ask_on_parallel_stage": False,
            },
        )

        self.assertEqual(result["requested_mode"], ASSISTIVE_SUBAGENT)
        self.assertEqual(result["resolved_mode"], CURRENT_CONTEXT)
        self.assertFalse(result["should_ask_user"])
        self.assertIn("requires an explicit parallel_subagent override", result["warning_reason"])

    def test_assistive_node_uses_default_mode_when_ask_is_disabled(self) -> None:
        result = resolve_delegation(
            "ship-build.spec-scan",
            {
                "default_mode": ASSISTIVE_SUBAGENT,
                "ask_on_assistive_node": False,
            },
        )

        self.assertEqual(result["resolved_mode"], ASSISTIVE_SUBAGENT)
        self.assertFalse(result["should_ask_user"])
        self.assertIsNone(result["warning_reason"])

    def test_hard_gate_maps_assistive_default_to_gate_check_subagent(self) -> None:
        result = resolve_delegation(
            "ship-design-review",
            {"default_mode": ASSISTIVE_SUBAGENT},
        )

        self.assertEqual(result["requested_mode"], ASSISTIVE_SUBAGENT)
        self.assertEqual(result["resolved_mode"], GATE_CHECK_SUBAGENT)
        self.assertFalse(result["should_ask_user"])
        self.assertIsNone(result["warning_reason"])

    def test_hard_gate_invalid_override_falls_back_to_default_mode(self) -> None:
        result = resolve_delegation(
            "ship-plan-review",
            {
                "default_mode": ASSISTIVE_SUBAGENT,
                "node_overrides": {"ship-plan-review": PARALLEL_SUBAGENT},
            },
        )

        self.assertEqual(result["requested_mode"], PARALLEL_SUBAGENT)
        self.assertEqual(result["resolved_mode"], GATE_CHECK_SUBAGENT)
        self.assertTrue(result["used_override"])
        self.assertIn("fell back to default_mode", result["warning_reason"])

    def test_record_delegation_warning_appends_and_can_be_cleared(self) -> None:
        warning = record_delegation_warning(
            self.meta_path,
            node_id="ship-verify.backend-contract",
            requested_mode=PARALLEL_SUBAGENT,
            resolved_mode=CURRENT_CONTEXT,
            reason="invalid override for assistive_only node",
        )

        saved = self.load_meta()
        self.assertEqual(saved["delegation"]["warnings"], [warning])

        clear_delegation_warning_log(self.meta_path)
        saved = self.load_meta()
        self.assertEqual(saved["delegation"]["warnings"], [])

    def test_set_node_override_and_default_mode_update_meta(self) -> None:
        set_node_override(
            self.meta_path,
            node_id="ship-verify.backend-contract",
            execution_mode=ASSISTIVE_SUBAGENT,
        )
        set_default_delegation_mode(self.meta_path, CURRENT_CONTEXT)

        saved = self.load_meta()
        self.assertEqual(
            saved["delegation"]["node_overrides"]["ship-verify.backend-contract"],
            ASSISTIVE_SUBAGENT,
        )
        self.assertEqual(saved["delegation"]["default_mode"], CURRENT_CONTEXT)


if __name__ == "__main__":
    unittest.main()
