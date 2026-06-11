#!/usr/bin/env python3
"""Smoke and negative tests for ShipKit validators.

The tests create temporary feature fixtures under /tmp and intentionally leave them
there for inspection. They do not touch repository feature data.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "skills" / "ship-orchestrator" / "scripts"
sys.path.insert(0, str(SCRIPTS))
from _lib import parse_loose_yaml, parse_meta_yaml  # noqa: E402


def run(script: str, feature_dir: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script), str(feature_dir)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


def meta_text(
    *,
    workflow: str = "full_flow",
    workspace_mode: str = "single_project",
    projects: list[str] | None = None,
    source_refs: str | None = None,
    template_ref: str = "builtin:fullstack-feature@1",
    current_stage: str = "done",
    status: str = "completed",
    build_approved_at: str = "2026-06-09T16:00:00Z",
    build_approved_by: str = "user",
    build_approval_note: str = "用户确认进入 Build",
) -> str:
    projects_text = "[" + ", ".join(f'"{project}"' for project in (projects or [])) + "]"
    if source_refs is None:
        source_refs = """source_refs:
  - id: SRC-001
    type: prd
    title: 示例 PRD
    path_or_url: resource/prd.md
    role: primary
    status: available
    notes: ""
"""

    template_fields = ""
    if template_ref:
        template_fields = (
            f"design_template_ref: \"{template_ref}\"\n"
            "design_template_reason: \"AC-1/AC-2 同时涉及 API、状态和后端服务\"\n"
        )

    approval_fields = ""
    if build_approved_at:
        approval_fields += f"build_approved_at: \"{build_approved_at}\"\n"
    if build_approved_by:
        approval_fields += f"build_approved_by: {build_approved_by}\n"
    if build_approval_note:
        approval_fields += f"build_approval_note: \"{build_approval_note}\"\n"

    return (
        "feature_name: \"示例\"\n"
        f"workflow: {workflow}\n"
        f"workspace_mode: {workspace_mode}\n"
        "workspace_name: \"示例工作区\"\n"
        f"projects: {projects_text}\n"
        f"current_stage: {current_stage}\n"
        f"status: {status}\n"
        "created_at: \"2026-06-09T10:00:00Z\"\n"
        "updated_at: \"2026-06-09T18:00:00Z\"\n"
        f"{source_refs}"
        "spec_refs: [\"rest-api-standard\"]\n"
        "requested_design_template: \"\"\n"
        f"{template_fields}"
        f"{approval_fields}"
        "artifacts:\n"
        "  requirements: requirements.md\n"
        "  design: design.md\n"
        "  build_plan: build-plan.yml\n"
        "  verification: verification.md\n"
    )


def valid_design_text(template_ref: str = "builtin:fullstack-feature@1") -> str:
    return f"""---
status: ready
updated_at: "2026-06-09T14:00:00Z"
spec_refs: ["rest-api-standard"]
---
# 技术设计：示例
## 方案模板引用
- 主模板：`{template_ref}`（来自 `meta.yml.design_template_ref`）
- 选择依据：AC-1 和 AC-2 同时涉及 API、前端状态和后端服务。
- 候选模板：`backend-service(score=5)`、`fullstack-feature(score=8)`
- 未选原因：`backend-service` 仅作为后端辅助 checklist。
- 项目 spec 优先级：模板与 spec 冲突时，以 `rest-api-standard` 为准。

### 模板偏离
| 偏离项 | 原因 | 影响 | 替代设计 |
|---|---|---|---|
| 无 | 完全按模板补齐 | 无 | 不涉及 |

## AC 覆盖映射
| AC | 设计位置 | 测试建议 |
|---|---|---|
| AC-1 | API 契约、前端设计、后端设计 | 成功测试 |
| AC-2 | API 错误响应、前端错误展示、后端鉴权 | 失败测试 |
## API 契约
### POST /api/example
**AC refs**: AC-1, AC-2
**Request**
```json
{{}}
```
**Response - 200 OK**
```json
{{}}
```
**Error Responses**
- 400 `BAD_REQUEST`: 错误
## 数据模型
不涉及数据变更，原因：本功能只读取既有数据并返回计算结果。
## 前端设计
### 状态管理
- 使用现有页面局部 state 保存提交状态。
- 错误处理：toast + 字段级错误。
## 后端设计
### 鉴权与权限
- 复用现有登录用户鉴权；无权限返回 403。
### Service 分层
- Controller -> Service。
## 性能考量
P95 < 500ms。
## 风险和回滚
### 回滚方案
- 关闭入口配置即可回滚到旧行为。
## 设计审查记录
| Round | Reviewer | Blocking findings | 处理结果 |
|---|---|---:|---|
| 1 | ship-grill-me | 0 | ready |
"""


def write_valid_feature(base: Path, name: str = "valid") -> Path:
    feature = base / name
    feature.mkdir(parents=True, exist_ok=True)
    (feature / "meta.yml").write_text(meta_text(), encoding="utf-8")
    (feature / "requirements.md").write_text(
        """---
status: ready
updated_at: "2026-06-09T12:00:00Z"
spec_refs: ["auth-flow"]
---
# 需求：示例
## 功能概述
示例。
## Domain 模型
- D-EXAMPLE-001: 示例域
## 验收标准 (AC)
### AC-1: 成功路径
**Given** 用户存在  
**When** 用户提交请求  
**Then** 系统返回成功
### AC-2: 失败路径
**Given** 用户不存在  
**When** 用户提交请求  
**Then** 系统返回错误
## 非功能需求
- 响应时间：P95 < 500ms
""",
        encoding="utf-8",
    )
    (feature / "design.md").write_text(valid_design_text(), encoding="utf-8")
    (feature / "build-plan.yml").write_text(
        """tasks:
  - id: T-001
    name: 示例
    type: backend
    files: ["src/example.ts"]
    dependencies: []
    ac_refs: ["AC-1", "AC-2"]
""",
        encoding="utf-8",
    )
    (feature / "verification.md").write_text(
        """---
status: ready
updated_at: "2026-06-09T18:00:00Z"
all_ac_passed: true
---
# 验证报告
## AC 验证状态
- ✅ AC-1: 成功路径 (covered by: tests/example.test.ts)
- ✅ AC-2: 失败路径 (covered by: tests/example.test.ts)
## 测试覆盖
- Unit: 2 passed
- Integration: 0 failed
## 代码质量
- Lint: 0 errors
- Typecheck: passed
## 产出文件
- src/example.ts
## 未覆盖项
无。
""",
        encoding="utf-8",
    )
    return feature


def clone_feature(src: Path, dst: Path) -> Path:
    shutil.copytree(src, dst)
    return dst


def expect(script: str, feature: Path, should_pass: bool, label: str) -> None:
    result = run(script, feature)
    ok = result.returncode == 0
    if ok != should_pass:
        print(f"FAIL: {label} expected {'pass' if should_pass else 'fail'} but got rc={result.returncode}")
        print(result.stdout)
        raise SystemExit(1)
    print(f"PASS: {label}")


def main() -> int:
    base = Path(tempfile.mkdtemp(prefix="shipkit-validator-tests-", dir="/tmp"))
    valid = write_valid_feature(base)

    expect("validate_requirements.py", valid, True, "valid requirements")
    expect("validate_design.py", valid, True, "valid design with template")
    expect("validate_build.py", valid, True, "valid build")
    expect("validate_current_stage.py", valid, True, "valid current stage")

    parsed_meta = parse_meta_yaml(valid / "meta.yml")
    first_source = parsed_meta["source_refs"][0]
    if (
        parsed_meta["workflow"] != "full_flow"
        or parsed_meta["workspace_mode"] != "single_project"
        or parsed_meta["projects"] != []
        or first_source["role"] != "primary"
        or first_source["status"] != "available"
        or parsed_meta["build_approved_at"] != "2026-06-09T16:00:00Z"
    ):
        print("FAIL: parse_meta_yaml must read workflow/workspace/projects/source_refs/build approval")
        raise SystemExit(1)
    print("PASS: meta YAML parser reads workflow/workspace/source_refs/build approval")

    parse_probe = base / "parse-project-ref.yml"
    project_ref = "project:.docs/技术方案模版.md#backend-enterprise@1"
    parse_probe.write_text(f'design_template_ref: "{project_ref}" # comment\n', encoding="utf-8")
    if parse_loose_yaml(parse_probe)["design_template_ref"] != project_ref:
        print("FAIL: loose YAML parser must preserve quoted project template fragment")
        raise SystemExit(1)
    print("PASS: loose YAML preserves quoted project template fragment")

    project_doc = base / "技术方案模版.md"
    project_doc.write_text("# template\n", encoding="utf-8")
    abs_project_ref = f"project:{project_doc}#backend-enterprise@1"
    project_template = clone_feature(valid, base / "project-template-ref")
    (project_template / "meta.yml").write_text(meta_text(template_ref=abs_project_ref), encoding="utf-8")
    (project_template / "design.md").write_text(valid_design_text(abs_project_ref), encoding="utf-8")
    expect("validate_design.py", project_template, True, "project template ref with fragment")

    missing_ac = clone_feature(valid, base / "missing-ac")
    (missing_ac / "requirements.md").write_text(
        (missing_ac / "requirements.md").read_text(encoding="utf-8").replace("### AC-1", "### XX-1").replace("### AC-2", "### XX-2"),
        encoding="utf-8",
    )
    expect("validate_requirements.py", missing_ac, False, "requirements missing AC")

    bad_ac = clone_feature(valid, base / "bad-ac-format")
    (bad_ac / "requirements.md").write_text(
        (bad_ac / "requirements.md").read_text(encoding="utf-8").replace("**Then** 系统返回成功", "系统返回成功"),
        encoding="utf-8",
    )
    expect("validate_requirements.py", bad_ac, False, "requirements bad AC format")

    no_sources = clone_feature(valid, base / "missing-source-refs")
    (no_sources / "meta.yml").write_text(meta_text(source_refs="source_refs: []\n"), encoding="utf-8")
    expect("validate_requirements.py", no_sources, False, "requirements missing source_refs")

    unavailable_primary = clone_feature(valid, base / "unavailable-primary-source")
    (unavailable_primary / "meta.yml").write_text(
        meta_text(source_refs="""source_refs:
  - id: SRC-001
    type: prd
    title: 示例 PRD
    path_or_url: resource/prd.md
    role: primary
    status: needs_user
"""),
        encoding="utf-8",
    )
    expect("validate_requirements.py", unavailable_primary, False, "requirements primary source unavailable")

    project_group_missing_projects = clone_feature(valid, base / "project-group-missing-projects")
    (project_group_missing_projects / "meta.yml").write_text(meta_text(workspace_mode="project_group", projects=[]), encoding="utf-8")
    expect("validate_requirements.py", project_group_missing_projects, False, "project_group missing projects")

    ship_config = base / "ship"
    ship_config.mkdir(exist_ok=True)
    (ship_config / "project.yml").write_text(
        """workspace_mode: project_group
workspace_name: repo-group
projects:
  - web
  - api
""",
        encoding="utf-8",
    )

    valid_project_scope = clone_feature(valid, base / "valid-project-scope")
    (valid_project_scope / "meta.yml").write_text(meta_text(workspace_mode="project_group", projects=["web"]), encoding="utf-8")
    expect("validate_requirements.py", valid_project_scope, True, "valid project.yml subset scope")

    invalid_project_scope = clone_feature(valid, base / "invalid-project-scope")
    (invalid_project_scope / "meta.yml").write_text(meta_text(workspace_mode="project_group", projects=["mobile"]), encoding="utf-8")
    expect("validate_requirements.py", invalid_project_scope, False, "projects outside project.yml fail")

    design_uncovered = clone_feature(valid, base / "design-uncovered-ac")
    (design_uncovered / "design.md").write_text(
        (design_uncovered / "design.md").read_text(encoding="utf-8").replace("AC-2", "AC-X"),
        encoding="utf-8",
    )
    expect("validate_design.py", design_uncovered, False, "design uncovered AC")

    design_missing_error = clone_feature(valid, base / "design-missing-error")
    (design_missing_error / "design.md").write_text(
        (design_missing_error / "design.md").read_text(encoding="utf-8").replace("**Error Responses**", "**Failure Cases**").replace("- 400 `BAD_REQUEST`: 错误", "- failed request"),
        encoding="utf-8",
    )
    expect("validate_design.py", design_missing_error, False, "design missing error response")

    design_missing_template = clone_feature(valid, base / "design-missing-template")
    (design_missing_template / "meta.yml").write_text(meta_text(template_ref=""), encoding="utf-8")
    expect("validate_design.py", design_missing_template, False, "missing template ref fails")

    design_unknown_template = clone_feature(valid, base / "design-unknown-template")
    (design_unknown_template / "meta.yml").write_text(meta_text(template_ref="builtin:no-such-template@1"), encoding="utf-8")
    (design_unknown_template / "design.md").write_text(valid_design_text("builtin:no-such-template@1"), encoding="utf-8")
    expect("validate_design.py", design_unknown_template, False, "template id does not exist")

    design_missing_template_section = clone_feature(valid, base / "design-missing-template-section")
    (design_missing_template_section / "design.md").write_text(
        (design_missing_template_section / "design.md").read_text(encoding="utf-8").replace("## 方案模板引用", "## 模板说明"),
        encoding="utf-8",
    )
    expect("validate_design.py", design_missing_template_section, False, "missing template section")

    design_nested_top_section = clone_feature(valid, base / "design-nested-top-section")
    (design_nested_top_section / "design.md").write_text(
        (design_nested_top_section / "design.md").read_text(encoding="utf-8").replace("## API 契约", "### API 契约"),
        encoding="utf-8",
    )
    expect("validate_design.py", design_nested_top_section, False, "design base sections must be top-level")

    design_ready_tbd = clone_feature(valid, base / "design-ready-tbd")
    (design_ready_tbd / "design.md").write_text(
        (design_ready_tbd / "design.md").read_text(encoding="utf-8") + "\nTBD\n",
        encoding="utf-8",
    )
    expect("validate_design.py", design_ready_tbd, False, "ready design contains TBD")

    async_missing_subsection = clone_feature(valid, base / "async-missing-subsection")
    (async_missing_subsection / "meta.yml").write_text(meta_text(template_ref="builtin:async-task@1"), encoding="utf-8")
    (async_missing_subsection / "design.md").write_text(valid_design_text("builtin:async-task@1"), encoding="utf-8")
    expect("validate_design.py", async_missing_subsection, False, "async-task missing required subsection")

    build_uncovered = clone_feature(valid, base / "build-uncovered-ac")
    (build_uncovered / "verification.md").write_text(
        (build_uncovered / "verification.md").read_text(encoding="utf-8").replace("- ✅ AC-2: 失败路径 (covered by: tests/example.test.ts)", "- AC-2: 失败路径"),
        encoding="utf-8",
    )
    expect("validate_build.py", build_uncovered, False, "build uncovered AC")

    build_tests_failed = clone_feature(valid, base / "build-tests-failed")
    (build_tests_failed / "verification.md").write_text(
        (build_tests_failed / "verification.md").read_text(encoding="utf-8").replace("- Unit: 2 passed", "- Unit: 1 failed").replace("- Integration: 0 failed", "- Integration: 1 failed"),
        encoding="utf-8",
    )
    expect("validate_build.py", build_tests_failed, False, "build tests failed")

    build_mixed_failed = clone_feature(valid, base / "build-mixed-failed")
    (build_mixed_failed / "verification.md").write_text(
        (build_mixed_failed / "verification.md").read_text(encoding="utf-8").replace("- Integration: 0 failed", "- Integration: 1 failed"),
        encoding="utf-8",
    )
    expect("validate_build.py", build_mixed_failed, False, "build mixed passed and failed")

    build_missing_approval = clone_feature(valid, base / "build-missing-approval")
    (build_missing_approval / "meta.yml").write_text(meta_text(build_approved_at=""), encoding="utf-8")
    expect("validate_build.py", build_missing_approval, False, "build missing approval fails")

    build_missing_approval_by = clone_feature(valid, base / "build-missing-approval-by")
    (build_missing_approval_by / "meta.yml").write_text(meta_text(build_approved_by=""), encoding="utf-8")
    expect("validate_build.py", build_missing_approval_by, False, "build missing approval by fails")

    build_missing_approval_note = clone_feature(valid, base / "build-missing-approval-note")
    (build_missing_approval_note / "meta.yml").write_text(meta_text(build_approval_note=""), encoding="utf-8")
    expect("validate_build.py", build_missing_approval_note, False, "build missing approval note fails")

    build_wrong_stage = clone_feature(valid, base / "build-wrong-stage")
    (build_wrong_stage / "meta.yml").write_text(meta_text(current_stage="design"), encoding="utf-8")
    expect("validate_build.py", build_wrong_stage, False, "build wrong stage fails")

    print(f"All validator smoke tests passed. Fixtures left at: {base}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
