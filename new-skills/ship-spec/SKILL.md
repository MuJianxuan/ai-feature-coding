---
name: ship-spec
description: "新 ShipKit 规范管理技能。维护 .docs/spec 知识库，按阶段和项目隔离加载规范，并在 Build 完成后更新已有功能索引。"
---

# ship-spec

## 目标

维护项目知识库，让 Understand、Design、Build 读到正确上下文。spec 是现实约束，不是摆设。

参考模板不是 spec。spec 是项目现实约束；模板只是 Design 阶段的检查清单。两者冲突时，优先级永远是：`requirements/AC > 项目 spec > 现有代码事实 > 参考模板 > AI 默认习惯`。

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
4. 不让 web 的 frontend 规范污染 api 后端实现。

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

不要把敏感信息写进 spec：密码、token、生产密钥、内部部署地址都禁止。

## 与 Design Reference Template 的边界

- 不把模板文件放进 `.docs/spec/`，除非它已经成为项目长期规范。
- 不把 `.docs/技术方案模版.md` 当成全局 spec；它最多是项目级 `backend-enterprise` 参考模板候选。
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

- 没有 `.docs/spec`：返回空上下文 + warning，不阻塞 quick_start。
- INDEX 缺失：扫描少量常见文件，但提示补 INDEX。
- 规范冲突：project 优先，shared fallback，报告冲突。
- 文件权限/解析失败：记录 warning，并让阶段技能决定是否阻塞。

## 不做什么

- 不替阶段技能写 requirements/design/build。
- 不把每次实现都沉淀成规范。
- 不把旧 ShipKit 的复杂状态字段加回来。
- 不把参考模板和项目规范混成一锅粥。
