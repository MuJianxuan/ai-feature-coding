---
name: ship-spec
description: "ShipKit utility. Manages and evolves project coding specifications. Use when establishing conventions, after delivery to capture learnings, or when checking existing specs during design."
---

# 规范管理 (Spec Management)

## Overview

规范管理是一个 Utility Skill，贯穿整个开发工作流。它负责沉淀、维护和分发项目编码规范，确保团队（包括 AI agent）在编码时遵循一致的约定。

规范不是一次性产物，而是随项目演进持续更新的活文档。每次交付后的经验教训、每次 code review 中发现的模式，都应该沉淀为规范。

## When to Use

- 新项目初始化时，建立基础规范
- tech-selection 完成后，根据技术栈生成对应规范
- implementation 阶段开始前，确认 agent 已加载相关规范
- 交付完成后（acceptance 阶段），沉淀新发现的模式
- code review 中发现重复问题时

## When NOT to Use

- 简单 bug fix 不需要触发规范更新
- 规范已存在且无需修改时不要重复生成
- 不要在 implementation 中途停下来写规范（完成后再沉淀）

## Spec Directory Structure

```
.docs/spec/
├── INDEX.md              # 规范索引（所有规范的目录）
├── naming.md             # 命名规范
├── error-handling.md     # 错误处理规范
├── api-style.md          # API 风格规范
├── testing.md            # 测试规范
├── git-workflow.md       # Git 工作流规范
└── <domain>-<topic>.md   # 按需新增
```

## Process

### 1. 创建规范

```
触发 → 检查 INDEX.md 是否已有同类规范 → 无则创建 / 有则更新
```

每份规范文件结构：

```markdown
---
spec_id: <kebab-case-id>
scope: project  # project / module / file
applies_to: ["*.ts", "*.tsx"]  # glob 模式
last_updated: ""
---

# <规范标题>

## 规则

1. **规则名** — 具体要求
   - 正例：`...`
   - 反例：`...`

## 例外

- 场景 X 下可以不遵循规则 Y，因为...

## 来源

- 从 feature-YYYYMMDD-xxx 的 code review 中沉淀
```

### 2. 消费规范

在以下阶段自动加载相关规范：
- **ship-stack**：读取 INDEX.md，确认选型不与已有规范冲突
- **ship-frontend-design / ship-backend-design**：加载对应技术栈的规范
- **ship-build**：每个任务开始前加载 `applies_to` 匹配的规范

### 3. 沉淀规范

在以下时机触发沉淀：
- **ship-handoff** 完成后：review 过程中发现的模式
- 用户主动要求："把这个模式沉淀为规范"

## Integration Points (与主流程的接入)

| 阶段 | 接入方式 | 动作 |
|------|---------|------|
| tech-selection | 读取 | 检查选型与已有规范的兼容性 |
| frontend-design | 读取 | 加载前端相关规范作为设计约束 |
| backend-design | 读取 | 加载后端相关规范作为设计约束 |
| implementation | 读取 | 每个任务开始前加载匹配规范 |
| acceptance | 写入 | 沉淀新发现的模式为规范 |

## Anti-Rationalizations

| Agent 可能的借口 | 现实 |
|-----------------|------|
| "这个项目太小不需要规范" | 即使是 TODO app，命名和错误处理规范也能防止 agent 风格漂移 |
| "规范写了也没人看" | agent 在 implementation 阶段会自动加载，这是给 AI 看的 |
| "等项目稳定了再写规范" | 越早建立规范，后期返工越少 |
| "这个模式太特殊不值得沉淀" | 如果出现两次，就值得沉淀 |

## Red Flags

- INDEX.md 长期不更新（说明沉淀机制失效）
- 规范与实际代码不一致（说明规范过时需要更新）
- implementation 阶段没有加载任何规范
- 规范过于宽泛（"写好代码"）而非具体可执行

## Verification

- [ ] INDEX.md 存在且列出所有规范文件
- [ ] 每份规范有 frontmatter（spec_id, scope, applies_to）
- [ ] 每条规则有正例和反例
- [ ] 规范与当前技术栈匹配
- [ ] implementation 阶段的任务描述中引用了相关规范
