---
name: coding-spec-management
description: "编码规约 wiki 管理（coding standards / conventions / guidelines / 约定 / 规约 / 守则 / best practice）。引导基于代码现状、文档或提示词，新增或补充 .docs/spec/coding/ 下的团队编码规范。不用于 feature 级需求或设计文档（请改用 coding-requirement-intake / coding-technical-design）。"
---

# Coding Spec Management

## 目标

帮助用户将编码经验、架构决策和技术约束沉淀为简洁可执行的团队规范，统一维护在 `.docs/spec/coding/` 目录下，并通过 `.docs/spec/INDEX.md` 暴露给其它 coding-* skill 消费。

## 何时使用 / 何时不使用

**使用**：

- 用户明确要求“添加 / 新增 / 补充 / 更新 / 管理 规范”，或写出 `coding-spec-management`。
- 用户使用同义词：规范 / 规约 / 约定 / 守则 / convention / standard / guideline / best practice / coding rule。
- 用户提供代码片段、文档或口述经验，要求沉淀为规范。

**不使用**：

- feature 级需求文档 → 改用 `coding-requirement-intake`。
- 技术设计文档 → 改用 `coding-technical-design`。
- 任务拆解与计划 → 改用 `coding-task-planning`。
- 不得自动触发；不得在其它 coding-* skill 执行过程中自动创建规范。

## 前置检查

1. 确认 `.docs/spec/INDEX.md` 存在。不存在则从本 skill 的 `assets/INDEX.md` 复制。
2. 确认 `.docs/spec/coding/` 目录存在。不存在则创建。
3. 若 `INDEX.md` 存在但 frontmatter 损坏或缺字段：报告问题，请用户确认是否修复，不擅自重置。

## 输入来源

- **代码现状**：用户指定文件或模块，AI 从中提炼模式和约束。
- **文档**：用户提供的技术文档、最佳实践文章或内部 wiki。
- **提示词**：用户口头描述的原则或经验。

## frontmatter 词表

所有 spec / guide 文档的 frontmatter 必须使用以下统一词表：

| 字段 | 必填 | 取值 / 格式 | 说明 |
| --- | --- | --- | --- |
| `doc_type` | 是 | `spec-index` \| `spec` \| `guide` | `spec-index` 仅用于 INDEX.md；`spec` 写实施契约（怎么做）；`guide` 写思考清单（写之前想什么） |
| `topic` | 是 | kebab-case | 主题标识，与文件名一致；INDEX.md 可省略 |
| `scope` | 是 | `coding` | 当前固定为 `coding` |
| `status` | 是 | `active` \| `deprecated` | 生命周期状态 |
| `superseded_by` | 否 | 字符串 | 仅当 `status: deprecated` 时填写继任 spec 的 `topic` |
| `tags` | 否 | 字符串数组 | 用于检索与场景匹配 |
| `related` | 否 | 字符串数组 | 关联 spec 的 `topic` |
| `updated_at` | 是 | ISO 8601 含时区 | 例：`2026-05-16T10:30:00+08:00` |

## 工作流

### Step 1 理解意图（结构化提问）

如用户未提供以下字段，逐一询问：

1. `topic`（kebab-case）
2. `doc_type`（`spec` 写实施契约；`guide` 写思考清单）
3. 适用场景（一句话描述）
4. 输入来源类型（代码现状 / 既有文档 / 用户口述）
5. 目标读者（前端 / 后端 / 全栈 / 运维）
6. 是否已有相关 spec（让用户列出 topic 或回答“不知道”）

### Step 2 判断新建 vs 补充（三段判定）

按优先级依次判定：

1. **文件名匹配**：`.docs/spec/coding/<topic>.md` 已存在 → 视为同主题，走“补充”。
2. **frontmatter `topic` / `tags` 匹配**：扫描 `.docs/spec/coding/*.md` 的 frontmatter，命中即提示用户确认是补充还是新建。
3. **关键词匹配**：标题或正文出现高度相似关键词，提示用户确认。

**冲突解决**：若新内容与已有规约抵触，必须先与用户确认是替换、并存，还是把旧条目标 `status: deprecated` 并填写 `superseded_by`。

### Step 3 提炼规范（原则 + 分级规约 + rationale）

- **原则**：3-5 条，每条一句话 + 一句 rationale（“为什么”）。格式：`- <原则> — Why: <rationale>`。
- **规约**：每条以分级开头：`MUST` / `SHOULD` / `MAY` / `MUST NOT` / `SHOULD NOT`。
- 每条规约附最小代码片段或反例（`spec` 类型必填，`guide` 类型可选）。
- **反例约束**：不写显而易见的常识；不写纯个人偏好；不写本质上是 lint 默认规则的内容。

### Step 4 写入文档（确定性更新规则）

**新建**：

1. 复制对应模板（`spec` → `assets/spec-template.md`；`guide` → `assets/guide-template.md`）到 `.docs/spec/coding/<topic>.md`。
2. 填充全部必填 frontmatter 字段，`updated_at` 取当前 ISO 8601 时间（含时区）。
3. 在 `.docs/spec/INDEX.md` 的 `coding/` 表格新增一行。
4. 若该规约影响某场景，同步更新 INDEX.md 的 `Pre-Development Checklist` 与 `Quality Check` 两节。
5. 更新 `INDEX.md` 自身的 `updated_at`。

**补充**：

1. 直接编辑现有文件。
2. 必须更新文档 frontmatter 的 `updated_at` 为当前 ISO 8601。
3. 若标题、适用场景、`tags`、`related` 任一变化，对应更新 INDEX.md 的表行；并视影响更新 Checklist 两节。
4. 同步更新 `INDEX.md` 自身的 `updated_at`。

### Step 5 Review 闭环（三态）

输出 diff 摘要 + 文件路径，邀请用户回复以下三态之一：

- `confirm`：保留改动，输出最终摘要。
- `change <说明>`：根据说明再改一轮。
- `cancel`：撤回本轮所有改动（删除新建文件 / `git checkout` 还原修改），并报告已回滚。

## 模板与示例

模板位于本 skill 的 `assets/`，是唯一事实源（不在 SKILL.md 内嵌完整模板）：

- `assets/spec-template.md` — `doc_type: spec` 模板（实施契约）。
- `assets/guide-template.md` — `doc_type: guide` 模板（思考清单）。
- `assets/INDEX.md` — 索引种子文件。
- `assets/examples/redis.md` — `spec` 类型完整示例。
- `assets/examples/error-handling.md` — `guide` 类型完整示例。

每份产物的章节骨架（必含）：

- `spec`：`# <主题> 使用规范` → `## 原则` → `## 规约` → `## 示例`（可选）。
- `guide`：`# <主题> 思考清单` → `## 写代码前先想` → `## 写完后核对` → `## 相关 spec`。

## INDEX.md 结构

详见 `assets/INDEX.md`。INDEX.md 既是规范目录，也是 sibling skill 的消费入口，必含以下三节：

1. `## Pre-Development Checklist` — 写代码前应读的 spec（按场景）。
2. `## Quality Check` — 提交前应核对的 spec（按场景）。
3. `## coding/` — 完整规范表，列：文件 / doc_type / 主题 / 适用场景 / status / tags / 更新时间。

## How specs are consumed

`.docs/spec/coding/` 是 sibling 的 feature spec workflow 的共享知识层。各 sibling 应在以下时机读取：

- `coding-requirement-intake` 收集需求时：可选读 INDEX 的 `Pre-Development Checklist`，把相关规约作为非功能需求引用。
- `coding-technical-design` 设计阶段开始：必读 INDEX 的 `Pre-Development Checklist` 中匹配场景的条目。
- `coding-implementation-execution` 实施前：必读匹配条目；实施后：必读 `Quality Check` 对应条目。

以上是文档级约定，不强制 sibling 改动；sibling 已通过 CLAUDE.md 约定优先读 `.docs/`。

## Safety policy

- 不删除已有规范文档，除非用户明确许可。
- 不修改规范文档中用户已确认的内容，除非用户要求更新；遇冲突走 Step 2 的“冲突解决”路径。
- 文档用中文写，保留 technical English names。
- INDEX.md frontmatter 损坏时只报告不擅改。

## 输出

完成后输出：

- 操作类型（新建 / 补充）。
- 文件路径列表。
- 规范内容 diff 摘要。
- INDEX.md 是否更新（含 Checklist 两节是否变动）。
- 邀请用户回复 `confirm` / `change <说明>` / `cancel`。
