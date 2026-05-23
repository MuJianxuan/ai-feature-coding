#!/usr/bin/env python3
"""Unit tests for ship-spec runtime helpers."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from feature_meta_runtime import sync_spec_context
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


if __name__ == "__main__":
    unittest.main()
