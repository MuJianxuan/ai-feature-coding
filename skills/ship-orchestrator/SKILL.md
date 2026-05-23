---
name: ship-orchestrator
description: "ShipKit orchestrator. Routes development workflow stages. Use when user wants to start a new feature, continue an existing feature, or check feature status."
---

# Workflow Orchestrator

## Overview

Workflow Orchestrator 是开发工作流 skills 套件的总调度器，负责入口判断、阶段推断和路由分发。它不执行具体阶段工作，而是识别用户意图后将控制权交给对应的阶段 skill。

本 skill 支持三种入口模式：NEW_FEATURE（启动新功能开发）、CONTINUE_FEATURE（恢复中断的功能开发）、INSPECT_FEATURES（查看功能状态总览）。调度器通过读取 `meta.yml.current_stage`、`meta.yml.macro_stage`、各产物 frontmatter 和 `meta.yml` 摘要状态来判断当前位置，并根据门禁规则决定是否允许推进到下一阶段。

设计原则是"放宽触发、严格推进"——用户无需记住 14 个内部阶段名，只要表达出开发意图，调度器就能识别并给出 4 个大阶段视图下的执行摘要。内部仍然按细阶段和门禁推进，但默认对外只展示：当前大阶段、当前目标、下一次需要用户确认的动作。

协议约束：
- Canonical stage id、门禁字段、`verification.md` ownership 统一以 [`workflow-protocol.md`](./_templates/protocol/workflow-protocol.md) 为准
- 阶段文档 frontmatter 是事实源；`meta.yml` 仅是 orchestrator 索引层
- 默认对外展示 `macro_stage`，只在高级模式和诊断模式下展开 `current_stage`

## When to Use

- 用户表达"做一个功能""开发一个 feature""启动项目""新需求来了"等开发意图
- 用户说"继续上次的""接着做""回到 XX 功能"等恢复意图
- 用户问"现在到哪一步了""功能进度怎样""还有哪些没做完"等查询意图
- 任何阶段 skill 完成后需要判断下一步去向时

## When NOT to Use

- 用户在做与 feature 开发无关的事（修 bug、写文档、配置环境）
- 用户已明确指定要执行某个具体阶段 skill 且上下文无歧义
- 纯代码问答、技术咨询、不涉及工作流推进的对话

## Trigger Recognition

意图识别采用宽松匹配策略，以下模式均应触发：

| 意图类别 | 触发词/模式示例 |
|---------|---------------|
| 新功能启动 | "做一个…""开发…功能""新需求""启动…项目""我想加一个…""帮我实现…""搞一个…" |
| 恢复开发 | "继续""接着做""上次到哪了""回到…功能""还没做完的""刚才那个" |
| 状态查询 | "进度""到哪一步""状态""还剩什么""看看功能列表""哪些在做" |
| 阶段跳转 | "开始设计""进入实现""做技术选型"（需验证门禁后路由） |

意图歧义处理规则：
- 若用户输入同时匹配多个类别，优先级为 CONTINUE > NEW > INSPECT
- 若存在进行中的 feature 且用户说"做一个功能"但未明确是新功能，先询问是继续还是新建
- 若用户直接说阶段名（如"做技术选型"），先检查是否有活跃 feature，有则路由，无则启动 NEW 流程

识别到意图后的标准响应流程：
1. 判断入口模式（NEW / CONTINUE / INSPECT）
2. 若 NEW：生成执行计划摘要（一段话描述即将启动的 4 阶段流程），请用户确认
3. 若 CONTINUE：读取 meta.yml，定位 current_stage，并优先用 macro stage 报告当前状态后路由
4. 若 INSPECT：扫描 .docs/ 下所有 feature 目录，汇总状态表格

NEW_FEATURE 启动确认模板：
- 简述功能名称和目标
- 列出将要经历的大阶段序列（standard 或 fast-track）
- 预估涉及的技术领域
- 标明下一次需要用户确认的门禁时点
- 等待用户一句话确认（"好的""开始""go"等均视为确认）

## Process

```
用户输入
    │
    ▼
┌─────────────────────┐
│  意图识别 & 分类     │
│  NEW / CONTINUE /   │
│  INSPECT            │
└─────────┬───────────┘
          │
    ┌─────┼─────────────────┐
    │     │                 │
    ▼     ▼                 ▼
  NEW   CONTINUE         INSPECT
    │     │                 │
    ▼     ▼                 ▼
┌──────┐ ┌──────────┐  ┌──────────┐
│创建   │ │读取      │  │扫描所有   │
│feature│ │meta.yml  │  │feature   │
│目录   │ │定位阶段   │  │目录      │
└──┬───┘ └────┬─────┘  └────┬─────┘
   │          │              │
   ▼          ▼              ▼
┌──────┐ ┌──────────┐  ┌──────────┐
│初始化 │ │检查门禁   │  │输出状态   │
│meta  │ │条件      │  │汇总表    │
│.yml  │ │          │  │          │
└──┬───┘ └────┬─────┘  └──────────┘
   │          │
   ▼          ▼
┌─────────────────────┐
│  路由到目标阶段 skill │
│  传递 feature_dir    │
│  + context          │
└─────────────────────┘
```

## Stage Routing Rules

默认对外阶段视图（4 个大阶段）：

```
Define → Design → Build → Close
```

内部阶段序列（14 个执行阶段）：

```
ship-intake → ship-intake-review [硬门禁]
→ ship-research → ship-stack
→ ship-contract → ship-frontend-design → ship-backend-design
→ ship-design-review [硬门禁]
→ ship-frontend-plan → ship-backend-plan
→ ship-plan-review [硬门禁]
→ ship-build → ship-verify → ship-handoff
```

各阶段入口/出口条件：

| 阶段 | 入口条件 | 出口产物 | 出口条件 |
|------|---------|---------|---------|
| ship-intake | NEW_FEATURE 确认启动 | requirements.md | frontmatter stage_status: ready |
| ship-intake-review | requirements.md 存在且 stage_status: ready | review-requirement.md | review_status: approved + user_sign_off/signed_at |
| ship-research | review-requirement.md review_status: approved | tech-research.md | stage_status: ready |
| ship-stack | tech-research.md ready | tech-selection.md | stage_status: ready |
| ship-contract | tech-selection.md ready | api-contract.md | stage_status: ready |
| ship-frontend-design | api-contract.md ready | frontend-design.md | stage_status: ready |
| ship-backend-design | api-contract.md ready | backend-design.md | stage_status: ready |
| ship-design-review | frontend-design + backend-design ready | review-design.md | review_status: approved + user_sign_off/signed_at |
| ship-frontend-plan | review-design.md review_status: approved | frontend-plan.md | stage_status: ready |
| ship-backend-plan | review-design.md review_status: approved | backend-plan.md | stage_status: ready |
| ship-plan-review | frontend-plan + backend-plan ready | review-plan.md | review_status: approved + user_sign_off/signed_at |
| ship-build | review-plan.md review_status: approved | 代码产物 | 所有 task 完成 |
| ship-verify | ship-build 完成 | verification.md | `stage_status: ready` |
| ship-handoff | verification.md stage_status: ready | handoff.md + verification.md | `handoff.md` 完成且 `verification.md stage_status: complete` |

并行规则：
- ship-frontend-design 和 ship-backend-design 可并行执行（共同依赖 05 的产出）
- ship-frontend-plan 和 ship-backend-plan 可并行执行（共同依赖 08 的产出）

Macro stage 映射：
- `Define`：`ship-intake`, `ship-intake-review`
- `Design`：`ship-research`, `ship-stack`, `ship-contract`, `ship-frontend-design`, `ship-backend-design`, `ship-design-review`
- `Build`：`ship-frontend-plan`, `ship-backend-plan`, `ship-plan-review`, `ship-build`, `ship-verify`
- `Close`：`ship-handoff`

### Pipeline Modes

standard 模式（默认）：
- 对外显示 `Define → Design → Build → Close`
- 内部完整执行 14 个阶段，适用于中大型功能
- 所有硬门禁必须通过
- 所有文档产物必须完整

fast-track 模式：
- 适用于小型功能或紧急修复
- 最小路径：01→02→12→13→14（`ship-intake → ship-intake-review → ship-build → ship-verify → ship-handoff`）
- 可选扩展：在最小路径基础上按需插入 03-04（技术调研选型）或 05-07（设计）
- 切换条件：用户在 NEW_FEATURE 确认时明确要求，或 02 评审时 reviewer 判定功能复杂度为 low
- 硬门禁 02 仍然必须执行；fast-track 允许不生成设计/计划产物，但不允许绕过需求录入、需求评审、测试和验收

模式切换规则：
- standard → fast-track：仅在 02 评审通过后、03 开始前允许降级
- fast-track → standard：任何阶段均可升级，已完成的阶段产物保留

### 路由分发机制

调度器路由到阶段 skill 时传递的上下文包：
- feature_dir：feature 目录绝对路径
- current_stage：当前阶段标识
- macro_stage：当前大阶段标识与摘要
- pipeline_mode：standard / fast-track
- project_context：unknown / existing_project / new_project
- tech_stack：已确定的技术栈信息（可能为空）
- upstream_docs：上游阶段产出文档路径列表

阶段 skill 完成后必须回调调度器：
- 先读取对应产物 frontmatter，确认事实状态
- 将 `meta.yml` 中对应阶段状态回写为摘要状态（如 `ready` / `approved` / `completed`）
- 更新 `current_stage` 为下一阶段 canonical stage id
- 同步刷新 `macro_stage.current`、`macro_stage.label`、`macro_stage.summary`、`macro_stage.next_user_decision`
- 若发现 `meta.yml` 与产物 frontmatter 不一致，优先修正 `meta.yml`

## Gate Protocol

### 硬门禁（Hard Gate）

适用阶段：ship-intake-review、ship-design-review、ship-plan-review

执行规则：
1. 生成 review-<stage>.md 文档，包含以下必填字段：
   - reviewer：执行评审的角色（AI / 用户 / 两者）
   - checklist：评审检查项列表，每项标注 pass/fail/na
   - issues：发现的问题列表，含严重级别和处理建议
   - review_status：pending / approved / rejected / revision_needed
   - user_sign_off：用户确认文本
   - signed_at：用户确认时间戳
   - conditions：必须解决的条件列表（如有）
2. 只有 `review_status=approved` 且 `user_sign_off`、`signed_at` 非空时，才允许推进
3. 若 `rejected`：回退到对应的产出阶段重新执行
4. 若 `revision_needed`：列出必须解决的问题，解决后重新提交评审

### 软门禁（Soft Gate）

适用阶段：所有非硬门禁的阶段间过渡

执行规则：
1. 检查上游文档 frontmatter 中 stage_status 字段
2. stage_status: ready → 允许推进
3. stage_status: draft / in_progress → 提示用户当前阶段未完成，询问是否强制推进
4. 上游文档不存在 → 阻断，路由回上游阶段

### 门禁失败处理

- 硬门禁失败：必须回退，不可跳过，不可强制通过
- 软门禁失败：警告用户风险后，用户可选择强制推进（记录到 meta.yml 的 skip_log）
- 连续两次门禁失败：建议用户重新审视需求或方案
- 评审产物缺失：阻断推进，路由回评审阶段重新生成

### 门禁文档 frontmatter 规范

每个评审产物必须包含 frontmatter，字段约定：
- stage：所属阶段标识
- gate_type：固定为 `hard`
- review_status：`pending / approved / rejected / revision_needed`
- reviewer：评审者标识
- reviewed_at：评审时间
- reviewed_documents：本轮评审涉及文档
- revision_count：重审次数
- user_sign_off：用户签字文本
- signed_at：签字时间戳（ISO 8601）
- conditions：若 `revision_needed`，列出待解决条件

调度器读取 frontmatter 后才判定门禁结果，正文内容仅作参考不影响判定。

## Feature Directory Initialization

NEW_FEATURE 模式下的目录创建流程：

1. 根据用户输入提取功能短名（short-name），转换为 kebab-case
2. 生成日期前缀 YYYYMMDD（基于当前日期）
3. 创建目录 .docs/feature-YYYYMMDD-<short-name>/
4. 创建 resource/ 子目录用于存放 PRD、原型、截图等参考资料
5. 复制 `./_templates/meta/meta.yml.template` 到 feature 目录，重命名为 `meta.yml`
6. 填充 meta.yml 初始字段：feature_name、feature_id、created_at、current_stage: ship-intake
7. 初始化 `macro_stage.current: define`、`macro_stage.label: Define`
8. 初始化 `macro_stage.summary` 与 `macro_stage.next_user_decision`
9. 将所有阶段的 status 初始化为 pending
10. 将控制权交给 ship-intake skill

短名生成规则：
- 优先使用用户输入中的功能名词
- 若用户未提供，从需求描述中提取核心动词+名词组合
- 长度控制在 2-5 个英文单词或拼音
- 避免特殊字符，仅保留字母数字和连字符

目录命名冲突处理：
- 同日同短名：追加 -v2、-v3 后缀
- 短名为空：使用 feature-YYYYMMDD-<timestamp> 兜底

## Resume Protocol

中断恢复流程（CONTINUE_FEATURE 模式）：

1. 扫描 .docs/ 目录，列出所有 feature-YYYYMMDD-* 目录
2. 读取每个 feature 的 meta.yml，过滤出 `ship-handoff` 尚未 `completed` 的活跃 feature
3. 若只有一个进行中的 feature：自动选中并报告
4. 若有多个：列表展示（功能名 / 当前大阶段 / 最后更新时间），让用户选择
5. 若无活跃 feature：提示用户是否启动新功能或查看历史 feature
6. 读取选中 feature 的 meta.yml
7. 根据 current_stage 和该阶段 status 判断恢复点：
   - status: completed → 检查门禁后推进到下一阶段
   - status: in_progress → 恢复当前阶段（传递已有产物作为上下文）
   - status: approved / ready → 检查门禁后推进到下一阶段
   - status: blocked → 报告阻塞原因，询问用户决策（解除阻塞 / 切换 feature / 终止）
   - status: pending → 路由到该阶段重新启动
8. 检查门禁条件后路由到目标阶段 skill

恢复时的默认输出：
- 优先报告 `macro_stage.label`
- 说明当前阶段目标与下一次用户确认点
- 仅在用户要求详情或遇到阻塞时展开 `current_stage`

恢复时的上下文传递：
- 将 feature 目录绝对路径作为 feature_dir 传递
- 将 meta.yml 中的 tech_stack 和 project_context 作为环境信息传递
- 将当前阶段已有的文档内容作为续写上下文传递
- 将 pipeline_mode 字段透传给目标阶段 skill

恢复时的状态校验：
- 若 meta.yml 中 current_stage 与实际文档产出不一致（如 current_stage 为 04 但 tech-research.md 不存在），优先信任文件系统状态，回退 current_stage
- 若发现孤立产物（如存在 frontend-plan.md 但无 review-design.md），警告用户并询问处理方式
- 若 `meta.yml` 摘要状态与产物 frontmatter 冲突，优先信任产物 frontmatter 并回写 `meta.yml`

## Inspect Protocol

INSPECT_FEATURES 模式输出规范：

汇总表格列：
- 功能名（feature_name）
- 创建时间（created_at）
- 当前大阶段（macro_stage.label）
- 当前内部阶段（current_stage，仅高级视图显示）
- 整体进度（已完成阶段数 / 总阶段数）
- 流水线模式（standard / fast-track）
- 状态标识（in_progress / blocked / completed / abandoned）

排序规则：进行中 > 阻塞 > 待评审 > 已完成 > 已废弃，同状态内按 updated_at 倒序。

输出后追加可选行动建议：
- 进行中 feature：提示可输入"继续 <name>"恢复
- 阻塞 feature：提示阻塞原因摘要
- 已完成 feature：提示可查看 handoff.md 总结

## Anti-Rationalizations

| 编号 | 禁止行为 | 正确做法 |
|------|---------|---------|
| AR-1 | "用户说快点做，所以跳过评审" | 硬门禁不可跳过。可建议切换 fast-track 模式（合并部分阶段），但评审仍必须执行 |
| AR-2 | "需求很简单，不需要走完整流程" | 即使简单需求，也至少执行 01→02→12→13→14 最小路径，评审可简化但不可省略 |
| AR-3 | "上一阶段的文档差不多了，先往下走" | 软门禁要求 stage_status: ready。"差不多"不等于 ready，必须明确标记 |
| AR-4 | "用户没说要恢复哪个 feature，我猜一个" | 多个 feature 时必须列表让用户选择，不可自行假设 |
| AR-5 | "这个阶段 skill 不存在，跳过" | 阶段 skill 缺失时报告错误，不可静默跳过。建议用户手动完成该阶段产物 |

## Verification

退出 checklist（调度器每次路由前自检）：

- [ ] 已正确识别用户意图并分类为 NEW / CONTINUE / INSPECT
- [ ] NEW 模式：feature 目录已创建，meta.yml 已初始化，用户已确认执行计划
- [ ] CONTINUE 模式：已读取 meta.yml，已定位 current_stage / macro_stage，已验证门禁条件
- [ ] INSPECT 模式：已扫描所有 feature 目录，已输出状态汇总
- [ ] 路由目标阶段 skill 存在且可调用
- [ ] 已将 feature_dir 和必要上下文传递给目标阶段 skill
- [ ] meta.yml 的 current_stage 与 macro_stage 已同步更新为即将执行的阶段
- [ ] 未跳过任何硬门禁
- [ ] 软门禁跳过已记录到 meta.yml 的 skip_log（如有）
