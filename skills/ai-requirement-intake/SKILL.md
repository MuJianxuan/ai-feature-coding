---
name: ai-requirement-intake
description: "AI 需求澄清技能。Activation restricted: use only when the user explicitly names `ai-requirement-intake`, or a legally activated workflow/orchestrator explicitly routes here with `feature_dir`. Do not auto-trigger for ordinary requirement clarification or feature discussion."
---

# AI Requirement Intake

## 目标

把用户输入变成可执行、可验证、可追踪的 `requirements.md`。不要急着写方案或代码。

## Activation policy

本 skill 只能在以下情况下使用：

1. 用户在当前请求中明确写出 `ai-requirement-intake`，或明确要求使用这套 AI feature workflow 的需求澄清阶段。
2. `ai-feature-orchestrator` 或另一个已经合法触发的 skill 显式路由到本 skill，并传入 `feature_dir`。

不满足时：

- 不得进入本 skill。
- 不得创建、猜测或切换 `.docs/feature-*` 目录。
- 不得把普通需求讨论自动升级成这套工作流。

## 前置检查

开始前必须确认：

- 已收到明确的 `feature_dir`。
- `feature_dir` 目录存在。
- `requirements.md` 和 `resource/README.md` 已由 orchestrator/template 准备好。

如果缺少上述任一条件，立即停止并报告缺失项；不要临时补造上游准备文件。

## 工作流

1. 读取当前需求目录和 `resource/README.md`，找已有业务资料、会议纪要、原型或接口草案。
2. 从仓库中查可回答的问题，例如已有模块、相似功能、路由、数据表、枚举、权限模型。
3. 补齐 `requirements.md`：
   - 背景与业务目标
   - in-scope
   - out-of-scope
   - 用户路径或业务流程
   - acceptance criteria
   - 非功能要求
   - 约束与假设
   - 待确认问题
4. 只询问仓库无法回答的问题。每次提问必须附带已查证据。
5. 不进入技术设计，直到 acceptance criteria 可验证且范围边界稳定。

## 质量标准

- 每条验收标准都能被测试、日志、接口响应、UI 行为或数据状态验证。
- out-of-scope 要明确，避免 AI 在实现阶段擅自扩大范围。
- 待确认问题要区分 `BLOCKING` 和 `NON_BLOCKING`。
- 需求资料必须在 `resource/README.md` 建索引，写清文件名、来源、更新时间和用途。

## 输出

更新 `requirements.md` 和 `resource/README.md`。如果仍有阻塞问题，在 `requirements.md` 的“待确认问题”中标记。
