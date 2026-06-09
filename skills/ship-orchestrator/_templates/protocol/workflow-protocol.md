# Ship Solo Workflow Protocol

> `skills/` 的共享协议源。新版 ShipKit 面向个人开发者：默认轻量、证据驱动、一次只推进一个清晰 slice。旧版多重审批关与签字 preflight 不再是默认流程；review 类 skill 保留为可选检查工具。

## 1. 目标与非目标

目标：

- 用一套通用开发流程覆盖 feature、bugfix、refactor、UI、docs、release 小闭环。
- 降低个人开发者认知负担：默认只记一个入口 `ship-orchestrator`。
- 保持证据驱动：先读仓库事实，再计划和修改。
- 保持外科手术式实现：每次只做最小可验证 slice。
- 让产物足够轻：默认写入 `.docs/ship/<work-id>/`，不强迫企业级治理。

非目标：

- 不模拟多人团队审批流。
- 不要求每个阶段都有用户签字。
- 不要求前后端、契约、评审、计划全部独立成阻塞文档。
- 不把流程当作编码许可系统；最终仍由当前 agent 按用户授权和仓库规则执行。

## 2. Canonical Runtime Stages

默认运行时阶段只有 8 个：

| 顺序 | Stage ID | 主要产物 | 默认是否阻塞 |
|---|---|---|---|
| 01 | `ship-discover` | `intent.md` | 仅缺少真实目标时阻塞 |
| 02 | `ship-define` | `brief.md` | AC 或范围不清时阻塞 |
| 03 | `ship-tech-discovery` | `context-map.md` | 仓库事实不足时阻塞 |
| 04 | `ship-contract` | `contract.md` | 边界/数据形状不清时阻塞 |
| 05 | `ship-delivery-plan` | `plan.md` | 无可执行 slice 时阻塞 |
| 06 | `ship-build` | 代码改动 + `build-log.md` | 验证失败或越界时阻塞 |
| 07 | `ship-verify` | `verification.md` | AC 无证据时阻塞 |
| 08 | `ship-handoff` | `handoff.md` | 风险未说明时阻塞 |

支持类 skills 不写入 `meta.yml.current_stage`：

- `ship-shape`：UI/UX shaping，可在 UI 任务中由 orchestrator 插入。
- `ship-frontend-design` / `ship-backend-design`：复杂任务的深度设计辅助。
- `ship-define-review` / `ship-design-review` / `ship-plan-review`：可选 review checklist，不再是 hard gate。
- `ship-grill-me`：一次一个阻塞问题的质询 hook。
- `ship-spec`：workspace 规范管理 utility。

## 3. Macro Stage View

| Macro | Label | 包含阶段 |
|---|---|---|
| `discover` | `Discover` | `ship-discover` |
| `define` | `Define` | `ship-define` |
| `understand` | `Understand` | `ship-tech-discovery` |
| `design` | `Design` | `ship-contract` |
| `plan` | `Plan` | `ship-delivery-plan` |
| `build` | `Build` | `ship-build` |
| `verify` | `Verify` | `ship-verify` |
| `close` | `Close` | `ship-handoff` |

默认对用户展示 `macro_stage.label`、当前目标、下一步需要用户决定的内容；只有恢复、诊断或用户明确要求时才展开内部文件名。

## 4. Mode Selection

`ship-orchestrator` 先选择工作模式：

| Mode | 适用场景 | 起点 | 可跳过 |
|---|---|---|---|
| `feature` | 新功能、MVP、迭代增强 | `ship-discover` 或 `ship-define` | 目标清晰时可跳过 discover |
| `bugfix` | 复现、定位、修复缺陷 | `ship-tech-discovery` | define 可压缩成 3 行 bug brief |
| `refactor` | 不改变外部行为的内部改造 | `ship-tech-discovery` | contract 可写成 invariant contract |
| `ui` | 页面、组件、体验改造 | `ship-define` + 可选 `ship-shape` | backend 深度设计通常跳过 |
| `docs` | 文档、README、规范沉淀 | `ship-define` | build 是文档编辑 slice |
| `release` | 收尾、验证、发布说明 | `ship-verify` | 上游阶段按现有证据恢复 |

## 5. Artifact Contract

所有运行时产物使用轻量 frontmatter：

```yaml
---
stage: ship-define
stage_status: draft   # draft | ready | blocked | complete
updated_at: ""
blocking_gaps: []
evidence:
  - "path-or-command-output"
---
```

规则：

- `draft`：内容还不够可靠。
- `ready`：足够进入下一阶段。
- `blocked`：缺少用户决策、仓库事实、依赖或验证条件。
- `complete`：该阶段已消费完毕或关闭。
- `blocking_gaps` 非空时不得静默推进；必须询问、查证、缩 scope 或记录风险接受。

## 6. Lightweight Gates

默认门禁是检查清单，不是签字审批：

- **Scope Gate**：目标、非目标、AC、风险是否清楚。
- **Reality Gate**：是否读过相关代码、配置、测试和文档。
- **Slice Gate**：下一步是否足够小、文件范围是否合理、验证命令是否明确。
- **Evidence Gate**：改动是否有测试、构建、截图、手工步骤或代码引用证据。
- **Close Gate**：未完成项、残余风险和后续建议是否写清楚。

review skills 的输出字段建议：

```yaml
review_status: pass | needs_revision | blocked
findings:
  - severity: critical | major | minor
    evidence: "file/path or command"
    recommendation: "specific fix"
```

`pass` 表示 AI 检查通过，不代表用户签字，也不强制阻塞所有后续工作。Critical finding 必须修复、缩 scope 或经用户明确接受风险。

## 7. Source Discipline

修改业务源码前必须满足：

- 当前任务有明确 brief 或 plan。
- 已读取相关现有文件，不凭记忆修改。
- 本 slice 的目标、允许文件、验证命令已明确。
- 不顺手重构、不补未要求功能、不扩大范围。
- 若发现必须改额外文件，先停下说明原因并更新 plan。

`implementation_preflight.py` 在新版中是轻量检查器：它检查 `meta.yml.current_stage == ship-build`、当前 plan 是否存在一个 DOING slice、`allowed_files` 是否覆盖目标文件、验证命令是否存在。不再要求 `review-plan.md` 签字。

## 8. Delegation Contract

个人开发者默认主上下文收口；子代理只在降低成本时使用：

- 仓库探索、技术调研、代码审查、测试缺口分析适合委派。
- 正式状态推进、用户决策、风险接受由主上下文完成。
- 并行子代理不得各自修改同一事实源文件。
- 子代理输出必须合并为证据或建议，不直接替用户决定。

## 9. Directory Layout

默认工作目录：

```text
.docs/ship/<work-id>/
├── meta.yml
├── intent.md              # ship-discover
├── brief.md               # ship-define
├── context-map.md         # ship-tech-discovery
├── contract.md            # ship-contract
├── plan.md                # ship-delivery-plan
├── build-log.md           # ship-build
├── verification.md        # ship-verify
├── handoff.md             # ship-handoff
├── reviews/               # optional review skill outputs
└── resource/              # user materials, screenshots, notes
```

兼容读取旧 feature 目录时，orchestrator 可以把旧 `requirements.md`、`api-contract.md`、`frontend-plan.md`、`backend-plan.md` 映射为新版 brief / contract / plan 的证据来源，但新产物默认使用上方命名。

## 10. Acceptance Criteria for the Skill Suite

- 新用户只需要知道 `ship-orchestrator`。
- 默认流程可在 bugfix 和小 feature 中压缩到 3-4 个产物。
- 复杂项目仍可调用 shape、frontend/backend design、review、spec 等支持 skill。
- 所有阶段都能回答：输入是什么、输出是什么、何时停止、如何验证。
- 校验脚本能检查阶段映射、README、协议、meta 模板的一致性。
