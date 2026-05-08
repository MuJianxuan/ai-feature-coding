---
name: ai-verification-closeout
description: "AI 验证收口技能。Use when a feature needs final verification, acceptance mapping, regression checks, unresolved risk documentation, delivery summary, or handoff updates in `verification.md` and `handoff.md`."
---

# AI Verification Closeout

## 目标

证明需求已经按 scope 交付，或清楚说明还剩什么风险和阻塞。验证不是跑一个命令，而是把 acceptance criteria 和实际证据对齐。

## 验证顺序

1. 读取 `requirements.md` 的 acceptance criteria。
2. 读取 `tasks.md`，确认所有 in-scope 任务为 `DONE` 或有明确 `BLOCKED` 说明。
3. 按 `design.md` 的验证策略执行 targeted checks。
4. 对每条验收标准记录证据：命令、日志、截图路径、接口响应摘要、数据查询或手工步骤。
5. 检查相关同类路径是否需要回归。
6. 汇总无法验证的项目和原因。

## 文档更新

`verification.md` 记录：

- 验收标准映射表
- 执行过的命令和结果
- 手工验证步骤
- 未覆盖场景
- 回归风险

`handoff.md` 记录：

- 交付摘要
- 变更文件和影响范围
- 配置、SQL、部署或数据操作
- 用户复核入口
- 后续建议

## 完成定义

- in-scope acceptance criteria 都有验证结论。
- 失败或未覆盖项不能被隐藏，必须写入残余风险。
- 如果需要用户验收，给出最短复核路径，不要求用户自行翻找。
