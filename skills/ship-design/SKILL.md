---
name: ship-design
description: "ShipKit Design 阶段。必须接收 feature_dir，基于 ready requirements 选择 Design Reference Template，完成 blocking design review，并在 Build 前 handoff 回 orchestrator。"
---

# ship-design

## 目标

基于 `requirements.md(status: ready)` 产出可实现的 `design.md`。一份文档同时包含 API Contract、数据模型、前端设计、后端设计、AC 覆盖映射、方案模板引用和设计审查记录。

## 硬前置

必须同时满足：

- 用户明确提供 `feature_dir`。
- `feature_dir/meta.yml` 存在且可读取。
- `requirements.md` frontmatter `status: ready`。
- `validate_requirements.py <feature_dir>` 无 errors。

缺 `feature_dir` 时停止，不自动扫描 `.docs/feature-*`，不创建新目录。

## TODO preflight

开始阶段工作前，必须调用可用 TODO 工具（例如 `TaskCreate`/agent todo 工具）创建或恢复 Design 阶段 TODO：

1. 加载 `feature_dir`、`meta.yml`、`requirements.md`。
2. 运行 `validate_requirements.py <feature_dir>`。
3. 根据 `workspace_mode/projects` 限定技术探索、代码阅读和架构影响面。
4. 探索项目结构与相关代码。
5. 加载 Design 阶段 spec。
6. 解析 `requested_design_template`，选择 Design Reference Template。
7. 针对阻塞设计决策采访用户。
8. 编写推荐技术方案 `design.md`。
9. 调用 `ship-grill-me` 做对抗式设计审查。
10. 运行 `validate_design.py <feature_dir>`。
11. 标记 `design.md(status: ready)`。
12. 更新 `meta.yml.status: blocked`、`blocked_reason: awaiting_user_confirmation`。
13. 停止并询问是否进入 Build。
14. 输出 handoff：要求用户回到/调用 `ship-orchestrator` 处理 Build approval。

## 输入

- `feature_dir/meta.yml`。
- `requirements.md(status: ready)`。
- `meta.yml.source_refs` 与 `resource/` 材料，用于追溯来源。
- `meta.yml.requested_design_template`（可为空）。
- 使用 `ship-spec` CLI 按 workspace scope 加载的 API 规范、前端模式、数据模型规范、技术栈。
- Design Reference Template：项目级模板或 `skills/ship-orchestrator/templates/design-reference/` 内置模板。
- 现有代码结构（只读探索）。

## Workspace scope

- `workspace_mode: single_project`：默认当前项目。
- `workspace_mode: project_group`：只围绕 `meta.yml.projects` 指定项目和 `_shared` 做技术探索与 spec 加载。
- 设计影响面疑似超出范围时，必须说明证据并询问是否扩大 `projects`。

## 流程

1. 运行 `validate_requirements.py <feature_dir>`；失败则退回 Understand。
2. 加载 Design 阶段 spec：API、frontend、backend、database、shared。
3. 读取 `meta.yml.requested_design_template`；按“模板选择与引用”解析参考模板。
4. 必要时做技术调研；熟悉技术栈直接引用 spec，不搞论文式调研。
5. 生成 `design.md`，必须保留稳定基础章节，并写 `## 方案模板引用`。
6. 调用 `ship-grill-me` 做 blocking design review；有 blocking 就修设计或提问。
7. 运行 `validate_design.py <feature_dir>`；有 error 不得 ready。
8. 标记 `design.md status: ready`。
9. 更新 `meta.yml.status: blocked`、`blocked_reason: awaiting_user_confirmation`。
10. 停止并询问用户是否进入 Build。
11. 输出 handoff，要求用户回到/调用 `ship-orchestrator` 持久化 Build approval。

`ship-design` 不得把 `meta.yml.current_stage` 改为 `build`，也不得直接启动 `ship-build`。

## blocking review

Design 阶段必须执行 `ship-grill-me`。blocking 问题包括：

- API 缺 Request/Response/Error。
- 数据模型与 spec 或现有表冲突。
- 错误处理缺失。
- 性能目标无法由设计解释。
- 前后端责任边界不清。
- 设计未覆盖某个 AC。
- 模板选择明显不匹配需求类型。
- 缺少 `meta.yml.design_template_ref` 或正文 `## 方案模板引用`。
- 模板必填项缺失且无“不涉及 + 原因”或模板偏离说明。
- 偏离项目 spec、现有代码事实或 AC，且没有解释影响与替代设计。
- `status: ready` 仍包含未替换模板变量、`TBD`、`待补充`、`后续再说`、无解释的“视情况而定”。

## 模板选择与引用

参考模板是 Design 阶段的护栏，不是新阶段，也不是替代 requirements/spec 的硬编码文档。

优先级：

```text
用户显式指定模板
    ↓
项目级模板（如 .docs/ship/design-templates/ 或 .docs/技术方案模版.md）
    ↓
ShipKit 内置模板（templates/design-reference/）
```

规则：

1. `ship-orchestrator` 只把用户原话记录为 `meta.yml.requested_design_template`；本技能负责解析。
2. 能解析到项目文件时，写入 `meta.yml.design_template_ref: "project:<path>#<id>@1"`。
3. 使用内置模板时，写入 `meta.yml.design_template_ref: "builtin:<template-id>@1"`。
4. 所有 ShipKit feature 都必须写入 `meta.yml.design_template_ref` 和 `meta.yml.design_template_reason`。
5. `design.md` frontmatter 不重复模板机器事实；正文 `## 方案模板引用` 必须与 `meta.yml.design_template_ref` 一致。
6. 多模板命中时只选一个主模板，其他最多 2 个作为候选/辅助 checklist，不把模板拼成怪物文档。
7. 项目 spec 优先级高于模板；冲突时以 `requirements/AC > 项目 spec > 现有代码事实 > 参考模板 > AI 默认习惯` 为准。

内置模板 ID：`backend-service`、`frontend-ui`、`fullstack-feature`、`async-task`、`data-migration`、`integration`、`config-change`。

## design.md 结构

````markdown
---
status: ready
updated_at: "2026-06-09T14:00:00Z"
spec_refs: ["rest-api-standard", "react-patterns"]
---

# 技术设计：用户登录

## 方案模板引用
- 主模板：`builtin:fullstack-feature@1`（来自 `meta.yml.design_template_ref`）
- 选择依据：本需求同时涉及前端、API 和数据模型。
- 候选模板：`backend-service(score=5)`、`fullstack-feature(score=8)`
- 未选原因：`backend-service` 仅作为后端辅助 checklist。
- 项目 spec 优先级：模板与 spec 冲突时，以已引用 spec 为准。

### 模板偏离
| 偏离项 | 原因 | 影响 | 替代设计 |
|---|---|---|---|
| 不新增 Session 表 | 项目现有 spec 使用 Redis session | 无 DB migration；依赖 Redis TTL | 在风险章节记录 Redis 不可用时登录失败 |

## AC 覆盖映射
| AC | 设计位置 | 测试建议 |
|---|---|---|
| AC-1 | API 契约、登录页面、AuthService | e2e login success |

## API 契约
### POST /api/v1/auth/login
**AC refs**: AC-1, AC-2
**Request**
```json
{"email":"user@example.com","password":"plain_password"}
```
**Response - 200 OK**
```json
{"token":"jwt_token","user":{"id":123,"name":"张三"}}
```
**Error Responses**
- 401 `AUTH_FAILED`: 邮箱或密码错误

## 数据模型
### Session 表（新增）
| 字段 | 类型 | 说明 |
|---|---|---|
| id | bigint | 主键 |

## 前端设计
- 页面：`/login`
- 组件：`LoginForm`
- 状态管理：按 spec 使用现有方案
- 错误处理：toast + 字段级错误

## 后端设计
- Controller → Service → Repository
- 事务边界、缓存、外部依赖写清楚

## 性能考量
- P95 < 500ms，通过索引和缓存满足。

## 风险和回滚
- 风险、替代方案、回滚方式。

## 设计审查记录
| Round | Reviewer | Blocking findings | 处理结果 |
|---|---|---:|---|
| 1 | ship-grill-me | 0 | ready |
````

## 质量标准

必须满足：

- API 契约包含 Request、成功 Response、错误 Response。
- 数据模型存在，或明确说明不涉及数据变更。
- 前后端责任边界清晰。
- 每个 AC 在设计中可追踪。
- 引用的 spec 不能被设计违反；若冲突，先解决。
- 错误处理明确，不把异常路径留给实现阶段猜。
- `status: ready` 时不得出现 `{{...}}`、未替换的 `{功能名称}`、`TBD`、`待补充`、`后续再说`、无解释的“视情况而定”。
- 必须说明“模板与 spec 冲突时 spec 优先”。
- 偏离模板不是问题；没有原因、影响、替代设计的偷偷偏离才是问题。

## 用户确认门禁

Design 完成后必须停止，不直接实现：

```text
设计方案已完成并通过质量检查。
核心设计：
- ...
是否开始实现？
[yes] 开始 Build
[modify] 修改设计
[review] 查看详细设计
```

用户明确确认后，必须 handoff 回 `ship-orchestrator`。只有 orchestrator 能把 `current_stage` 改为 `build` 并写入 `build_approved_at/build_approved_by/build_approval_note`。

## 输出 handoff

```text
design.md 已 ready，并通过 validate_design.py。
当前状态：blocked(awaiting_user_confirmation)
workspace：project_group
涉及项目：web, api
请回到/调用 ship-orchestrator 处理 Build approval；确认后再调用 ship-build，并传入 feature_dir：
.docs/feature-20260610-user-login
```

## 不做什么

- 不在用户确认前改业务代码。
- 不把 `current_stage` 改为 `build`。
- 不直接启动 `ship-build`。
- 不拆成旧 ShipKit 的 contract/frontend/backend 三份设计文档。
- 不为了“灵活”添加未被 AC 驱动的扩展点。
