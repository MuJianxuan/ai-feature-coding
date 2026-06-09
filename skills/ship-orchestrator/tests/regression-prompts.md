# Ship Solo Workflow Regression Prompts

这些 prompts 用于验证新版个人开发者流程是否保持轻量、证据驱动、可执行。

## 1. Small Bugfix Starts From Understand

```text
使用 ship-orchestrator 修复登录页空邮箱时报 500 的问题。
```

期望：

- `work_mode = bugfix`
- 可压缩 `ship-discover` / `ship-define`
- 先进入或快速到达 `ship-tech-discovery`
- 不要求 `review-define.md` 签字
- 输出复现思路、相关文件读取计划、最小验证命令

## 2. Feature Creates Brief And Plan

```text
使用 ship-orchestrator，给任务列表加一个按状态筛选的功能。
```

期望：

- 默认进入 `Discover → Define`
- 产出 in scope / out of scope / AC
- 进入实现前有 `plan.md` slices
- 每个 slice 包含 allowed_files 和 verification_command

## 3. No Direct Coding Without Context

```text
直接帮我改用户权限逻辑，应该在 auth 相关文件里。
```

期望：

- 不凭猜测改代码
- 先执行 repository reality check
- 要求或生成最小 brief：目标、期望行为、风险

## 4. Review Skills Are Optional

```text
这个任务很小，不用正式评审，直接按轻量流程走。
```

期望：

- 不强制生成 `review-define.md` / `review-design.md` / `review-plan.md`
- 仍保留 Scope / Reality / Slice / Evidence checks

## 5. Complex UI Can Insert Shape

```text
我要重做设置页，没设计稿，你先给我几个方向。
```

期望：

- `work_mode = ui`
- 可调用 `ship-shape`
- 产出设计方向、页面状态、HTML 原型或 wireframe 说明
- 回到 `ship-define` / `ship-contract` 时把 UI 决策作为证据

## 6. Refactor Uses Invariant Contract

```text
重构订单金额计算模块，但不要改变外部行为。
```

期望：

- `work_mode = refactor`
- `contract.md` 记录行为不变量、现有测试、风险
- plan slices 不扩大功能范围

## 7. Build Preflight Is Lightweight

```text
当前 plan.md 有一个 DOING slice，allowed_files 覆盖 src/a.ts，verification_command 已写，准备修改 src/a.ts。
```

期望：

- `implementation_preflight.py --files src/a.ts` 可通过
- 不要求 `review-plan.md`、`user_sign_off`、`signed_at`

## 8. Evidence Required To Close

```text
功能写完了，直接 close。
```

期望：

- 若缺少 verification evidence，进入 `ship-verify`
- `handoff.md` 必须列出验证命令、结果、风险和 follow-up

## 9. Docs Task Skips Heavy Design

```text
更新 README，补充本地启动和测试说明。
```

期望：

- `work_mode = docs`
- 可跳过 `ship-contract` 或写 `contract_forms: [none]`
- plan 是文档编辑 slice

## 10. Support Skill Not Runtime Stage

```text
使用 ship-plan-review 检查这个计划有没有漏任务。
```

期望：

- `ship-plan-review` 输出 checklist review
- 不写入 `meta.yml.current_stage`
- 不要求用户签字才能继续
