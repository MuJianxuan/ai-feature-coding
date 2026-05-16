---
name: coding-technical-design
description: "Coding 技术设计技能。Activation restricted: use only when the user explicitly names `coding-technical-design`, or `coding-feature-orchestrator` explicitly routes here with complete route payload. Do not auto-trigger for ordinary architecture, design, planning, or proposal work."
---

# Coding Technical Design

## 目标

基于 `discovery.md` 和 `requirements.md` 做详细技术设计。`existing_project` 做仓库勘探和真实链路核对；`empty_project` 做 bootstrap architecture、脚手架依据和首个可运行目标设计。产出能直接拆任务的 `design.md`。设计必须解释为什么这样改，以及如何验证它真的满足需求。

## 共享契约

执行前必须遵守 `../coding-feature-orchestrator/WORKFLOW_CONTRACT.md`。如果本文件与 contract 冲突，采用更严格、更不容易误触发或越界的规则。

## Activation policy

本 skill 只能在以下情况下使用：

1. 用户在当前请求中明确写出 `coding-technical-design`，或明确要求使用 Coding Feature Workflow 的技术设计阶段。
2. `coding-feature-orchestrator` 显式路由到本 skill，并提供完整 route payload（`activation_source`、`feature_dir`、`stage_evidence`）。

不满足时：

- 不得进入本 skill。
- 不得创建、猜测或切换 `.docs/feature-*` 目录。
- 不得把普通技术方案讨论自动升级成 Coding Feature Workflow。

## 启动模式与 route contract

- `direct_explicit`：用户在当前请求中明确写出 `coding-technical-design`。这种模式也必须提供已有 `feature_dir`；如果缺少，立即停止并提示用户改用 `coding-feature-orchestrator` 新建或选择 feature 目录。
- `routed_invocation`：不是用户直接点名本 skill，而是被 `coding-feature-orchestrator` 路由。此时必须同时收到：
  - `activation_source: coding-feature-orchestrator`
  - `feature_dir: <相对或绝对路径>`
  - `stage_evidence: <为什么进入技术设计阶段的证据>`
- 被动触发时缺少任一 route 字段，都必须拒绝启动；不得自行猜目录或补造上游文件。

## 前置检查

开始前必须确认：

- 已收到明确的 `feature_dir`。
- `feature_dir` 目录存在。
- `discovery.md` 和 `requirements.md` 已存在。
- `discovery.md stage_status: ready`。
- `requirements.md stage_status: ready`。
- `requirements.md evidence_complete: true`。
- `discovery.md evidence_complete: true`。
- `discovery.md project_context` 是 `existing_project` 或 `empty_project`，且 `project_context_evidence` 已写明。
- `discovery.md` 和 `requirements.md` 的 `updated_at` 均已写入 ISO 8601 + timezone。

如果缺少上述任一条件，立即停止并报告缺失项；不要临时补造上游阶段文档。

## Safety policy

- 禁止删除文件或目录，除非用户明确许可。
- 禁止 git commit / push / checkout / branch / reset / worktree 等仓库状态变更，除非用户明确许可。
- 禁止覆盖用户未提交改动；写入 `design.md` 前后都要检查工作区状态。
- 设计必须基于 `discovery.md`、`requirements.md` 和本阶段新完成的技术上下文证据，不得引入无关重构。
- 发现 scope 变化时按 contract 的 `Scope change protocol` 记录并停止，不得把未确认变更直接写进方案。
- 发现影响交付的新澄清问题时，先逐一询问用户；回答影响需求、链路或方案时回流更新上游文档后再继续。
- 本阶段完成后必须停下，输出下一阶段建议；除非用户明确要求连续推进，不得自行调用下一阶段。

## 输入检查

开始前确认：

- `requirements.md` 有可验证 acceptance criteria。
- `discovery.md` 有项目上下文调研、必要外部调研、方案方向和关键问题澄清记录。
- 阻塞问题不存在，或已被明确标为不会影响当前设计。

## 阶段 2：代码库探索

目标：从高层次和低层次理解当前项目上下文，并把证据直接写入 `design.md` 的“技术上下文与架构依据”章节，不再生成 `investigation.md`。

操作：

1. 读取 `discovery.md` 的项目上下文调研、外部调研、方案方向和已澄清问题，确认哪些证据可复用、哪些需要按 AC 精查。
2. `existing_project`：确认当前工作目录、项目结构、关键配置和技术栈；用 `rg` / `rg --files` 找入口、接口、store、DB、测试、相似实现；顺调用链读文件。
3. `empty_project`：确认官方脚手架命令、初始化目录结构、基础依赖、配置/env、测试框架、lint/format、启动命令和首个可运行目标。
4. 对涉及数据的需求，区分 raw source、aggregated source、cache、derived state；空项目则定义 planned source of truth、初始 schema/config 和未来迁移边界。
5. 对涉及协议/API 的需求，核对 request shape、response shape、stream 行为、错误处理、日志和持久化；空项目则定义首版接口/事件形态和兼容预期。
6. 对涉及 UI 的需求，核对用户入口、状态来源、刷新触发、loading/error/empty state；空项目则定义首屏/首路径和基础状态模型。
7. 复杂功能、大仓库或跨层改动时，条件性并行启动 2-3 个代码探索代理；小改动可本地完成。每个代理必须聚焦不同方面，例如类似功能、高层架构、数据/API 链路、UI/测试模式，并返回 5-10 个关键文件阅读列表。代理返回后，主 agent 必须亲自阅读代理识别的关键文件再下结论。

`design.md` 的技术上下文与架构依据部分必须记录：

- `existing_project` 已查文件：路径 + 关键行/函数 + 结论；`empty_project` 已查官方资料：来源 + 版本/命令 + 结论。
- 目标链路：已有项目按执行顺序列出真实链路；空项目列出 bootstrap 后的首个可运行链路。
- 数据来源：source of truth、派生数据、缓存、写入点、读取点；空项目列 planned source of truth。
- 接口与协议：request shape、response shape、stream/event、错误处理、logging/persistence。
- 相似实现：可复用模式和不能复用的原因。
- 风险与未知：区分已证实、推断、未验证。
- 对设计的约束：必须保留的兼容性、性能、权限、事务或运行时语义。

## 阶段 3：澄清性问题

目标：在架构设计前填补空白并解决所有模糊之处。这个阶段不能跳过。

操作：

1. 回顾代码库发现和 `requirements.md`。
2. 识别未明确方面：边界情况、错误处理、集成点、范围边界、设计偏好、向后兼容性、性能需求、数据/API/UI 行为、测试验收口径。
3. 以清晰列表向用户呈现所有影响设计或验收的问题，并附上已查证据。
4. 在进入架构设计前等待用户回答；如果用户表示“你认为最佳方案即可”，先给出推荐方案和理由，并获取明确确认。
5. 用户回答后按影响范围回流更新 `requirements.md` 或 `design.md`，再继续设计。

如果仍有 blocking 问题，在 `design.md` 顶部标记 `DESIGN_BLOCKED`，并将 frontmatter `stage_status: blocked`、`evidence_complete: false`、`approval_status: blocked`。

## 阶段 4：架构设计

目标：设计具有不同权衡的多种实现方案，并形成明确推荐。

操作：

1. 复杂功能、大仓库或高风险改动时，条件性并行启动 2-3 个架构代理，分别聚焦：
   - 最小变更：改动最小、复用最多。
   - 清晰架构：可维护性、边界和抽象更优。
   - 实用平衡：速度 + 质量。
2. 评估所有方案，并结合任务类型、紧急性、复杂性和团队背景形成主张。
3. 在 `design.md` 中呈现每个方案的简要总结、权衡比较、推荐理由和具体实现差异。
4. 用户未批准前只输出 `approval_status: pending`，不得进入任务拆解。

## 设计内容

`design.md` 至少包含：

- 方案摘要：一句话说明核心改动。
- 技术上下文与架构依据：已查文件或官方脚手架资料、目标链路、数据来源、相似实现或参考架构、风险未知、设计约束。
- 澄清问题：勘探后发现的问题、用户回答、更新位置；没有 blocking 问题时也要显式写明。
- 方案比较：基于 discovery / repo evidence 列出可行方案、不可行方案和推荐理由。
- 影响范围：模块、文件、接口、数据表、配置、权限、任务、UI。
- 目标链路：改动后的调用链或数据流。
- API 变更：endpoint、request、response、错误码、兼容性。
- 数据变更：DDL、DML、迁移、回滚、幂等性。
- 状态与并发：事务边界、缓存刷新、stream/event、异步任务。
- 错误处理与日志：异常传播、可观测字段、PII 处理。
- 风险和降级：已知风险、回滚策略、灰度或开关。
- 验证策略：单测、集成、手工验证、数据校验、UI 验证。
- 外部证据引用：如方案依赖第三方库、框架、OpenAI/API 或版本行为，引用 discovery 或本阶段技术上下文调研中的 Context7 / 官方文档结论。

## 决策原则

- 优先沿用仓库已有模式，不引入不必要的新抽象。
- 方案要服务当前 scope，不做无关重构。
- 涉及数据库时，需求目录 `sql/` 先放草案，最终脚本再按项目规范落正式目录。
- 涉及接口或协议时，显式写清兼容对象和 breaking change。

## 输出

更新 `design.md`。如果方案仍依赖未确认业务决策，在文档顶部标记 `DESIGN_BLOCKED`，并将 frontmatter `stage_status` 标记为 `blocked`、`evidence_complete: false`、`approval_status` 标记为 `blocked`；如果设计可直接拆任务，将 `stage_status` 标记为 `ready`、`evidence_complete: true`，但保持 `approval_status: pending`，等待用户明确批准后才能进入 `coding-task-planning`。每次写入 `design.md` 都必须同步更新 `updated_at`，并保持 `project_context` / `project_context_evidence` 与 discovery 一致。输出下一步建议后停止。

## Metrics 写入规则

本阶段在以下时机向 `metrics.json` 追加事件（参见 WORKFLOW_CONTRACT.md section 16）：

1. **进入阶段时**：追加 `stage_enter` 事件，`stage: "design"`，`trigger` 为 `direct_explicit` 或 `routed_invocation`。
2. **阶段完成时**（`stage_status` 标记为 `ready`）：追加 `stage_complete` 事件，计算 `duration_minutes` 和 `user_interactions`。
3. **阶段阻塞时**（`stage_status` 标记为 `blocked`）：追加 `stage_blocked` 事件，记录 `blocker` 描述。
4. **阻塞解除时**：追加 `blocker_resolved` 事件。
5. **组合调用时**（如咨询 `agent-solution-architect`）：追加 `composition_call` 事件。

写入失败不阻塞主流程；`metrics.json` 不存在时尝试从模板重建空结构。
