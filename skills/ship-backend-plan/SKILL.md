---
name: ship-backend-plan
description: "ShipKit stage. Breaks backend design into executable task list. Use after ship-backend-design completes."
---

# 后端实施计划 (Backend Plan)

## Overview

本阶段基于 `backend-design.md` 将后端设计方案拆解为可执行的任务清单。核心原则：**Infrastructure-First（基础设施优先）**，确保业务任务在稳定的基础设施之上推进，避免后期重构。

产出物：`backend-plan.md`

## When to Use

- backend-design.md 已通过 design-review gate（stage_status: ready）
- api-contract.md 已完成（提供接口定义）
- requirements.md 中的业务域建模（Domain ID）已完成
- 需要将后端设计拆解为可分配、可追踪的开发任务

## When NOT to Use

- backend-design.md 尚未完成或未通过评审
- api-contract.md 不存在或未定稿 — 接口契约是任务拆解的前提
- 仅涉及前端变更，无后端工作
- 数据模型仍在变动中，设计未稳定

## Infrastructure-First Task Ordering

基础设施任务（Infrastructure Tasks）**必须**排在所有业务任务之前。原因：

1. 项目脚手架决定后续所有代码的组织方式
2. 数据库 schema + migration 是业务逻辑的基础
3. 认证/错误处理/日志中间件是所有接口的横切关注点
4. API 路由骨架决定 Controller 层的统一规范

执行顺序铁律：
```
Infrastructure Tasks (BE-I-xxx) → 公共服务任务 → 业务域任务 → 集成任务
```

## Process

```
1. 读取 backend-design.md + api-contract.md + requirements.md
   verify: 三份文档均为 ready 状态
2. 提取基础设施任务（脚手架/DB/中间件/路由骨架）
   verify: 覆盖项目运行所需全部基础组件
3. 按业务域（Domain ID）拆解任务
   verify: 每个 Domain 至少包含 Controller+Service+Repository+测试子任务
4. 为每个任务关联 AC ID 和接口 ID
   verify: 无孤立任务（每个任务至少关联一个 AC）
5. 建立依赖关系
   verify: 无循环依赖，Infrastructure Tasks 无上游依赖
6. 估算工时
   verify: 单个任务不超过 2 小时（超过则需继续拆分）
7. 绘制依赖关系图
   verify: 图与任务清单一致
8. 写入 backend-plan.md
   verify: frontmatter 完整，task_count 准确
```

## Task Structure (任务字段说明)

每个任务必须包含以下字段：

```markdown
### BE-001: [任务标题]

- **描述**：具体要做什么，产出什么
- **关联业务域**：D-XXX-NNN（requirements.md 中的 Domain ID）
- **关联接口**：API-xxx（api-contract.md 中的接口 ID）
- **关联 AC ID**：AC-xxx（requirements.md 中的验收标准 ID）
- **依赖**：depends_on: [BE-xxx, BE-xxx]
- **完成判定**：
  - [ ] 代码实现完成（Controller / Service / Repository）
  - [ ] 单元测试通过，覆盖率 ≥ 80%
  - [ ] 接口文档与 api-contract.md 一致
  - [ ] 错误处理覆盖所有异常路径
- **预估工时**：x h
- **状态**：TODO / DOING / DONE
```

### Infrastructure Task 特殊字段

Infrastructure Tasks 使用 `BE-I-xxx` 编号，额外包含：
- **影响范围**：该基础设施影响哪些业务任务
- **配置项清单**：涉及的环境变量、配置文件

## Task Granularity Rules

### 粒度标准

每个任务应能在**一次 AI 对话中完成并验证**，具体约束：

| 维度 | 约束 |
|------|------|
| 代码量 | 单任务产出不超过 400 行（含测试） |
| 文件数 | 单任务涉及不超过 6 个文件 |
| 工时 | 单任务预估 0.5-2 小时 |
| 测试 | 每个业务任务必须包含单元测试 |
| 验证 | 单任务有可独立运行的测试用例 |

### 接口实现任务拆分模板

一个完整接口（API endpoint）通常拆为以下子任务：

```
BE-0x1: 数据模型 + Repository 层（DAO + 单元测试）
BE-0x2: Service 层业务逻辑（含单元测试）
BE-0x3: Controller 层 + 参数校验 + 错误处理
BE-0x4: 集成测试（端到端接口测试）
```

如果接口逻辑简单（CRUD），可合并为：
```
BE-0x1: Repository + Service + Controller + 测试（单一接口完整实现）
```

### 业务域任务拆分

每个 Domain ID 至少拆分为：

```
BE-0x1: 数据模型定义 + Migration
BE-0x2: 核心业务逻辑（Service 层）
BE-0x3: 接口层实现（按接口数拆分子任务）
BE-0x4: 域内集成测试
```

### 测试任务规则

- **单元测试**：与业务代码同一任务内完成（不单独立任务）
- **集成测试**：作为独立子任务，在所有相关业务任务完成后执行
- **覆盖率要求**：单元测试 ≥ 80%，关键路径 100%

## Output: backend-plan.md

### Frontmatter

```yaml
---
stage: ship-backend-plan
stage_status: draft  # draft / ready
updated_at: ""
evidence_complete: false
task_count: 0
---
```

### 核心章节

#### 1. 实施概览
- 总任务数
- 预估总工时
- 关键里程碑（按业务域或按阶段）
- 技术栈确认（框架/ORM/数据库/缓存/消息队列）

#### 2. 基础设施任务 (Infrastructure Tasks)
- BE-I-001: 项目初始化（官方脚手架）
- BE-I-002: 数据库 schema + migration 框架搭建
- BE-I-003: 基础中间件（认证 / 错误处理 / 日志 / 请求追踪）
- BE-I-004: API 路由骨架（统一响应格式 / 全局异常处理）
- BE-I-005: 测试框架配置（单元测试 + 集成测试）
- BE-I-006: CI/CD 基础配置（如适用）

#### 3. 任务清单（按业务域分组）
- 按 Domain ID 分组，每组内按依赖顺序排列
- 跨域共享服务单独分组，排在业务任务之前

```markdown
### Domain: D-AUTH-001 (用户认证)
- BE-001: 用户数据模型 + Migration
- BE-002: 密码加密 Service
- BE-003: 登录接口实现
- BE-004: Token 签发 + 校验
- BE-005: 集成测试

### Domain: D-ORD-001 (订单创建)
- BE-006: ...
```

#### 4. 依赖关系图（ASCII）
```
BE-I-001 ──→ BE-I-002 ──→ BE-I-003 ──→ BE-I-004
                                          │
              ┌───────────────────────────┼───────────────┐
              ▼                           ▼               ▼
        [D-AUTH 任务组]              [D-ORD 任务组]    [D-PAY 任务组]
              │                           │
              └────────────┬──────────────┘
                           ▼
                    [跨域集成测试]
```

#### 5. 执行顺序建议
- 推荐的并行开发路径
- 关键路径标注
- 里程碑检查点（如：基础设施完成、核心域完成、全量集成测试通过）

### stage_status 流转规则

- `draft`：任务拆解进行中，或存在未关联 AC 的任务
- `ready`：所有任务已拆解、关联、估时，依赖关系无冲突，可进入实施阶段

### evidence_complete 判定标准

- 所有 backend-design.md 中的业务域均已拆解为任务
- 所有 api-contract.md 中后端相关接口均已覆盖
- 所有业务任务均包含测试要求
- 无孤立任务（每个任务至少关联一个 AC ID）
- task_count 与实际任务数一致

## Anti-Rationalizations

1. **"先把接口写完，测试后面统一补"** — 不行。"后面"通常意味着"永远不"。每个业务任务必须内置测试要求，作为完成判定的一部分。
2. **"基础设施先简单搭一下，业务遇到问题再改"** — 基础设施改动会牵连所有上层业务代码。Infrastructure Tasks 必须一次到位，包括认证、错误处理、日志这些"看起来不紧急"的部分。
3. **"这个 Service 逻辑很复杂，一个任务就够了"** — 复杂正是要拆的理由。复杂逻辑拆成 Repository / Service / Controller 三层，每层独立可测。
4. **"工时估不准，写个 8h 兜底"** — 8h 任务等于无法在一次对话中完成，等于无法独立验证，等于回到了瀑布开发。超过 2h 必须拆分。
5. **"AC 都关联到 Controller 任务就行了"** — Controller 只是入口，AC 的真正实现往往在 Service 和 Repository。每一层任务都应关联其覆盖的 AC。

## Red Flags

- Infrastructure Tasks 不在任务清单最前面 → 违反 Infrastructure-First 原则
- 业务任务缺少测试要求 → 违反"测试与代码同任务"规则
- 存在超过 2 小时的单个任务 → 粒度不足，需继续拆分
- 有任务未关联任何 AC ID → 任务可能是多余的，或 AC 覆盖不全
- 有 AC 未被任何任务覆盖 → 存在实施遗漏
- 有 Domain ID 未被任何任务覆盖 → 业务域遗漏
- 依赖关系图中存在循环 → 任务边界定义有问题
- 接口任务未明确拆分 Controller / Service / Repository → 分层架构不清晰
- task_count 与实际任务数不一致 → frontmatter 未更新

## Verification

完成 backend-plan.md 后，执行以下检查：

```
□ Infrastructure Tasks 是否排在所有业务任务之前？
□ 每个任务是否关联至少一个 AC ID？
□ 每个 AC 是否被至少一个任务覆盖？
□ 每个 Domain ID 是否被至少一组任务覆盖？
□ api-contract.md 中所有后端相关接口是否已覆盖？
□ 每个业务任务是否包含测试要求（单元测试 + 覆盖率）？
□ 单个任务预估工时是否均 ≤ 2h？
□ 依赖关系是否无循环？
□ 接口任务是否明确分层（Controller / Service / Repository）？
□ 依赖关系图是否与任务清单一致？
□ task_count 是否与实际任务数一致？
□ frontmatter 字段是否正确填写？
```

全部通过后，将 `stage_status` 设为 `ready`。
