---
name: ai-technical-design
description: "AI 技术设计技能。Use when requirements and repository evidence need to be turned into `design.md`, including architecture impact, module boundaries, API/database changes, compatibility, migration, error handling, rollback, and verification strategy."
---

# AI Technical Design

## 目标

基于 `requirements.md` 和 `investigation.md` 产出能直接拆任务的技术方案。设计必须解释为什么这样改，以及如何验证它真的满足需求。

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
