#!/usr/bin/env python3
"""Unit tests for ship-spec runtime helpers."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
import sys

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from feature_meta_runtime import (
    ASSISTIVE_SUBAGENT,
    CURRENT_CONTEXT,
    GATE_CHECK_SUBAGENT,
    PARALLEL_SUBAGENT,
    advance_stage,
    clear_delegation_warning_log,
    create_feature_meta,
    feature_dir_for,
    mark_materials_ready,
    record_delegation_warning,
    record_skip,
    record_spec_proposal,
    resolve_delegation,
    resolve_project_context,
    set_default_delegation_mode,
    set_lifecycle_status,
    set_node_override,
    sync_spec_context,
)
from spec_runtime import load_project_context, resolve_specs, scan_specs


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

    def write_project_config(
        self,
        project_root: Path,
        *,
        spec_root: str = ".docs/spec",
        feature_root: str = ".docs",
        project_id: str = "project-a",
    ) -> Path:
        path = project_root / ".docs/ship/project.yml"
        self.write_text(
            path,
            yaml.safe_dump(
                {
                    "schema_version": 1,
                    "project_id": project_id,
                    "project_name": "Project A",
                    "project_root": ".",
                    "spec_root": spec_root,
                    "feature_root": feature_root,
                    "module_layout": {
                        "mode": "project_level_only",
                        "module_roots": [],
                    },
                    "notes": "",
                },
                sort_keys=False,
            ),
        )
        return path

    def test_scan_specs_returns_ready_for_valid_spec(self) -> None:
        result = scan_specs(self.spec_root, project_root=self.root)
        self.assertEqual(result["index_status"], "ready")
        self.assertEqual(result["warnings"], [])
        self.assertEqual(result["specs"][0]["spec_id"], "react-query-data-fetching")
        self.assertEqual(result["specs"][0]["path"], ".docs/spec/coding/frontend-data.md")
        self.assertEqual(result["target_project_root"], ".")

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
        result = scan_specs(self.spec_root, project_root=self.root)
        self.assertEqual(result["index_status"], "invalid")
        self.assertTrue(any("invalid spec frontmatter" in warning for warning in result["warnings"]))

    def test_resolve_specs_filters_by_hook_tags_and_files(self) -> None:
        result = resolve_specs(
            spec_root=self.spec_root,
            stage_hook="ship-build",
            stack_tags=["react"],
            domains=["todo"],
            files=["src/features/todo/list/TodoList.tsx"],
            project_root=self.root,
        )
        self.assertEqual(result["matched_spec_ids"], ["react-query-data-fetching"])

        miss = resolve_specs(
            spec_root=self.spec_root,
            stage_hook="ship-build",
            stack_tags=["vue"],
            domains=["todo"],
            files=["src/features/todo/list/TodoList.tsx"],
            project_root=self.root,
        )
        self.assertEqual(miss["matched_spec_ids"], [])
        self.assertTrue(any("no matching specs found" in warning for warning in miss["warnings"]))

    def test_sync_spec_context_updates_meta_summary(self) -> None:
        project_config = self.write_project_config(self.root)
        meta_path = self.root / ".docs/feature-demo/meta.yml"
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
            stack_tags=["react"],
            domains=["todo"],
            files=["src/features/todo/list/TodoList.tsx"],
            project_config=project_config,
        )

        saved = yaml.safe_load(meta_path.read_text(encoding="utf-8"))
        spec_context = saved["spec_context"]
        self.assertEqual(spec_context["index_status"], "ready")
        self.assertEqual(spec_context["last_checked_stage"], "ship-build")
        self.assertEqual(spec_context["referenced_spec_ids"], ["react-query-data-fetching"])
        self.assertEqual(saved["delegation"]["default_mode"], CURRENT_CONTEXT)
        self.assertEqual(saved["delegation"]["node_overrides"], {})
        self.assertEqual(saved["delegation"]["warnings"], [])

    def test_scan_specs_uses_project_root_for_custom_spec_root_paths(self) -> None:
        custom_root = self.root / "custom-spec"
        self.write_text(
            custom_root / "x.md",
            """---
spec_id: custom
scope: project
stage_hooks:
  - ship-build
last_updated: ""
---

# Custom
""",
        )

        result = scan_specs(custom_root, project_root=self.root)

        self.assertEqual(result["specs"][0]["path"], "custom-spec/x.md")

    def test_project_config_resolves_spec_and_feature_roots(self) -> None:
        config_path = self.write_project_config(
            self.root,
            spec_root=".docs/spec",
            feature_root="docs/features",
        )

        project_context = load_project_context(config_path)

        self.assertEqual(project_context.target_project_id, "project-a")
        self.assertEqual(project_context.target_project_root, ".")
        self.assertEqual(project_context.spec_root, ".docs/spec")
        self.assertEqual(project_context.feature_root, "docs/features")
        self.assertEqual(project_context.resolved_spec_root, (self.root / ".docs/spec").resolve())
        self.assertEqual(project_context.resolved_feature_root, (self.root / "docs/features").resolve())

    def test_resolve_specs_normalizes_files_against_target_project_root(self) -> None:
        workspace_root = self.root
        project_root = workspace_root / "project-a"
        spec_root = project_root / ".docs/spec"
        self.write_text(
            spec_root / "INDEX.md",
            "---\ndoc_type: spec-index\ndoc_status: active\nschema_version: 2\nupdated_at: \"\"\n---\n",
        )
        self.write_text(
            spec_root / "coding/backend.md",
            """---
spec_id: backend-rule
scope: file
stage_hooks:
  - ship-build
stack_tags: []
domains: []
applies_to:
  - "src/app.ts"
last_updated: "2026-05-29T10:00:00+08:00"
---
""",
        )
        config_path = self.write_project_config(project_root)
        previous_cwd = Path.cwd()
        os.chdir(workspace_root)
        try:
            result = resolve_specs(
                spec_root=None,
                project_context=load_project_context(config_path),
                stage_hook="ship-build",
                files=["project-a/src/app.ts"],
            )
        finally:
            os.chdir(previous_cwd)

        self.assertEqual(result["matched_spec_ids"], ["backend-rule"])
        self.assertEqual(result["normalized_files"], ["src/app.ts"])

    def test_scan_specs_returns_warning_when_project_spec_root_missing(self) -> None:
        config_path = self.write_project_config(self.root, spec_root=".docs/missing-spec")

        result = scan_specs(project_context=load_project_context(config_path))

        self.assertEqual(result["index_status"], "missing")
        self.assertTrue(any("spec directory does not exist" in warning for warning in result["warnings"]))


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

    def test_discover_and_shape_are_assistive_delegation_nodes(self) -> None:
        for node_id in ("ship-discover", "ship-shape"):
            result = resolve_delegation(
                node_id,
                {
                    "default_mode": ASSISTIVE_SUBAGENT,
                    "ask_on_assistive_node": False,
                },
            )
            self.assertEqual(result["resolved_mode"], ASSISTIVE_SUBAGENT)

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


class FeatureMetaRuntimeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def load_meta(self, feature_dir: Path) -> dict:
        return yaml.safe_load((feature_dir / "meta.yml").read_text(encoding="utf-8"))

    def write_project_config(
        self,
        project_root: Path,
        *,
        spec_root: str = ".docs/spec",
        feature_root: str = ".docs",
        project_id: str = "project-a",
    ) -> Path:
        path = project_root / ".docs/ship/project.yml"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            yaml.safe_dump(
                {
                    "schema_version": 1,
                    "project_id": project_id,
                    "project_name": "Project A",
                    "project_root": ".",
                    "spec_root": spec_root,
                    "feature_root": feature_root,
                    "module_layout": {
                        "mode": "project_level_only",
                        "module_roots": [],
                    },
                    "notes": "",
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )
        return path

    def test_create_feature_meta_initializes_greenfield_at_discover(self) -> None:
        feature_dir = self.root / "greenfield"
        create_feature_meta(
            feature_dir=feature_dir,
            feature_name="Greenfield",
            feature_id="feature-greenfield",
            pipeline_mode="standard",
            project_context="new_project",
            project_scope="fullstack",
            scenario="greenfield",
        )

        saved = self.load_meta(feature_dir)
        self.assertEqual(saved["scenario"], "greenfield")
        self.assertEqual(saved["current_stage"], "ship-discover")
        self.assertEqual(saved["macro_stage"]["current"], "discover")
        self.assertEqual(saved["stages"]["ship-discover"]["discovery_mode"], "greenfield")
        self.assertEqual(saved["stages"]["ship-define"]["generation_mode"], "interview")
        self.assertEqual(saved["lifecycle_status"], "active")
        self.assertEqual(saved["skip_log"], [])

    def test_feature_dir_for_uses_target_project_feature_root(self) -> None:
        project_root = self.root / "project-a"
        project_context = load_project_context(
            self.write_project_config(project_root, feature_root="docs/features")
        )

        feature_dir = feature_dir_for("feature-20260529-demo", project_context)

        self.assertEqual(feature_dir, (project_root / "docs/features/feature-20260529-demo").resolve())

    def test_create_feature_meta_initializes_prd_direct_at_define_and_skips_discover(self) -> None:
        feature_dir = self.root / "prd-direct"
        create_feature_meta(
            feature_dir=feature_dir,
            feature_name="PRD Direct",
            feature_id="feature-prd-direct",
            pipeline_mode="standard",
            project_context="existing_project",
            project_scope="fullstack",
            scenario="prd_direct",
        )

        saved = self.load_meta(feature_dir)
        self.assertEqual(saved["scenario"], "prd_direct")
        self.assertEqual(saved["current_stage"], "ship-define")
        self.assertEqual(saved["macro_stage"]["current"], "define")
        self.assertEqual(saved["stages"]["ship-discover"]["status"], "skipped")
        self.assertEqual(saved["stages"]["ship-shape"]["status"], "skipped")
        self.assertEqual(saved["stages"]["ship-define"]["status"], "blocked")
        self.assertEqual(saved["stages"]["ship-define"]["block_reason"], "awaiting_materials")
        self.assertFalse(saved["stages"]["ship-define"]["evidence_complete"])
        self.assertEqual(saved["stages"]["ship-define"]["generation_mode"], "prd_direct")
        self.assertTrue((feature_dir / "requirements.md").exists())
        self.assertTrue((feature_dir / "resource/README.md").exists())

    def test_create_feature_meta_initializes_product_provided_as_materials_wait(self) -> None:
        feature_dir = self.root / "product-provided"
        create_feature_meta(
            feature_dir=feature_dir,
            feature_name="Product Provided",
            feature_id="feature-product-provided",
            pipeline_mode="standard",
            project_context="existing_project",
            project_scope="fullstack",
            scenario="product_provided",
        )

        saved = self.load_meta(feature_dir)
        self.assertEqual(saved["current_stage"], "ship-define")
        self.assertEqual(saved["stages"]["ship-define"]["status"], "blocked")
        self.assertEqual(saved["stages"]["ship-define"]["block_reason"], "awaiting_materials")
        self.assertEqual(saved["stages"]["ship-define"]["generation_mode"], "interview")

    def test_mark_materials_ready_keeps_empty_template_blocked(self) -> None:
        feature_dir = self.root / "empty-materials"
        create_feature_meta(
            feature_dir=feature_dir,
            feature_name="Empty Materials",
            feature_id="feature-empty-materials",
            pipeline_mode="standard",
            project_context="existing_project",
            project_scope="fullstack",
            scenario="prd_direct",
        )

        payload = mark_materials_ready(feature_dir / "meta.yml")

        saved = self.load_meta(feature_dir)
        self.assertFalse(payload["materials_ready"])
        self.assertEqual(saved["stages"]["ship-define"]["status"], "blocked")
        self.assertEqual(saved["stages"]["ship-define"]["block_reason"], "awaiting_materials")

    def test_mark_materials_ready_releases_when_raw_prd_is_filled(self) -> None:
        feature_dir = self.root / "filled-prd"
        create_feature_meta(
            feature_dir=feature_dir,
            feature_name="Filled PRD",
            feature_id="feature-filled-prd",
            pipeline_mode="standard",
            project_context="existing_project",
            project_scope="fullstack",
            scenario="prd_direct",
        )
        requirements_path = feature_dir / "requirements.md"
        requirements_path.write_text(
            requirements_path.read_text(encoding="utf-8").replace(
                "[在这里粘贴 PRD 原文]",
                "完整 PRD 原文：用户可以创建订单并查看订单状态。",
            ),
            encoding="utf-8",
        )

        payload = mark_materials_ready(feature_dir / "meta.yml")

        saved = self.load_meta(feature_dir)
        self.assertTrue(payload["materials_ready"])
        self.assertEqual(saved["stages"]["ship-define"]["status"], "pending")
        self.assertEqual(saved["stages"]["ship-define"]["block_reason"], "")
        self.assertFalse(saved["stages"]["ship-define"]["evidence_complete"])

    def test_create_feature_meta_backend_only_sets_delivery_plan_part(self) -> None:
        feature_dir = self.root / "backend-only"
        create_feature_meta(
            feature_dir=feature_dir,
            feature_name="Backend Only",
            feature_id="feature-backend-only",
            pipeline_mode="standard",
            project_context="existing_project",
            project_scope="backend_only",
            scenario="product_provided",
        )

        saved = self.load_meta(feature_dir)
        self.assertEqual(saved["stages"]["ship-frontend-design"]["status"], "skipped")
        self.assertEqual(saved["stages"]["ship-delivery-plan"]["current_part"], "backend")

    def test_create_feature_meta_writes_target_project_spec_context(self) -> None:
        project_root = self.root / "project-a"
        project_context = load_project_context(self.write_project_config(project_root))
        feature_dir = feature_dir_for("feature-project-local", project_context)

        create_feature_meta(
            feature_dir=feature_dir,
            feature_name="Project Local",
            feature_id="feature-project-local",
            pipeline_mode="standard",
            project_context="existing_project",
            project_scope="fullstack",
            scenario="product_provided",
            project_spec_context=project_context,
        )

        saved = self.load_meta(feature_dir)
        self.assertEqual(saved["spec_context"]["target_project_id"], "project-a")
        self.assertEqual(saved["spec_context"]["target_project_root"], ".")
        self.assertEqual(saved["spec_context"]["spec_root"], ".docs/spec")
        self.assertEqual(saved["spec_context"]["feature_root"], ".docs")
        self.assertEqual(saved["spec_context"]["resolution_source"], "project_config")

    def test_sync_spec_context_updates_target_project_fields(self) -> None:
        project_root = self.root / "project-a"
        spec_root = project_root / ".docs/spec"
        project_config = self.write_project_config(project_root)
        (spec_root / "coding").mkdir(parents=True, exist_ok=True)
        (spec_root / "INDEX.md").write_text(
            "---\ndoc_type: spec-index\ndoc_status: active\nschema_version: 2\nupdated_at: \"\"\n---\n",
            encoding="utf-8",
        )
        (spec_root / "coding/frontend-data.md").write_text(
            """---
spec_id: react-query-data-fetching
scope: module
stage_hooks:
  - ship-build
stack_tags:
  - react
domains:
  - todo
applies_to:
  - "src/features/todo/**/*.tsx"
last_updated: "2026-05-23T10:00:00+08:00"
---
""",
            encoding="utf-8",
        )
        feature_dir = feature_dir_for("feature-sync", load_project_context(project_config))
        create_feature_meta(
            feature_dir=feature_dir,
            feature_name="Sync",
            feature_id="feature-sync",
            pipeline_mode="standard",
            project_context="existing_project",
            project_scope="fullstack",
            scenario="product_provided",
        )

        sync_spec_context(
            meta_path=feature_dir / "meta.yml",
            stage_hook="ship-build",
            stack_tags=["react"],
            domains=["todo"],
            files=["src/features/todo/list/TodoList.tsx"],
            project_config=project_config,
        )

        saved = self.load_meta(feature_dir)
        self.assertEqual(saved["spec_context"]["target_project_id"], "project-a")
        self.assertEqual(saved["spec_context"]["target_project_root"], ".")
        self.assertEqual(saved["spec_context"]["spec_root"], ".docs/spec")
        self.assertEqual(saved["spec_context"]["feature_root"], ".docs")
        self.assertEqual(saved["spec_context"]["referenced_spec_ids"], ["react-query-data-fetching"])

    def test_sync_spec_context_requires_project_config_or_meta_target_project(self) -> None:
        feature_dir = self.root / "feature-missing-target"
        feature_dir.mkdir(parents=True, exist_ok=True)
        (feature_dir / "meta.yml").write_text(
            yaml.safe_dump(
                {
                    "feature_name": "Missing Target",
                    "feature_id": "feature-missing-target",
                    "current_stage": "ship-build",
                    "spec_context": {},
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )

        with self.assertRaisesRegex(ValueError, "provide --project-config"):
            sync_spec_context(
                meta_path=feature_dir / "meta.yml",
                stage_hook="ship-build",
                stack_tags=[],
                domains=[],
                files=["src/app.ts"],
            )

    def test_resolve_project_context_does_not_guess_between_multiple_child_projects(self) -> None:
        workspace_root = self.root / "workspace"
        project_a = workspace_root / "project-a"
        project_b = workspace_root / "project-b"
        self.write_project_config(project_a, project_id="project-a")
        self.write_project_config(project_b, project_id="project-b")

        with self.assertRaisesRegex(ValueError, "provide --project-config"):
            resolve_project_context(search_from=workspace_root)

    def test_record_spec_proposal_only_allows_handoff_source(self) -> None:
        feature_dir = self.root / "proposal"
        create_feature_meta(
            feature_dir=feature_dir,
            feature_name="Proposal",
            feature_id="feature-proposal",
            pipeline_mode="standard",
            project_context="existing_project",
            project_scope="fullstack",
            scenario="product_provided",
        )
        meta_path = feature_dir / "meta.yml"

        with self.assertRaisesRegex(ValueError, "ship-handoff"):
            record_spec_proposal(
                meta_path=meta_path,
                proposal_id="proposal-001",
                title="Too early",
                source_stage="ship-build",
                target_spec_id="error-handling",
                summary="early proposal",
            )

        proposal = record_spec_proposal(
            meta_path=meta_path,
            proposal_id="proposal-001",
            title="Handoff proposal",
            source_stage="ship-handoff",
            target_spec_id="error-handling",
            summary="handoff proposal",
        )
        self.assertEqual(proposal["source_stage"], "ship-handoff")

    def test_record_skip_lifecycle_and_advance_stage(self) -> None:
        feature_dir = self.root / "advance"
        create_feature_meta(
            feature_dir=feature_dir,
            feature_name="Advance",
            feature_id="feature-advance",
            pipeline_mode="standard",
            project_context="new_project",
            project_scope="fullstack",
            scenario="greenfield",
        )
        meta_path = feature_dir / "meta.yml"

        skip = record_skip(
            meta_path=meta_path,
            from_stage="ship-discover",
            to_stage="ship-define",
            gate_type="soft",
            reason="user requested direct define",
            user_sign_off="skip discover",
        )
        self.assertEqual(skip["from_stage"], "ship-discover")

        lifecycle = set_lifecycle_status(meta_path, "blocked")
        self.assertEqual(lifecycle["lifecycle_status"], "blocked")

        payload = advance_stage(
            meta_path=meta_path,
            from_stage="ship-discover",
            to_stage="ship-define",
        )
        self.assertEqual(payload["current_stage"], "ship-define")

        saved = self.load_meta(feature_dir)
        self.assertEqual(saved["stages"]["ship-discover"]["status"], "completed")
        self.assertEqual(saved["stages"]["ship-define"]["status"], "pending")
        self.assertEqual(saved["macro_stage"]["current"], "define")
        self.assertEqual(saved["skip_log"][0]["reason"], "user requested direct define")
        self.assertEqual(saved["delegation"]["default_mode"], CURRENT_CONTEXT)


if __name__ == "__main__":
    unittest.main()
