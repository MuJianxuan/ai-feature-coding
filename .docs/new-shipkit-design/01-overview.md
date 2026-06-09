# 新 ShipKit 设计方案 v1

## 设计目标

1. **简洁但完整**：减少阶段和状态复杂度，但保留必要的质量门禁
2. **目标驱动**：以"交付可工作软件"为目标，而非"完成文档"
3. **AI 友好**：减少认知负载，让 AI agent 能自主推进
4. **渐进式**：支持快速启动，也支持复杂项目的严格流程

## 核心流程：4 阶段 + 1 辅助技能

```
[Split] → Understand → Design → Build
   ↓          ↓          ↓        ↓
  Spec      Spec      Spec     Spec
  (知识库，随时加载)
```

### 技能清单

1. **ship-split**（需求拆分）- 可选前置
   - 输入：大需求描述、TAPD/Jira 链接、会议纪要
   - 输出：独立的小需求列表（每个可独立交付）
   - 支持：TAPD/Jira API 集成

2. **ship-spec**（规范管理）- 工具技能
   - 维护项目规范库（技术栈、设计规范、已有功能、项目结构）
   - 支持多项目
   - 其他阶段按需加载

3. **ship-understand**（理解需求）
   - 输入：需求描述 / PRD / 原型
   - 过程：结合 spec 了解现有功能 + grill-me 审查
   - 输出：requirements.md（AC + Domain 模型）

4. **ship-design**（技术设计）
   - 输入：requirements.md + spec
   - 过程：技术调研 + 方案设计 + grill-me 审查
   - 输出：design.md（API contract + 前后端方案 + 数据模型）

5. **ship-build**（实现验证）
   - 输入：design.md
   - 输出：代码 + 测试 + 验证报告

6. **ship-grill-me**（质询助手）- 嵌入在 Understand 和 Design 中
   - 不是独立阶段
   - 在 ready 前审查阻塞问题

## 状态管理：极简化

只用一个 `meta.yml`：

```yaml
feature_name: "用户登录"
current_stage: understand | design | build | done
status: in_progress | blocked | completed
scenario: quick_start | full_flow | prd_direct
created_at: "2026-06-09T10:00:00Z"
updated_at: "2026-06-09T11:30:00Z"

# 简单引用
spec_refs: ["auth-flow", "react-routing"]
requirements_file: "requirements.md"
design_file: "design.md"

# 只在阻塞时才写
blocked_reason: ""
```

产物文件 frontmatter 只保留：
```yaml
status: draft | ready | approved
updated_at: "..."
```

## 门禁策略：信任 + 验证

- **Understand → Design**：AI 自检通过（grill-me 无阻塞问题）即可推进
- **Design → Build**：用户确认设计方案（只需一次 yes/no）
- **Build → Done**：测试通过 + AC 覆盖验证

## 场景模式

### 1. 快速启动（quick_start）
适合：小功能、熟悉的技术栈
```
直接进 Understand → 快速 Design（跳过 grill-me）→ Build
```

### 2. 完整流程（full_flow）
适合：中等复杂度
```
Understand（含 grill-me）→ Design（含 grill-me）→ Build
```

### 3. PRD 直通（prd_direct）
适合：已有完整 PRD
```
解析 PRD → Design → Build
```

### 4. 需求拆分（split_first）
适合：大需求、多子任务
```
Split → 为每个子需求启动 full_flow
```

## 与旧方案对比

| 维度 | 旧方案 | 新方案 |
|------|--------|--------|
| 阶段数 | 14（5 对外） | 4 |
| 门禁数 | 3 道硬门禁 | 1 道用户确认 + 2 道自检 |
| 状态字段 | meta.yml 20+ 字段 | 8 个核心字段 |
| 文档产物 | 13 个 .md 文件 | 3 个核心文件 |
| validator | 27 个脚本 | 3 个（requirements / design / build） |
| 场景入口 | 5 种，需识别 | 4 种，自动降级 |
| 代码编辑限制 | 6 层前置检查 | 到 Build 阶段即可 |

## 下一步

第二轮设计：
1. 详细定义每个技能的输入输出
2. 定义 grill-me 如何嵌入 Understand 和 Design
3. 定义 spec 的加载时机和使用方式
4. 设计 Split 技能的 TAPD 集成
