#!/usr/bin/env python3
"""Smoke tests for the explicit-only AI Feature Workflow skills."""

from __future__ import annotations

import importlib.util
from pathlib import Path
import re
import shutil
import sys
import tempfile

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[3]
SKILLS = ROOT / "skills"
ORCHESTRATOR = SKILLS / "ai-feature-orchestrator"
TEMPLATE = ORCHESTRATOR / "assets" / "feature-template"
CHILD_SKILLS = [
    "ai-requirement-intake",
    "ai-repo-investigation",
    "ai-technical-design",
    "ai-task-planning",
    "ai-implementation-execution",
    "ai-verification-closeout",
]
ROUTE_FIELDS = ["activation_source", "feature_dir", "stage_evidence"]
FORBIDDEN_ROUTE_SOURCE_PATTERNS = [
    "another legally activated",
    "legally activated AI Feature Workflow or orchestrator",
    "另一个已经合法触发",
    "被工作流路由",
]
CHILD_OUTPUT_REQUIREMENTS = {
    "ai-requirement-intake": ["updated_at", "evidence_complete"],
    "ai-repo-investigation": ["updated_at", "evidence_complete"],
    "ai-technical-design": ["updated_at", "evidence_complete"],
    "ai-task-planning": ["updated_at", "evidence_complete", "task_count", "真实任务数量"],
    "ai-implementation-execution": ["updated_at", "evidence_complete", "task_count"],
    "ai-verification-closeout": ["updated_at", "evidence_complete"],
}
CHILD_PREFLIGHT_REQUIREMENTS = {
    "ai-repo-investigation": [
        "`requirements.md stage_status: ready`",
        "`requirements.md evidence_complete: true`",
    ],
    "ai-technical-design": [
        "`requirements.md stage_status: ready`",
        "`investigation.md stage_status: ready`",
        "`requirements.md evidence_complete: true`",
        "`investigation.md evidence_complete: true`",
    ],
    "ai-task-planning": [
        "`requirements.md stage_status: ready`",
        "`investigation.md stage_status: ready`",
        "`design.md stage_status: ready`",
        "`design.md evidence_complete: true`",
        "`design.md approval_status: approved`",
        "`approved_by`、`approved_at`、`approval_evidence`",
    ],
    "ai-implementation-execution": [
        "`requirements.md stage_status: ready`",
        "`investigation.md stage_status: ready`",
        "`design.md stage_status: ready`",
        "`tasks.md stage_status: ready`",
        "`design.md approval_status: approved`",
        "`task_count` 与真实任务数量一致",
        "至少存在一个真实 `TODO` 或 `DOING` 任务",
    ],
    "ai-verification-closeout": [
        "`requirements.md stage_status: ready`",
        "`investigation.md stage_status: ready`",
        "`design.md stage_status: ready`",
        "`tasks.md stage_status: ready`",
        "`design.md approval_status: approved`",
        "`task_count` 与真实任务数量一致",
        "不存在 `TODO` 或 `DOING` 任务",
    ],
}
STAGE_TEMPLATE_FILES = {
    "requirements.md": "requirements",
    "investigation.md": "investigation",
    "design.md": "design",
    "tasks.md": "tasks",
    "verification.md": "verification",
    "handoff.md": "handoff",
}
VALID_STAGE_STATUS = {"draft", "ready", "blocked", "complete"}
STAGE_ALLOWED_STATUS = {
    "requirements": {"draft", "ready", "blocked"},
    "investigation": {"draft", "ready", "blocked"},
    "design": {"draft", "ready", "blocked"},
    "tasks": {"draft", "ready", "blocked"},
    "verification": {"draft", "blocked", "complete"},
    "handoff": {"draft", "blocked", "complete"},
}
ISO_WITH_TZ = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:Z|[+-]\d{2}:\d{2})$")
BAD_TEMPLATE_PATTERNS = [
    "BLOCKING / NON_BLOCKING",
    "TODO / PASS / FAIL / BLOCKED",
    "<任务名>",
    "| Q-01 |",
    "| AC-01 |",
    "| T01 |  | TODO |",
    "- status: TODO",
]


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def parse_frontmatter(path: Path, errors: list[str]) -> dict[str, str]:
    text = path.read_text()
    if not text.startswith("---\n"):
        fail(errors, f"{path}: missing YAML frontmatter")
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        fail(errors, f"{path}: unterminated YAML frontmatter")
        return {}
    metadata: dict[str, str] = {}
    for line in text[4:end].splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in stripped:
            fail(errors, f"{path}: invalid frontmatter line {line!r}")
            continue
        key, value = stripped.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"').strip("'")
    return metadata


def read_frontmatter_text(path: Path, errors: list[str]) -> str:
    text = path.read_text()
    if not text.startswith("---\n"):
        fail(errors, f"{path}: missing YAML frontmatter")
        return ""
    end = text.find("\n---", 4)
    if end == -1:
        fail(errors, f"{path}: unterminated YAML frontmatter")
        return ""
    return text[4:end]


def assert_order(text: str, first: str, second: str, errors: list[str], label: str) -> None:
    first_index = text.find(first)
    second_index = text.find(second)
    if first_index == -1:
        fail(errors, f"missing order marker {first!r} for {label}")
        return
    if second_index == -1:
        fail(errors, f"missing order marker {second!r} for {label}")
        return
    if first_index > second_index:
        fail(errors, f"{label}: {first!r} must appear before {second!r}")


def assert_contains_all(text: str, required_values: list[str], errors: list[str], label: str) -> None:
    for required in required_values:
        if required not in text:
            fail(errors, f"{label}: missing {required!r}")


def assert_not_contains_any(text: str, forbidden_values: list[str], errors: list[str], label: str) -> None:
    for forbidden in forbidden_values:
        if forbidden in text:
            fail(errors, f"{label}: contains forbidden route-source wording {forbidden!r}")


def write_doc(path: Path, frontmatter: dict[str, object], body: str) -> None:
    lines = ["---"]
    for key, value in frontmatter.items():
        if isinstance(value, bool):
            rendered = "true" if value else "false"
        else:
            rendered = str(value)
        lines.append(f"{key}: {rendered}")
    lines.extend(["---", "", body.lstrip()])
    path.write_text("\n".join(lines))


def rewrite_frontmatter(path: Path, updates: dict[str, object] | None = None, remove: set[str] | None = None) -> None:
    updates = updates or {}
    remove = remove or set()
    text = path.read_text()
    if not text.startswith("---\n"):
        raise ValueError(f"{path}: missing frontmatter")
    end = text.find("\n---", 4)
    if end == -1:
        raise ValueError(f"{path}: unterminated frontmatter")

    seen: set[str] = set()
    lines: list[str] = []
    for line in text[4:end].splitlines():
        if ":" not in line:
            lines.append(line)
            continue
        key = line.split(":", 1)[0].strip()
        if key in remove:
            seen.add(key)
            continue
        if key in updates:
            value = updates[key]
            if isinstance(value, bool):
                rendered = "true" if value else "false"
            else:
                rendered = str(value)
            lines.append(f"{key}: {rendered}")
            seen.add(key)
        else:
            lines.append(line)

    for key, value in updates.items():
        if key in seen or key in remove:
            continue
        if isinstance(value, bool):
            rendered = "true" if value else "false"
        else:
            rendered = str(value)
        lines.append(f"{key}: {rendered}")

    path.write_text("---\n" + "\n".join(lines) + text[end:])


def stage_meta(stage: str, status: str, evidence_complete: bool, **extra: object) -> dict[str, object]:
    metadata: dict[str, object] = {
        "feature_stage": stage,
        "stage_status": status,
        "updated_at": "2026-05-09T20:30:00+08:00",
        "evidence_complete": evidence_complete,
    }
    metadata.update(extra)
    return metadata


def write_ready_requirements(
    feature_dir: Path,
    *,
    include_non_blocking_question: bool = False,
    include_second_ac: bool = False,
) -> None:
    non_blocking_question = (
        """
## 8. 待确认问题

| ID | 问题 | 阻塞级别 | 已查证据 | 需要用户确认 |
| --- | --- | --- | --- | --- |
| Q-01 | CSV 字段展示顺序是否要固定 | NON_BLOCKING | 已查现有列表无固定导出顺序约束 | 后续可确认，不阻塞当前链路勘察 |
"""
        if include_non_blocking_question
        else ""
    )
    second_ac = (
        "| AC-02 | 无权限用户不能导出 CSV | 使用无权限账号调用导出接口 | READY |"
        if include_second_ac
        else ""
    )
    write_doc(
        feature_dir / "requirements.md",
        stage_meta("requirements", "ready", True),
        f"""
# Requirements

## 1. 背景

- 需求来源：测试场景
- 业务背景：管理员需要导出审计日志。
- 当前问题：缺少 CSV 导出入口。

## 2. 目标

- 业务目标：支持导出 CSV。
- 用户价值：降低排查成本。
- 成功标准：管理员可下载 CSV。

## 3. 范围

### In Scope

- 管理员导出审计日志 CSV。

### Out of Scope

- 不支持 PDF 导出。

## 4. 用户路径 / 业务流程

- 管理员打开审计日志页面，按当前筛选条件点击导出 CSV。

## 5. Acceptance Criteria

| ID | 验收标准 | 验证方式 | 状态 |
| --- | --- | --- | --- |
| AC-01 | 管理员可以导出 CSV | 手工点击导出并检查文件 | READY |
{second_ac}
{non_blocking_question}

## 6. 非功能要求

- 性能：导出请求沿用现有分页查询条件，不新增全表扫描。
- 安全：复用管理员权限校验。
- 兼容性：不改变现有审计日志列表接口。
- 可观测性：记录导出请求结果。

## 7. 约束与假设

- 约束：首期只覆盖 CSV，不覆盖 PDF。
- 假设：现有审计日志表是 source of truth。
""",
    )


def write_ready_requirements_with_placeholder_gap(feature_dir: Path) -> None:
    write_doc(
        feature_dir / "requirements.md",
        stage_meta("requirements", "ready", True),
        """
# Requirements

## 1. 背景

- 需求来源：测试场景
- 业务背景：UNSET

## 2. 目标

- 业务目标：支持导出 CSV。

## 3. 范围

### In Scope

- 管理员导出审计日志 CSV。

### Out of Scope

- 不支持 PDF 导出。

## 4. 用户路径 / 业务流程

- 管理员打开审计日志页面并点击导出。

## 5. Acceptance Criteria

| ID | 验收标准 | 验证方式 | 状态 |
| --- | --- | --- | --- |
| AC-01 | 管理员可以导出 CSV | 手工点击导出并检查文件 | READY |

## 6. 非功能要求

- 安全：复用管理员权限校验。

## 7. 约束与假设

- 约束：首期只覆盖 CSV。
""",
    )


def write_requirements_with_duplicate_ac(feature_dir: Path) -> None:
    write_ready_requirements(feature_dir)
    path = feature_dir / "requirements.md"
    path.write_text(
        path.read_text().replace(
            "| AC-01 | 管理员可以导出 CSV | 手工点击导出并检查文件 | READY |",
            "\n".join(
                [
                    "| AC-01 | 管理员可以导出 CSV | 手工点击导出并检查文件 | READY |",
                    "| AC-01 | 导出结果包含当前筛选条件 | 检查 CSV 内容 | READY |",
                ]
            ),
        )
    )


def write_ready_investigation(feature_dir: Path) -> None:
    write_doc(
        feature_dir / "investigation.md",
        stage_meta("investigation", "ready", True),
        """
# Investigation

## 1. 结论摘要

- 导出入口应复用现有审计日志查询链路。

## 2. 已查文件

| 路径 | 关键位置 | 结论 |
| --- | --- | --- |
| src/audit/export.ts | exportAuditLogs | 可复用查询条件 |

## 3. 真实调用链 / 数据流

- UI export button -> API client -> audit service -> audit_logs table。

## 4. 数据来源

- Source of truth：audit_logs 表。
- 写入点：审计事件写入器。
- 读取点：审计日志查询 service。

## 5. 接口与协议

- Request shape：复用现有审计日志查询参数。
- Response shape：返回 text/csv 下载响应。
- Stream / event 行为：不涉及 stream。
- 错误处理：复用现有权限错误。
- logging / persistence：记录导出请求日志。

## 6. 相似实现

| 位置 | 可复用点 | 限制 |
| --- | --- | --- |
| src/report/export.ts | CSV 生成与响应头模式 | 字段和权限不同，不能直接复用字段列表 |

## 7. 风险与未知

| 类型 | 内容 | 证据 | 处理方式 |
| --- | --- | --- | --- |
| 已证实 | 需复用权限 guard | 已查 audit service | 设计中明确权限链路 |

## 8. 对设计的约束

- 必须沿用现有权限判断。
""",
    )


def write_ready_design(feature_dir: Path, *, approved: bool = False) -> None:
    write_doc(
        feature_dir / "design.md",
        stage_meta(
            "design",
            "ready",
            True,
            approval_status="approved" if approved else "pending",
            approved_by="user" if approved else "",
            approved_at="2026-05-09T20:31:00+08:00" if approved else "",
            approval_evidence="用户确认进入任务拆解" if approved else "",
        ),
        """
# Design

## 1. 方案摘要

- 新增 CSV 导出按钮与后端导出接口，复用审计日志查询条件。

## 2. 影响范围

| 类型 | 模块 / 文件 | 影响说明 |
| --- | --- | --- |
| backend | src/audit/export.ts | 新增导出逻辑 |

## 3. 目标链路

- UI -> API -> audit service -> CSV response。

## 4. API 变更

- Endpoint：新增或扩展审计日志导出 endpoint。
- Request：复用审计日志筛选参数。
- Response：返回 CSV 文件响应。
- Error code：复用现有权限错误。
- 兼容性：不改变现有列表接口。

## 5. 数据变更

- DDL：不涉及。
- DML：不涉及。
- Migration：不涉及。
- Rollback：删除导出入口和导出 handler。
- 幂等性：导出为只读操作。

## 6. 状态、事务与并发

- 事务边界：只读查询，无新增写事务。
- 缓存刷新：不涉及。
- Stream / event：不涉及。
- 异步任务：不涉及。

## 7. 错误处理与日志

- 异常传播：复用现有 API error response。
- 日志字段：记录导出用户、筛选条件摘要和结果。
- PII 处理：CSV 字段沿用审计日志展示规则。

## 8. 风险与回滚

| 风险 | 影响 | 缓解方案 | 回滚方式 |
| --- | --- | --- | --- |
| 权限遗漏 | 非管理员误导出 | 复用权限 guard | 关闭导出入口 |

## 9. 验证策略

- 自动化验证：运行 audit export targeted tests。
- 手工验证：管理员点击导出。
""",
    )


def write_tasks(feature_dir: Path, *, status: str, delivery_record: str | None = None) -> None:
    if delivery_record is None:
        delivery_record = (
            "改动文件：src/audit/export.ts, src/pages/Audit.tsx；验证命令：targeted tests；结果：PASS；残余风险：无"
            if status == "DONE"
            else "待执行"
        )
    write_doc(
        feature_dir / "tasks.md",
        stage_meta("tasks", "ready", True, task_count=1),
        f"""
# Tasks

## 2. 任务清单

### T01 - 实现审计日志导出

- status: {status}
- 输入：requirements.md#AC-01，design.md#目标链路
- 输出：导出 API 和 UI 入口
- 关联模块/文件：src/audit/export.ts, src/pages/Audit.tsx
- 执行要点：复用现有权限 guard
- 完成判定：targeted tests 通过，手工导出 CSV 成功
- 风险：CSV 字段兼容性
- 交付记录：{delivery_record}
""",
    )


def write_multiline_task(feature_dir: Path) -> None:
    write_doc(
        feature_dir / "tasks.md",
        stage_meta("tasks", "ready", True, task_count=1),
        """
# Tasks

## 2. 任务清单

### T01 - 实现审计日志导出

- status: TODO
- 输入：
  - requirements.md#AC-01
  - design.md#目标链路
- 输出：
  - 导出 API
  - UI 导出入口
- 关联模块/文件：
  - src/audit/export.ts
  - src/pages/Audit.tsx
- 执行要点：
  - 复用现有权限 guard
  - 复用 CSV 响应头 helper
- 完成判定：
  - targeted tests 通过
  - 手工导出 CSV 成功
- 风险：
  - CSV 字段兼容性
- 交付记录：待执行
""",
    )


def write_task_missing_required_field(feature_dir: Path) -> None:
    write_doc(
        feature_dir / "tasks.md",
        stage_meta("tasks", "ready", True, task_count=1),
        """
# Tasks

## 2. 任务清单

### T01 - 实现审计日志导出

- status: TODO
- 输入：requirements.md#AC-01，design.md#目标链路
- 输出：导出 API 和 UI 入口
- 关联模块/文件：src/audit/export.ts, src/pages/Audit.tsx
- 完成判定：targeted tests 通过，手工导出 CSV 成功
- 交付记录：待执行
""",
    )


def write_duplicate_task_ids(feature_dir: Path) -> None:
    write_doc(
        feature_dir / "tasks.md",
        stage_meta("tasks", "ready", True, task_count=2),
        """
# Tasks

## 2. 任务清单

### T01 - 实现审计日志导出接口

- status: TODO
- 输入：requirements.md#AC-01
- 输出：导出 API
- 关联模块/文件：src/audit/export.ts
- 执行要点：复用现有权限 guard
- 完成判定：targeted tests 通过
- 风险：CSV 字段兼容性
- 交付记录：待执行

### T01 - 接入审计日志导出按钮

- status: TODO
- 输入：design.md#目标链路
- 输出：导出按钮
- 关联模块/文件：src/pages/Audit.tsx
- 执行要点：复用现有 toast 模式
- 完成判定：手工导出 CSV 成功
- 风险：导出失败提示一致性
- 交付记录：待执行
""",
    )


def write_multiple_doing_tasks(feature_dir: Path) -> None:
    write_doc(
        feature_dir / "tasks.md",
        stage_meta("tasks", "ready", True, task_count=2),
        """
# Tasks

## 2. 任务清单

### T01 - 实现审计日志导出接口

- status: DOING
- 输入：requirements.md#AC-01
- 输出：导出 API
- 关联模块/文件：src/audit/export.ts
- 执行要点：复用现有权限 guard
- 完成判定：targeted tests 通过
- 风险：CSV 字段兼容性
- 交付记录：已开始实现 API

### T02 - 接入审计日志导出按钮

- status: DOING
- 输入：design.md#目标链路
- 输出：导出按钮
- 关联模块/文件：src/pages/Audit.tsx
- 执行要点：复用现有 toast 模式
- 完成判定：手工导出 CSV 成功
- 风险：导出失败提示一致性
- 交付记录：已开始接入按钮
""",
    )


def write_complete_verification(feature_dir: Path) -> None:
    write_doc(
        feature_dir / "verification.md",
        stage_meta("verification", "complete", True),
        """
# Verification

## 1. 验收标准映射

| AC ID | 验收标准 | 验证证据 | 结果 | 备注 |
| --- | --- | --- | --- | --- |
| AC-01 | 管理员可以导出 CSV | targeted tests + 手工导出 | PASS | 覆盖权限 guard |

## 2. 结论摘要

- 未发现 FAIL 或 BLOCKED 项。
""",
    )


def write_failed_complete_verification(feature_dir: Path) -> None:
    write_doc(
        feature_dir / "verification.md",
        stage_meta("verification", "complete", True),
        """
# Verification

## 1. 验收标准映射

| AC ID | 验收标准 | 验证证据 | 结果 | 备注 |
| --- | --- | --- | --- | --- |
| AC-01 | 管理员可以导出 CSV | targeted tests 失败 | FAIL | 权限 guard 未覆盖 |
""",
    )


def write_complete_handoff(feature_dir: Path) -> None:
    write_doc(
        feature_dir / "handoff.md",
        stage_meta("handoff", "complete", True),
        """
# Handoff

## 1. 交付摘要

- 已完成审计日志 CSV 导出。

## 2. 变更范围

| 文件 / 模块 | 变更说明 |
| --- | --- |
| src/audit/export.ts | 新增导出逻辑 |

## 3. 配置 / SQL / 部署事项

- 配置：无配置变更。
- SQL：无 SQL 变更。
- 部署：无额外部署事项。
- 数据修复：无数据修复。

## 4. 用户复核入口

- 使用管理员账号打开 Audit 页面，点击导出。

## 5. 验证结论

- AC-01 已通过。

## 6. 残余风险与后续建议

- 暂无残余风险。
""",
    )


def write_empty_complete_handoff(feature_dir: Path) -> None:
    write_doc(
        feature_dir / "handoff.md",
        stage_meta("handoff", "complete", True),
        """
# Handoff
""",
    )


def write_complete_handoff_without_ops(feature_dir: Path) -> None:
    write_doc(
        feature_dir / "handoff.md",
        stage_meta("handoff", "complete", True),
        """
# Handoff

## 1. 交付摘要

- 已完成审计日志 CSV 导出。

## 2. 变更范围

| 文件 / 模块 | 变更说明 |
| --- | --- |
| src/audit/export.ts | 新增导出逻辑 |

## 4. 用户复核入口

- 使用管理员账号打开 Audit 页面，点击导出。

## 5. 验证结论

- AC-01 已通过。

## 6. 残余风险与后续建议

- 暂无残余风险。
""",
    )


def write_complete_handoff_with_unlabeled_ops(feature_dir: Path) -> None:
    write_doc(
        feature_dir / "handoff.md",
        stage_meta("handoff", "complete", True),
        """
# Handoff

## 1. 交付摘要

- 已完成审计日志 CSV 导出。

## 2. 变更范围

| 文件 / 模块 | 变更说明 |
| --- | --- |
| src/audit/export.ts | 新增导出逻辑 |

## 3. 配置 / SQL / 部署事项

- 无额外操作。

## 4. 用户复核入口

- 使用管理员账号打开 Audit 页面，点击导出。

## 5. 验证结论

- AC-01 已通过。

## 6. 残余风险与后续建议

- 暂无残余风险。
""",
    )


def load_inspector(errors: list[str]):
    inspector_path = ORCHESTRATOR / "scripts" / "inspect_feature_state.py"
    if not inspector_path.is_file():
        fail(errors, f"{inspector_path}: missing state inspector")
        return None
    spec = importlib.util.spec_from_file_location("inspect_feature_state", inspector_path)
    if spec is None or spec.loader is None:
        fail(errors, f"{inspector_path}: cannot load module spec")
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_scenario(root: Path, name: str) -> Path:
    target = root / name
    shutil.copytree(TEMPLATE, target)
    return target


def assert_state(result: dict[str, object], *, state: str, next_skill: str | None, blocking: bool, errors: list[str], label: str) -> None:
    if result.get("state") != state:
        fail(errors, f"{label}: expected state {state!r}, got {result.get('state')!r}")
    if result.get("next_skill") != next_skill:
        fail(errors, f"{label}: expected next_skill {next_skill!r}, got {result.get('next_skill')!r}")
    if result.get("blocking") is not blocking:
        fail(errors, f"{label}: expected blocking {blocking!r}, got {result.get('blocking')!r}")


def run_inspector_scenarios(errors: list[str]) -> None:
    inspector = load_inspector(errors)
    if inspector is None:
        return

    result = inspector.inspect_feature_state(TEMPLATE)
    assert_state(
        result,
        state="template_dir_rejected",
        next_skill=None,
        blocking=True,
        errors=errors,
        label="inspector must reject the bundled feature template directory",
    )

    with tempfile.TemporaryDirectory(prefix="ai-feature-workflow-scenarios-") as tmpdir:
        scenarios_root = Path(tmpdir)

        initial = make_scenario(scenarios_root, "initial-template")
        result = inspector.inspect_feature_state(initial)
        assert_state(
            result,
            state="requirements_draft",
            next_skill="ai-requirement-intake",
            blocking=False,
            errors=errors,
            label="inspector initial template",
        )

        non_blocking = make_scenario(scenarios_root, "non-blocking-requirement")
        write_ready_requirements(non_blocking, include_non_blocking_question=True)
        result = inspector.inspect_feature_state(non_blocking)
        assert_state(
            result,
            state="investigation_draft_or_incomplete",
            next_skill="ai-repo-investigation",
            blocking=False,
            errors=errors,
            label="inspector non-blocking requirement question",
        )

        requirement_placeholder_gap = make_scenario(scenarios_root, "requirement-placeholder-gap")
        write_ready_requirements_with_placeholder_gap(requirement_placeholder_gap)
        result = inspector.inspect_feature_state(requirement_placeholder_gap)
        assert_state(
            result,
            state="requirements_incomplete",
            next_skill="ai-requirement-intake",
            blocking=False,
            errors=errors,
            label="inspector ready requirements must not keep placeholder gaps",
        )

        duplicate_ac = make_scenario(scenarios_root, "duplicate-ac")
        write_requirements_with_duplicate_ac(duplicate_ac)
        result = inspector.inspect_feature_state(duplicate_ac)
        assert_state(
            result,
            state="requirement_duplicate_ac_id",
            next_skill="ai-requirement-intake",
            blocking=True,
            errors=errors,
            label="inspector duplicate acceptance criteria IDs must block",
        )

        req_metadata_inconsistent = make_scenario(scenarios_root, "requirement-metadata-inconsistent")
        write_ready_requirements(req_metadata_inconsistent)
        rewrite_frontmatter(req_metadata_inconsistent / "requirements.md", {"evidence_complete": False})
        result = inspector.inspect_feature_state(req_metadata_inconsistent)
        assert_state(
            result,
            state="requirements_metadata_inconsistent",
            next_skill="ai-requirement-intake",
            blocking=True,
            errors=errors,
            label="inspector ready requirement must have evidence_complete true",
        )

        req_invalid_status = make_scenario(scenarios_root, "requirement-invalid-status")
        write_ready_requirements(req_invalid_status)
        rewrite_frontmatter(req_invalid_status / "requirements.md", {"stage_status": "finished"})
        result = inspector.inspect_feature_state(req_invalid_status)
        assert_state(
            result,
            state="requirements_metadata_inconsistent",
            next_skill="ai-requirement-intake",
            blocking=True,
            errors=errors,
            label="inspector requirement stage_status must be a valid enum",
        )

        req_complete_status = make_scenario(scenarios_root, "requirement-complete-status")
        write_ready_requirements(req_complete_status)
        rewrite_frontmatter(req_complete_status / "requirements.md", {"stage_status": "complete"})
        result = inspector.inspect_feature_state(req_complete_status)
        assert_state(
            result,
            state="requirements_metadata_inconsistent",
            next_skill="ai-requirement-intake",
            blocking=True,
            errors=errors,
            label="inspector requirement stage_status complete must be rejected",
        )

        inv_metadata_inconsistent = make_scenario(scenarios_root, "investigation-metadata-inconsistent")
        write_ready_requirements(inv_metadata_inconsistent)
        write_ready_investigation(inv_metadata_inconsistent)
        rewrite_frontmatter(inv_metadata_inconsistent / "investigation.md", {"updated_at": ""})
        result = inspector.inspect_feature_state(inv_metadata_inconsistent)
        assert_state(
            result,
            state="investigation_metadata_inconsistent",
            next_skill="ai-repo-investigation",
            blocking=True,
            errors=errors,
            label="inspector ready investigation must have updated_at",
        )

        inv_stage_mismatch = make_scenario(scenarios_root, "investigation-stage-mismatch")
        write_ready_requirements(inv_stage_mismatch)
        write_ready_investigation(inv_stage_mismatch)
        rewrite_frontmatter(inv_stage_mismatch / "investigation.md", {"feature_stage": "design"})
        result = inspector.inspect_feature_state(inv_stage_mismatch)
        assert_state(
            result,
            state="investigation_metadata_inconsistent",
            next_skill="ai-repo-investigation",
            blocking=True,
            errors=errors,
            label="inspector investigation feature_stage must match filename",
        )

        approval_pending = make_scenario(scenarios_root, "approval-pending")
        write_ready_requirements(approval_pending)
        write_ready_investigation(approval_pending)
        write_ready_design(approval_pending, approved=False)
        result = inspector.inspect_feature_state(approval_pending)
        assert_state(
            result,
            state="waiting_design_approval",
            next_skill="ai-task-planning",
            blocking=True,
            errors=errors,
            label="inspector design approval pending",
        )

        approval_incomplete = make_scenario(scenarios_root, "approval-incomplete")
        write_ready_requirements(approval_incomplete)
        write_ready_investigation(approval_incomplete)
        write_ready_design(approval_incomplete, approved=True)
        rewrite_frontmatter(
            approval_incomplete / "design.md",
            {"approved_by": "", "approved_at": "", "approval_evidence": ""},
        )
        result = inspector.inspect_feature_state(approval_incomplete)
        assert_state(
            result,
            state="design_approval_incomplete",
            next_skill="ai-task-planning",
            blocking=True,
            errors=errors,
            label="inspector approved design must include approval evidence fields",
        )

        task_planning = make_scenario(scenarios_root, "task-planning")
        write_ready_requirements(task_planning)
        write_ready_investigation(task_planning)
        write_ready_design(task_planning, approved=True)
        result = inspector.inspect_feature_state(task_planning)
        assert_state(
            result,
            state="tasks_draft_or_empty",
            next_skill="ai-task-planning",
            blocking=False,
            errors=errors,
            label="inspector task planning",
        )

        task_missing_field = make_scenario(scenarios_root, "task-missing-required-field")
        write_ready_requirements(task_missing_field)
        write_ready_investigation(task_missing_field)
        write_ready_design(task_missing_field, approved=True)
        write_task_missing_required_field(task_missing_field)
        result = inspector.inspect_feature_state(task_missing_field)
        assert_state(
            result,
            state="task_count_mismatch",
            next_skill="ai-task-planning",
            blocking=True,
            errors=errors,
            label="inspector task missing required field",
        )

        multiline_task = make_scenario(scenarios_root, "multiline-task")
        write_ready_requirements(multiline_task)
        write_ready_investigation(multiline_task)
        write_ready_design(multiline_task, approved=True)
        write_multiline_task(multiline_task)
        result = inspector.inspect_feature_state(multiline_task)
        assert_state(
            result,
            state="task_todo",
            next_skill="ai-implementation-execution",
            blocking=False,
            errors=errors,
            label="inspector multiline task fields",
        )

        task_count_missing = make_scenario(scenarios_root, "task-count-missing")
        write_ready_requirements(task_count_missing)
        write_ready_investigation(task_count_missing)
        write_ready_design(task_count_missing, approved=True)
        write_tasks(task_count_missing, status="TODO")
        rewrite_frontmatter(task_count_missing / "tasks.md", remove={"task_count"})
        result = inspector.inspect_feature_state(task_count_missing)
        assert_state(
            result,
            state="task_count_missing",
            next_skill="ai-task-planning",
            blocking=True,
            errors=errors,
            label="inspector tasks.md must include task_count",
        )

        done_delivery_incomplete = make_scenario(scenarios_root, "done-delivery-incomplete")
        write_ready_requirements(done_delivery_incomplete)
        write_ready_investigation(done_delivery_incomplete)
        write_ready_design(done_delivery_incomplete, approved=True)
        write_tasks(done_delivery_incomplete, status="DONE", delivery_record="待执行")
        result = inspector.inspect_feature_state(done_delivery_incomplete)
        assert_state(
            result,
            state="task_done_delivery_incomplete",
            next_skill="ai-implementation-execution",
            blocking=True,
            errors=errors,
            label="inspector DONE tasks must have real delivery records",
        )

        weak_delivery_record = make_scenario(scenarios_root, "weak-delivery-record")
        write_ready_requirements(weak_delivery_record)
        write_ready_investigation(weak_delivery_record)
        write_ready_design(weak_delivery_record, approved=True)
        write_tasks(weak_delivery_record, status="DONE", delivery_record="已完成")
        result = inspector.inspect_feature_state(weak_delivery_record)
        assert_state(
            result,
            state="task_done_delivery_incomplete",
            next_skill="ai-implementation-execution",
            blocking=True,
            errors=errors,
            label="inspector DONE tasks must include structured delivery evidence",
        )

        duplicate_task_ids = make_scenario(scenarios_root, "duplicate-task-ids")
        write_ready_requirements(duplicate_task_ids)
        write_ready_investigation(duplicate_task_ids)
        write_ready_design(duplicate_task_ids, approved=True)
        write_duplicate_task_ids(duplicate_task_ids)
        result = inspector.inspect_feature_state(duplicate_task_ids)
        assert_state(
            result,
            state="task_duplicate_id",
            next_skill="ai-task-planning",
            blocking=True,
            errors=errors,
            label="inspector duplicate task IDs must block execution",
        )

        multiple_doing = make_scenario(scenarios_root, "multiple-doing")
        write_ready_requirements(multiple_doing)
        write_ready_investigation(multiple_doing)
        write_ready_design(multiple_doing, approved=True)
        write_multiple_doing_tasks(multiple_doing)
        result = inspector.inspect_feature_state(multiple_doing)
        assert_state(
            result,
            state="task_doing_ambiguous",
            next_skill="ai-implementation-execution",
            blocking=True,
            errors=errors,
            label="inspector multiple DOING tasks must be ambiguous",
        )

        doing = make_scenario(scenarios_root, "doing-task")
        write_ready_requirements(doing)
        write_ready_investigation(doing)
        write_ready_design(doing, approved=True)
        write_tasks(doing, status="DOING")
        result = inspector.inspect_feature_state(doing)
        assert_state(
            result,
            state="task_doing",
            next_skill="ai-implementation-execution",
            blocking=False,
            errors=errors,
            label="inspector doing task",
        )

        verification = make_scenario(scenarios_root, "verification")
        write_ready_requirements(verification)
        write_ready_investigation(verification)
        write_ready_design(verification, approved=True)
        write_tasks(verification, status="DONE")
        result = inspector.inspect_feature_state(verification)
        assert_state(
            result,
            state="verification_incomplete",
            next_skill="ai-verification-closeout",
            blocking=False,
            errors=errors,
            label="inspector verification closeout",
        )

        verification_missing_ac = make_scenario(scenarios_root, "verification-missing-ac")
        write_ready_requirements(verification_missing_ac, include_second_ac=True)
        write_ready_investigation(verification_missing_ac)
        write_ready_design(verification_missing_ac, approved=True)
        write_tasks(verification_missing_ac, status="DONE")
        write_complete_verification(verification_missing_ac)
        result = inspector.inspect_feature_state(verification_missing_ac)
        assert_state(
            result,
            state="verification_incomplete",
            next_skill="ai-verification-closeout",
            blocking=False,
            errors=errors,
            label="inspector complete verification must cover every requirement AC",
        )
        diagnostics = result.get("diagnostics") or []
        if not any("AC-02" in diagnostic for diagnostic in diagnostics):
            fail(errors, "inspector missing-AC diagnostic should mention AC-02")

        failed_verification = make_scenario(scenarios_root, "failed-verification")
        write_ready_requirements(failed_verification)
        write_ready_investigation(failed_verification)
        write_ready_design(failed_verification, approved=True)
        write_tasks(failed_verification, status="DONE")
        write_failed_complete_verification(failed_verification)
        result = inspector.inspect_feature_state(failed_verification)
        assert_state(
            result,
            state="verification_incomplete",
            next_skill="ai-verification-closeout",
            blocking=False,
            errors=errors,
            label="inspector failed verification cannot be complete",
        )

        verification_metadata_inconsistent = make_scenario(scenarios_root, "verification-metadata-inconsistent")
        write_ready_requirements(verification_metadata_inconsistent)
        write_ready_investigation(verification_metadata_inconsistent)
        write_ready_design(verification_metadata_inconsistent, approved=True)
        write_tasks(verification_metadata_inconsistent, status="DONE")
        write_complete_verification(verification_metadata_inconsistent)
        rewrite_frontmatter(verification_metadata_inconsistent / "verification.md", {"updated_at": ""})
        result = inspector.inspect_feature_state(verification_metadata_inconsistent)
        assert_state(
            result,
            state="verification_metadata_inconsistent",
            next_skill="ai-verification-closeout",
            blocking=True,
            errors=errors,
            label="inspector complete verification must have updated_at",
        )

        verification_ready_status = make_scenario(scenarios_root, "verification-ready-status")
        write_ready_requirements(verification_ready_status)
        write_ready_investigation(verification_ready_status)
        write_ready_design(verification_ready_status, approved=True)
        write_tasks(verification_ready_status, status="DONE")
        rewrite_frontmatter(
            verification_ready_status / "verification.md",
            {
                "stage_status": "ready",
                "updated_at": "2026-05-09T20:30:00+08:00",
                "evidence_complete": True,
            },
        )
        result = inspector.inspect_feature_state(verification_ready_status)
        assert_state(
            result,
            state="verification_metadata_inconsistent",
            next_skill="ai-verification-closeout",
            blocking=True,
            errors=errors,
            label="inspector verification stage_status ready must be rejected",
        )

        empty_handoff = make_scenario(scenarios_root, "empty-handoff")
        write_ready_requirements(empty_handoff)
        write_ready_investigation(empty_handoff)
        write_ready_design(empty_handoff, approved=True)
        write_tasks(empty_handoff, status="DONE")
        write_complete_verification(empty_handoff)
        write_empty_complete_handoff(empty_handoff)
        result = inspector.inspect_feature_state(empty_handoff)
        assert_state(
            result,
            state="handoff_incomplete",
            next_skill="ai-verification-closeout",
            blocking=False,
            errors=errors,
            label="inspector empty handoff cannot be complete",
        )

        handoff_without_ops = make_scenario(scenarios_root, "handoff-without-ops")
        write_ready_requirements(handoff_without_ops)
        write_ready_investigation(handoff_without_ops)
        write_ready_design(handoff_without_ops, approved=True)
        write_tasks(handoff_without_ops, status="DONE")
        write_complete_verification(handoff_without_ops)
        write_complete_handoff_without_ops(handoff_without_ops)
        result = inspector.inspect_feature_state(handoff_without_ops)
        assert_state(
            result,
            state="handoff_incomplete",
            next_skill="ai-verification-closeout",
            blocking=False,
            errors=errors,
            label="inspector complete handoff must include config/sql/deploy notes",
        )

        handoff_unlabeled_ops = make_scenario(scenarios_root, "handoff-unlabeled-ops")
        write_ready_requirements(handoff_unlabeled_ops)
        write_ready_investigation(handoff_unlabeled_ops)
        write_ready_design(handoff_unlabeled_ops, approved=True)
        write_tasks(handoff_unlabeled_ops, status="DONE")
        write_complete_verification(handoff_unlabeled_ops)
        write_complete_handoff_with_unlabeled_ops(handoff_unlabeled_ops)
        result = inspector.inspect_feature_state(handoff_unlabeled_ops)
        assert_state(
            result,
            state="handoff_incomplete",
            next_skill="ai-verification-closeout",
            blocking=False,
            errors=errors,
            label="inspector complete handoff must label config/sql/deploy/data repair notes",
        )

        handoff_metadata_inconsistent = make_scenario(scenarios_root, "handoff-metadata-inconsistent")
        write_ready_requirements(handoff_metadata_inconsistent)
        write_ready_investigation(handoff_metadata_inconsistent)
        write_ready_design(handoff_metadata_inconsistent, approved=True)
        write_tasks(handoff_metadata_inconsistent, status="DONE")
        write_complete_verification(handoff_metadata_inconsistent)
        write_complete_handoff(handoff_metadata_inconsistent)
        rewrite_frontmatter(handoff_metadata_inconsistent / "handoff.md", {"evidence_complete": False})
        result = inspector.inspect_feature_state(handoff_metadata_inconsistent)
        assert_state(
            result,
            state="handoff_metadata_inconsistent",
            next_skill="ai-verification-closeout",
            blocking=True,
            errors=errors,
            label="inspector complete handoff must have evidence_complete true",
        )

        complete = make_scenario(scenarios_root, "complete")
        write_ready_requirements(complete)
        write_ready_investigation(complete)
        write_ready_design(complete, approved=True)
        write_tasks(complete, status="DONE")
        write_complete_verification(complete)
        write_complete_handoff(complete)
        result = inspector.inspect_feature_state(complete)
        if result.get("state") != "complete" or result.get("complete") is not True:
            fail(errors, f"inspector complete: expected complete state, got {result}")


def main() -> int:
    errors: list[str] = []

    for yaml_path in sorted(SKILLS.glob("*/agents/openai.yaml")):
        text = yaml_path.read_text()
        if "allow_implicit_invocation: false" not in text:
            fail(errors, f"{yaml_path}: allow_implicit_invocation must be false")
        if "allow_implicit_invocation: true" in text:
            fail(errors, f"{yaml_path}: implicit invocation is still true")

    orchestrator_skill = ORCHESTRATOR / "SKILL.md"
    orch_text = orchestrator_skill.read_text()
    for required in ["Workflow contract", "阶段停止点", "Safety policy", "WORKFLOW_CONTRACT.md", "approval_status", "references/golden-examples.md"]:
        if required not in orch_text:
            fail(errors, f"{orchestrator_skill}: missing {required}")
    for field in ROUTE_FIELDS:
        if field not in orch_text:
            fail(errors, f"{orchestrator_skill}: missing route field {field}")
    assert_not_contains_any(orch_text, FORBIDDEN_ROUTE_SOURCE_PATTERNS, errors, str(orchestrator_skill))
    if "本 skill 自身不接受其他 skill 的被动路由" not in orch_text:
        fail(errors, f"{orchestrator_skill}: orchestrator must reject passive routing from other skills")
    if "`updated_at` 并保持 `evidence_complete: true`" not in orch_text:
        fail(errors, f"{orchestrator_skill}: design approval must preserve metadata updates")
    assert_order(
        orch_text,
        "`investigation.md` 的 `stage_status` 为 `blocked`",
        "`investigation.md` 的 `stage_status` 为 `draft`",
        errors,
        "investigation stage inference",
    )
    assert_order(
        orch_text,
        "`design.md` 的 `stage_status` 为 `blocked`",
        "`design.md` 的 `stage_status` 为 `draft`",
        errors,
        "design stage inference",
    )

    contract = ORCHESTRATOR / "WORKFLOW_CONTRACT.md"
    if not contract.exists():
        fail(errors, "missing WORKFLOW_CONTRACT.md")
    else:
        contract_text = contract.read_text()
        for required in [
            "Activation contract",
            "Route contract",
            "Document metadata contract",
            "Design approval contract",
            "Gate policy",
            "Safety policy",
            "Service startup and port-check protocol",
            "Scope change protocol",
            "Resume protocol",
        ]:
            if required not in contract_text:
                fail(errors, f"{contract}: missing {required}")
        assert_not_contains_any(contract_text, FORBIDDEN_ROUTE_SOURCE_PATTERNS, errors, str(contract))
        assert_contains_all(
            contract_text,
            [
                "`ai-feature-orchestrator` 显式路由到目标阶段 skill",
                "路由执行机制",
                "scripts/inspect_feature_state.py <feature_dir>",
                "阶段文档 metadata 写入规则",
                "`updated_at`",
                "`evidence_complete: true`",
                "`task_count` 必须等于真实任务数量",
                "只有所有 in-scope acceptance criteria 都有真实验证证据且结果为 `PASS`",
                "辅助模板 Markdown 可解析，但不得包含 `feature_stage` 或 `stage_status`",
                "输出规则必须说明 `updated_at` / `evidence_complete`",
            ],
            errors,
            str(contract),
        )

    for name in CHILD_SKILLS:
        path = SKILLS / name / "SKILL.md"
        text = path.read_text()
        frontmatter_text = read_frontmatter_text(path, errors)
        if "complete route payload" not in frontmatter_text:
            fail(errors, f"{path}: description must require complete route payload for routed invocation")
        if "routes here with `feature_dir`" in frontmatter_text:
            fail(errors, f"{path}: description must not imply feature_dir alone is sufficient")
        assert_not_contains_any(text, FORBIDDEN_ROUTE_SOURCE_PATTERNS, errors, str(path))
        for required in ["Activation policy", "启动模式与 route contract", "Safety policy"]:
            if required not in text:
                fail(errors, f"{path}: missing {required}")
        for field in ROUTE_FIELDS:
            if field not in text:
                fail(errors, f"{path}: missing route field {field}")
        if "自行猜目录" not in text:
            fail(errors, f"{path}: missing no-guess-directory guard")
        if "WORKFLOW_CONTRACT.md" not in text:
            fail(errors, f"{path}: missing shared contract reference")
        if "`ai-feature-orchestrator` 显式路由到本 skill" not in text:
            fail(errors, f"{path}: routed invocation must be restricted to ai-feature-orchestrator")
        if "完整 route payload" not in text:
            fail(errors, f"{path}: routed invocation must require a complete route payload")
        if "被 `ai-feature-orchestrator` 路由" not in text:
            fail(errors, f"{path}: route contract must name ai-feature-orchestrator as router")
        assert_contains_all(text, CHILD_OUTPUT_REQUIREMENTS[name], errors, str(path))
        if name in CHILD_PREFLIGHT_REQUIREMENTS:
            assert_contains_all(
                text,
                CHILD_PREFLIGHT_REQUIREMENTS[name],
                errors,
                f"{path} metadata preflight",
            )

    implementation_text = (SKILLS / "ai-implementation-execution" / "SKILL.md").read_text()
    assert_order(
        implementation_text,
        "真实 `DOING` 任务，优先恢复",
        "第一个真实 `TODO` 任务",
        errors,
        "implementation task selection",
    )

    task_planning_text = (SKILLS / "ai-task-planning" / "SKILL.md").read_text()
    assert_contains_all(
        task_planning_text,
        ["每项规划期任务必须写", "执行要点", "风险", "任务进入 `DONE` 时必须由执行阶段补齐真实记录"],
        errors,
        "task planning required task fields",
    )

    verification_text = (SKILLS / "ai-verification-closeout" / "SKILL.md").read_text()
    assert_contains_all(
        verification_text,
        [
            "`requirements.md`、`investigation.md`、`design.md` 和 `tasks.md` 已存在",
            "读取 `investigation.md` 的真实调用链",
            "source of truth",
            "结合 `investigation.md` 的真实链路和数据来源",
            "只有所有 in-scope acceptance criteria 都有真实验证证据且结果为 `PASS`",
            "存在 `FAIL`、`BLOCKED`、未覆盖项或无法解释的验证缺口",
        ],
        errors,
        "verification closeout investigation dependency",
    )

    required_template_dirs = [TEMPLATE / "resource", TEMPLATE / "sql"]
    for directory in required_template_dirs:
        if not directory.is_dir():
            fail(errors, f"{directory}: missing template directory")
    for sql_name in ["DDL.sql", "DML.sql", "ROLLBACK.sql"]:
        if not (TEMPLATE / "sql" / sql_name).is_file():
            fail(errors, f"{TEMPLATE / 'sql' / sql_name}: missing SQL draft file")

    for md_path in sorted(TEMPLATE.rglob("*.md")):
        text = md_path.read_text()
        metadata = parse_frontmatter(md_path, errors)
        for pattern in BAD_TEMPLATE_PATTERNS:
            if pattern in text:
                fail(errors, f"{md_path}: contains misleading placeholder pattern {pattern!r}")

        relative_name = md_path.relative_to(TEMPLATE).as_posix()
        if relative_name in STAGE_TEMPLATE_FILES:
            expected_stage = STAGE_TEMPLATE_FILES[relative_name]
            for required in ["feature_stage", "stage_status", "updated_at", "evidence_complete"]:
                if required not in metadata:
                    fail(errors, f"{md_path}: missing stage metadata {required}")
            if metadata.get("stage_status") not in VALID_STAGE_STATUS:
                fail(errors, f"{md_path}: invalid stage_status {metadata.get('stage_status')!r}")
            elif metadata.get("stage_status") not in STAGE_ALLOWED_STATUS[expected_stage]:
                fail(
                    errors,
                    f"{md_path}: invalid stage_status {metadata.get('stage_status')!r} for {expected_stage}",
                )
            if metadata.get("feature_stage") != expected_stage:
                fail(errors, f"{md_path}: feature_stage must be {expected_stage!r}")
            if metadata.get("evidence_complete") not in {"false", "true"}:
                fail(errors, f"{md_path}: evidence_complete must be true or false")
            updated_at = metadata.get("updated_at", "")
            if updated_at and not ISO_WITH_TZ.match(updated_at):
                fail(errors, f"{md_path}: updated_at must be ISO 8601 with timezone")
        elif relative_name in {"README.md", "resource/README.md"}:
            for forbidden in ["feature_stage", "stage_status"]:
                if forbidden in metadata:
                    fail(errors, f"{md_path}: auxiliary doc must not include {forbidden}")
            for required in ["doc_type", "doc_status", "updated_at"]:
                if required not in metadata:
                    fail(errors, f"{md_path}: missing auxiliary metadata {required}")

    tasks_text = (TEMPLATE / "tasks.md").read_text()
    if "task_count: 0" not in tasks_text:
        fail(errors, "template tasks.md should start with task_count: 0")
    if "当前无真实任务" not in tasks_text:
        fail(errors, "template tasks.md should explicitly state no real tasks")
    tasks_metadata = parse_frontmatter(TEMPLATE / "tasks.md", errors)
    if tasks_metadata.get("evidence_complete") != "false":
        fail(errors, "template tasks.md should include evidence_complete: false")

    design_metadata = parse_frontmatter(TEMPLATE / "design.md", errors)
    for field in ["approval_status", "approved_by", "approved_at", "approval_evidence"]:
        if field not in design_metadata:
            fail(errors, f"template design.md missing approval metadata {field}")
    if design_metadata.get("approval_status") != "pending":
        fail(errors, "template design.md should start with approval_status: pending")

    golden_examples = ORCHESTRATOR / "references" / "golden-examples.md"
    if not golden_examples.is_file():
        fail(errors, f"{golden_examples}: missing golden examples reference")
    else:
        examples_text = golden_examples.read_text()
        for required in ["Happy path", "Blocked requirement", "Resume DOING", "Verification failed"]:
            if required not in examples_text:
                fail(errors, f"{golden_examples}: missing {required} example")
        assert_contains_all(
            examples_text,
            [
                "`evidence_complete: true`",
                "`evidence_complete: false`",
                "`updated_at`",
                "`task_count` 等于真实任务数量",
                "必须读取 `investigation.md`",
                "source of truth",
                "未读取 `investigation.md` 就把验证结论写成 complete",
                "执行要点：",
                "风险：",
            ],
            errors,
            str(golden_examples),
        )

    for doc_path in [*sorted(SKILLS.glob("*/SKILL.md")), ORCHESTRATOR / "WORKFLOW_CONTRACT.md"]:
        if "AI feature workflow" in doc_path.read_text():
            fail(errors, f"{doc_path}: use unified term AI Feature Workflow")

    run_inspector_scenarios(errors)

    if errors:
        print("AI skill smoke test failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("AI skill smoke test passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
