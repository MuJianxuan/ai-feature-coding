# ship-design 技术方案参考模板机制设计

## 0. 结论

应该加。当前 `new-skills/ship-design/` 已经要求产出 `design.md`，但只有固定骨架和结构校验，没有“参考模板选择、引用、偏离说明、模板覆盖校验”这条链路。结果就是：AI 很容易按自己的习惯临场发挥，今天写 API，明天写架构图，后天漏掉幂等和回滚。

但不能加成一个新阶段，更不能搞模板 DSL。那是把新 ShipKit 从 4 阶段又拖回旧 ShipKit 的复杂泥坑。

**推荐方案：在 Design 阶段内增加轻量级 `Design Reference Template` 机制。**

核心规则：

1. 模板是 **参考清单 + 必填项定义**，不是替代需求、spec、AC 的硬编码文档。
2. `ship-design` 负责选择和应用模板；`ship-orchestrator` 只传递/记录选择结果；`ship-spec` 仍只管项目规范。
3. `meta.yml` 保存模板机器事实，`design.md` 正文记录模板引用、选择理由和偏离项。
4. `validate_design.py` 做结构校验，不做重语义判断。
5. `ship-grill-me` 审查模板是否选错、漏项是否无理由、偏离是否会导致实现返工。
6. `quick_start` 允许轻量模板；`full_flow` / `prd_direct` / `split_first` 子 feature 必须显式记录模板引用。

---

## 1. 现状证据

### 1.1 ship-design 当前职责

`new-skills/ship-design/SKILL.md` 当前定义：

- 输入：`requirements.md(status: ready)`、`meta.yml.scenario/spec_refs`、Design 阶段 spec、现有代码结构。
- 流程：校验 requirements → 加载 spec → 必要调研 → 生成 `design.md` → grill-me 审查 → validate design → 等用户确认进入 Build。
- 输出结构：AC 覆盖映射、API 契约、数据模型、前端设计、后端设计、性能、风险回滚。

这套结构是必要底盘，但不是“技术方案参考模板机制”。它只规定了要写什么大类，没有规定不同技术场景下必须追问什么、不能漏什么、偏离模板如何解释。

### 1.2 当前模板只是固定骨架

`new-skills/ship-orchestrator/templates/design.md.template` 只有一个通用骨架：

- `## AC 覆盖映射`
- `## API 契约`
- `## 数据模型`
- `## 前端设计`
- `## 后端设计`
- `## 性能考量`
- `## 风险和回滚`

它无法区分：

- 纯后端 API
- 纯前端页面
- 全栈功能
- MQ / 异步任务
- 数据迁移 / 回填
- 第三方系统集成
- 配置 / 权限 / 灰度类改动

这些场景漏掉的关键项完全不同。用一个骨架糊所有场景，必然让 AI 靠猜。

### 1.3 validate_design.py 当前只做基础完整性检查

`new-skills/ship-orchestrator/scripts/validate_design.py` 当前检查：

- API 章节是否有 Request / Response / Error。
- 数据模型是否存在或明确不涉及。
- 前端/后端章节是否存在。
- AC 是否都在设计中出现。
- spec_refs 是否存在（无 spec 仅 warning）。
- 性能章节是否存在（缺失 warning）。

它不检查：

- 是否引用了参考模板。
- 模板是否匹配需求类型。
- 模板要求的专项内容是否存在。
- 偏离模板是否有理由。
- ready 状态下是否仍有 `{占位符}`、`TBD`、未决问题。

### 1.4 已存在 `.docs/技术方案模版.md`

仓库已有 `.docs/技术方案模版.md`，内容更像企业后端技术方案模板，覆盖：

- 前言、修订历史、词汇表。
- 项目背景、总体设计、系统边界。
- MQ 变更设计。
- 方案设计、存储设计、接口设计。
- 部署、风险、依赖、Q&A。

这个文件有价值，但不能直接硬套到所有 `ship-design` 产物。纯前端小改也强迫写 MQ 和 SQL，只会制造垃圾文档。

正确用法：把它纳入 `backend-heavy / enterprise-backend` 参考模板，作为项目级模板源之一，而不是全局唯一模板。

---

## 2. 设计目标

### 2.1 要解决的真问题

用户真正要的是：**让 AI 在写技术方案时有工程约束，不要自由发挥，也不要漏掉关键设计项。**

这不是“多写一份模板文档”的问题，而是要建立一条可执行链路：

```text
用户需求 / requirements.md
    ↓
识别技术场景
    ↓
选择参考模板
    ↓
按模板生成 design.md
    ↓
记录模板引用和偏离
    ↓
grill-me 审查关键遗漏
    ↓
validate_design.py 做结构校验
    ↓
用户确认后进入 Build
```

### 2.2 不破坏现有 ShipKit 简洁性

必须保留新 ShipKit 的核心原则：

- 仍然是 `[Split] → Understand → Design → Build`。
- 不新增 `template` 阶段。
- 不新增用户确认门禁。
- `meta.yml` 仍是单一事实源。
- validator 仍是 3 个核心 validator，不新增第四个核心 validator。
- `Design → Build` 仍是唯一硬用户确认门禁。

---

## 3. 总体架构

### 3.1 角色分工

| 模块 | 职责 | 不做什么 |
|---|---|---|
| `ship-orchestrator` | 只识别用户是否有“显式模板意图”，原样记录为 `requested_design_template`，然后路由到 Design | 不解析模板 ID，不判断模板是否存在，不自动选择模板，不生成技术方案 |
| `ship-design` | 读取 `requested_design_template`；解析/选择模板；写入 `meta.yml.design_template_ref/reason`；按模板生成 `design.md`；记录引用、理由、偏离 | 不绕过 AC/spec，不在确认前写业务代码 |
| `ship-spec` | 加载项目规范、技术栈、API 标准、前端/后端模式 | 不把模板当项目规范，不污染 `.docs/spec` |
| `ship-grill-me` | 审查模板选择、漏项、偏离、技术风险；维护 Design 内部审查循环 | 不把非阻塞格式偏好升级成硬门禁 |
| `validate_design.py` | 读取 `meta.yml` 的模板事实；校验模板引用、必填章节、偏离格式、无未填占位符 | 不做复杂语义推理，不判断架构优劣 |

### 3.2 模板来源分层

推荐三层来源，优先级从高到低：

```text
用户显式指定模板
    ↓
项目级模板
    ↓
ShipKit 内置模板
```

#### A. 用户显式指定模板

例：

```text
按 .docs/技术方案模版.md 写这个设计
按后端技术方案模板生成
这个是 MQ 异步任务，按异步任务模板走
```

处理：`ship-orchestrator` 只把原文意图记为 `requested_design_template`；`ship-design` 负责解析成实际 `design_template_ref`。

#### B. 项目级模板

推荐目录：

```text
.docs/ship/design-templates/
├── INDEX.md
├── backend-enterprise.md
├── frontend-page.md
├── async-task.md
└── integration.md
```

兼容当前已有文件：

```text
.docs/技术方案模版.md
```

该文件可作为默认项目级 `backend-enterprise` 模板候选，但只有命中后端/全栈/MQ 场景时才使用。

#### C. ShipKit 内置模板

推荐目录：

```text
new-skills/ship-orchestrator/templates/design-reference/
├── INDEX.md
├── backend-service.md
├── frontend-ui.md
├── fullstack-feature.md
├── async-task.md
├── data-migration.md
├── integration.md
└── config-change.md
```

这些是流程内置模板，不是业务知识，不应放进 `.docs/spec/`。

---

## 4. 模板分类与选择规则

### 4.1 模板 ID

| 模板 ID | 适用场景 | 必须重点检查 |
|---|---|---|
| `backend-service` | API、服务层、权限、业务规则，无明显 UI | API contract、错误码、权限、事务、幂等、数据模型 |
| `frontend-ui` | 页面、组件、交互、状态管理，无后端变更 | 页面状态、交互流、校验、错误展示、可访问性、埋点 |
| `fullstack-feature` | 同时涉及 UI + API + 数据 | 前后端边界、接口契约、状态同步、端到端 AC 覆盖 |
| `async-task` | MQ、定时任务、批处理、重试、长耗时任务 | 触发条件、幂等、重试、死信、补偿、可观测性 |
| `data-migration` | 表结构、数据迁移、回填、清洗 | 迁移脚本、回滚、数据校验、灰度、锁表风险 |
| `integration` | 第三方 API、Webhook、外部系统 | 鉴权、超时、重试、限流、降级、签名验证 |
| `config-change` | 配置、灰度、开关、权限矩阵 | 默认值、回滚、兼容性、灰度范围、审计 |
| `backend-enterprise` | 企业后端方案，尤其需要 MQ/存储/部署章节 | 可复用 `.docs/技术方案模版.md` 的结构 |

### 4.2 自动选择规则

`ship-design` 使用最小可执行 resolver，不靠一句“我觉得”：

```text
1. 用户显式指定模板：优先使用；解析不到或文件不存在则 blocking。
2. 项目级模板命中：优先于 builtin。
3. builtin 模板评分：
   - 用户原文关键词命中：+3
   - AC / NFR 命中：+2
   - spec / 现有代码路径命中：+1
   - 明确“不涉及”信号：-3
4. 最高分为 primary template。
5. 分数差 <= 1 的候选作为 secondary checklist，最多 2 个。
6. 最高分 < 3：quick_start 可不使用模板；full_flow / prd_direct / split_first 子 feature 默认 `builtin:fullstack-feature@1`，记录低置信度原因，必要时触发 grill-me。
```

推荐优先级只作为同分 tie-breaker：

```text
async-task > integration > data-migration > fullstack-feature > backend-service / frontend-ui > config-change
```

原因：异步任务、第三方集成、数据迁移的失败成本更高，漏项也更隐蔽，优先用专项模板。

### 4.3 冲突处理

多模板命中时，不要把所有模板拼成怪物文档。选择一个主模板，其他模板作为专项 checklist。

示例：

```yaml
primary_template: async-task@1
secondary_checklists:
  - backend-service@1
reason: "AC-2 涉及订单状态变更后投递 MQ，并由消费者异步生成报表"
```

`design.md` 顶层结构始终保持 ShipKit 基础骨架；主模板只决定哪些专项小节和 checklist 必须补进对应基础章节。

---

## 5. meta.yml 设计

`meta.yml` 保存机器事实，`design.md` 正文保存人类可读说明。不要把同一事实同时塞进 `meta.yml` 和 `design.md` frontmatter，双写就是制造状态不一致。

推荐字段：

```yaml
requested_design_template: "按 .docs/技术方案模版.md 写" # 可选，来自用户原话或入口识别
design_template_ref: "builtin:fullstack-feature@1"
design_template_reason: "AC-1 涉及登录页，AC-2 涉及 POST /auth/login 和 users/sessions 表"
```

项目模板示例：

```yaml
requested_design_template: ".docs/技术方案模版.md"
design_template_ref: "project:.docs/技术方案模版.md#backend-enterprise@1"
design_template_reason: "需求涉及后端服务、MQ、存储和部署评审，需要企业后端技术方案结构"
```

规则：

- `requested_design_template` 是用户意图原文，可为空。
- `design_template_ref` 是解析后的唯一机器事实。
- `design_template_reason` 是简短选择依据。
- `design.md` frontmatter 不再重复这些字段；正文 `## 方案模板引用` 必须与 `meta.yml.design_template_ref` 一致。
- 当前 parser 是 loose YAML，保持简单字符串最稳；不要把模板内容、嵌套对象、长 checklist 塞进 `meta.yml`。

---

## 6. design.md 输出结构

### 6.1 必须保留的 ShipKit 基础结构

不管是否使用参考模板，`design.md` 都必须保留稳定基础章节；唯一降级是 quick_start 缺少 `## 方案模板引用` 时只给 warning：

```markdown
## 方案模板引用
## AC 覆盖映射
## API 契约
## 数据模型
## 前端设计
## 后端设计
## 性能考量
## 风险和回滚
```

纯前端/纯后端可以写“不涉及”，但不能删除基础章节。删除章节会让 validator 和后续 Build 任务提取失去稳定锚点。

### 6.2 推荐 frontmatter

`design.md` frontmatter 只保存文档自身状态和 spec 引用，不保存模板机器事实：

```yaml
---
status: ready
updated_at: "2026-06-10T12:00:00Z"
spec_refs: ["rest-api-standard", "react-patterns"]
---
```

模板事实来自 `meta.yml.design_template_ref`；正文 `## 方案模板引用` 用于给人读，并接受 validator 一致性检查。

### 6.3 `方案模板引用` 章节

full_flow / prd_direct / split_first 子 feature 必须写清楚：

```markdown
## 方案模板引用

- 主模板：`builtin:fullstack-feature@1`
- 选择依据：AC-1 涉及 `/login` 页面；AC-2 涉及 `POST /api/v1/auth/login`；AC-3 涉及 sessions 表。
- 候选模板：`async-task(score=1)`、`backend-service(score=5)`、`fullstack-feature(score=8)`
- 未选原因：`backend-service` 仅作为辅助 checklist，因为本需求同时涉及 UI 状态。
- 项目 spec 优先级：当模板与 `rest-api-standard` 冲突时，以 spec 为准。

### 模板偏离

| 偏离项 | 原因 | 影响 | 替代设计 |
|---|---|---|---|
| 不新增 Session 表 | 当前系统使用 Redis session，spec 禁止持久化 token | 减少 DB 迁移；依赖 Redis HA | 在 Redis 中设置 TTL，并在风险章节记录 Redis 故障降级 |
```

quick_start 如果不使用模板，允许降级为：

```markdown
## 方案模板引用

- 主模板：未使用
- 原因：quick_start / 低风险 / 不涉及跨模块设计
- 已检查：API 契约、数据模型、前后端边界无新增复杂点
```

偏离项不是坏事。坏的是偷偷偏离，让 Build 阶段猜。

### 6.4 ready 状态禁止内容

`status: ready` 的 `design.md` 不允许出现：

- `{{PLACEHOLDER}}`
- `{功能名称}` 这类模板变量
- `TBD`
- `待补充`
- `后续再说`
- 没有解释的“视情况而定”

如果确实未知，就不能 ready；应该进入 `ship-grill-me` 或记录为明确风险/依赖，并说明为什么不阻塞。

---

## 7. 内置模板规格

每个模板文件不用很长，只定义：

1. 适用场景。
2. 必填章节。
3. 专项 checklist。
4. 常见反模式。
5. 输出片段示例。

### 7.1 模板索引和模板文件示例

不要用复杂嵌套 YAML。当前 validator 的 parser 很轻，只适合顶层 key/value 和一行数组。模板索引用 Markdown 表即可，模板自身用简单 frontmatter。

`design-reference/INDEX.md`：

```markdown
| id | file | priority | 说明 |
|---|---:|---:|---|
| backend-service | backend-service.md | 50 | API / 服务层 / 权限 / 数据模型 |
| frontend-ui | frontend-ui.md | 40 | 页面 / 组件 / 状态管理 |
| fullstack-feature | fullstack-feature.md | 60 | UI + API + 数据 |
| async-task | async-task.md | 90 | MQ / 定时 / 批处理 / 重试 |
```

`async-task.md`：

```markdown
---
id: async-task
version: 1
priority: 90
triggers: ["mq", "queue", "cron", "schedule", "batch", "retry", "dead-letter", "异步", "定时", "批处理"]
required_sections: ["方案模板引用", "AC 覆盖映射", "API 契约", "数据模型", "前端设计", "后端设计", "性能考量", "风险和回滚"]
required_subsections: ["后端设计/触发与调度", "后端设计/幂等设计", "后端设计/重试与失败处理", "后端设计/可观测性"]
review_checklist: ["idempotency_key", "retry_policy", "failure_compensation", "monitoring_alert"]
---

# async-task

## 适用场景
MQ、定时任务、批处理、重试、死信、长耗时任务。

## 输出要求
专项内容写进稳定基础章节，不能替代顶层 `design.md` 骨架。
```

规则：

- `required_sections` 是 validator 检查的顶层章节。
- `required_subsections` 可以做轻量字符串检查；复杂语义不在 validator 做。
- `review_checklist` 只给 `ship-grill-me` 审查，不给 validator 当硬规则。

### 7.2 backend-service 模板要点

必须回答：

- API path/method/request/response/error。
- 鉴权和权限边界。
- Service/Repository 分层。
- 事务边界。
- 错误码和异常映射。
- 数据模型/索引/唯一约束。
- 幂等要求：不需要也要说明为什么。
- 回滚方案。

### 7.3 frontend-ui 模板要点

必须回答：

- 页面/组件树。
- 用户交互流。
- 状态管理归属。
- 表单校验和错误展示。
- loading/empty/error 状态。
- 权限态/不可用态。
- 可访问性和响应式要求。
- 与 API 的契约边界。

### 7.4 async-task 模板要点

必须回答：

- 触发条件：事件、定时、手动、补偿。
- 消息体结构。
- 幂等 key。
- 重试策略：次数、间隔、是否指数退避。
- 死信/失败队列。
- 消费并发和顺序性。
- 补偿机制。
- 监控指标和告警。
- 回滚和重放策略。

### 7.5 data-migration 模板要点

必须回答：

- schema 变更。
- 数据回填范围。
- 是否在线迁移。
- 锁表/性能风险。
- 校验 SQL / 校验脚本。
- 回滚策略。
- 灰度和分批。
- 与旧代码兼容窗口。

### 7.6 integration 模板要点

必须回答：

- 第三方系统边界。
- 鉴权方式。
- 请求签名/验签。
- 超时、重试、限流。
- 幂等和重复回调。
- 降级策略。
- 敏感信息处理。
- 沙箱/生产环境差异。

---

## 8. validate_design.py 增强方案

### 8.1 新增检查

在现有 `validate_design.py` 内增强，不新增 validator。

| 检查 | 类型 | 规则 |
|---|---|---|
| 模板引用 | error/warning | `full_flow` / `prd_direct` / `split_first` 子 feature 必须在 `meta.yml` 有 `design_template_ref`；`quick_start` 缺失只 warning |
| 模板存在性 | error | `builtin:*` 必须存在于 `design-reference/INDEX.md`；`project:*` 路径必须存在 |
| 正文引用一致性 | error/warning | 非 quick_start 必须有 `## 方案模板引用`，且主模板与 `meta.yml.design_template_ref` 一致；quick_start 缺章节只 warning |
| 必填顶层章节 | error | 固定 ShipKit 基础章节必须存在；模板不能替代顶层骨架 |
| 必填子章节 | error/warning | `required_subsections` 做轻量字符串检查；允许“不涉及 + 原因” |
| 偏离格式 | error | 有“偏离”但没有原因/影响/替代设计，不能 ready |
| 未填占位符 | error | `status: ready` 下不得出现 `{{`、`}}`、`{功能名称}`、`TBD`、`待补充` |
| spec 优先声明 | warning | 有模板但没说明模板与 spec 冲突时 spec 优先 |

### 8.2 不做的检查

不要让 validator 做这些事：

- 判断架构好坏。
- 自动推断模板是否选得“最优”。
- 判断 `review_checklist` 是否语义满足，例如“事务边界是否合理”“幂等 key 是否正确”。
- 检查每个流程图是否正确。
- 强制所有设计都有修订历史、词汇表、部署章节。

validator 是门框，不是架构师。语义审查交给 `ship-grill-me` 和用户确认。

---

## 9. ship-grill-me 审查增强

Design 阶段新增 blocking 判定：

| 问题 | 是否阻塞 | 处理 |
|---|---|---|
| 模板选择明显不匹配 | blocking | 自动改正或问用户 |
| 模板必填项缺失且无偏离说明 | blocking | 补齐或记录偏离 |
| 偏离项目 spec | blocking | 必须解释，必要时改设计 |
| 存在未决模板变量/TBD | blocking | 不能 ready |
| 模板要求项与需求无关 | non-blocking | 可记录“不涉及”，不问用户 |

提问格式沿用现有 `ship-grill-me` 规则：一次只问一个会影响实现的问题。

示例：

```text
问题 1/2：异步任务幂等策略
当前阻塞：需求包含 MQ 消费，但 design.md 未定义幂等 key。重复消费会导致订单状态被重复推进。
已检查证据：async-task@1 要求定义 idempotency_key；现有 spec 未提供统一规则。
推荐答案：使用 order_id + event_type + event_version 作为幂等 key，写入 processed_events 表。
影响：不确认该策略，Build 阶段无法安全实现消费者。

你的决定？
[采纳推荐] / [自定义答案]
```

### 9.1 Design 内部审查循环

这不是新增阶段，也不是新增用户门禁；它只是 Design 阶段内部的质量循环：

```text
生成 design draft
  ↓
validate_design.py
  ↓
ship-grill-me adversarial review
  ↓
修复 design.md
  ↓
重新 validate_design.py
  ↓
仍有 blocking？继续循环
  ↓
无 blocking + validator 无 error
  ↓
status: ready，等待用户确认进入 Build
```

`design.md` 建议记录审查摘要：

```markdown
## 设计审查记录

| Round | Reviewer | Blocking findings | 处理结果 |
|---|---|---:|---|
| 1 | ship-grill-me | 2 | 已补幂等 key、补错误码映射 |
| 2 | ship-grill-me | 0 | ready |
```

没有 blocking 且 validator 无 error，才允许 `status: ready`。warning 可以进入风险章节，但不能假装不存在。

---

## 10. 与 `.docs/技术方案模版.md` 的关系

这个文件不应该被丢弃，也不应该全局硬套。

推荐处理：

1. 保留原文件作为项目已有模板。
2. 不直接原样套用，而是通过 `backend-enterprise adapter` 使用：

```text
project:.docs/技术方案模版.md#backend-enterprise@1
```

3. 优先级规则：

```text
ShipKit ready 规则 > 项目模板占位规则。
项目模板可以作为结构参考，但不得把 TBD 占位符带入 status: ready 的 design.md。
```

4. draft 阶段允许按原模板保留 `TBD`；ready 前必须处理为三选一：

- 明确值。
- `不涉及 + 原因`。
- `外部依赖/待决策 + 是否阻塞`；如果阻塞，则不能 ready。

5. 只有以下场景默认使用它：

- 后端服务设计需要正式评审。
- 涉及 MQ / 存储 / 部署 / 依赖方。
- 用户明确要求“按技术方案模板”。

6. 使用时要裁剪：

- “修订历史”“词汇表”无输入时可写“不涉及/无新增术语”，不要编造。
- “MQ 变更设计”无 MQ 时写“不涉及”，不要硬造 topic。
- “部署设计”无部署变化时写“不涉及部署变更”。
- “Q&A”没有真实问题时写“暂无”，不要凑内容。

这叫参考模板，不叫文档填空游戏。

---

## 11. 实施方案

### Phase 1：只改指令和文档，先把行为钉住

修改：

- `new-skills/ship-design/SKILL.md`
  - 增加“模板选择与引用”流程。
  - 增加 `design.md` 的 `方案模板引用` 章节要求。
  - 增加 ready 禁止占位符规则。

- `new-skills/ship-grill-me/SKILL.md`
  - 增加 Design 模板审查 blocking 项。

- `new-skills/ship-spec/SKILL.md`
  - 明确模板不是 spec；冲突时 spec 优先。

- `new-skills/ship-orchestrator/SKILL.md`
  - 明确只记录/传递用户显式模板意图，不解析模板。

验收：人工读 `SKILL.md` 能明确知道模板机制怎么触发、怎么记录、怎么审查。

### Phase 2：增加内置参考模板

新增：

```text
new-skills/ship-orchestrator/templates/design-reference/
├── INDEX.md
├── backend-service.md
├── frontend-ui.md
├── fullstack-feature.md
├── async-task.md
├── data-migration.md
├── integration.md
└── config-change.md
```

验收：每个模板都有适用场景、必填章节、checklist、反模式。

### Phase 3：增强 validate_design.py

修改：

- `new-skills/ship-orchestrator/scripts/validate_design.py`

新增测试：

- valid design with template passes。
- full_flow 缺模板引用失败。
- template id 不存在失败。
- 非 quick_start 缺 `方案模板引用` 失败。
- ready 状态含 `TBD` 失败。
- async-task 缺必填子章节失败或 warning（取决于是否明确“不涉及 + 原因”）。
- quick_start 缺模板只 warning。

验收：`python3 new-skills/ship-orchestrator/tests/test_validators.py` 通过。

### Phase 4：更新验收清单

修改：

- `new-skills/ACCEPTANCE.md`
- `new-skills/MANIFEST.yml`
- `new-skills/README.md`

把模板机制纳入交付证据，而不是靠口头承诺。

---

## 12. 示例：fullstack-feature 输出片段

```markdown
---
status: ready
updated_at: "2026-06-10T12:00:00Z"
spec_refs: ["rest-api-standard", "react-patterns", "mysql-conventions"]
---

# 技术设计：用户登录

## 方案模板引用

- 主模板：`builtin:fullstack-feature@1`（来自 `meta.yml.design_template_ref`）
- 选择依据：本需求同时修改前端页面、后端 API 和会话数据模型。
- 候选模板：`backend-service(score=5)`、`fullstack-feature(score=8)`
- 项目 spec 优先级：模板与 spec 冲突时，以 `rest-api-standard` 和 `react-patterns` 为准。

### 模板偏离

| 偏离项 | 原因 | 影响 | 替代设计 |
|---|---|---|---|
| 不新增 Session 表 | 项目现有 spec 使用 Redis 保存 session | 无 DB migration；依赖 Redis TTL | 在风险章节记录 Redis 不可用时登录失败 |

## AC 覆盖映射
| AC | 设计位置 | 测试建议 |
|---|---|---|
| AC-1 | 前端设计 /login | e2e 登录成功 |
| AC-2 | API 契约 POST /auth/login | integration 登录失败 |
| AC-3 | 后端设计 AuthService | unit token 过期 |

## API 契约
...
```

---

## 13. 对抗式审查

### Round 1：复杂度审查

**攻击：** 你又在加目录、加字段、加模板分类，会不会把新 ShipKit 搞回旧 ShipKit 的 14 阶段复杂度？

**修正：** 不新增阶段，不新增 validator，不新增用户门禁。模板机制只嵌入 Design 阶段；`meta.yml` 只加少量字符串事实字段。模板文件是 checklist，不是流程状态机。

### Round 2：AI 仍可随意发挥

**攻击：** 只写模板引用，AI 还是能胡写，甚至随便选一个模板糊弄。

**修正：** 三道约束叠加：

1. `design.md` 必须写选择依据。
2. `validate_design.py` 校验模板存在、章节存在、占位符清零。
3. `ship-grill-me` 把明显错选、漏项、无理由偏离视为 blocking。

这比单纯“请按模板写”强得多。

### Round 3：模板可能压过项目 spec

**攻击：** 模板里说要 `created_at bigint`，项目 spec 说用 `timestamp with timezone`，AI 该听谁？

**修正：** 明确优先级：`requirements/AC > 项目 spec > 现有代码事实 > 参考模板 > AI 默认习惯`。模板只能补漏，不能推翻项目规范。

### Round 4：`.docs/技术方案模版.md` 怎么办

**攻击：** 已有模板如果不用，就是浪费；如果全局硬套，就是垃圾。

**修正：** 把它作为项目级 `backend-enterprise` 候选模板。后端/MQ/存储/部署评审场景用；纯前端/小改不硬套。无关章节写“不涉及”，不得编造。

### Round 5：validator 误杀

**攻击：** validator 如果强制所有模板章节，quick_start 会被形式主义卡死。

**修正：** quick_start 缺模板只 warning；full_flow/prd_direct 才强模板引用。模板必填项也应允许“不涉及 + 原因”，而不是逼 AI 硬造内容。

### Round 6：安全与敏感信息

**攻击：** 技术方案模板可能诱导 AI 写生产地址、token、内部账号。

**修正：** `ship-spec` 已禁止敏感信息进入 spec；模板也要加入反模式：不写密码、token、生产密钥、内部部署地址明文。第三方集成只写 secret 来源，例如“从环境变量读取”，不写值。

### Round 7：真实对抗审查后的修正

**攻击：** 初稿有四个硬伤：`meta.yml` 和 `design.md` frontmatter 双写模板事实；`.docs/技术方案模版.md` 要求 `TBD` 与 ready 禁止 `TBD` 冲突；validator 试图做语义审查；async-task 模板顶层章节会破坏稳定 `design.md` 骨架。

**修正：** 本版已调整：模板机器事实只放 `meta.yml`，`design.md` 正文仅做人类可读引用；项目模板通过 adapter 使用，ready 规则优先；validator 只查结构和占位符，`review_checklist` 交给 `ship-grill-me`；模板专项内容只能作为基础章节内的小节，不能替代顶层骨架。

---

## 14. 最终推荐

采用这个方案。

它解决了用户的核心担忧：**AI 写设计不能再凭感觉编结构，必须先选模板、说明理由、按模板补齐关键项、对偏离负责。**

它也没有破坏新 ShipKit 的好设计：

- 不增加阶段。
- 不增加硬门禁。
- 不把 spec 和 template 混成一锅粥。
- 不强迫所有需求写同一份臃肿文档。
- 不让 validator 假装自己是架构师。

一句话：

> 把模板变成 Design 阶段的“护栏”，不是变成新的“官僚流程”。
