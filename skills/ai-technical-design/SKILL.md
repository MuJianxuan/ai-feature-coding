---
name: ai-technical-design
description: "AI 技术设计技能。Activation restricted: use only when the user explicitly names `ai-technical-design`, or a legally activated workflow/orchestrator explicitly routes here with `feature_dir`. Do not auto-trigger for ordinary architecture, design, planning, or proposal work."
---

# AI Technical Design

## 目标

基于 `requirements.md` 和 `investigation.md` 产出能直接拆任务的技术方案。设计必须解释为什么这样改，以及如何验证它真的满足需求。

## Activation policy

本 skill 只能在以下情况下使用：

1. 用户在当前请求中明确写出 `ai-technical-design`，或明确要求使用这套 AI feature workflow 的技术设计阶段。
2. `ai-feature-orchestrator` 或另一个已经合法触发的 skill 显式路由到本 skill，并传入 `feature_dir`。

不满足时：

- 不得进入本 skill。
- 不得创建、猜测或切换 `.docs/feature-*` 目录。
- 不得把普通技术方案讨论自动升级成这套工作流。

## 前置检查

开始前必须确认：

- 已收到明确的 `feature_dir`。
- `feature_dir` 目录存在。
- `requirements.md` 和 `investigation.md` 已存在。

如果缺少上述任一条件，立即停止并报告缺失项；不要临时补造上游阶段文档。

## 输入检查

开始前确认：

- `requirements.md` 有可验证 acceptance criteria。
- `investigation.md` 有真实代码链路和数据来源。
- 阻塞问题不存在，或已被明确标为不会影响当前设计。

## 设计内容

`design.md` 至少包含：

- 方案摘要：一句话说明核心改动。
- 影响范围：模块、文件、接口、数据表、配置、权限、任务、UI。
- 目标链路：改动后的调用链或数据流。
- API 变更：endpoint、request、response、错误码、兼容性。
- 数据变更：DDL、DML、迁移、回滚、幂等性。
- 状态与并发：事务边界、缓存刷新、stream/event、异步任务。
- 错误处理与日志：异常传播、可观测字段、PII 处理。
- 风险和降级：已知风险、回滚策略、灰度或开关。
- 验证策略：单测、集成、手工验证、数据校验、UI 验证。

## 决策原则

- 优先沿用仓库已有模式，不引入不必要的新抽象。
- 方案要服务当前 scope，不做无关重构。
- 涉及数据库时，需求目录 `sql/` 先放草案，最终脚本再按项目规范落正式目录。
- 涉及接口或协议时，显式写清兼容对象和 breaking change。

## 输出

更新 `design.md`。如果方案仍依赖未确认业务决策，在文档顶部标记 `DESIGN_BLOCKED`。
