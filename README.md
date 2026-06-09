# AI Coding Skills

面向个人开发者的通用开发流程技能套件。它保留 `ship-*` 命名和 `ship-orchestrator` 入口，但默认流程已从企业式审批链重构为轻量、证据驱动、可快速落地的 solo developer workflow。

## 安装

```bash
npx skills add MuJianxuan/ai-feature-coding
```

## 默认入口

只需要记住一个入口：

```text
使用 ship-orchestrator，帮我完成：<你的需求 / bug / refactor / UI / docs / release 任务>
```

默认阶段：

```text
Discover → Define → Understand → Design → Plan → Build → Verify → Close
```

其中阶段会按任务自动压缩：小 bug 可能从 `Understand` 开始；文档任务可能跳过 `Design`；UI 任务可能插入 `ship-shape`。

## 设计原则

- **个人开发者优先**：减少 ceremony，不模拟团队审批。
- **证据先行**：改代码前先读仓库事实、相关文件和现有测试。
- **最小 slice**：一次只实现一个可验证片段。
- **轻量门禁**：review skills 是 checklist，不是默认 hard gate。
- **可恢复**：工作产物默认写入 `.docs/ship/<work-id>/`。
- **可扩展**：复杂任务可按需调用 UI shaping、前后端深度设计、规范管理和 review 工具。

## 技能总览

| Skill | 角色 |
|---|---|
| `ship-orchestrator` | 默认入口、模式识别、阶段路由、恢复和总结 |
| `ship-discover` | 澄清真实目标、范围、非目标和成功标准 |
| `ship-define` | 生成轻量 brief、AC、假设和风险 |
| `ship-tech-discovery` | 阅读仓库现状，生成 context map |
| `ship-contract` | 定义最小稳定边界：API、事件、CLI、数据或不变量 |
| `ship-delivery-plan` | 拆成可执行 slices，列文件范围和验证命令 |
| `ship-build` | 单 slice 实现，保持外科手术式改动 |
| `ship-verify` | 跑测试/构建/检查，映射 AC 证据 |
| `ship-handoff` | 交付总结、风险、后续建议 |
| `ship-shape` | 可选 UI/UX shaping 和 HTML 原型 |
| `ship-frontend-design` / `ship-backend-design` | 可选深度设计工具 |
| `ship-define-review` / `ship-design-review` / `ship-plan-review` | 可选 review checklist |
| `ship-grill-me` | 一次一个关键问题的质询工具 |
| `ship-spec` | workspace 规范管理 utility |

## 文档入口

- 主文档：`skills/README.md`
- 共享协议：`skills/ship-orchestrator/_templates/protocol/workflow-protocol.md`
- 阶段映射：`skills/ship-orchestrator/scripts/workflow_stage_map.py`
- 元数据模板：`skills/ship-orchestrator/_templates/meta/meta.yml.template`
- 回归提示：`skills/ship-orchestrator/tests/regression-prompts.md`

## 维护校验

```bash
python3 skills/ship-orchestrator/scripts/validate_workflow_docs.py
python3 skills/ship-orchestrator/scripts/workflow_stage_map.py --list
```
