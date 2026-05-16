# Skill Composition Contract

本文件定义 Coding Feature Workflow 中阶段 skill 与其他 skill 之间的组合调用协议。组合调用允许阶段 skill 在不离开当前阶段的前提下，获取其他 skill 的专业输入。

## 组合类型

### 1. Advisory Call（咨询调用）

- **调用方**：任何阶段 skill
- **被调用方**：`agent-product-manager`、`agent-solution-architect`
- **协议**：调用方提供 context snippet + specific question
- **返回**：structured advice（不修改阶段文档）
- **写入责任**：仍由调用方阶段 skill 负责，将 advice 吸收到阶段文档的"协作者输入"section

### 2. Utility Call（工具调用）

- **调用方**：任何阶段 skill
- **被调用方**：`coding-spec-management`
- **协议**：调用方请求特定规范查询（如"当前项目的错误处理规范"）
- **返回**：applicable spec content
- **无状态变更**

### 3. Validation Call（验证调用）

- **调用方**：`coding-implementation-execution`、`coding-verification-closeout`
- **被调用方**：`coding-code-review`
- **协议**：调用方提供 diff + design context
- **返回**：review findings + pass/fail
- **可阻塞当前任务**：blocking issue 导致任务回退为 DOING

## Call Payload

组合调用时，调用方必须构造以下 payload：

```yaml
composition_call:
  caller: <当前阶段 skill 名>
  callee: <被调用 skill 名>
  call_type: advisory | utility | validation
  context:
    feature_dir: .docs/feature-YYYYMMDD-short-name
    stage: <当前阶段>
    question: "<具体问题描述>"
    evidence: |
      <支撑问题的关键上下文，如方案摘要、代码片段、冲突描述>
  response_format: structured_advice | spec_content | review_findings
```

## Composition Rules

1. **不改变 gate policy**：组合调用完成后仍在当前阶段，不触发阶段推进。
2. **不需要 route payload**：被调用 skill 不是阶段推进，不受 route contract 约束。
3. **不修改阶段文档**：被调用 skill 不得直接修改 feature 目录下的阶段文档。
4. **结果记录**：调用结果记录在当前阶段文档的"协作者输入"section，标注来源。
5. **同步执行**：组合调用是同步的，调用方等待返回后继续。
6. **Metrics 记录**：每次组合调用必须追加 `composition_call` 事件到 `metrics.json`。
7. **非强制**：组合调用是建议性的，用户可以跳过或拒绝。
8. **幂等性**：同一问题重复调用应返回一致结果（除非上下文变化）。

## 适用场景

| 阶段 | 建议的组合调用 | 触发条件 |
| --- | --- | --- |
| discovery | Advisory → `agent-product-manager` | 原始需求缺乏产品结构化思考 |
| discovery | Advisory → `agent-solution-architect` | `empty_project` 技术栈选型 |
| requirements | Advisory → `agent-product-manager` | 优先级冲突或 PRD 质量评审 |
| design | Advisory → `agent-solution-architect` | 复杂架构设计或多方案评审 |
| design | Utility → `coding-spec-management` | 需要查询项目编码规范 |
| implementation | Utility → `coding-spec-management` | 需要查询项目编码规范 |
| implementation | Validation → `coding-code-review` | 所有任务 DONE 后 |
| verification | Validation → `coding-code-review` | 发现代码质量问题需要复查 |

## 协作者输入 section 格式

阶段文档中记录组合调用结果的标准格式：

```markdown
## 协作者输入

### [来源 skill 名] — [调用时间 ISO 8601]

**问题**：<调用时提出的问题>

**建议**：
<被调用 skill 返回的结构化建议>

**采纳决策**：<采纳 / 部分采纳 / 不采纳>
**采纳理由**：<为什么采纳或不采纳>
```

## 与 WORKFLOW_CONTRACT.md 的关系

- 本 contract 是 WORKFLOW_CONTRACT.md section 15 (Optional collaborator contract) 的执行层扩展。
- Section 15 定义了协作者的定位和边界；本 contract 定义了具体的调用协议和 payload 格式。
- 两者不冲突：section 15 的"建议引入"现在有了结构化的执行路径。
