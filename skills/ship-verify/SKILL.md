---
name: ship-verify
description: "ShipKit stage. Runs frontend and backend tests to verify implementation correctness. Use after ship-build completes or during ship-build for TDD."
---

# 测试 (Testing)

## Overview

测试阶段负责对实现产物进行系统性验证，覆盖前端、后端及前后端契约一致性。核心原则：**前后端分轨执行 + 契约层统一校验**。

核心目标：
- 后端测试在 `ship-build` 阶段随任务同步完成（TDD 风格）
- 前端 E2E 测试在所有前端任务完成后统一执行
- 契约测试验证前后端对 api-contract.md 的实现一致性
- 输出可审计的测试结果，创建或更新 `verification.md` 的测试章节
- 自动化验证通过后，将 `verification.md.stage_status` 置为 `ready`，交由 `ship-handoff` 完成最终验收
- `verification.md` 的测试章节是本阶段事实源，不把 `plan.md` 当作唯一输入

产物：测试代码 + 测试报告 + `verification.md`（测试章节）

## When to Use

- `ship-build` 阶段的任务正在/已完成，需要验证
- TDD 模式下：每个后端任务实现前先写测试
- 前端任务全部完成后，准备跑 E2E
- 需要验证前后端集成一致性时

## When NOT to Use

- `ship-build` 尚未启动 —— 没有可测对象
- 需求/契约未稳定 —— 测试会大量返工，先稳定上游产物
- 纯文档/配置类改动 —— 不需要传统测试，使用 `ship-handoff` 阶段的手工验证

## Testing Strategy (前后端分轨)

```
┌────────────────────────────────────────────────────────┐
│              测试策略矩阵                                │
├──────────────┬──────────────┬──────────────────────────┤
│   类型       │   范围       │   执行时机                │
├──────────────┼──────────────┼──────────────────────────┤
│ 后端单元测试  │ 单个函数/类   │ ship-build 同步           │
│ 后端集成测试  │ 多模块协作   │ ship-build 任务结束       │
│ 后端契约测试  │ API endpoint │ 契约层任务完成后          │
│ 前端组件测试  │ 单个组件     │ ship-build 同步           │
│ 前端 E2E     │ 关键用户路径 │ 所有前端任务完成后        │
│ 视觉回归     │ 关键页面     │ 可选，UI 重构时           │
│ 契约一致性   │ 前后端对齐   │ 集成联调时                │
└──────────────┴──────────────┴──────────────────────────┘
```

### 分轨原则

1. **后端先行**：后端测试与代码同步，TDD 优先
2. **前端聚合**：前端 E2E 集中跑，避免每改一处就跑全套
3. **契约统一**：前后端对契约的理解必须由独立的契约测试验证

若存在 `blocking_gaps`，必须保持 `stage_status: draft` 或 meta blocked，不得进入下游。

## Delegation Boundary

本阶段适合按测试轨道做**辅助并行委派**。

可并行的测试轨道：
- backend unit
- backend integration
- backend contract
- frontend component
- frontend E2E

对应的 canonical `node_id`：
- `ship-verify.backend-unit`
- `ship-verify.backend-integration`
- `ship-verify.backend-contract`
- `ship-verify.frontend-component`
- `ship-verify.frontend-e2e`

约束：
- 子代理可以各自运行测试、整理失败分类和覆盖率结果
- `verification.md` 仍由主上下文统一更新
- 只有主上下文可以决定 `verification.md.stage_status = ready | draft`
- 子代理只返回测试结果与失败归类，不直接编辑 `verification.md` 正文或 frontmatter

## Scope Adaptation

本阶段根据 `project_scope` 裁剪测试轨道：

| project_scope | 需要执行的轨道 | 说明 |
|---------------|---------------|------|
| `fullstack` | backend unit / backend integration / backend contract / frontend component / frontend E2E | 完整执行所有轨道 |
| `backend_only` | backend unit / backend integration / backend contract | 跳过前端轨道 |
| `frontend_only` | frontend component / frontend E2E | 跳过后端轨道 |

适配规则：

- `backend_only`：`verification.md` 只记录后端轨道结果，`frontend-*` 轨道标记为 `na`
- `frontend_only`：`verification.md` 只记录前端轨道结果，`backend-*` 轨道标记为 `na`
- `fullstack`：所有轨道都必须在 `verification.md` 中有对应结果
- 无论哪种 scope，`verification.md` 的测试章节都必须保留完整的命令、结果和失败分类
- 文档/配置类变更仍必须写入测试命令和人工验证记录，不因为 scope 缩小而省略证据

## Backend Testing (单元/集成/契约)

### 单元测试 (Unit Tests)

测试目标：单个函数、类、模块的纯逻辑

要求：
- 每个 Service 方法至少 1 个正常路径 + 1 个异常路径测试
- 边界条件必测（空值、极值、非法输入）
- 不依赖外部资源（DB、网络），需要时使用 mock/fake
- 执行速度快（单测套件 < 30s）

示例覆盖维度：
```
- 正常输入 → 期望输出
- 空输入 / null / 空字符串
- 边界值（0、负数、最大长度）
- 非法类型 / 非法格式
- 业务规则违反
- 并发/状态相关（如适用）
```

### 集成测试 (Integration Tests)

测试目标：多模块协作 + 真实外部依赖（DB、缓存、消息队列）

要求：
- 使用真实的依赖（测试数据库、内存版 Redis 等）
- 每个测试自带 setup/teardown，保证隔离
- 覆盖跨模块的数据流转
- 执行速度可接受（集成套件 < 5min）

### 契约测试 (Contract Tests)

测试目标：API endpoint 的请求/响应格式与 api-contract.md 完全一致

要求：
- 对每个 endpoint 至少覆盖：成功响应、各类错误响应（400/401/403/404/500）
- 校验 response schema 与契约文档定义一致
- 校验请求参数验证规则（必填、类型、长度）
- 推荐使用 schema 校验工具（如 JSON Schema、Zod、Pydantic）

## Frontend Testing (组件/E2E/视觉回归)

### 组件测试 (Component Tests)

测试目标：单个组件的渲染、props、事件、状态

要求：
- Presentational 组件：覆盖 props 变化、事件触发、条件渲染
- Container 组件：覆盖与 store/hook 的交互、副作用
- 推荐工具：Vitest + Testing Library / Jest + React Testing Library

示例覆盖维度：
```
- 不同 props 下的渲染快照
- 用户交互事件（click、input、submit）
- 条件渲染（loading、error、empty、success）
- 可访问性属性（aria-*、role、tabindex）
```

### E2E 测试 (End-to-End Tests)

测试目标：模拟真实用户路径，跨页面、跨组件、跨前后端

要求：
- 覆盖每条核心用户路径（来自 requirements.md 的用户故事）
- 覆盖关键异常路径（认证失败、网络错误、表单校验）
- 执行环境：独立的测试环境（含真实后端或高仿真 mock 后端）
- 推荐工具：Playwright / Cypress

E2E 路径选择原则：
1. **覆盖 AC 中的关键路径**，不追求 100% 覆盖率
2. **优先级排序**：登录/注册 > 核心业务流程 > 边缘功能
3. **稳定性优先**：宁可少测，不要 flaky

### 视觉回归 (Visual Regression, 可选)

测试目标：UI 截图对比，捕捉非预期的样式变化

适用场景：
- 大规模 UI 重构
- 设计系统升级
- 跨浏览器/分辨率验证

不适用场景：
- 纯逻辑功能开发
- UI 频繁迭代期（基线频繁变化）

## Contract Testing (前后端一致性验证)

契约测试是前后端"握手"的最终保险，必须独立于前端组件测试和后端单元测试。

### 验证维度

1. **请求格式一致**：前端发出的请求结构与后端期望一致
2. **响应格式一致**：后端返回的响应结构与前端解析逻辑一致
3. **错误码语义一致**：错误码、错误消息格式前后端共识
4. **类型定义同源**：推荐前后端共享类型定义（如 OpenAPI 生成、tRPC、Protobuf）

### 实施方式（择一或组合）

| 方式 | 适用场景 | 工具示例 |
|------|---------|---------|
| Schema-First | 强类型约束 | OpenAPI + 代码生成 |
| Consumer-Driven Contract | 微服务架构 | Pact |
| 共享类型定义 | 单仓 monorepo | TypeScript shared types |
| 集成 E2E 兜底 | 小项目 | Playwright + 真实后端 |

## Process

```
┌──────────────────────────────────────────────────┐
│              测试执行流程                          │
├──────────────────────────────────────────────────┤
│                                                  │
│  1. 读取当前事实源，识别已 DONE 的任务            │
│         │                                        │
│         ▼                                        │
│  2. 检查每个 DONE 任务的测试是否已编写            │
│         │                                        │
│    ┌────┴────┐                                   │
│    │ 缺测试？ │                                   │
│    └────┬────┘                                   │
│      Y/ │ \N                                     │
│      ▼  │  ▼                                     │
│  3.补齐  跳过                                     │
│      │                                           │
│      ▼                                           │
│  4. 分轨运行（后端单测 → 集成 → 契约 → 前端组件）  │
│         │                                        │
│         ▼                                        │
│  5. 跑 E2E（如前端任务全部完成）                  │
│         │                                        │
│         ▼                                        │
│  6. 收集失败用例，分类（真 bug / 测试问题 / 环境）│
│         │                                        │
│         ▼                                        │
│  7. 真 bug 回到 ship-build 修复                   │
│         │                                        │
│         ▼                                        │
│  8. 收集覆盖率与结果，更新 verification.md        │
│                                                  │
└──────────────────────────────────────────────────┘
```

### 步骤详解

**Step 1-3: 测试覆盖审计**
- 列出所有 DONE 任务
- 对照 Verification Per Task 检查测试是否齐全
- 缺失测试者补齐，不再以 `ship-build` 已结束为由跳过

**Step 4-5: 分轨执行**
- 优先级：后端单测 → 后端集成 → 后端契约 → 前端组件 → 前端 E2E
- 前序失败时不阻塞后序，但需要分类标记

**Step 6-7: 失败诊断**
- 真 bug → 创建修复任务，回到 `ship-build`
- 测试问题（写错的断言、过期的 fixture）→ 修测试
- 环境问题（端口冲突、依赖缺失）→ 修环境，记录到 README

**Step 8: 结果归档**
- 测试运行命令与输出
- 覆盖率报告路径
- 失败列表与处理状态
- 若自动化验证通过且无阻塞，设置 `verification.md.stage_status: ready` 且保持 `artifact_phase: testing`、`produced_by: [ship-verify]`、`accepted_by: ship-handoff`
- 若仍有未解决 blocker，保持 `verification.md.stage_status: draft`

## Output: verification.md

`verification.md` 是 `ship-verify` 与 `ship-handoff` 的共享产物。`ship-verify` 负责写入测试章节，不负责最终 AC 验收结论。

注意：`verification.md` frontmatter 中的 `stage: ship-handoff` 是刻意的 ownership 设计，用于表示最终验收归 `ship-handoff` 收口；这不代表 `ship-verify` 缺少产物。

### Frontmatter

```yaml
---
stage: ship-handoff
stage_status: draft  # draft / ready / complete
produced_by:
  - ship-verify
accepted_by: ship-handoff
artifact_phase: testing       # testing | acceptance
updated_at: ""
all_ac_verified: false
---
```

### 本阶段必须写入的章节

- 自动化测试结果汇总
- 覆盖率结果与报告路径
- 失败用例分类（真 bug / 测试问题 / 环境）
- 测试运行命令
- 已知的测试环境限制

### Test Run Schema

每条测试轨道结果至少记录：

```yaml
track: backend-unit | backend-integration | backend-contract | frontend-component | frontend-e2e
command: ""
status: pass | fail | skipped | na
evidence: ""
failure_class: none | product_bug | test_bug | environment | flaky
linked_ac: []
```

维护者可运行：

```bash
python3 skills/ship-orchestrator/scripts/validate_verification.py <feature-dir> --project-scope <fullstack|backend_only|frontend_only>
```

## Coverage Requirements

| 范围 | 最低要求 | 建议 |
|------|---------|------|
| 核心业务逻辑 (Service/Domain) | > 80% | > 90% |
| API endpoint | 100%（每个至少 1 个测试） | 含正常 + 异常路径 |
| 数据访问层 | > 70% | 覆盖核心 query |
| 前端核心组件 | > 70% | 含交互与状态 |
| 前端工具函数 | > 90% | 纯函数易测必测 |
| E2E 关键路径 | 100% AC 关键路径 | 含主要异常 |

### 覆盖率不是目标

- 覆盖率高但测试质量差（无断言、无边界）≈ 没测
- 覆盖率低但每条都覆盖了关键路径 > 高覆盖率的水化测试
- AC 是否被验证 > 行覆盖率数字

## Anti-Rationalizations

1. **"我手动点过了，能跑就行"** —— 手动测试无法回归，无法证明"昨天能用今天还能用"。自动化测试是给未来的自己买保险。
2. **"覆盖率到了 80% 就行"** —— 覆盖率统计的是行执行，不是断言质量。一行 `expect(result).toBeDefined()` 也算覆盖。
3. **"E2E 太慢，跳过吧"** —— E2E 慢是事实，但它是唯一能验证前后端真实联通的手段。慢不是不跑的理由，是优化的理由。
4. **"flaky 测试再跑一次就过"** —— flaky 是测试有 bug 或被测对象有竞态。重试掩盖问题，最终会在生产环境爆雷。
5. **"测试失败但代码确实没问题"** —— 这种判断需要证据。读代码、加日志、复现，确认根因后再说测试错了。

## Red Flags

以下情况必须暂停处理：

- **多个测试同时失败但模式相似**：可能是共享基础设施问题（如测试 DB 未清理）
- **测试通过但 AC 失败**：测试与需求不对齐，回到 `ship-verify` 补齐验证设计
- **修复一个 bug 引发其他测试失败**：可能是修复方向错了，或测试在测错的东西
- **覆盖率剧烈下降**：可能新增代码无测试，或测试被误删
- **E2E 通过但用户实际操作失败**：测试环境与真实环境差异过大
- **同一测试连续 flaky ≥ 3 次**：必须根因分析，不能继续重试

## Verification

测试阶段完成前逐项确认：

```markdown
## 测试阶段退出检查

- [ ] 所有 DONE 任务都有对应的自动化测试
- [ ] `project_scope` 已确认；`fullstack` 执行全部测试轨道，`backend_only` 跳过 frontend 轨道并在 verification.md 记录 `na`，`frontend_only` 跳过 backend 轨道并记录 `na`
- [ ] backend scope 存在时，后端单元测试通过率 100%；否则标记为 `na`
- [ ] backend scope 存在时，后端集成测试通过率 100%；否则标记为 `na`
- [ ] backend scope 存在时，后端契约测试通过率 100%；否则标记为 `na`
- [ ] frontend scope 存在时，前端组件测试通过率 100%；否则标记为 `na`
- [ ] frontend scope 存在时，E2E 关键路径通过率 100%；否则标记为 `na`
- [ ] 适用范围内的核心业务逻辑覆盖率 > 80%
- [ ] 失败用例已分类处理（真 bug / 测试问题 / 环境）
- [ ] 真 bug 已创建修复任务并解决
- [ ] 测试运行命令已写入项目 README 或 CI 配置
- [ ] 测试结果与覆盖率已写入 verification.md
- [ ] verification.md 的测试章节完整，且 `stage_status` 已正确设置为 `ready` 或 `draft`
- [ ] 无未处理的 flaky 测试（要么修，要么显式标记 skip 并记录原因）
```
