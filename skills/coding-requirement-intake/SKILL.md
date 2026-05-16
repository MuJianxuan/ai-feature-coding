---
name: coding-requirement-intake
description: "Coding 需求澄清技能。Activation restricted: use only when the user explicitly names `coding-requirement-intake`, or `coding-feature-orchestrator` explicitly routes here with complete route payload. Do not auto-trigger for ordinary requirement clarification or feature discussion."
---

# Coding Requirement Intake

## 目标

把 `discovery.md` 中已经澄清的前置发现结论规格化为可执行、可验证、可追踪的 `requirements.md`。不要急着写方案或代码。

## 共享契约

执行前必须遵守 `../coding-feature-orchestrator/WORKFLOW_CONTRACT.md`。如果本文件与 contract 冲突，采用更严格、更不容易误触发或越界的规则。

## Activation policy

本 skill 只能在以下情况下使用：

1. 用户在当前请求中明确写出 `coding-requirement-intake`，或明确要求使用 Coding Feature Workflow 的需求澄清阶段。
2. `coding-feature-orchestrator` 显式路由到本 skill，并提供完整 route payload（`activation_source`、`feature_dir`、`stage_evidence`）。

不满足时：

- 不得进入本 skill。
- 不得创建、猜测或切换 `.docs/feature-*` 目录。
- 不得把普通需求讨论自动升级成 Coding Feature Workflow。

## 启动模式与 route contract

- `direct_explicit`：用户在当前请求中明确写出 `coding-requirement-intake`。这种模式也必须提供已有 `feature_dir`；如果缺少，立即停止并提示用户改用 `coding-feature-orchestrator` 新建或选择 feature 目录。
- `routed_invocation`：不是用户直接点名本 skill，而是被 `coding-feature-orchestrator` 路由。此时必须同时收到：
  - `activation_source: coding-feature-orchestrator`
  - `feature_dir: <相对或绝对路径>`
  - `stage_evidence: <为什么进入需求澄清阶段的证据>`
- 被动触发时缺少任一 route 字段，都必须拒绝启动；不得自行猜目录或补造上游文件。

## 前置检查

开始前必须确认：

- 已收到明确的 `feature_dir`。
- `feature_dir` 目录存在。
- `discovery.md` 已存在。
- `discovery.md stage_status: ready`。
- `discovery.md evidence_complete: true`。
- `discovery.md project_context` 是 `existing_project` 或 `empty_project`，且 `project_context_evidence` 已写明。
- `discovery.md updated_at` 已写入 ISO 8601 + timezone。
- `requirements.md` 和 `resource/README.md` 已由 orchestrator/template 准备好。

如果缺少上述任一条件，立即停止并报告缺失项；不要临时补造上游准备文件。

## Safety policy

- 禁止删除文件或目录，除非用户明确许可。
- 禁止 git commit / push / checkout / branch / reset / worktree 等仓库状态变更，除非用户明确许可。
- 禁止覆盖用户未提交改动；写入文档前后都要检查工作区状态。
- 只询问仓库无法回答的问题；提问必须附已查证据。
- 用户新增或改变 scope 时，先更新 `requirements.md` 的 in-scope / out-of-scope / acceptance criteria，再让后续阶段重算证据和设计。
- 本阶段完成后必须停下，输出下一阶段建议；除非用户明确要求连续推进，不得自行调用下一阶段。

## 工作流

1. 读取当前需求目录、`discovery.md` 和 `resource/README.md`，找已有业务资料、会议纪要、原型或接口草案。
2. 基于 discovery 的项目上下文调研、外部调研、方案方向和逐问逐答记录整理 PRD；不要重复提出已回答的问题。
3. 从仓库中查可回答的问题，例如已有模块、相似功能、路由、数据表、枚举、权限模型。
4. 补齐 `requirements.md`：
   - 背景与业务目标
   - in-scope（标注 MoSCoW 优先级）
   - out-of-scope
   - 用户路径或业务流程
   - 业务域建模：`Domain ID`、业务能力、Actor / Role、核心 Entity、业务规则 / 边界、关联 AC
   - acceptance criteria（每条标注优先级）
   - 优先级矩阵（见"优先级排序框架"）
   - 非功能要求
   - 约束与假设
   - 待确认问题
5. 如果发现 discovery 漏掉的关键模糊点或 `project_context` 判定错误，先记录完整清单，再逐一提问；回答影响前置发现时同步回写 `discovery.md`。
6. 只询问仓库无法回答的问题。每次提问必须附带已查证据。
7. 不进入后置仓库精查或技术设计，直到 acceptance criteria 可验证且范围边界稳定。

## 渐进式澄清策略

需求澄清不是一次性填表，而是分层递进的对话过程。目的是让用户在每一轮都能确认"你理解对了"，避免最终交付时才发现理解偏差。

### 三层递进结构

**第一层：Scope 边界确认**
- 先用一两句话回放你对核心目标的理解，让用户确认方向正确。
- 明确 in-scope 和 out-of-scope 的边界。如果用户描述模糊，给出两到三个可能的边界划分方案，让用户选择。
- 这一层没有达成共识前，不要深入细节。

**第二层：用户路径与业务流程细化**
- 逐条梳理主路径（happy path）和关键分支路径。
- 对每条路径，确认：触发条件、参与角色、预期结果、异常处理。
- 每梳理完一条路径，简要回放并确认，再进入下一条。

**第三层：边缘场景与非功能约束**
- 主动提出用户可能遗漏的边缘场景（并发、权限越界、数据为空、超时、幂等性等）。
- 补齐非功能需求：性能指标、安全要求、兼容性、可观测性。
- 对每个假设，显式写出并标记为"待用户确认"或"已确认"。

### 澄清原则

- **假设显式化**：任何你做出的推断都必须写成假设条目，标记状态（`ASSUMED` / `CONFIRMED` / `REJECTED`）。不允许静默假设。
- **回放确认**：每完成一个层级的澄清，用简洁语言回放结论，等用户确认后再进入下一层。回放格式："我的理解是：[结论]。如果有偏差请指出。"
- **批量提问，逐条编号**：一次提出的问题不超过 5 个，每个问题编号，方便用户逐条回复。问题按影响范围从大到小排列。
- **区分"需要用户决策"和"需要用户确认"**：决策类问题给出选项和各选项的 trade-off；确认类问题给出你的判断并请用户 approve/reject。
- **不重复提问**：已在 `discovery.md` 中回答过的问题不再提出。如果需要追问细节，引用原始回答并说明为什么需要进一步澄清。

## 优先级排序框架

每个 in-scope 条目和 acceptance criteria 都必须标注优先级。使用 MoSCoW 方法：

| 级别 | 含义 | 判断标准 |
|------|------|----------|
| **Must** | 没有就不能上线 | 缺失会导致核心业务流程无法完成，或违反合规/安全要求 |
| **Should** | 重要但可延期到下一迭代 | 影响用户体验或效率，但有临时替代方案 |
| **Could** | 锦上添花 | 提升体验但不影响核心功能，实现成本低时可顺手做 |
| **Won't (this time)** | 本次明确不做 | 记录在 out-of-scope，防止实现阶段 scope creep |

### 排序规则

1. 用户明确指定优先级时，直接采纳。
2. 用户未指定时，根据以下维度建议优先级并请用户确认：
   - 业务影响：该功能缺失对核心业务流程的阻断程度
   - 用户频率：该功能被目标用户使用的频率
   - 依赖关系：是否有其他功能依赖它先完成
   - 实现风险：技术不确定性或外部依赖的风险
3. 优先级冲突时（如用户认为所有都是 Must），主动挑战："如果只能上线 3 个功能，哪 3 个？" 帮助用户做真正的取舍。

### 输出格式

在 `requirements.md` 中，优先级以标签形式标注在每个条目后：

```
- 用户可以通过邮箱注册账号 [Must]
- 注册时支持手机号验证 [Should]
- 支持第三方 OAuth 登录（Google/GitHub）[Could]
- 支持企业 SSO 集成 [Won't]
```

在 acceptance criteria 中同样标注：

```
AC-1 [Must]: 当用户提交有效邮箱和密码时，系统应创建账号并发送验证邮件
AC-2 [Should]: 当用户输入已注册邮箱时，系统应提示"该邮箱已注册"并提供登录链接
```

## 质量标准

- 每条验收标准都能被测试、日志、接口响应、UI 行为或数据状态验证。
- 每条验收标准都必须绑定真实业务域；业务域必须有稳定 `Domain ID`，并能解释业务能力、Actor / Role、核心 Entity 和业务规则 / 边界。
- out-of-scope 要明确，避免 AI 在实现阶段擅自扩大范围。
- 待确认问题要区分 `BLOCKING` 和 `NON_BLOCKING`。
- 凡影响 scope、acceptance criteria、用户路径、数据/API/UI 行为、风险验证或任务拆解的问题，都必须逐一澄清，不能静默假设。
- 需求资料必须在 `resource/README.md` 建索引，写清文件名、来源、更新时间和用途。

## 输出

更新 `requirements.md` 和 `resource/README.md`。如果仍有阻塞问题，在 `requirements.md` frontmatter 将 `stage_status` 标记为 `blocked`、`evidence_complete: false`，并在“待确认问题”中记录；如果范围和 acceptance criteria 已稳定，将 `stage_status` 标记为 `ready`、`evidence_complete: true`。每次写入 `requirements.md` 或 `resource/README.md` 都必须同步更新对应 frontmatter 的 `updated_at`。输出下一步建议后停止。
