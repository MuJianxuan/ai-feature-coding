---
name: coding-feature-discovery
description: "Coding 需求前置发现技能。Activation restricted: use only when the user explicitly names `coding-feature-discovery`, or `coding-feature-orchestrator` explicitly routes here with complete route payload. Do not auto-trigger for ordinary brainstorming, repo investigation, requirement clarification, or design prep."
---

# Coding Feature Discovery

## 目标

在正式 PRD 前完成需求前置发现：先基于原始 brief 做仓库广扫、必要的外部依赖调研、头脑风暴式方案方向探索和模糊点穷举，再逐一澄清影响交付的关键问题。产物是 `discovery.md`，它是 `requirements.md` 的前置输入。

## 共享契约

执行前必须遵守 `../coding-feature-orchestrator/WORKFLOW_CONTRACT.md`。如果本文件与 contract 冲突，采用更严格、更不容易误触发或越界的规则。

## Activation policy

本 skill 只能在以下情况下使用：

1. 用户在当前请求中明确写出 `coding-feature-discovery`，或明确要求使用 Coding Feature Workflow 的 discovery / 需求前置发现阶段。
2. `coding-feature-orchestrator` 显式路由到本 skill，并提供完整 route payload（`activation_source`、`feature_dir`、`stage_evidence`）。

不满足时：

- 不得进入本 skill。
- 不得创建、猜测或切换 `.docs/feature-*` 目录。
- 不得把普通 brainstorming / repo investigation / requirement clarification 自动升级成 Coding Feature Workflow。

## 启动模式与 route contract

- `direct_explicit`：用户在当前请求中明确写出 `coding-feature-discovery`。这种模式也必须提供已有 `feature_dir`；如果缺少，立即停止并提示用户改用 `coding-feature-orchestrator` 新建或选择 feature 目录。
- `routed_invocation`：不是用户直接点名本 skill，而是被 `coding-feature-orchestrator` 路由。此时必须同时收到：
  - `activation_source: coding-feature-orchestrator`
  - `feature_dir: <相对或绝对路径>`
  - `stage_evidence: <为什么进入 discovery 阶段的证据>`
- 被动触发时缺少任一 route 字段，都必须拒绝启动；不得自行猜目录或补造上游文件。

## 前置检查

开始前必须确认：

- 已收到明确的 `feature_dir`。
- `feature_dir` 目录存在。
- `discovery.md` 和 `resource/README.md` 已由 orchestrator/template 准备好。
- 用户原始 brief、需求资料索引或已有 resource 路径足以启动仓库广扫；如果连目标主题都无法识别，先只问一个短名 / 主题问题。

如果缺少上述任一条件，立即停止并报告缺失项；不要临时补造上游准备文件。

## Safety policy

- 禁止删除文件或目录，除非用户明确许可。
- 禁止 git commit / push / checkout / branch / reset / worktree 等仓库状态变更，除非用户明确许可。
- 禁止覆盖用户未提交改动；写入 `discovery.md` 前后都要检查工作区状态。
- 先查仓库和可验证资料，再问用户；提问必须附已查证据。
- 本阶段只形成方案方向，不写最终 `design.md`，不进入任务拆解或编码。
- 本阶段完成后必须停下，输出下一阶段建议；除非用户明确要求连续推进，不得自行调用下一阶段。

## 工作流

1. 读取 feature 目录、`resource/README.md`、用户原始资料和当前 `discovery.md`。
2. 做仓库广扫：确认项目结构、相关入口、相似功能、路由/API、数据表、权限模型、UI 或任务链路。
3. 按依赖触发外部调研：涉及第三方库、框架、OpenAI/API、版本行为或不确定实现时，必须用 Context7 或官方文档验证，并记录来源、适用范围和结论。
4. 生成 2-3 个方案方向，只写适用条件、约束、风险和取舍；不得伪装成最终设计。
5. 穷举模糊点和边界情况，至少覆盖 scope、acceptance criteria、用户路径、数据/API/UI 行为、权限、安全、性能、兼容性、验证方式和任务拆解风险。
6. 判断关键问题：凡影响交付范围、验收、用户路径、数据/API/UI 行为、风险验证或任务拆解的问题，都必须标为 `BLOCKING`。
7. 逐问逐答：每次只问一个最高优先级 `BLOCKING` 问题，问题必须具体、明确，并附已查证据。用户回答后，记录回答、结论和更新位置，再继续下一个关键问题。
8. 所有关键问题澄清后，更新进入 requirements 的完成判定。

## 质量标准

- `discovery.md` 必须列出全部已识别模糊点；不能只记录当前问题。
- `BLOCKING` 问题未清空时，`stage_status` 必须是 `blocked` 或 `draft`，`evidence_complete: false`。
- `ready` 只表示 discovery 证据足以进入 PRD 规格化，不表示最终技术方案已批准。
- 外部证据集中记录在 discovery；后续 design / tasks 只引用关键结论和来源。

## 输出

更新 `discovery.md`。如果仍有关键问题未回答，将 frontmatter `stage_status` 标记为 `blocked`、`evidence_complete: false`，并在“模糊点清单”与“逐问逐答记录”中记录证据；如果关键问题已清空且仓库广扫、必要外部调研、方案方向、进入 requirements 的完成判定齐备，将 `stage_status` 标记为 `ready`、`evidence_complete: true`。每次写入 `discovery.md` 都必须同步更新 `updated_at`。输出下一步建议后停止。
