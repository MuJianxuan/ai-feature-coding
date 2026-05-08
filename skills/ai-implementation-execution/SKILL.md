---
name: ai-implementation-execution
description: "AI 编码执行技能。Use when Codex should implement the next `tasks.md` item, modify code or configuration, keep task status current, preserve user changes, and record implementation evidence for a feature directory."
---

# AI Implementation Execution

## 目标

严格按 `tasks.md` 执行代码修改，不擅自扩大范围。每次执行都留下可复核证据。

## 开始前

1. 读取 `requirements.md`、`investigation.md`、`design.md`、`tasks.md`。
2. 选择第一个 `TODO` 任务，或用户明确指定的任务。
3. 将任务状态改为 `DOING`，记录开始时间和执行者为 AI。
4. 检查工作区状态。不要覆盖用户已有改动；遇到冲突先读懂再处理。

## 执行规则

- 只改当前任务需要的文件。
- 优先沿用现有架构、helper、类型和测试模式。
- 涉及接口时同步处理 request、response、stream/logging/persistence。
- 涉及数据时同步处理 schema、migration、读写路径、回滚草案。
- 涉及 UI 时同步处理 loading、empty、error、refresh、权限和响应式边界。
- 发现同类 bug 或相邻风险时，先记录在任务风险或新增任务中；只有与当前交付强相关才一并修。

## 完成规则

1. 执行任务的完成判定。
2. 通过则把状态改为 `DONE`，写交付记录：改动文件、验证命令、结果、残余风险。
3. 未通过但可继续排查时继续；确实缺少外部条件时改为 `BLOCKED` 并写明证据。
4. 更新 `verification.md` 中对应检查项。

## 禁止

- 禁止跳过 `tasks.md` 直接凭记忆改代码。
- 禁止删除文件、切换分支、提交或推送，除非用户明确许可。
- 禁止把未验证任务标成 `DONE`。
