---
name: ship-frontend-plan
description: "ShipKit stage. Breaks frontend design into executable task list. Use after ship-frontend-design completes."
---

# 前端实施计划 (Frontend Plan)

## Overview

本阶段基于 `frontend-design.md` 将前端设计方案拆解为可执行的任务清单。核心原则：**Contract-First（接口优先）**，确保前端开发从第一天起就能基于稳定的接口契约独立推进。

产出物：`frontend-plan.md`

## When to Use

- frontend-design.md 已通过 design-review gate（stage_status: ready）
- api-contract.md 已完成（提供接口定义）
- 需要将前端设计拆解为可分配、可追踪的开发任务

## When NOT to Use

- frontend-design.md 尚未完成或未通过评审
- api-contract.md 不存在或未定稿 — 接口契约是任务拆解的前提
- 仅涉及后端变更，无前端工作
- 需求仍在变动中，设计未稳定

## Contract-First Task Ordering

接口对齐任务（Contract Tasks）**必须**排在所有页面/组件任务之前。原因：

1. TypeScript 类型定义是所有组件的基础依赖
2. Mock 服务使前端开发不被后端进度阻塞
3. API 调用层封装提供统一的数据获取模式

执行顺序铁律：
```
Contract Tasks (FE-C-xxx) → 公共组件任务 → 页面任务 → 集成任务
```

## Process

```
1. 读取 frontend-design.md + api-contract.md
   verify: 两份文档均为 ready 状态
2. 提取接口对齐任务（Mock / Types / API Layer）
   verify: 覆盖 api-contract.md 中所有前端相关接口
3. 按页面/组件拆解任务
   verify: 每个页面至少包含路由+组件+状态+接口+样式子任务
4. 为每个任务关联 AC ID
   verify: 无孤立任务（每个任务至少关联一个 AC）
5. 建立依赖关系
   verify: 无循环依赖，Contract Tasks 无上游依赖
6. 估算工时
   verify: 单个任务不超过 2 小时（超过则需继续拆分）
7. 绘制依赖关系图
   verify: 图与任务清单一致
8. 写入 frontend-plan.md
   verify: frontmatter 完整，task_count 准确
```

## Task Structure (任务字段说明)

每个任务必须包含以下字段：

```markdown
### FE-001: [任务标题]

- **描述**：具体要做什么，产出什么
- **关联页面/组件**：所属页面或公共组件名称
- **关联接口**：API-xxx（api-contract.md 中的接口 ID）
- **关联 AC ID**：AC-xxx（requirements.md 中的验收标准 ID）
- **依赖**：depends_on: [FE-xxx, FE-xxx]
- **完成判定**：
  - [ ] 具体验证标准 1
  - [ ] 具体验证标准 2
- **预估工时**：x h
- **状态**：TODO / DOING / DONE
```

### Contract Task 特殊字段

Contract Tasks 使用 `FE-C-xxx` 编号，额外包含：
- **覆盖接口列表**：该任务覆盖的所有 API ID

## Task Granularity Rules

### 粒度标准

每个任务应能在**一次 AI 对话中完成并验证**，具体约束：

| 维度 | 约束 |
|------|------|
| 代码量 | 单任务产出不超过 300 行（含测试） |
| 文件数 | 单任务涉及不超过 5 个文件 |
| 工时 | 单任务预估 0.5-2 小时 |
| 验证 | 单任务有明确的、可独立运行的验证方式 |

### 页面级任务拆分模板

一个完整页面通常拆为以下子任务：

```
FE-0x1: 路由配置 + 页面骨架
FE-0x2: 页面状态管理（store/hooks）
FE-0x3: 核心交互组件实现
FE-0x4: 接口对接 + 数据流转
FE-0x5: 样式完善 + 响应式适配
FE-0x6: 异常处理 + Loading/Empty 状态
```

### 公共组件任务拆分

```
FE-0x1: 组件 API 设计 + 基础渲染
FE-0x2: 交互逻辑 + 状态管理
FE-0x3: 样式变体 + 主题适配
FE-0x4: 可访问性 + 键盘导航
```

### 任务命名规范

| 编号前缀 | 用途 | 示例 |
|---------|------|------|
| FE-C-xxx | Contract Tasks（接口对齐） | FE-C-001 Mock 搭建 |
| FE-S-xxx | Shared（公共组件/工具） | FE-S-001 Button 组件 |
| FE-P-xxx | Page（页面级任务） | FE-P-001 登录页路由 |
| FE-I-xxx | Integration（集成/E2E） | FE-I-001 登录流程 E2E |

## Output: frontend-plan.md

### Frontmatter

```yaml
---
stage: ship-frontend-plan
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
- 关键里程碑（按周或按阶段）
- 技术栈确认（框架/状态管理/UI 库/构建工具）

#### 2. 接口对齐任务 (Contract Tasks)
- FE-C-001: Mock 服务搭建（MSW / json-server 等）
- FE-C-002: API TypeScript 类型定义（从 api-contract.md 生成）
- FE-C-003: API 调用层封装（axios/fetch wrapper + 错误处理）

#### 3. 任务清单（按页面/组件分组）
- 按页面分组，每组内按依赖顺序排列
- 公共组件单独分组，排在页面任务之前

#### 4. 依赖关系图（ASCII）
```
FE-C-001 ──→ FE-C-002 ──→ FE-C-003
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
          [页面 A 组]     [页面 B 组]     [页面 C 组]
```

#### 5. 执行顺序建议
- 推荐的并行开发路径
- 关键路径标注
- 里程碑检查点

### stage_status 流转规则

- `draft`：任务拆解进行中，或存在未关联 AC 的任务
- `ready`：所有任务已拆解、关联、估时，依赖关系无冲突，可进入实施阶段

### evidence_complete 判定标准

- 所有 frontend-design.md 中的页面/组件均已拆解为任务
- 所有 api-contract.md 中前端相关接口均已覆盖
- 无孤立任务（每个任务至少关联一个 AC ID）
- task_count 与实际任务数一致

## Anti-Rationalizations

1. **"接口还没定稿，先做页面再说"** — 不行。没有 Contract Tasks 的前端开发会导致后期大量返工。即使接口未最终确定，也必须基于 api-contract.md 当前版本建立 Mock 和类型。
2. **"这个页面很简单，不用拆那么细"** — 粒度不是为了"看起来专业"，是为了让每个任务可独立验证。一个"简单页面"拆开后往往有 5+ 个验证点。
3. **"工时估不准，随便填个数"** — 工时估算的目的不是精确预测，而是识别过大的任务。超过 2h 的任务说明粒度不够细，必须继续拆分。
4. **"依赖关系太复杂，画不出来"** — 画不出来说明任务边界不清晰。回去重新定义任务的输入和输出。
5. **"AC 太多关联不过来"** — 如果一个任务无法关联到任何 AC，说明这个任务可能不应该存在。如果一个 AC 没有任务覆盖，说明遗漏了任务。

## Red Flags

- Contract Tasks 不在任务清单最前面 → 违反 Contract-First 原则
- 存在超过 2 小时的单个任务 → 粒度不足，需继续拆分
- 有任务未关联任何 AC ID → 任务可能是多余的，或 AC 覆盖不全
- 有 AC 未被任何任务覆盖 → 存在实施遗漏
- 依赖关系图中存在循环 → 任务边界定义有问题
- 页面任务缺少异常处理/Loading 状态子任务 → 用户体验考虑不全
- task_count 与实际任务数不一致 → frontmatter 未更新

## Verification

完成 frontend-plan.md 后，执行以下检查：

```
□ Contract Tasks 是否排在所有页面任务之前？
□ 每个任务是否关联至少一个 AC ID？
□ 每个 AC 是否被至少一个任务覆盖？
□ api-contract.md 中所有前端相关接口是否已覆盖？
□ 单个任务预估工时是否均 ≤ 2h？
□ 依赖关系是否无循环？
□ 页面任务是否包含完整子任务（路由/组件/状态/接口/样式）？
□ 依赖关系图是否与任务清单一致？
□ task_count 是否与实际任务数一致？
□ frontmatter 字段是否正确填写？
```

全部通过后，将 `stage_status` 设为 `ready`。
