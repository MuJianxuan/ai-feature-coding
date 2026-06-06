#!/usr/bin/env python3
"""Tests for workflow doctor and feature artifact validators."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import sys

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from stage_transition_check import check_transition
from validate_feature_artifacts import validate_feature
from validate_contract import validate_contract_file
from validate_delivery_plan import validate_delivery_plan
from build_task_preflight import build_task_preflight
from validate_requirements import validate_requirements_file
from validate_traceability import validate_traceability
from validate_verification import validate_verification_file
from validate_handoff import validate_handoff
from validate_tech_discovery import validate_tech_discovery
from validate_design_alignment import validate_design_alignment
from validate_frontend_design import validate_frontend_design
from validate_backend_design import validate_backend_design
from workflow_doctor import diagnose_feature


class WorkflowHardeningTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.feature_dir = self.root / "feature-demo"
        self.feature_dir.mkdir(parents=True)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def write_text(self, relative_path: str, content: str) -> None:
        path = self.feature_dir / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def write_meta(
        self,
        *,
        current_stage: str = "ship-define-review",
        project_scope: str = "fullstack",
        project_scope_evidence: str = "",
        project_context: str = "existing_project",
        scenario: str = "product_provided",
        pipeline_mode: str = "standard",
        define_status: str = "ready",
        define_review_status: str = "pending",
    ) -> None:
        stages = {
            "ship-discover": {"status": "skipped"},
            "ship-shape": {"status": "skipped"},
            "ship-define": {"status": define_status, "block_reason": ""},
            "ship-define-review": {"status": define_review_status, "approved": define_review_status == "approved"},
            "ship-tech-discovery": {"status": "pending"},
            "ship-contract": {"status": "pending"},
            "ship-frontend-design": {"status": "pending"},
            "ship-backend-design": {"status": "pending"},
            "ship-design-review": {"status": "pending", "approved": False},
            "ship-delivery-plan": {"status": "pending"},
            "ship-plan-review": {"status": "pending", "approved": False},
            "ship-build": {"status": "pending", "tasks_done": 0, "tasks_total": 0},
            "ship-verify": {"status": "pending"},
            "ship-handoff": {"status": "pending"},
        }
        macro_by_stage = {
            "ship-discover": ("discover", "Discover"),
            "ship-shape": ("discover", "Discover"),
            "ship-define": ("define", "Define"),
            "ship-define-review": ("define", "Define"),
            "ship-tech-discovery": ("design", "Design"),
            "ship-contract": ("design", "Design"),
            "ship-frontend-design": ("design", "Design"),
            "ship-backend-design": ("design", "Design"),
            "ship-design-review": ("design", "Design"),
            "ship-delivery-plan": ("build", "Build"),
            "ship-plan-review": ("build", "Build"),
            "ship-build": ("build", "Build"),
            "ship-verify": ("build", "Build"),
            "ship-handoff": ("close", "Close"),
        }
        macro_current, macro_label = macro_by_stage[current_stage]
        payload = {
            "feature_name": "Demo",
            "feature_id": "feature-demo",
            "current_stage": current_stage,
            "scenario": scenario,
            "pipeline_mode": pipeline_mode,
            "project_scope": project_scope,
            "project_scope_evidence": project_scope_evidence,
            "project_context": project_context,
            "macro_stage": {"current": macro_current, "label": macro_label, "summary": "", "next_user_decision": ""},
            "lifecycle_status": "active",
            "stages": stages,
        }
        self.write_text("meta.yml", yaml.safe_dump(payload, sort_keys=False))

    def write_requirements(self, *, status: str = "ready") -> None:
        self.write_text(
            "requirements.md",
            f"""---
stage: ship-define
stage_status: {status}
updated_at: "2026-05-31T10:00:00+08:00"
evidence_complete: true
---

# Requirements

## 3. 功能范围
In Scope: 用户登录。
Out of Scope: 用户注册。

## 4. 业务域建模
- D-AUTH-001 用户认证

## 5. 验收标准
- AC-AUTH-001 | D-AUTH-001 | Given 用户在登录页, When 提交正确凭证, Then 进入首页

## 6. 非功能需求
性能：登录 API P95 < 500ms。
安全：登录接口需要认证、授权和审计。
可用性：认证服务异常时返回明确错误。
可访问性：表单支持键盘导航。

## 8. 待确认问题清单
- 无阻塞问题。

## 9. 需求资料索引
- resource/prd.md 已解析
""",
        )

    def write_define_review(self, *, status: str = "pending", signed: bool = False) -> None:
        sign_off = '"approved by user"' if signed else '""'
        signed_at = '"2026-05-31T10:00:00+08:00"' if signed else '""'
        self.write_text(
            "review-define.md",
            f"""---
stage: ship-define-review
gate_type: hard
review_status: {status}
reviewer: ""
reviewed_at: ""
reviewed_documents: ["requirements.md"]
revision_count: 0
user_sign_off: {sign_off}
signed_at: {signed_at}
conditions: []
---

# Review
""",
        )

    def test_ready_requirements_allows_define_review_entry(self) -> None:
        self.write_meta(current_stage="ship-define")
        self.write_requirements(status="ready")

        result = check_transition(self.feature_dir, "ship-define-review")

        self.assertTrue(result["allowed"], result["issues"])

    def test_unsigned_approved_gate_blocks_transition(self) -> None:
        self.write_meta(current_stage="ship-define-review", define_review_status="approved")
        self.write_requirements(status="ready")
        self.write_define_review(status="approved", signed=False)

        validation = validate_feature(self.feature_dir)
        transition = check_transition(self.feature_dir, "ship-tech-discovery")
        doctor = diagnose_feature(self.feature_dir)

        self.assertFalse(validation["ok"])
        self.assertTrue(any(issue["code"] == "unsigned_approved_gate" for issue in validation["issues"]))
        self.assertFalse(transition["allowed"])
        self.assertEqual(doctor["next_action"]["action"], "fix_blocking_issues")

    def test_meta_artifact_conflict_is_reported(self) -> None:
        self.write_meta(current_stage="ship-define-review", define_status="ready")
        self.write_requirements(status="draft")

        result = validate_feature(self.feature_dir)

        self.assertFalse(result["ok"])
        self.assertTrue(any(issue["code"] == "meta_artifact_status_conflict" for issue in result["issues"]))

    def test_requirements_ready_requires_domain_ac_and_no_blockers(self) -> None:
        self.write_requirements(status="ready")
        self.write_text(
            "requirements.md",
            """---
stage: ship-define
stage_status: ready
generation_mode: interview
updated_at: "2026-05-31T10:00:00+08:00"
evidence_complete: true
---

# Requirements

## 3. 功能范围
In Scope: 支持登录。
Out of Scope: 注册。

## 5. 验收标准
- AC-AUTH-001 | Given 用户在登录页, When 提交正确凭证, Then 进入首页

## 6. 非功能需求
性能：P95 < 500ms。
安全：需要认证。

## 8. 待确认问题清单
- [ ] Q-1: OAuth provider 未确认 | 影响: High | 阻塞: 是

## 9. 需求资料索引
- resource/prd.md
""",
        )

        result = validate_requirements_file(self.feature_dir / "requirements.md")

        self.assertFalse(result["ok"])
        codes = {issue["code"] for issue in result["issues"]}
        self.assertIn("missing_domain_ids", codes)
        self.assertIn("ac_missing_domain_ref", codes)
        self.assertIn("ready_with_blocking_questions", codes)

    def test_requirements_valid_ready_passes_with_warnings_allowed(self) -> None:
        self.write_text(
            "requirements.md",
            """---
stage: ship-define
stage_status: ready
generation_mode: interview
updated_at: "2026-05-31T10:00:00+08:00"
evidence_complete: true
---

# Requirements

## 3. 功能范围
In Scope: 用户登录。
Out of Scope: 用户注册。

## 4. 业务域建模
- D-AUTH-001 用户认证

## 5. 验收标准
- AC-AUTH-001 | D-AUTH-001 | Given 用户在登录页, When 提交正确凭证, Then 进入首页

## 6. 非功能需求
性能：登录 API P95 < 500ms。
安全：登录接口需要认证、授权和审计。
可用性：认证服务异常时返回明确错误。
可访问性：表单支持键盘导航。

## 8. 待确认问题清单
- 无阻塞问题。

## 9. 需求资料索引
- resource/prd.md 已解析
""",
        )

        result = validate_requirements_file(self.feature_dir / "requirements.md")

        self.assertTrue(result["ok"], result["issues"])

    def test_technical_plan_requirements_ready_requires_selected_scope_source_index(self) -> None:
        self.write_text(
            "requirements.md",
            """---
stage: ship-define
stage_status: ready
generation_mode: technical_plan
updated_at: "2026-05-31T10:00:00+08:00"
evidence_complete: true
---

# Requirements

## 3. 功能范围
In Scope: 订单导出。
Out of Scope: 订单导入。

## 4. 业务域建模
- D-ORDER-001 订单导出

## 5. 验收标准
- AC-ORDER-001 | D-ORDER-001 | Given 管理员在订单页, When 提交导出, Then 系统返回导出任务 ID

## 6. 非功能需求
性能：导出请求 P95 < 500ms。
安全：导出接口需要认证、授权和审计。
可用性：任务服务异常时返回明确错误。
可访问性：下载入口支持键盘导航。

## 8. 待确认问题清单
- 无阻塞问题。

## 9. 需求资料索引
- resource/order-export-tech-design.md 已解析
""",
        )

        result = validate_requirements_file(self.feature_dir / "requirements.md")

        self.assertFalse(result["ok"])
        self.assertTrue(any(issue["code"] == "technical_plan_missing_source_index" for issue in result["issues"]))

    def test_technical_plan_requirements_ready_passes_with_selected_scope_source_index(self) -> None:
        self.write_text(
            "requirements.md",
            """---
stage: ship-define
stage_status: ready
generation_mode: technical_plan
source_documents:
  - resource/order-export-tech-design.md#3.2-order-export
selected_scope:
  - 3.2 Order export async task
updated_at: "2026-05-31T10:00:00+08:00"
evidence_complete: true
---

# Requirements

## 3. 功能范围
In Scope: 订单导出。
Out of Scope: 订单导入。

## 4. 业务域建模
- D-ORDER-001 订单导出

## 5. 验收标准
- AC-ORDER-001 | D-ORDER-001 | Given 管理员在订单页, When 提交导出, Then 系统返回导出任务 ID

## 6. 非功能需求
性能：导出请求 P95 < 500ms。
安全：导出接口需要认证、授权和审计。
可用性：任务服务异常时返回明确错误。
可访问性：下载入口支持键盘导航。

## 8. 待确认问题清单
- 无阻塞问题。

## 9. 需求资料索引
- selected scope: resource/order-export-tech-design.md#3.2-order-export
""",
        )

        result = validate_requirements_file(self.feature_dir / "requirements.md")

        self.assertTrue(result["ok"], result["issues"])

    def test_traceability_reports_ac_gaps_and_orphans(self) -> None:
        self.write_requirements(status="ready")
        self.write_text(
            "api-contract.md",
            """---
stage: ship-contract
stage_status: ready
updated_at: ""
evidence_complete: true
---

AC-AUTH-999
""",
        )
        self.write_text(
            "frontend-plan.md",
            """---
stage: ship-delivery-plan
artifact_role: frontend-plan
stage_status: ready
updated_at: ""
evidence_complete: true
---

AC-AUTH-001
""",
        )

        result = validate_traceability(self.feature_dir)

        self.assertTrue(result["ok"], result["issues"])
        codes = {issue["code"] for issue in result["issues"]}
        self.assertIn("ac_trace_gap", codes)
        self.assertIn("orphan_ac_ref", codes)

    def test_traceability_passes_when_required_links_exist(self) -> None:
        self.write_requirements(status="ready")
        for relative_path in ("api-contract.md", "frontend-plan.md", "verification.md"):
            self.write_text(relative_path, "AC-AUTH-001\n")

        result = validate_traceability(self.feature_dir)

        self.assertTrue(result["ok"], result["issues"])
        self.assertFalse(any(issue["code"] == "ac_trace_gap" for issue in result["issues"]))

    def test_contract_ready_requires_endpoint_error_schema_and_ac_refs(self) -> None:
        self.write_text(
            "api-contract.md",
            """---
stage: ship-contract
stage_status: ready
contract_forms: [rest]
updated_at: "2026-05-31T10:00:00+08:00"
evidence_complete: true
---

# API Contract

#### POST /api/v1/login
- 描述：登录
""",
        )

        result = validate_contract_file(self.feature_dir / "api-contract.md")

        self.assertFalse(result["ok"])
        codes = {issue["code"] for issue in result["issues"]}
        self.assertIn("missing_ac_refs", codes)
        self.assertIn("endpoint_missing_ac_refs", codes)
        self.assertIn("missing_schema_section", codes)
        self.assertIn("missing_error_codes", codes)

    def test_contract_valid_rest_ready_passes(self) -> None:
        self.write_text(
            "api-contract.md",
            """---
stage: ship-contract
stage_status: ready
contract_forms: [rest]
updated_at: "2026-05-31T10:00:00+08:00"
evidence_complete: true
---

# API Contract

## 1. Summary
REST contract for D-AUTH-001. OpenAPI artifact: resource/openapi.yaml.
Change classification: additive.

## 3. Domain Contract Blocks
#### POST /api/v1/login
- 描述：登录
- 关联 AC：AC-AUTH-001
- 关联页面：LoginPage
- 请求参数：
  | 位置 | 字段 | 类型 | 必填 | 校验 | 说明 |
  | body | email | string | 是 | email | 邮箱 |
- 成功响应：200
- 错误响应：
  | 错误码 | HTTP Status | 条件 | 前端处理 |
  | ERR_AUTH_INVALID | 401 | 凭证错误 | 显示错误 |

## 4. 数据模型
```ts
interface LoginRequest { email: string; password: string }
```
""",
        )

        result = validate_contract_file(self.feature_dir / "api-contract.md")

        self.assertTrue(result["ok"], result["issues"])

    def write_plan(self, relative_path: str, role: str, body: str) -> None:
        self.write_text(
            relative_path,
            f"""---
stage: ship-delivery-plan
artifact_role: {role}
stage_status: ready
updated_at: "2026-05-31T10:00:00+08:00"
evidence_complete: true
task_count: 1
---

{body}
""",
        )

    def task_brief(self, *, goal: str = "完成登录信息变更", context: str = "仓库探索证据：src/auth.ts；接口：POST /api/v1/login。") -> str:
        return f"""任务目标：
{goal}

上下文：
{context}

约束：
不要改后端接口；不要重写鉴权系统；保留现有 storage key。

验收：
AC-AUTH-001 通过；verification_command 通过。

输出：
直接修改 allowed_files 中列出的代码，并说明改了哪些文件。
"""

    def test_delivery_plan_requires_task_schema_and_detects_cycles(self) -> None:
        self.write_plan(
            "frontend-plan.md",
            "frontend-plan",
            f"""## Tasks
### FE-AUTH-001
- project: web
- scope: login UI
- allowed_files: src/login.tsx
- depends_on: FE-AUTH-002
- AC refs: AC-AUTH-001
- contract refs: POST /api/v1/login
- verification command: npm test
- done evidence: test output
{self.task_brief()}

### FE-AUTH-002
- project: web
- scope: api client
- allowed_files: src/api.ts
- depends_on: FE-AUTH-001
- AC refs: AC-AUTH-001
- contract refs: POST /api/v1/login
- verification command: npm test
- done evidence: test output
{self.task_brief(goal="完成登录 API client 变更", context="仓库探索证据：src/api.ts；接口：POST /api/v1/login。")}
""",
        )
        self.write_plan(
            "backend-plan.md",
            "backend-plan",
            f"""## Tasks
### BE-AUTH-001
- project: api
- scope: login endpoint
- allowed_files: src/auth.ts
- depends_on:
- AC refs: AC-AUTH-001
- contract refs: POST /api/v1/login
- verification command: npm test
- done evidence: test output
{self.task_brief(context="仓库探索证据：src/auth.ts；接口：POST /api/v1/login。")}
""",
        )

        result = validate_delivery_plan(self.feature_dir)

        self.assertFalse(result["ok"])
        self.assertTrue(any(issue["code"] == "task_dependency_cycle" for issue in result["issues"]))

    def test_delivery_plan_backend_only_valid_ready_passes(self) -> None:
        self.write_plan(
            "backend-plan.md",
            "backend-plan",
            f"""## Tasks
### BE-AUTH-001
- project: api
- scope: login endpoint
- allowed_files: src/auth.ts
- depends_on:
- AC refs: AC-AUTH-001
- contract refs: POST /api/v1/login
- verification command: npm test
- done evidence: test output
{self.task_brief(context="仓库探索证据：src/auth.ts；接口：POST /api/v1/login。")}
""",
        )

        result = validate_delivery_plan(self.feature_dir, project_scope="backend_only")

        self.assertTrue(result["ok"], result["issues"])

    def test_delivery_plan_ready_requires_task_brief_sections(self) -> None:
        self.write_plan(
            "backend-plan.md",
            "backend-plan",
            f"""## Tasks
### BE-AUTH-001
- project: api
- scope: login endpoint
- allowed_files: src/auth.ts
- depends_on:
- AC refs: AC-AUTH-001
- contract refs: POST /api/v1/login
- verification command: npm test
- done evidence: test output
任务目标：
完成登录 endpoint 变更

约束：
不要改后端接口。

验收：
AC-AUTH-001 通过。

输出：
直接修改代码，并说明改了哪些文件。
""",
        )

        result = validate_delivery_plan(self.feature_dir, project_scope="backend_only")

        self.assertFalse(result["ok"])
        self.assertTrue(any(issue["code"] == "task_missing_brief_section" and "上下文" in issue["message"] for issue in result["issues"]))

    def test_build_task_preflight_requires_single_ready_doing_task(self) -> None:
        self.write_plan(
            "backend-plan.md",
            "backend-plan",
            f"""## Tasks
### BE-AUTH-001
- status: DOING
- project: api
- scope: login endpoint
- allowed_files: src/auth.ts
- depends_on:
- AC refs: AC-AUTH-001
- contract refs: POST /api/v1/login
- verification command: npm test
- done evidence: test output
{self.task_brief(context="仓库探索证据：src/auth.ts；接口：POST /api/v1/login。")}
""",
        )

        result = build_task_preflight(self.feature_dir, project_scope="backend_only")

        self.assertTrue(result["ok"], result["issues"])
        self.assertEqual(len(result["doing_tasks"]), 1)

    def test_build_task_preflight_blocks_multiple_doing_tasks(self) -> None:
        self.write_plan(
            "backend-plan.md",
            "backend-plan",
            """## Tasks
### BE-AUTH-001
- status: DOING
- project: api
- scope: login endpoint
- allowed_files: src/auth.ts
- AC refs: AC-AUTH-001
- verification command: npm test
{self.task_brief(context="仓库探索证据：src/auth.ts；接口：POST /api/v1/login。")}

### BE-AUTH-002
- status: DOING
- project: api
- scope: auth tests
- allowed_files: src/auth.test.ts
- AC refs: AC-AUTH-001
- verification command: npm test
{self.task_brief(goal="补充认证测试", context="仓库探索证据：src/auth.test.ts；接口：POST /api/v1/login。")}
""",
        )

        result = build_task_preflight(self.feature_dir, project_scope="backend_only")

        self.assertFalse(result["ok"])
        self.assertTrue(any(issue["code"] == "doing_count_invalid" for issue in result["issues"]))

    def test_fast_track_build_preflight_reads_fast_track_tasks(self) -> None:
        self.write_text(
            "fast-track-tasks.md",
            f"""---
stage: ship-build
artifact_role: fast-track-tasks
stage_status: draft
evidence_complete: false
---

### Task FT-001: Fix login button state
- status: DOING
- allowed_files:
  - src/pages/Login.tsx
- ac_refs:
  - AC-AUTH-001
- verification_command: pnpm test -- Login
- evidence:
  - pending
{self.task_brief(goal="修复登录按钮状态", context="仓库探索证据：src/pages/Login.tsx；前端为 React 登录页。")}
""",
        )

        result = build_task_preflight(self.feature_dir, pipeline_mode="fast-track")

        self.assertTrue(result["ok"], result["issues"])
        self.assertEqual(result["tasks"][0]["path"], "fast-track-tasks.md")

    def test_fast_track_build_preflight_requires_task_brief_sections(self) -> None:
        self.write_text(
            "fast-track-tasks.md",
            """---
stage: ship-build
artifact_role: fast-track-tasks
stage_status: draft
evidence_complete: false
---

### Task FT-001: Fix login button state
- status: DOING
- allowed_files:
  - src/pages/Login.tsx
- ac_refs:
  - AC-AUTH-001
- verification_command: pnpm test -- Login
- evidence:
  - pending
任务目标：
修复登录按钮状态

上下文：
仓库探索证据：src/pages/Login.tsx；前端为 React 登录页。

约束：
不要重写登录页。

输出：
直接修改代码，并说明改了哪些文件。
""",
        )

        result = build_task_preflight(self.feature_dir, pipeline_mode="fast-track")

        self.assertFalse(result["ok"])
        self.assertTrue(any(issue["code"] == "doing_missing_task_brief_section" and "验收" in issue["message"] for issue in result["issues"]))

    def test_standard_build_preflight_still_requires_plan_source(self) -> None:
        self.write_text(
            "fast-track-tasks.md",
            """---
stage: ship-build
artifact_role: fast-track-tasks
stage_status: draft
evidence_complete: false
---

### Task FT-001
- status: DOING
- allowed_files: src/pages/Login.tsx
- ac_refs: AC-AUTH-001
- verification_command: pnpm test -- Login
""",
        )

        result = build_task_preflight(self.feature_dir, project_scope="backend_only")

        self.assertFalse(result["ok"])
        self.assertTrue(any(issue["code"] == "missing_plan" for issue in result["issues"]))

    def write_verification(self, body: str, *, status: str = "ready", all_ac_verified: bool = False) -> None:
        self.write_text(
            "verification.md",
            f"""---
stage: ship-handoff
stage_status: {status}
updated_at: "2026-05-31T10:00:00+08:00"
all_ac_verified: {str(all_ac_verified).lower()}
---

{body}
""",
        )

    def test_verification_requires_tracks_and_linked_ac(self) -> None:
        self.write_verification(
            """## Test Runs
track: backend-unit
command: npm test
status: PASS
evidence: output
failure_class: none
linked_ac: AC-AUTH-001
""",
            status="ready",
        )

        result = validate_verification_file(self.feature_dir / "verification.md", project_scope="fullstack")

        self.assertFalse(result["ok"])
        self.assertTrue(any(issue["code"] == "missing_required_test_tracks" for issue in result["issues"]))

    def test_verification_backend_only_valid_ready_passes(self) -> None:
        self.write_verification(
            """## Test Runs
track: backend-unit
track: backend-integration
track: backend-contract
command: npm test
status: PASS
evidence: output
failure_class: none
linked_ac: AC-AUTH-001
N/A frontend-component reason: backend_only scope
N/A frontend-e2e reason: backend_only scope
""",
            status="ready",
        )

        result = validate_verification_file(self.feature_dir / "verification.md", project_scope="backend_only")

        self.assertTrue(result["ok"], result["issues"])

    def write_handoff(self) -> None:
        self.write_text(
            "handoff.md",
            """---
stage: ship-handoff
stage_status: complete
updated_at: "2026-05-31T10:00:00+08:00"
---

## 交付摘要
完成登录。

## 变更范围
- src/auth.ts

## 部署事项
- 环境变量：无
- 数据库迁移：无
- 配置变更：无
- 第三方依赖：无

## 后续建议
- 无

## Spec Proposals
- 无新增规范
""",
        )

    def test_handoff_requires_ac_evidence_and_complete_flag(self) -> None:
        self.write_requirements(status="ready")
        self.write_verification("AC-AUTH-001 | PASS | 自动化 E2E\n", status="complete", all_ac_verified=False)
        self.write_handoff()

        result = validate_handoff(self.feature_dir)

        self.assertFalse(result["ok"])
        codes = {issue["code"] for issue in result["issues"]}
        self.assertIn("pass_ac_missing_evidence", codes)
        self.assertIn("complete_without_all_ac_verified", codes)

    def test_handoff_valid_complete_passes(self) -> None:
        self.write_requirements(status="ready")
        self.write_verification("AC-AUTH-001 | PASS | evidence `e2e/auth.spec.ts:12`\n", status="complete", all_ac_verified=True)
        self.write_handoff()

        result = validate_handoff(self.feature_dir)

        self.assertTrue(result["ok"], result["issues"])

    def test_tech_discovery_requires_source_refs_when_ready(self) -> None:
        self.write_text(
            "tech-research.md",
            """---
stage: ship-tech-discovery
artifact_role: research
stage_status: ready
updated_at: ""
evidence_complete: true
---

# Research
No sources.
""",
        )
        self.write_text(
            "tech-selection.md",
            """---
stage: ship-tech-discovery
artifact_role: selection
stage_status: ready
updated_at: ""
evidence_complete: true
---

# Selection
Decision: use FastAPI.
""",
        )

        result = validate_tech_discovery(self.feature_dir)

        self.assertFalse(result["ok"])
        self.assertTrue(any(issue["code"] == "research_missing_source_ids" for issue in result["issues"]))

    def write_selection_ready(self) -> None:
        self.write_text(
            "tech-selection.md",
            """---
stage: ship-tech-discovery
artifact_role: selection
stage_status: ready
updated_at: ""
evidence_complete: true
---

# Selection

Decision: use existing auth stack. source_id: SRC-AUTH-001
Rejected: custom auth.
ADR: ADR-AUTH-001
tech_stack: Node service
""",
        )

    def write_research_ready(self, body: str) -> None:
        self.write_text(
            "tech-research.md",
            f"""---
stage: ship-tech-discovery
artifact_role: research
stage_status: ready
updated_at: ""
evidence_complete: true
---

{body}
""",
        )

    def valid_research_body(self, project_context: str = "existing_project") -> str:
        project_scan = (
            "Target project: demo. project_context: existing_project. "
            "Confirmed src/modules/auth/auth.service.ts, src/routes/auth.ts, prisma/schema.prisma, src/pages/LoginPage.tsx. source_id: SRC-AUTH-001"
            if project_context == "existing_project"
            else "不适用：new_project，无既有代码基线。project_context: new_project. source_id: SRC-AUTH-001"
        )
        mapping = (
            "| Domain / AC | 需求摘要 | 现有项目发现 | 关系类型 | 证据路径 | 不确定项 |\n"
            "|---|---|---|---|---|---|\n"
            "| D-AUTH-001 / AC-AUTH-001 | 登录 | 已有 auth route 和 AuthService | extend | src/routes/auth.ts, src/modules/auth/auth.service.ts | 无 |\n"
        )
        if project_context == "new_project":
            mapping = (
                "| Domain / AC | 需求摘要 | 现有项目发现 | 关系类型 | 证据路径 | 不确定项 |\n"
                "|---|---|---|---|---|---|\n"
                "| D-AUTH-001 / AC-AUTH-001 | 登录 | new_project 无既有代码基线 | new | requirements.md | 初始化方案待 selection |\n"
            )
        return f"""# Tech Research

## Project Reality Scan / 项目现状发现
{project_scan}

## Requirement-to-Reality Mapping / 需求与已有系统映射
{mapping}
Relation types covered: reuse / extend / replace / new / avoid / unknown.

## Existing Surface Inventory / 现有表面清单
| Surface | Existing Item | Path / Source | Relation | Notes |
|---|---|---|---|---|
| API | POST /api/v1/login | src/routes/auth.ts | extend | existing_project auth endpoint |
| Backend Service | AuthService | src/modules/auth/auth.service.ts | extend | credential validation |

## Evidence and Uncertainty / 证据与不确定项
### Confirmed Facts
- FACT-001: Auth route exists at src/routes/auth.ts. source_id: SRC-AUTH-001
### Conflicting Evidence
- None.
### Open Questions
- None.

## Research Alignment Check / 产出前对齐记录
### Alignment Summary Presented to User
- 当前理解：复用已有 AuthService 和 POST /api/v1/login。
- 准备复用 / 扩展：src/routes/auth.ts, src/modules/auth/auth.service.ts。
- 不确定项：无阻塞项。
- 若按当前理解继续，将影响：api-contract.md 与 backend-design.md 会扩展现有 auth surface。
### User Feedback
- 用户确认：继续按现有 auth surface 扩展。
- 用户纠正：无。
- 用户要求按假设继续：无。
### Follow-up Exploration
- 重新探索的路径：无纠正，未触发。
- 修正后的结论：无。
### Final Research Baseline
- 本 research 产物基于 FACT-001 和 SRC-AUTH-001。
- assumptions：无阻塞假设。

## Technical Research / 技术调研
- source_id: SRC-AUTH-001 official auth framework docs.

## Selection Inputs / 给 tech-selection.md 的输入
- 复用 AuthService，扩展 existing endpoint，保持 additive change。

## 信息来源清单
- source_id: SRC-AUTH-001 official auth framework docs and local src/routes/auth.ts.
"""

    def test_tech_discovery_existing_project_requires_project_reality_scan(self) -> None:
        self.write_meta(project_context="existing_project")
        body = self.valid_research_body().replace("## Project Reality Scan / 项目现状发现", "## Removed Reality")
        self.write_research_ready(body)
        self.write_selection_ready()

        result = validate_tech_discovery(self.feature_dir)

        self.assertFalse(result["ok"])
        self.assertTrue(any(issue["code"] == "missing_project_reality_scan" for issue in result["issues"]))

    def test_tech_discovery_existing_project_requires_alignment_check(self) -> None:
        self.write_meta(project_context="existing_project")
        body = self.valid_research_body().replace("## Research Alignment Check / 产出前对齐记录", "## Removed Alignment")
        self.write_research_ready(body)
        self.write_selection_ready()

        result = validate_tech_discovery(self.feature_dir)

        self.assertFalse(result["ok"])
        self.assertTrue(any(issue["code"] == "missing_research_alignment_check" for issue in result["issues"]))

    def test_tech_discovery_existing_project_rejects_na_reality_scan(self) -> None:
        self.write_meta(project_context="existing_project")
        body = self.valid_research_body().replace(
            "Target project: demo. project_context: existing_project. Confirmed src/modules/auth/auth.service.ts, src/routes/auth.ts, prisma/schema.prisma, src/pages/LoginPage.tsx. source_id: SRC-AUTH-001",
            "不适用：new_project，无既有代码基线。source_id: SRC-AUTH-001",
        )
        self.write_research_ready(body)
        self.write_selection_ready()

        result = validate_tech_discovery(self.feature_dir)

        self.assertFalse(result["ok"])
        self.assertTrue(any(issue["code"] == "existing_project_reality_scan_na" for issue in result["issues"]))

    def test_tech_discovery_new_project_allows_na_reality_scan_with_reason(self) -> None:
        self.write_meta(project_context="new_project")
        self.write_research_ready(self.valid_research_body(project_context="new_project"))
        self.write_selection_ready()

        result = validate_tech_discovery(self.feature_dir)

        self.assertTrue(result["ok"], result["issues"])

    def test_design_alignment_detects_unknown_frontend_endpoint(self) -> None:
        self.write_text("api-contract.md", "---\nstage: ship-contract\nstage_status: ready\ncontract_forms: [rest]\nupdated_at: \"\"\nevidence_complete: true\n---\nPOST /api/v1/login\nERR_AUTH_INVALID\n")
        self.write_text("frontend-design.md", "---\nstage: ship-frontend-design\nstage_status: ready\nupdated_at: \"\"\nevidence_complete: true\n---\nPOST /api/v1/logout\n")

        result = validate_design_alignment(self.feature_dir, project_scope="frontend_only")

        self.assertFalse(result["ok"])
        self.assertTrue(any(issue["code"] == "frontend_unknown_endpoint" for issue in result["issues"]))

    def test_frontend_design_ready_requires_page_api_and_ac_refs(self) -> None:
        self.write_text("frontend-design.md", "---\nstage: ship-frontend-design\nstage_status: ready\nupdated_at: \"\"\nevidence_complete: true\n---\n# Frontend\n")

        result = validate_frontend_design(self.feature_dir / "frontend-design.md")

        self.assertFalse(result["ok"])
        codes = {issue["code"] for issue in result["issues"]}
        self.assertIn("missing_api_refs", codes)
        self.assertIn("missing_ac_refs", codes)

    def test_backend_design_ready_requires_domain_and_endpoint_mapping(self) -> None:
        self.write_text("backend-design.md", "---\nstage: ship-backend-design\nstage_status: ready\nupdated_at: \"\"\nevidence_complete: true\n---\n# Backend\n")

        result = validate_backend_design(self.feature_dir / "backend-design.md")

        self.assertFalse(result["ok"])
        codes = {issue["code"] for issue in result["issues"]}
        self.assertIn("missing_domain_refs", codes)
        self.assertIn("missing_endpoint_mapping", codes)

    def test_doctor_reports_blocked_stage_next_action(self) -> None:
        self.write_meta(current_stage="ship-define", define_status="blocked")
        meta = yaml.safe_load((self.feature_dir / "meta.yml").read_text(encoding="utf-8"))
        meta["stages"]["ship-define"]["block_reason"] = "awaiting_materials"
        self.write_text("meta.yml", yaml.safe_dump(meta, sort_keys=False))

        result = diagnose_feature(self.feature_dir)

        self.assertFalse(result["ok"])
        self.assertEqual(result["next_action"]["action"], "fix_blocking_issues")
        self.assertTrue(any(issue["code"] == "missing_artifact" for issue in result["issues"]))

    def test_backend_only_scope_skips_frontend_design_for_design_review(self) -> None:
        self.write_meta(
            current_stage="ship-backend-design",
            project_scope="backend_only",
            project_scope_evidence="用户明确声明纯后端 API 项目",
            scenario="prd_direct",
            define_review_status="approved",
        )
        self.write_requirements(status="ready")
        for relative_path, stage, role in (
            ("review-define.md", "ship-define-review", None),
        ):
            if stage == "ship-define-review":
                self.write_define_review(status="approved", signed=True)
                continue
            role_line = f"artifact_role: {role}\n" if role else ""
            self.write_text(
                relative_path,
                f"""---
stage: {stage}
{role_line}stage_status: ready
updated_at: "2026-05-31T10:00:00+08:00"
evidence_complete: true
---

# {stage}
""",
            )
        self.write_text(
            "tech-research.md",
            """---
stage: ship-tech-discovery
artifact_role: research
stage_status: ready
updated_at: "2026-05-31T10:00:00+08:00"
evidence_complete: true
---

# Tech Research

## Project Reality Scan / 项目现状发现
Target project: demo. project_context: existing_project. Confirmed src/modules/auth/auth.service.ts, src/routes/auth.ts, prisma/schema.prisma, src/pages/LoginPage.tsx. source_id: SRC-AUTH-001

## Requirement-to-Reality Mapping / 需求与已有系统映射
| Domain / AC | 需求摘要 | 现有项目发现 | 关系类型 | 证据路径 | 不确定项 |
|---|---|---|---|---|---|
| D-AUTH-001 / AC-AUTH-001 | 登录 | 已有 auth route 和 AuthService | extend | src/routes/auth.ts, src/modules/auth/auth.service.ts | 无 |

## Existing Surface Inventory / 现有表面清单
| Surface | Existing Item | Path / Source | Relation | Notes |
|---|---|---|---|---|
| API | POST /api/v1/login | src/routes/auth.ts | extend | auth endpoint |
| Backend Service | AuthService | src/modules/auth/auth.service.ts | extend | credential validation |

## Evidence and Uncertainty / 证据与不确定项
### Confirmed Facts
- FACT-001: Auth route exists at src/routes/auth.ts. source_id: SRC-AUTH-001
### Conflicting Evidence
- None.
### Open Questions
- None.

## Research Alignment Check / 产出前对齐记录
### Alignment Summary Presented to User
- 当前理解：复用已有 AuthService 和 POST /api/v1/login。
- 准备复用 / 扩展：src/routes/auth.ts, src/modules/auth/auth.service.ts。
- 不确定项：无阻塞项。
- 若按当前理解继续，将影响：contract/backend design 扩展现有 auth surface。
### User Feedback
- 用户确认：继续按现有 auth surface 扩展。
- 用户纠正：无。
- 用户要求按假设继续：无。
### Follow-up Exploration
- 重新探索的路径：无纠正，未触发。
- 修正后的结论：无。
### Final Research Baseline
- 本 research 产物基于 FACT-001 和 SRC-AUTH-001。
- assumptions：无阻塞假设。

## Technical Research / 技术调研
- source_id: SRC-AUTH-001 official auth framework docs

## Selection Inputs / 给 tech-selection.md 的输入
- 复用 AuthService，扩展 existing endpoint。

## 信息来源清单
- source_id: SRC-AUTH-001 local auth source and official auth framework docs.
""",
        )
        self.write_text(
            "tech-selection.md",
            """---
stage: ship-tech-discovery
artifact_role: selection
stage_status: ready
updated_at: "2026-05-31T10:00:00+08:00"
evidence_complete: true
---

# Selection
Decision: use existing auth stack. source_id: SRC-AUTH-001
Rejected: custom auth.
ADR: ADR-AUTH-001
tech_stack: Node service
""",
        )
        self.write_text(
            "api-contract.md",
            """---
stage: ship-contract
stage_status: ready
contract_forms: [rest]
updated_at: "2026-05-31T10:00:00+08:00"
evidence_complete: true
---

# API Contract

## Summary
REST contract for D-AUTH-001. OpenAPI artifact: resource/openapi.yaml. Change classification: additive.

#### POST /api/v1/login
- 关联 AC：AC-AUTH-001
- 请求参数：body.email string required
- 成功响应：200
- 错误响应：ERR_AUTH_INVALID | HTTP Status 401 | 凭证错误

## 数据模型
interface LoginRequest { email: string; password: string }
""",
        )
        self.write_text(
            "backend-design.md",
            """---
stage: ship-backend-design
stage_status: ready
updated_at: "2026-05-31T10:00:00+08:00"
evidence_complete: true
---

# Backend Design
D-AUTH-001 maps to AuthController / AuthService / AuthRepository.

| 接口 | Controller | Service | Repository |
| POST /api/v1/login | AuthController.login | AuthService.login | AuthRepository.findByEmail |

Migration strategy: no migration. rollback: no DB change. backfill: none.
auth, rate limit, logging, metrics, error handling covered.
""",
        )
        meta = yaml.safe_load((self.feature_dir / "meta.yml").read_text(encoding="utf-8"))
        for stage in ("ship-define", "ship-tech-discovery", "ship-contract", "ship-backend-design"):
            meta["stages"][stage]["status"] = "ready"
        meta["stages"]["ship-define-review"]["status"] = "approved"
        meta["stages"]["ship-define-review"]["approved"] = True
        meta["stages"]["ship-frontend-design"]["status"] = "skipped"
        self.write_text("meta.yml", yaml.safe_dump(meta, sort_keys=False))

        result = check_transition(self.feature_dir, "ship-design-review")

        self.assertTrue(result["allowed"], result["issues"])

    def test_backend_only_discover_scope_skips_shape_for_define(self) -> None:
        self.write_meta(
            current_stage="ship-define-review",
            project_scope="backend_only",
            project_scope_evidence="用户明确声明纯后端 API 项目",
            scenario="greenfield",
            define_review_status="approved",
        )
        self.write_text(
            "product-brief.md",
            """---
stage: ship-discover
stage_status: ready
updated_at: "2026-05-31T10:00:00+08:00"
evidence_complete: true
---

# Product Brief
问题: 需要提供登录 API。
用户画像: API consumer.
Must Have: login endpoint.
成功标准: AC-AUTH-001 通过。
假设: 复用现有 auth stack。
evidence_index: FACT-001.
SLA: P95 < 500ms.
契约形态: REST.
备选: gRPC postponed because REST scope is smaller.
risk: auth compatibility.
""",
        )
        self.write_requirements(status="ready")
        self.write_define_review(status="approved", signed=True)
        meta = yaml.safe_load((self.feature_dir / "meta.yml").read_text(encoding="utf-8"))
        meta["stages"]["ship-discover"]["status"] = "ready"
        meta["stages"]["ship-shape"]["status"] = "skipped"
        meta["stages"]["ship-define"]["status"] = "ready"
        meta["stages"]["ship-define-review"]["status"] = "approved"
        meta["stages"]["ship-define-review"]["approved"] = True
        meta["stages"]["ship-frontend-design"]["status"] = "skipped"
        self.write_text("meta.yml", yaml.safe_dump(meta, sort_keys=False))

        result = check_transition(self.feature_dir, "ship-tech-discovery")

        self.assertTrue(result["allowed"], result["issues"])
        self.assertNotIn("ship-shape", result["checked_previous_stages"])

    def test_backend_only_scope_rejects_forbidden_frontend_artifacts(self) -> None:
        self.write_meta(
            current_stage="ship-backend-design",
            project_scope="backend_only",
            project_scope_evidence="用户明确声明纯后端 API 项目",
            scenario="prd_direct",
            define_review_status="approved",
        )
        self.write_text(
            "frontend-plan.md",
            """---
stage: ship-delivery-plan
artifact_role: frontend-plan
stage_status: ready
updated_at: "2026-05-31T10:00:00+08:00"
evidence_complete: true
---

# Frontend Plan
""",
        )

        result = validate_feature(self.feature_dir)

        self.assertFalse(result["ok"])
        self.assertTrue(any(issue["code"] == "scope_forbidden_artifact" for issue in result["issues"]))

    def test_backend_only_scope_requires_project_scope_evidence_in_validator(self) -> None:
        self.write_meta(
            current_stage="ship-backend-design",
            project_scope="backend_only",
            scenario="prd_direct",
            define_review_status="approved",
        )

        result = validate_feature(self.feature_dir)

        self.assertFalse(result["ok"])
        self.assertTrue(any(issue["code"] == "missing_project_scope_evidence" for issue in result["issues"]))

    def test_technical_plan_meta_requires_selected_scope(self) -> None:
        self.write_meta(
            current_stage="ship-define",
            scenario="technical_plan_provided",
            project_context="existing_project",
            define_status="blocked",
        )
        meta = yaml.safe_load((self.feature_dir / "meta.yml").read_text(encoding="utf-8"))
        meta["technical_plan_source"] = {
            "source_files": ["resource/order-export-tech-design.md"],
            "selection_mode": "referenced_sections",
            "selected_scope": [],
            "pasted_excerpt_file": "",
            "ignored_source_policy": "out_of_scope",
            "repository_scan_required": True,
            "repository_scan_status": "pending",
        }
        self.write_text("meta.yml", yaml.safe_dump(meta, sort_keys=False))

        result = validate_feature(self.feature_dir)

        self.assertFalse(result["ok"])
        self.assertTrue(any(issue["code"] == "missing_selected_scope" for issue in result["issues"]))

    def test_technical_plan_meta_requires_existing_project(self) -> None:
        self.write_meta(
            current_stage="ship-define",
            scenario="technical_plan_provided",
            project_context="new_project",
            define_status="blocked",
        )
        meta = yaml.safe_load((self.feature_dir / "meta.yml").read_text(encoding="utf-8"))
        meta["technical_plan_source"] = {
            "source_files": ["resource/order-export-tech-design.md"],
            "selection_mode": "referenced_sections",
            "selected_scope": [{"type": "section", "label": "3.2 Export", "source_file": "resource/order-export-tech-design.md", "locator": "heading"}],
            "pasted_excerpt_file": "",
            "ignored_source_policy": "out_of_scope",
            "repository_scan_required": True,
            "repository_scan_status": "pending",
        }
        self.write_text("meta.yml", yaml.safe_dump(meta, sort_keys=False))

        result = validate_feature(self.feature_dir)

        self.assertFalse(result["ok"])
        self.assertTrue(any(issue["code"] == "technical_plan_requires_existing_project" for issue in result["issues"]))

    def test_technical_plan_meta_requires_valid_selection_mode(self) -> None:
        self.write_meta(
            current_stage="ship-define",
            scenario="technical_plan_provided",
            project_context="existing_project",
            define_status="blocked",
        )
        meta = yaml.safe_load((self.feature_dir / "meta.yml").read_text(encoding="utf-8"))
        meta["technical_plan_source"] = {
            "source_files": ["resource/order-export-tech-design.md"],
            "selection_mode": "pages",
            "selected_scope": [{"type": "section", "label": "3.2 Export", "source_file": "resource/order-export-tech-design.md", "locator": "heading"}],
            "pasted_excerpt_file": "",
            "ignored_source_policy": "out_of_scope",
            "repository_scan_required": True,
            "repository_scan_status": "pending",
        }
        self.write_text("meta.yml", yaml.safe_dump(meta, sort_keys=False))

        result = validate_feature(self.feature_dir)

        self.assertFalse(result["ok"])
        self.assertTrue(any(issue["code"] == "invalid_technical_selection_mode" for issue in result["issues"]))

    def test_technical_plan_scan_status_must_be_ready_after_tech_discovery_ready(self) -> None:
        self.write_meta(
            current_stage="ship-contract",
            scenario="technical_plan_provided",
            project_context="existing_project",
        )
        meta = yaml.safe_load((self.feature_dir / "meta.yml").read_text(encoding="utf-8"))
        meta["technical_plan_source"] = {
            "source_files": ["resource/order-export-tech-design.md"],
            "selection_mode": "referenced_sections",
            "selected_scope": [{"type": "section", "label": "3.2 Export", "source_file": "resource/order-export-tech-design.md", "locator": "heading"}],
            "pasted_excerpt_file": "",
            "ignored_source_policy": "out_of_scope",
            "repository_scan_required": True,
            "repository_scan_status": "pending",
        }
        meta["stages"]["ship-tech-discovery"]["status"] = "ready"
        self.write_text("meta.yml", yaml.safe_dump(meta, sort_keys=False))

        result = validate_feature(self.feature_dir)

        self.assertFalse(result["ok"])
        self.assertTrue(any(issue["code"] == "repository_scan_not_ready" for issue in result["issues"]))

    def test_technical_plan_cannot_enter_delivery_plan_before_design_review_gate(self) -> None:
        self.write_meta(
            current_stage="ship-design-review",
            scenario="technical_plan_provided",
            project_context="existing_project",
            define_review_status="approved",
        )
        self.write_requirements(status="ready")
        meta = yaml.safe_load((self.feature_dir / "meta.yml").read_text(encoding="utf-8"))
        meta["technical_plan_source"] = {
            "source_files": ["resource/order-export-tech-design.md"],
            "selection_mode": "referenced_sections",
            "selected_scope": [{"type": "section", "label": "3.2 Export", "source_file": "resource/order-export-tech-design.md", "locator": "heading"}],
            "pasted_excerpt_file": "",
            "ignored_source_policy": "out_of_scope",
            "repository_scan_required": True,
            "repository_scan_status": "ready",
        }
        meta["stages"]["ship-define"]["status"] = "ready"
        meta["stages"]["ship-define-review"]["status"] = "approved"
        meta["stages"]["ship-define-review"]["approved"] = True
        meta["stages"]["ship-tech-discovery"]["status"] = "ready"
        meta["stages"]["ship-contract"]["status"] = "ready"
        meta["stages"]["ship-frontend-design"]["status"] = "ready"
        meta["stages"]["ship-backend-design"]["status"] = "ready"
        self.write_text("meta.yml", yaml.safe_dump(meta, sort_keys=False))
        self.write_define_review(status="approved", signed=True)

        result = check_transition(self.feature_dir, "ship-delivery-plan")

        self.assertFalse(result["allowed"])
        self.assertTrue(any(issue["code"] == "missing_stage_artifact" and "ship-design-review" in issue["message"] for issue in result["issues"]))

    def test_technical_plan_delivery_plan_requires_selected_scope_ref(self) -> None:
        self.write_meta(
            current_stage="ship-delivery-plan",
            scenario="technical_plan_provided",
            project_context="existing_project",
            project_scope="backend_only",
            project_scope_evidence="用户明确声明纯后端 API 项目",
        )
        meta = yaml.safe_load((self.feature_dir / "meta.yml").read_text(encoding="utf-8"))
        meta["technical_plan_source"] = {
            "source_files": ["resource/order-export-tech-design.md"],
            "selection_mode": "referenced_sections",
            "selected_scope": [{"type": "section", "label": "3.2 Order export async task", "source_file": "resource/order-export-tech-design.md", "locator": "heading"}],
            "pasted_excerpt_file": "",
            "ignored_source_policy": "out_of_scope",
            "repository_scan_required": True,
            "repository_scan_status": "ready",
        }
        self.write_text("meta.yml", yaml.safe_dump(meta, sort_keys=False))
        self.write_plan(
            "backend-plan.md",
            "backend-plan",
            f"""## Tasks
### BE-ORDER-001
- project: api
- scope: order import endpoint
- allowed_files: src/orders/import.ts
- depends_on:
- AC refs: AC-ORDER-001
- contract refs: POST /api/v1/orders/import
- verification command: npm test
- done evidence: test output
{self.task_brief(goal="实现订单导入 endpoint", context="仓库探索证据：src/orders/import.ts；接口：POST /api/v1/orders/import。")}
""",
        )

        result = validate_delivery_plan(self.feature_dir, project_scope="backend_only")

        self.assertFalse(result["ok"])
        self.assertTrue(any(issue["code"] == "task_missing_selected_scope_ref" for issue in result["issues"]))

    def test_frontend_only_scope_rejects_forbidden_backend_artifacts(self) -> None:
        self.write_meta(
            current_stage="ship-frontend-design",
            project_scope="frontend_only",
            project_scope_evidence="用户明确声明纯前端 UI 项目",
            scenario="prd_direct",
            define_review_status="approved",
        )
        self.write_text(
            "backend-design.md",
            """---
stage: ship-backend-design
artifact_role: backend-design
stage_status: ready
updated_at: "2026-05-31T10:00:00+08:00"
evidence_complete: true
---

# Backend Design
""",
        )

        result = validate_feature(self.feature_dir)

        self.assertFalse(result["ok"])
        self.assertTrue(any(issue["code"] == "scope_forbidden_artifact" for issue in result["issues"]))

    def test_fast_track_product_provided_enters_build_without_design_or_plan(self) -> None:
        self.write_meta(
            current_stage="ship-define-review",
            scenario="product_provided",
            pipeline_mode="fast-track",
            define_review_status="approved",
        )
        self.write_requirements(status="ready")
        self.write_define_review(status="approved", signed=True)
        meta = yaml.safe_load((self.feature_dir / "meta.yml").read_text(encoding="utf-8"))
        meta["stages"]["ship-define"]["status"] = "ready"
        meta["stages"]["ship-define-review"]["status"] = "approved"
        meta["stages"]["ship-define-review"]["approved"] = True
        self.write_text("meta.yml", yaml.safe_dump(meta, sort_keys=False))

        result = check_transition(self.feature_dir, "ship-build")

        self.assertTrue(result["allowed"], result["issues"])
        self.assertEqual(result["checked_previous_stages"], ["ship-define", "ship-define-review"])

    def test_fast_track_greenfield_enters_build_without_shape_design_or_plan(self) -> None:
        self.write_meta(
            current_stage="ship-define-review",
            scenario="greenfield",
            pipeline_mode="fast-track",
            define_review_status="approved",
        )
        self.write_text(
            "product-brief.md",
            """---
stage: ship-discover
stage_status: ready
updated_at: "2026-05-31T10:00:00+08:00"
evidence_complete: true
---

# Product Brief
问题: login button state incorrect.
用户: web 登录用户.
Must Have: 修复按钮状态.
成功标准: AC-AUTH-001 通过.
假设: 只改一个页面.
evidence_index: FACT-001.
备选: full redesign rejected because risk is higher.
risk: low.
""",
        )
        self.write_requirements(status="ready")
        self.write_define_review(status="approved", signed=True)
        meta = yaml.safe_load((self.feature_dir / "meta.yml").read_text(encoding="utf-8"))
        meta["stages"]["ship-discover"]["status"] = "ready"
        meta["stages"]["ship-shape"]["status"] = "skipped"
        meta["stages"]["ship-define"]["status"] = "ready"
        meta["stages"]["ship-define-review"]["status"] = "approved"
        meta["stages"]["ship-define-review"]["approved"] = True
        self.write_text("meta.yml", yaml.safe_dump(meta, sort_keys=False))

        result = check_transition(self.feature_dir, "ship-build")

        self.assertTrue(result["allowed"], result["issues"])
        self.assertEqual(result["checked_previous_stages"], ["ship-discover", "ship-define", "ship-define-review"])

    def test_fast_track_artifact_validation_does_not_require_design_or_plan(self) -> None:
        self.write_meta(
            current_stage="ship-build",
            scenario="product_provided",
            pipeline_mode="fast-track",
            define_review_status="approved",
        )
        self.write_requirements(status="ready")
        self.write_define_review(status="approved", signed=True)
        self.write_text(
            "fast-track-tasks.md",
            f"""---
stage: ship-build
artifact_role: fast-track-tasks
stage_status: draft
evidence_complete: false
---

### Task FT-001
- status: DOING
- allowed_files: src/pages/Login.tsx
- ac_refs: AC-AUTH-001
- verification_command: pnpm test -- Login
{self.task_brief(goal="修复登录按钮状态", context="仓库探索证据：src/pages/Login.tsx；前端为 React 登录页。")}
""",
        )
        meta = yaml.safe_load((self.feature_dir / "meta.yml").read_text(encoding="utf-8"))
        meta["stages"]["ship-define"]["status"] = "ready"
        meta["stages"]["ship-define-review"]["status"] = "approved"
        meta["stages"]["ship-define-review"]["approved"] = True
        self.write_text("meta.yml", yaml.safe_dump(meta, sort_keys=False))

        result = validate_feature(self.feature_dir)

        self.assertFalse(any(issue["path"] in {"tech-research.md", "frontend-plan.md", "backend-plan.md", "review-plan.md"} for issue in result["issues"]))


if __name__ == "__main__":
    unittest.main()
