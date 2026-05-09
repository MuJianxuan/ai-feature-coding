---
name: ai-repo-investigation
description: "AI 仓库证据勘察技能。Activation restricted: use only when the user explicitly names `ai-repo-investigation`, or a legally activated workflow/orchestrator explicitly routes here with `feature_dir`. Do not auto-trigger for ordinary debugging, repo investigation, root-cause analysis, or design prep."
---

# AI Repo Investigation

## 目标

在写方案或改代码前，先找出真实链路。输出应能支撑后续 `design.md` 和 `tasks.md`，而不是停留在猜测。

## Activation policy

本 skill 只能在以下情况下使用：

1. 用户在当前请求中明确写出 `ai-repo-investigation`，或明确要求使用这套 AI feature workflow 的仓库勘察阶段。
2. `ai-feature-orchestrator` 或另一个已经合法触发的 skill 显式路由到本 skill，并传入 `feature_dir`。

不满足时：

- 不得进入本 skill。
- 不得创建、猜测或切换 `.docs/feature-*` 目录。
- 不得把普通 debugging / code tracing 自动升级成这套工作流。

## 前置检查

开始前必须确认：

- 已收到明确的 `feature_dir`。
- `feature_dir` 目录存在。
- `requirements.md` 已存在，并包含当前阶段要服务的 scope / acceptance criteria。

如果缺少上述任一条件，立即停止并报告缺失项；不要临时补造上游阶段文档。

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
