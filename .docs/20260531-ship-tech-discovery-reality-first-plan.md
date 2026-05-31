# ShipKit 技术发现与 Spec 工作流完善实施计划

## 1. 背景复盘

本次讨论聚焦 `skills` 套件中 `ship-tech-discovery` 与 `ship-spec` 的工作流痛点。当前 workflow 已经具备完整阶段链路：

```text
[Discover ->] Define -> Design -> Build -> Close

内部阶段：
[ship-discover -> ship-shape ->]
ship-define -> ship-define-review
-> ship-tech-discovery
-> ship-contract -> ship-frontend-design -> ship-backend-design
-> ship-design-review
-> ship-delivery-plan -> ship-plan-review
-> ship-build -> ship-verify -> ship-handoff
```

现有设计里，`ship-tech-discovery` 名义上是“技术发现”，但实际核心更偏向：

- 外部技术调研；
- 框架 / 库 / 版本信息核查；
- 技术选型；
- ADR 决策；
- `ship-spec` compatibility check。

这对 0-1 项目或确实引入新技术的需求有价值，但对“已有项目上的新需求 / 迭代需求”不够贴近真实开发过程。

用户明确指出：在已有项目上开发新需求时，最重要的不是先做技术选型，而是先探索当前项目里和需求相关的真实功能、真实表、真实接口、真实页面、真实服务与现有链路。比如新需求围绕用户信息展开时，必须先确认现有用户信息功能、表结构、API、前端页面、权限和业务语义是否已经存在，以及本次需求到底是复用、扩展、替换还是新增。

因此，本次方案的核心不是新增复杂流程，而是重排 `ship-tech-discovery` 的优先级：

```text
已有项目事实发现 > 需求与现有系统关联映射 > 产出前用户对齐 > 技术调研 / 技术选型
```

## 2. 已确认的用户意图

### 2.1 Tech Discovery 的重心调整

已确认：

- 同意把 `ship-tech-discovery` 从“技术调研/选型优先”调整为“已有项目事实发现优先”。
- 对已有项目，必须先发现当前项目真实情况，再谈技术方案。
- 技术调研和技术选型仍保留，但它们不是已有项目迭代的第一优先级。

目标表达：

```text
ship-tech-discovery 需要先回答：
1. 当前需求和已有功能有什么关系？
2. 已有项目里哪些代码、表、API、页面、服务、worker、MQ topic 与本需求相关？
3. 哪些可以复用？哪些需要扩展？哪些不能动？哪些存在语义不确定？
4. 哪些发现已经有证据？哪些需要用户纠正或确认？
```

### 2.2 产物位置

已确认：

- 不新增 `project-discovery.md`。
- 继续使用现有 `tech-research.md`。
- 在 `tech-research.md` 中新增强制章节来承载项目事实发现。

原因：

- 不增加新的 canonical stage；
- 不增加新的产物心智负担；
- 保持 `ship-tech-discovery` 的双产物结构：`tech-research.md` + `tech-selection.md`；
- 让后续 `tech-selection.md`、`api-contract.md`、`frontend-design.md`、`backend-design.md` 都能继续读取同一个 research 事实源。

### 2.3 Spec 组织方式

已确认：

- 不引入 `spec_type` / `discipline` 等新的 schema 层级。
- 不新增过多概念。
- 只保留 `.docs/spec/INDEX.md` 一个总索引。
- 通过 `INDEX.md` 表格列出 frontend / backend 分类。
- agent 在当前需求和当前阶段下，先读 `INDEX.md`，再决定要读取哪些 spec 文件。

用户不接受的方向：

- 不采用 `.docs/spec/frontend/INDEX.md` + `.docs/spec/backend/INDEX.md` 多索引。
- 不在 spec frontmatter 增加 `spec_type: frontend|backend|...`。
- 暂不设计 contract / data / integration / verification 等多层级 spec 模型。

当前阶段的目标是保持简单：

```text
.docs/spec/INDEX.md 是唯一人工路由入口。
INDEX.md 表格中区分 frontend / backend。
backend 可以覆盖 Redis、MQ、接口方法、DB、Service 写法等规范。
frontend 可以覆盖组件、路由、状态管理、API client、UI 交互等规范。
```

### 2.4 Research Alignment Check 的性质

已确认：

- “产出前对齐”不是 hard gate。
- 不新增 `review-tech-research.md`。
- 不增加 `review_status / user_sign_off / signed_at`。
- 不改变 canonical stage。
- 它是 `ship-tech-discovery` research 子段内部的过程动作。

目标：

```text
在写出有价值的 tech-research.md 之前，
agent 必须向用户总结项目发现和理解，
让用户纠正明显错误或补充关键事实。
```

如果用户纠正：

- 不能只改文案；
- 必须回到相关代码路径重新探索；
- 更新证据和发现；
- 再产出或更新 `tech-research.md`。

如果用户明确说“先按假设继续”：

- 可以继续；
- 但必须在 `tech-research.md` 中记录 assumptions、风险和影响范围；
- 不得把假设伪装成已确认事实。

## 3. 当前 workflow 的真实冲突点

### 3.1 `ship-tech-discovery` 目前过度偏向外部技术调研

当前 `ship-tech-discovery/SKILL.md` 的核心原则是：

- `Source-Driven`；
- `Decision-Backed`；
- `Sequential Within Stage`。

当前 Process 是：

```text
读取 requirements.md
-> 执行 research 子段
-> 读取 tech-research.md + requirements.md
-> 执行 selection 子段
-> 交叉校验 research -> selection
-> 标记两个产物 ready
```

当前 research 子段要求：

- 从 requirements.md 提取调研点；
- 优先使用官方文档、release notes、官方 repo、registry；
- 输出对比矩阵、健康度信号、与非功能需求匹配度。

问题：

- 它没有把“已有项目真实功能和代码链路发现”作为 P0；
- 它默认 research 主要是技术资料来源，不是项目事实来源；
- 对已有项目迭代，可能产出一份技术调研充分但项目理解错误的 `tech-research.md`。

### 3.2 `ship-discover` 的 evolve 分支有现状扫描，但覆盖不够

`ship-discover` 的 evolve 分支已经有“现状扫描”：

- 读取已有 feature 目录；
- 读取相关代码文件；
- 读取过往 handoff 风险；
- 输出现状摘要；
- 做影响分析。

但它只在场景 C 激活。

场景 B / D 如果用户提供了完整 PRD / 原型 / 设计稿，会跳过 Discover，直接进入 Define。这样会出现一个漏洞：

```text
需求其实是已有项目上的迭代，
但因为用户提供了 PRD，
workflow 跳过 ship-discover，
后续又没有强制项目事实发现，
最终技术方案可能基于 PRD 想象，而不是基于真实代码。
```

因此不能只依赖 `ship-discover.evolve` 解决问题。`ship-tech-discovery` 必须承担 Design 阶段前统一的项目事实发现责任。

### 3.3 `ship-spec` 当前把 INDEX.md 定义为人工 registry

当前 `ship-spec` 文档写法是：

- `INDEX.md` 是 registry，面向人工浏览与目录维护；
- 运行时匹配事实源是每个 spec 文件的 frontmatter；
- 不是 `INDEX.md` 表格正文。

这和用户期望存在差异。

用户希望：

- 只保留 `.docs/spec/INDEX.md` 一个总索引；
- 通过表格标记 frontend / backend 分类；
- agent 先读 INDEX，再结合需求和阶段判断应使用哪个 spec。

因此需要调整文档语义：

- 不改变 `spec_runtime.py` 的基础扫描能力；
- 但 skill 行为上要求 agent 使用 `INDEX.md` 作为人工路由入口；
- runtime helper 仍可读取 frontmatter 做自动检查；
- `INDEX.md` 和 spec 文件 frontmatter 必须保持一致，否则产生 warning。

## 4. 目标设计

### 4.1 不改变的内容

本次不改变：

- 不新增 canonical stage；
- 不新增 hard gate；
- 不新增 `project-discovery.md`；
- 不新增 `review-tech-research.md`；
- 不新增 spec schema 层级字段；
- 不改变现有 14 个内部阶段；
- 不改变 `ship-tech-discovery` 的双产物结构；
- 不破坏 Warn Then Continue 的 spec 缺失策略。

### 4.2 改变的内容

本次改变：

- `ship-tech-discovery` 的 research 子段新增 Project Reality Scan。
- `tech-research.md` 新增强制章节。
- `ship-spec` 文档改成“单 INDEX 人工路由 + frontmatter/runtime 校验”的双层策略。
- `ship-frontend-design` / `ship-backend-design` 加强对 `tech-research.md` 的消费，不能只消费 `tech-selection.md`。
- validator 增加对 ready 状态下 `tech-research.md` 项目发现章节和 Research Alignment Check 的检查。
- regression tests 增加已有项目迭代场景。

## 5. `tech-research.md` 新章节设计

### 5.1 推荐章节

在 `tech-research.md` 中新增以下必备章节：

```markdown
## Project Reality Scan / 项目现状发现

## Requirement-to-Reality Mapping / 需求与已有系统映射

## Existing Surface Inventory / 现有表面清单

## Evidence and Uncertainty / 证据与不确定项

## Research Alignment Check / 产出前对齐记录

## Technical Research / 技术调研

## Selection Inputs / 给 tech-selection.md 的输入
```

说明：

- `Technical Research` 仍保留，用于外部技术信息、版本、框架、库、生态、官方文档等调研。
- 对已有项目，前五个章节优先级高于外部技术调研。
- 对新项目，`Project Reality Scan` 可明确写“不适用：new_project，无既有代码基线”，但不能完全消失。

### 5.2 Project Reality Scan

必须回答：

- 当前 target project 是什么？
- `project_context` 是 `existing_project`、`new_project` 还是 `unknown`？
- 本需求关联哪些已有业务域？
- 现有代码里是否已有相关功能？
- 现有 feature 文档里是否已有相同或相近功能？
- 现有 DB / ORM / migration 是否已有相关表或字段？
- 现有 API / route / RPC / message topic / cron / CLI 是否已有相关入口？
- 现有前端页面 / 组件 / store / API client 是否已有相关消费路径？
- 现有权限 / 角色 / 租户 / 审计 / 日志 / metrics 是否有约束？

### 5.3 Requirement-to-Reality Mapping

按 `requirements.md` 的 Domain ID / AC ID 建立映射。

推荐表格：

```markdown
| Domain / AC | 需求摘要 | 现有项目发现 | 关系类型 | 证据路径 | 不确定项 |
|---|---|---|---|---|---|
| D-USER-001 / AC-USER-001 | 用户可查看资料 | 已有 users 表和 user profile API | extend | src/modules/user/user.service.ts | profile 字段归属需确认 |
```

关系类型建议固定为：

- `reuse`：直接复用；
- `extend`：扩展已有功能；
- `replace`：替换旧实现；
- `new`：新增；
- `avoid`：明确不触碰；
- `unknown`：证据不足，需要用户确认。

### 5.4 Existing Surface Inventory

按层面梳理。

推荐表格：

```markdown
| Surface | Existing Item | Path / Source | Relation | Notes |
|---|---|---|---|---|
| DB | users | prisma/schema.prisma | extend | 已有 id/email/name |
| API | GET /api/users/:id | src/routes/user.ts | reuse | 当前返回字段不足 |
| Frontend | UserProfilePage | src/pages/user/Profile.tsx | extend | 已有展示，无编辑 |
| Backend Service | UserService | src/modules/user/user.service.ts | extend | 需要确认权限逻辑 |
| MQ | user.updated | src/events/user.ts | unknown | 是否需要发布事件待确认 |
```

Surface 类型建议包括：

- `DB`；
- `API`；
- `Frontend`；
- `Backend Service`；
- `Repository / DAO`；
- `Worker / MQ`；
- `Cron`；
- `Config`；
- `Auth / Permission`；
- `Observability`；
- `Test`；
- `Docs / Existing Feature`。

### 5.5 Evidence and Uncertainty

必须区分三类：

```markdown
### Confirmed Facts
- FACT-001: ...

### Conflicting Evidence
- CONFLICT-001: ...

### Open Questions
- Q-001: ...
```

规则：

- `Confirmed Facts` 必须有代码路径、文档路径、命令输出或用户确认作为证据。
- `Conflicting Evidence` 必须说明冲突来源。
- `Open Questions` 必须说明影响范围。

### 5.6 Research Alignment Check

这是过程动作，不是 hard gate。

推荐记录格式：

```markdown
## Research Alignment Check / 产出前对齐记录

### Alignment Summary Presented to User
- 当前理解：
- 准备复用 / 扩展：
- 不确定项：
- 若按当前理解继续，将影响：

### User Feedback
- 用户确认：
- 用户纠正：
- 用户要求按假设继续：

### Follow-up Exploration
- 重新探索的路径：
- 修正后的结论：

### Final Research Baseline
- 本 research 产物基于哪些已确认事实：
- 哪些仍是 assumptions：
```

要求：

- 若用户纠正，必须有 `Follow-up Exploration`。
- 若用户未明确确认但允许继续，必须有 assumptions。
- `tech-research.md.stage_status: ready` 不要求签字，但要求对齐记录存在。

## 6. Spec INDEX 设计

### 6.1 单 INDEX 策略

只保留：

```text
.docs/spec/INDEX.md
```

不新增：

```text
.docs/spec/frontend/INDEX.md
.docs/spec/backend/INDEX.md
```

### 6.2 INDEX.md 推荐表格

```markdown
# Spec Index

| Spec ID | 分类 | 适用阶段 | 适用技术/模块 | 文件路径 | 何时使用 | 备注 |
|---|---|---|---|---|---|---|
| react-query-data-fetching | frontend | ship-frontend-design, ship-build | React, data fetching | frontend/react-query-data-fetching.md | 页面需要 server state / cache / mutation |  |
| backend-service-methods | backend | ship-backend-design, ship-build | Node, service layer | backend/service-methods.md | 设计 Service 方法签名和调用边界 |  |
| redis-cache-policy | backend | ship-backend-design, ship-build | Redis | backend/redis-cache-policy.md | 需求涉及缓存、限流、会话、分布式锁 |  |
| mq-event-contract | backend | ship-contract, ship-backend-design, ship-build | MQ | backend/mq-event-contract.md | 需求涉及异步消息、事件、worker |  |
```

分类当前只建议：

- `frontend`
- `backend`
- `shared`

说明：

- `shared` 只用于真正跨前后端的规范，例如 error code、date/time、trace id。
- 不引入更多分类，避免理解负担。

### 6.3 Spec 文件 frontmatter 保持现有字段

仍保留当前 schema：

```yaml
spec_id: ""
scope: project
stage_hooks: []
stack_tags: []
domains: []
applies_to: []
last_updated: ""
```

不新增 `spec_type`。

### 6.4 Agent 使用规则

每个需要 spec 的阶段必须：

1. 先读 `.docs/spec/INDEX.md`；
2. 根据当前阶段、需求 domain、project_scope、tech_stack 和涉及文件，挑选候选 spec；
3. 再读取候选 spec 文件；
4. 把实际使用的 `spec_id` 写入对应产物的 `referenced_spec_ids` 或任务 `spec_refs`；
5. 若 INDEX 和 frontmatter 不一致，记录 warning；
6. 若找不到匹配 spec，Warn Then Continue。

## 7. 影响文件清单

### 7.1 必改文档

1. `skills/ship-tech-discovery/SKILL.md`
   - 重写 Overview，强调 Project Reality First。
   - 更新 When to Use / When NOT to Use。
   - research 子段新增 Project Reality Scan。
   - 增加 Research Alignment Check 过程。
   - 更新 `tech-research.md` 必备章节。
   - 更新 Evidence Rules / Verification。

2. `skills/ship-spec/SKILL.md`
   - 修改 Directory Structure 示例，保留单 `INDEX.md`。
   - 明确 `INDEX.md` 是人工路由入口。
   - 明确分类仅 `frontend / backend / shared`。
   - 保持 frontmatter schema 不新增字段。
   - 明确 runtime helper 仍可用 frontmatter 做扫描和校验。

3. `skills/ship-orchestrator/_templates/protocol/workflow-protocol.md`
   - 更新 Spec Hook Contract 中 `INDEX.md` 的语义。
   - 在 `ship-tech-discovery` hook 中加入 Project Reality Scan。
   - 明确 Research Alignment Check 不是 hard gate。
   - 保持 canonical stage map 不变。

4. `skills/README.md`
   - 更新 Design 大阶段说明。
   - 补充 `ship-tech-discovery` 已有项目优先发现。
   - 补充单 `INDEX.md` spec 路由策略。

5. `README.md`
   - 同步对外说明，避免 root README 与 skills README 漂移。

### 7.2 建议同步文档

6. `skills/ship-backend-design/SKILL.md`
   - 明确 backend design 必须读取 `tech-research.md` 的 Project Reality Scan。
   - 数据模型设计不能只从 `api-contract.md` 反推，还要结合已有 DB / ORM / migration 发现。
   - Service / Repository / MQ / Redis 等方案必须引用相关 backend spec。

7. `skills/ship-frontend-design/SKILL.md`
   - 明确 frontend design 必须读取 `tech-research.md` 的 Existing Surface Inventory。
   - 页面 / 组件 / store / API client 方案要区分复用、扩展、新增。
   - 前端规范从 `.docs/spec/INDEX.md` 的 frontend 分类中选择。

8. `skills/ship-contract/SKILL.md`
   - 明确 contract 设计应消费 `Requirement-to-Reality Mapping`。
   - 如果已有 API surface 存在，必须判断兼容新增、breaking change、deprecation。
   - message / cron / cli / sdk 形态需结合已有 surface，而不是只从 tech-selection 推断。

### 7.3 Validator / tests

9. `skills/ship-orchestrator/scripts/validate_tech_discovery.py`
   - ready 状态下检查 `tech-research.md` 是否包含 Project Reality Scan 相关章节。
   - 对 `existing_project` 场景，要求存在现有 surface / mapping / alignment 记录。
   - 保留 source_id 检查。

10. `skills/ship-orchestrator/scripts/validate_workflow_docs.py`
   - 增加对新关键文案的检查：
     - `Project Reality Scan`
     - `Research Alignment Check`
     - `.docs/spec/INDEX.md`
     - `frontend / backend / shared`
   - 更新旧的 “INDEX.md 仅人工浏览” 表述检查。

11. `skills/ship-orchestrator/scripts/test_workflow_hardening.py`
   - 增加 regression：
     - existing_project ready research 缺 Project Reality Scan 应失败；
     - existing_project ready research 缺 Research Alignment Check 应失败；
     - new_project 可以写“不适用”但必须说明；
     - spec INDEX frontend/backend/shared 表格被 workflow docs 检查覆盖。

12. `skills/ship-orchestrator/scripts/spec_runtime.py`
   - 本轮不强制改。
   - 可选增强：scan 时读取 `INDEX.md` 并检查 INDEX 表格路径与实际 spec 文件 frontmatter 是否明显冲突。
   - 若做增强，必须保持 Warn Then Continue。

13. `skills/ship-orchestrator/scripts/test_spec_runtime.py`
   - 仅当 `spec_runtime.py` 增强 INDEX 检查时再改。

## 8. 分阶段实施计划

### Phase 1: 文档合同更新

目标：

- 先把 workflow 行为合同写清楚。
- 不先动 runtime helper，避免过早复杂化。

改动：

1. 修改 `skills/ship-tech-discovery/SKILL.md`
2. 修改 `skills/ship-spec/SKILL.md`
3. 修改 `workflow-protocol.md`
4. 修改 `skills/README.md`
5. 修改 `README.md`

验收：

```bash
python3 skills/ship-orchestrator/scripts/validate_workflow_docs.py
```

预期：

- 当前命令可能先失败，因为 validator 还没更新新文案。
- Phase 1 完成后，旧 validator 至少不应因为基础阶段合同破坏而失败。

### Phase 2: 下游设计阶段消费更新

目标：

- 防止 `tech-research.md` 新增章节无人使用。
- 让 frontend/backend/contract design 真正消费项目事实发现。

改动：

1. `skills/ship-contract/SKILL.md`
2. `skills/ship-frontend-design/SKILL.md`
3. `skills/ship-backend-design/SKILL.md`
4. 可选更新对应 references template：
   - `skills/ship-contract/references/api-contract-template.md`
   - `skills/ship-frontend-design/references/frontend-design-template.md`
   - `skills/ship-backend-design/references/backend-design-template.md`

验收重点：

- Contract 不能忽略已有 API surface。
- Frontend design 要区分复用 / 扩展 / 新增页面组件。
- Backend design 要基于已有 DB / Service / MQ / Redis 等事实，不只从 contract 反推。

### Phase 3: Validator 更新

目标：

- 把新 workflow 变成可检查规则，而不是只写在文档里。

改动：

1. `validate_tech_discovery.py`
2. `validate_workflow_docs.py`
3. `test_workflow_hardening.py`

建议检查规则：

`validate_tech_discovery.py`：

- 若 `tech-research.md.stage_status=ready`：
  - 必须有 source refs；
  - 必须包含 `Project Reality Scan` 或中文等价标题；
  - 必须包含 `Requirement-to-Reality Mapping` 或中文等价标题；
  - 必须包含 `Research Alignment Check` 或中文等价标题。

- 若 feature `meta.yml.project_context=existing_project`：
  - Project Reality Scan 不能写“不适用”；
  - 必须出现至少一个代码路径 / 文档路径 / API / DB / frontend / service 证据信号；
  - Requirement-to-Reality Mapping 不能空。

- 若 `meta.yml.project_context=new_project`：
  - 允许 Project Reality Scan 写“不适用”；
  - 但必须说明因为 `new_project` 无既有代码基线。

`validate_workflow_docs.py`：

- 检查 `ship-tech-discovery/SKILL.md` 存在 Project Reality First / Research Alignment Check 等文案。
- 检查 `ship-spec/SKILL.md` 存在单 `.docs/spec/INDEX.md` 和 frontend/backend/shared 分类说明。
- 检查 protocol 与 README 同步。

### Phase 4: Spec INDEX 轻量模板补齐

目标：

- 给用户和 agent 一个最小可用的 `INDEX.md` 写法。

建议新增或更新：

- 可在 `ship-spec/SKILL.md` 内直接给模板；
- 或新增 `skills/ship-spec/references/spec-index-template.md`。

倾向：

- 如果模板不长，直接放进 `ship-spec/SKILL.md`；
- 如果后续还要加示例，再拆到 references。

不建议本轮新增复杂脚本。

### Phase 5: 可选 runtime 增强

目标：

- 在文档与 validator 稳定后，再决定是否增强 `spec_runtime.py`。

可选能力：

- `scan` 输出中加入 `index_entries`；
- 检查 INDEX 表格里的文件路径是否存在；
- 检查 INDEX 中列出的 `spec_id` 是否和文件 frontmatter 一致；
- 检查 INDEX 分类是否只使用 `frontend / backend / shared`。

限制：

- 只 warning，不阻塞。
- 不把 INDEX 变成唯一机器事实源。
- 不增加 `spec_type`。

## 9. 验证计划

### 9.1 基础文档一致性

```bash
python3 skills/ship-orchestrator/scripts/validate_workflow_docs.py
```

### 9.2 Tech discovery artifact 校验

准备一个 fixture feature，包含：

- `meta.yml` 中 `project_context: existing_project`
- `tech-research.md`
- `tech-selection.md`

执行：

```bash
python3 skills/ship-orchestrator/scripts/validate_tech_discovery.py <feature-dir>
```

至少覆盖：

- 缺 source_id 失败；
- 缺 Project Reality Scan 失败；
- 缺 Requirement-to-Reality Mapping 失败；
- 缺 Research Alignment Check 失败；
- existing_project 写“不适用”失败；
- new_project 写“不适用 + 原因”通过。

### 9.3 全量 hardening tests

```bash
python3 skills/ship-orchestrator/scripts/test_workflow_hardening.py
```

如果该脚本不是直接可执行测试入口，则按现有项目测试方式运行对应 unittest。

### 9.4 Spec runtime 回归

如果未改 `spec_runtime.py`：

```bash
python3 skills/ship-orchestrator/scripts/test_spec_runtime.py
```

如果改了 `spec_runtime.py`：

- 增加 INDEX 表格 warning 相关测试；
- 确认没有破坏现有 `scan / resolve` 行为。

## 10. 风险与处理

### 风险 1：把产出前对齐误做成 hard gate

处理：

- 文档明确 Research Alignment Check 不是 hard gate。
- 不新增 review 文档。
- 不新增 sign_off 字段。
- 只作为 `tech-research.md ready` 前的过程记录。

### 风险 2：spec INDEX 和 frontmatter 双事实源冲突

处理：

- INDEX 是人工路由入口。
- frontmatter 仍是 runtime helper 扫描事实源。
- 两者不一致只 warning。
- 后续如需要再增强 sync/doctor，不在本轮复杂化。

### 风险 3：Project Reality Scan 变成泛泛描述

处理：

- validator 要求 evidence signal。
- `tech-research.md` 必须包含路径、接口、表、服务、组件或已有 feature 文档证据。
- 不允许只写“已检查代码，无影响”这类空话。

### 风险 4：已有项目探索过重，拖慢小需求

处理：

- 对 `new_project` 轻量写不适用。
- 对 fast-track 可以压缩为最小 Project Reality Scan，但不能完全跳过已有项目关系确认。
- 对非常小的已有项目 patch，可限制扫描范围为需求相关模块和任务相关文件。

### 风险 5：下游设计阶段仍只看 tech-selection

处理：

- 更新 frontend/backend/contract SKILL。
- 设计评审可检查是否引用了 `tech-research.md` 的项目事实发现。
- 后续可在 `validate_design_alignment.py` 增加 project reality coverage，但本轮不是必做。

## 11. 推荐最终行为示例

### 输入场景

用户提供 PRD：

```text
新增用户资料编辑能力，支持昵称、头像、个人简介。
```

项目已有：

- `users` 表；
- `profiles` 表；
- `GET /api/users/:id`；
- `UserProfilePage`；
- `UserService`；
- 头像上传已有 object storage helper。

### 正确 tech discovery 行为

agent 不应直接调研“头像上传最佳实践”或“用户资料编辑技术选型”。

应先探索：

```text
1. users / profiles 表字段现状；
2. 当前 user profile API 和页面能力；
3. 头像上传 helper 是否已有；
4. 权限是否允许用户编辑自己的 profile；
5. 是否已有 user.updated event；
6. 本需求是扩展已有 profile 还是新建资料模型。
```

然后对齐用户：

```text
我发现当前项目已有 users 和 profiles 两张表。
昵称目前在 users.name，简介在 profiles.bio，头像字段未确认：
代码中有 avatar_url 但没有写入路径。
我准备按“扩展 profiles，复用现有 UserService，新增 PATCH /api/users/:id/profile”继续。
这里需要确认：头像字段是否归 profiles.avatar_url，而不是 users.avatar_url？
```

用户纠正后重新探索并更新 `tech-research.md`。

## 12. 实施顺序建议

推荐顺序：

1. 先改 `ship-tech-discovery/SKILL.md`。
2. 再改 `ship-spec/SKILL.md`。
3. 再同步 `workflow-protocol.md`。
4. 再同步 README。
5. 再改下游 `ship-contract / ship-frontend-design / ship-backend-design`。
6. 最后改 validator 和 tests。

原因：

- 先定行为合同，避免脚本先行导致语义不清。
- 下游阶段必须知道如何消费新增 research 章节。
- validator 最后收紧，避免中间态大量失败。

## 13. 完成定义

本次完善完成的标准：

- `ship-tech-discovery` 明确 Project Reality First。
- `tech-research.md` ready 前必须有项目现状发现、需求映射、证据不确定项和产出前对齐记录。
- 产出前对齐不是 hard gate，但被写入 research 过程。
- 单 `.docs/spec/INDEX.md` 成为 spec 人工路由入口。
- spec 只按 frontend / backend / shared 分类，不新增复杂 schema。
- frontend/backend/contract design 都明确消费 `tech-research.md` 的项目事实发现。
- validator 能发现缺少关键章节的 ready tech discovery 产物。
- workflow docs 校验通过。
- hardening tests 覆盖新规则。

