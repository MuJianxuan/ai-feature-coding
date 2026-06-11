---
name: ship-spec
description: "ShipKit 规范管理技能。维护 .docs/spec 知识库，按 meta.yml workspace/projects 隔离加载规范，并在 Build 完成后更新已有功能索引。"
---

# ship-spec

## 目标

维护项目知识库，让 Understand、Design、Build 读到正确上下文。spec 是项目现实约束，不是摆设。

参考模板不是 spec。spec 是项目现实约束；模板只是 Design 阶段的检查清单。两者冲突时，优先级永远是：`requirements/AC > 项目 spec > 现有代码事实 > 参考模板 > AI 默认习惯`。

## TODO preflight

独立调用 `ship-spec` 时，必须调用可用 TODO 工具（例如 `TaskCreate`/agent todo 工具）创建或恢复 Spec TODO：

1. 读取 `.docs/ship/project.yml`（若存在）。
2. 读取调用方传入的 `feature_dir/meta.yml`（若有）。
3. 根据 `workspace_mode/projects` 确定加载范围。
4. 加载当前阶段需要的 spec。
5. 返回引用列表、warning 和缺失影响。
6. Build 完成后更新 existing-features 或给出规范沉淀建议。

嵌入阶段调用时，更新父阶段 TODO 即可。

## 默认目录

单项目：

```text
.docs/spec/
├── INDEX.md
├── frontend/
├── backend/
└── shared/
    ├── tech-stack.md
    ├── existing-features.md
    └── error-codes.md
```

多项目：

```text
.docs/ship/project.yml
.docs/spec/
├── INDEX.md
├── _shared/
│   ├── INDEX.md
│   ├── tech-stack.md
│   └── error-codes.md
├── web/
│   ├── INDEX.md
│   └── frontend/
└── api/
    ├── INDEX.md
    └── backend/
```

## project.yml

```yaml
workspace_mode: single_project # single_project | project_group
workspace_name: my-workspace
projects:
  - web
  - api
```

`project.yml` 是仓库默认 workspace 配置；具体 feature 的实际范围以 `feature_dir/meta.yml.workspace_mode/workspace_name/projects` 为准。

## 与 source_refs 的边界

- `source_refs` 是需求输入：PRD、UI/UX、link、issue、meeting、note、screenshot 等。
- spec 是项目约束：API 标准、命名、数据类型、安全要求、前端模式、既有功能索引。
- 不把 PRD 正文塞进 `.docs/spec/`。
- 不把项目规范当作用户需求；spec 只能约束实现方式，不能新增 AC。

## 加载规则

按阶段加载，不要一股脑吞全库：

| 阶段 | 加载内容 |
|---|---|
| Understand | existing-features、domain glossary、naming conventions |
| Design | API standards、frontend patterns、data model、tech-stack |
| Build | coding conventions、test standards、deployment constraints |
| Done | existing-features 更新、新规范沉淀建议 |

多项目隔离：

1. 永远加载 `_shared`。
2. 只加载 `meta.yml.projects` 指定项目的 spec。
3. project spec 与 shared 同名时，project 优先，记录 warning。
4. 不让未涉及项目的 spec 污染需求、设计或实现。
5. 如果 `.docs/ship/project.yml` 存在，`meta.yml.projects` 应是配置项目子集；否则由 validator 或 orchestrator 阻塞修正。

## INDEX.md 建议格式

```markdown
# Spec Index

| spec_id | file | stages | projects | description |
|---|---|---|---|---|
| rest-api-standard | backend/rest-api-standard.md | design,build | api | REST API 规范 |
| existing-features | shared/existing-features.md | understand,done | all | 已有功能索引 |
```

## existing-features 更新

Build 完成后追加或更新：

```markdown
## 用户模块
- **用户登录**：完成时间 2026-06-09，Feature: feature-20260609-user-login
  - 表：users, sessions
  - API：POST /api/v1/auth/login
  - 页面：/login
  - 关键测试：tests/e2e/login.spec.ts
```

多项目组下：

- 通用能力写 `_shared/existing-features.md`。
- 项目专属能力写对应项目 spec。
- 不更新 `meta.yml.projects` 之外的项目。

不要把敏感信息写进 spec：密码、token、生产密钥、内部部署地址都禁止。

## 与 Design Reference Template 的边界

- 不把模板文件放进 `.docs/spec/`，除非它已经成为项目长期规范。
- 不把 `.docs/技术方案模版.md` 当成全局 spec；它最多是项目级参考模板候选。
- `ship-spec` 只提供项目约束：API 标准、命名、数据类型、安全要求、前端模式。
- `ship-design` 负责选择模板，并在模板与 spec 冲突时写明“以 spec 为准”。
- 模板不得诱导写入密码、token、生产密钥、内部部署地址等敏感信息；只允许描述 secret 来源，例如“从环境变量读取”。

## 新规范沉淀评分

只有分数 `>= 60` 才建议新增 spec：

- 复用次数 ≥ 3：+40
- 模式稳定：+30
- 跨模块使用：+20
- 中高复杂度：+10

低分就别污染知识库。现实里最烂的规范库就是没人敢删、没人会读。

## 失败降级

- 没有 `.docs/spec`：返回空上下文 + warning；full flow 需要在 requirements/design 中记录缺失影响。
- INDEX 缺失：扫描少量常见文件，但提示补 INDEX。
- 规范冲突：project 优先，shared fallback，报告冲突。
- 文件权限/解析失败：记录 warning，并让阶段技能决定是否阻塞。

## 不做什么

- 不替阶段技能写 requirements/design/build。
- 不把每次实现都沉淀成规范。
- 不把旧 ShipKit 的复杂状态字段加回来。
- 不把参考模板和项目规范混成一锅粥。
- 不让未涉及项目的 spec 污染当前 feature。
