---
name: ai-repo-investigation
description: "AI 仓库证据勘察技能。Use when Codex must trace real code paths, data sources, API contracts, persistence, frontend state, tests, logs, or similar implementations before proposing a fix or design. Produces `investigation.md` evidence for AI feature work."
---

# AI Repo Investigation

## 目标

在写方案或改代码前，先找出真实链路。输出应能支撑后续 `design.md` 和 `tasks.md`，而不是停留在猜测。

## 搜索顺序

1. 先确认当前工作目录、项目结构、关键配置和技术栈。
2. 用 `rg` / `rg --files` 找入口、接口、store、DB、测试、相似实现。
3. 顺调用链读文件：入口 -> service/use case -> persistence/API -> event/state -> UI/consumer。
4. 对涉及数据的需求，区分 raw source、aggregated source、cache、derived state。
5. 对涉及协议/API 的需求，核对 request shape、response shape、stream 行为、错误处理、日志和持久化。
6. 对涉及 UI 的需求，核对用户入口、状态来源、刷新触发、loading/error/empty state。

## 记录格式

在 `investigation.md` 中记录：

- 已查文件：路径 + 关键行/函数 + 结论。
- 真实链路：按执行顺序列出。
- 数据来源：source of truth、派生数据、缓存、写入点、读取点。
- 相似实现：可复用模式和不能复用的原因。
- 风险与未知：区分已证实、推断、未验证。
- 对设计的约束：必须保留的兼容性、性能、权限、事务或运行时语义。

## 禁止

- 禁止用“可能”“应该”替代证据。
- 禁止只看前端或只看后端就下结论。
- 禁止发现一个症状后停止排查同类路径。
