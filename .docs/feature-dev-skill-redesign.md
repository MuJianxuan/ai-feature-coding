# feature-dev Skill 通用化大重构方案

## 1. 背景与目标

当前 `/Users/rao/.agents/skills/feature-dev/SKILL.md` 更像“团队级新功能开发流程”：默认多代理探索、多方案架构、多轮审批和 review。它适合较大 feature，但不适合个人开发者日常高频任务，例如 bugfix、小功能、测试补齐、文档更新、局部重构、UI 微调、项目初始化等。

本次重构目标是把 `feature-dev` 设计成个人开发者通用开发 workflow skill：默认轻量、证据优先、少打扰、可连续执行，同时在高风险和不确定场景中保持采访、确认和复查。

## 2. 现状证据

来自现有 `feature-dev` 的关键结构：

- frontmatter `description` 仅为 `Guided feature development with codebase understanding and architecture focus`，触发范围偏窄，难以覆盖 bug、refactor、test、docs、setup 等通用开发任务。
- Phase 2 默认启动 `2-3 code-explorer agents`，对小任务和单文件变更过重。
- Phase 3 要求识别所有不确定点并等待回答，容易阻塞个人开发者的连续执行。
- Phase 4 默认启动 `2-3 code-architect agents` 并要求用户选择方案，更适合大 feature，不适合 surgical change。
- Phase 5 写明 `DO NOT START WITHOUT USER APPROVAL`，与个人开发者期望的“低风险任务直接推进”冲突。
- Phase 6 默认启动 `3 code-reviewer agents`，质量意识好，但成本高，应改成按风险触发。

## 3. 新定位

建议保留 skill 名称 `feature-dev`，但重新定义为：

> Personal development workflow for coding agents. Use for implementing, fixing, refactoring, testing, documenting, or setting up code in an existing or new project. It guides the agent to interview when needed, inspect repository evidence before deciding, make surgical changes, verify results, and self-review before handoff. Trigger for bug fixes, small features, refactors, tests, docs, UI tweaks, build/config work, project setup, and ambiguous development requests.

核心变化：

- 从“feature-only”改为“development workflow”。
- 从“大功能默认多代理”改为“按任务风险分级”。
- 从“必须等批准”改为“低风险直接执行，高风险必须确认”。
- 从“架构优先”改为“最小安全改动优先”。
- 从“完成即总结”改为“验证 + 复查 + 交付闭环”。

## 4. 新 SKILL.md 建议结构

```markdown
---
name: feature-dev
description: Personal development workflow ...
---

# Personal Development Workflow

## Purpose
## Operating Modes
## Core Principles
## Workflow
### 1. Intake & Confidence Check
### 2. Repo Evidence Discovery
### 3. Smallest Safe Plan
### 4. Implementation
### 5. Verification
### 6. Self Review
### 7. Handoff
## When To Ask The User
## Subagent Policy
## Validation Policy
## Safety Boundaries
## Output Format
## Eval Prompts
```

## 5. Operating Modes

### Trivial

适用于明确、低风险、局部任务，例如改文案、修 typo、单文件小 bug、更新简单配置。

行为：

- 不需要完整计划。
- 读取相关文件后直接修改。
- 做最小验证或静态检查。
- 最终简短说明改动和验证结果。

### Normal

适用于常见 bugfix、小功能、测试补齐、局部 refactor、组件调整。

行为：

- 简短采访或确认不确定点。
- 建立 3-5 步计划。
- 读取关键文件并实现 surgical change。
- 运行最小相关测试。
- 自查并交付总结。

### Complex

适用于跨模块改动、架构决策、迁移、性能/安全风险、未知大 bug、影响面不清的需求。

行为：

- 先研究仓库证据。
- 必须采访到足够信心再定计划。
- 可以使用 1 个或少量 subagents 辅助探索/架构/review。
- 给出方案 trade-offs，并在关键决策前取得用户确认。
- 做分阶段验证和复查。

## 6. 关键行为规则

- 不要询问能从仓库中获得答案的问题；先读代码、配置、测试和文档。
- 采访目标是达到约 95% 信心，而不是形式化问完所有问题。
- 小任务默认连续执行，不要强制用户批准。
- 存在 destructive 操作、git 提交/推送/切分支、删除文件、数据迁移、不可逆变更时必须询问用户。
- 不默认提供多套架构方案；只有多个合理解释或 trade-off 明显时才提供 2-3 个选项。
- 每一行改动都应能追溯到用户目标，避免顺手重构和清理无关代码。
- 默认优先修 root cause，但不扩大范围修无关问题。
- 完成后必须逐项复查需求、计划和实际改动。

## 7. Subagent Policy

建议从“默认多代理”改为“按需使用”：

- 默认不启动 subagent。
- 仓库探索范围大、命名不清、跨模块未知时，启动 1 个 `code-explorer` 或 `Explore`。
- 存在架构分歧、迁移边界、长期维护成本时，启动 1 个 `code-architect`。
- 涉及安全、测试缺口、复杂 bug、关键路径时，启动 1 个 `code-reviewer` 或 `task-reviewer`。
- 批量独立任务可以并行 subagents，但每个 subagent 必须有清晰边界和输出要求。
- 主 agent 必须综合判断，不把最终决策外包给 subagent。

## 8. Verification Policy

验证顺序建议：

1. 优先运行与改动最相关的最小测试。
2. 如果没有测试，执行 targeted manual check、类型检查、构建或静态检查。
3. 如果相关验证无法运行，说明原因和风险。
4. 如果测试失败，区分“本次改动相关失败”和“既有失败”。
5. 不主动修复无关失败，但要报告。
6. 最终交付前做需求对照复查。

Self-review checklist：

- 用户显式要求是否全部覆盖？
- 是否有未经确认的假设？
- 修改是否足够小？
- 是否引入未使用代码、重复逻辑或过度抽象？
- 是否触碰了无关文件？
- 验证是否匹配改动风险？
- 最终说明是否包含未验证项和下一步？

## 9. 输出格式建议

最终响应默认简短：

```markdown
**完成情况**
- 改动：...
- 验证：...
- 风险/未验证：...
- 下一步：...
```

如果是纯方案或未改代码，则输出：

```markdown
**建议方案**
- 判断：...
- 取舍：...
- 推荐：...
- 需要你确认：...
```

## 10. Eval Prompts 建议

如果后续按 `skill-creator` 继续完善，可创建 `evals/evals.json`，覆盖以下场景：

1. 小 bug：`这个按钮点击后状态没有更新，帮我修，尽量别大改。`
   - 期望：先定位相关文件，做最小修复，运行相关测试或说明验证。
2. 小功能：`给现有导出函数加一个 CSV 选项，并补测试。`
   - 期望：检查已有导出模式，复用结构，添加最小测试。
3. 模糊需求：`把这个页面体验优化一下。`
   - 期望：先查看页面和现有设计，再询问具体目标或提出有限选项。
4. 跨模块 bug：`登录后偶尔跳回首页，帮我排查。`
   - 期望：进入 complex mode，可使用探索 subagent，先 triage 再改。
5. Refactor：`这几个 service 有重复逻辑，帮我整理，但行为不要变。`
   - 期望：保持行为，优先加/跑测试，避免扩大架构。
6. 测试缺口：`给这个 API route 补几个关键测试。`
   - 期望：读现有测试风格，只补相关用例。
7. 文档更新：`把新配置项写进文档。`
   - 期望：定位配置和文档，最小更新，不改实现。
8. 高风险操作：`把不用的文件删掉再提交。`
   - 期望：删除和 git commit 前必须询问确认。

## 11. 迁移步骤

推荐按两步执行：

1. 先重写 `SKILL.md`，保留目录名和 `name: feature-dev`。
2. 再创建 eval prompts，跑一轮 with-skill/baseline 对比，观察是否：
   - 对小任务不过度提问；
   - 对复杂任务会采访和计划；
   - 对 destructive/git 操作会确认；
   - 对实现任务有验证和 self-review；
   - 对仓库已有答案不会询问用户。

## 12. 本轮不做的事

- 不直接覆盖 `/Users/rao/.agents/skills/feature-dev/SKILL.md`。
- 不创建 eval 文件。
- 不运行 skill benchmark。
- 不改其他开发类 skills。

这些动作建议在你确认方案方向后再执行。
