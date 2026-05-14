# Coding Feature Workflow 技能改进分析

基于对以下同类工具/框架的调研：
- **Addy Osmani / agent-skills** (25k+ stars) — Google 工程文化编码为 AI 工作流
- **BMAD Method** (39.5k stars) — 多角色 Agent 驱动的敏捷开发框架
- **GitHub Spec Kit** (93k+ stars) — 四阶段门控式 Spec-Driven Development
- **Superpowers by obra** (476k+ installs) — 反合理化 + TDD 纪律层
- **Anthropic 官方 Skill Authoring Best Practices** — Progressive Disclosure + Gotchas

---

## 一、你的技能套件现状总结

你的 Coding Feature Workflow 是一套 **6 阶段门控式** 开发流程：

```
需求澄清 → 仓库勘察 → 技术设计 → 任务拆解 → 编码执行 → 验证收口
```

**已有优势：**
- 严格的 activation policy 和 route contract，防止误触发
- 完整的 YAML frontmatter metadata 契约（stage_status, evidence_complete, updated_at）
- 设计审批门禁（approval_status）
- 每阶段有明确的前置检查和 safety policy
- Scope change protocol 防止范围蔓延
- Resume protocol 处理中断恢复
- WORKFLOW_CONTRACT.md 作为共享契约

---

## 二、各技能可借鉴的改进点

### 1. coding-requirement-intake（需求澄清）

| 借鉴来源 | 优点 | 建议集成方式 |
|---|---|---|
| GitHub Spec Kit `/spec` | **Constitution 概念** — 在 spec 之前先建立项目级约束（技术栈、设计系统、安全要求），避免每次重复声明 | 在 `requirements.md` 增加 `project_constraints` section，或引用 `.docs/spec/` 下已有规范 |
| BMAD Method | **多角色视角** — 用 Business Analyst 视角提问，确保覆盖商业目标、用户画像、成功指标 | 增加 "业务成功指标" 和 "用户画像" 字段到 requirements.md 模板 |
| Addy Osmani `/spec` | **Anti-rationalization table** — 列出 AI 可能跳过的验收标准，强制不能省略 | 在 requirements.md 底部增加 "不可省略项清单" |
| Spec Kit | **Iterative refinement checkpoint** — spec 完成后有明确的 "reflect and refine" 步骤 | 在 Step 5 增加 "自检清单"：每条 AC 是否可测试？scope 边界是否清晰？ |

### 2. coding-repo-investigation（仓库勘察）

| 借鉴来源 | 优点 | 建议集成方式 |
|---|---|---|
| Addy Osmani `source-driven-development` | **Official docs verification** — 实现前先验证官方文档，避免 API 幻觉 | 增加 "外部依赖验证" 步骤：对涉及的第三方库/API，核对版本和实际行为 |
| Addy Osmani `context-engineering` | **Right context at right time** — 不一次加载所有信息，按需深入 | 将搜索顺序改为分层策略：先广度扫描确定范围，再深度追踪关键链路 |
| BMAD Method | **Architecture Decision Records (ADR)** — 记录为什么选择某个方案而非另一个 | investigation.md 增加 "架构决策记录" section：记录发现的多种可能路径及取舍原因 |
| GitHub Spec Kit | **Research phase** — 独立的研究阶段产出 research.md | 可选：对复杂需求，investigation.md 拆分为 "已知事实" 和 "研究发现" 两部分 |

### 3. coding-technical-design（技术设计）

| 借鉴来源 | 优点 | 建议集成方式 |
|---|---|---|
| Addy Osmani `doubt-driven-development` | **Adversarial review** — 设计完成后用"怀疑者"视角审视每个非显而易见的决策 | 增加 "设计自审" 步骤：列出 3 个最可能出错的假设，逐一验证 |
| Addy Osmani `api-and-interface-design` | **Contract-first** — 先定义接口契约，再实现 | 对涉及 API 的设计，强制先输出 request/response schema，再写实现方案 |
| BMAD Method | **Complexity profiling** — 根据复杂度分级（atomic → enterprise），调整设计深度 | 在 design.md frontmatter 增加 `complexity_level: low/medium/high`，low 可简化设计内容 |
| Superpowers | **Iron Law: 不允许跳过设计直接编码** — 用反合理化表阻止 AI 找借口 | 增加 Gotchas section：列出常见的"跳过设计"借口及为什么不能接受 |

### 4. coding-task-planning（任务拆解）

| 借鉴来源 | 优点 | 建议集成方式 |
|---|---|---|
| Addy Osmani `planning-and-task-breakdown` | **2-5 分钟粒度** — 每个任务应该能在一个 AI turn 内完成 | 增加粒度指导：单个任务不超过 3 个文件修改，预计 1 个 AI turn 可完成 |
| Addy Osmani `incremental-implementation` | **Thin vertical slices** — 每个任务是一个可独立验证的垂直切片 | 拆解规则增加："每个任务必须产出可独立运行/测试的增量，不允许'准备工作'类空任务" |
| GitHub Spec Kit `/tasks` | **Testable increments** — 每个 task 自带测试标准 | 已有"完成判定"，可强化为：完成判定必须是可执行命令或可观测状态 |
| Superpowers | **Save Point Pattern** — 每个任务完成后 commit，失败可回滚到上一个 save point | 增加建议：每个任务完成后建议用户 commit，形成 save point |
| BMAD Method | **Epic sharding** — 大需求先拆 epic 再拆 task，避免一次性产出过多任务 | 对 task_count > 8 的情况，建议分 phase 执行，每 phase 3-5 个任务 |

### 5. coding-implementation-execution（编码执行）

| 借鉴来源 | 优点 | 建议集成方式 |
|---|---|---|
| Addy Osmani `test-driven-development` | **Red-Green-Refactor** — 先写失败测试，再实现，再重构 | 增加可选 TDD 模式：如果任务涉及逻辑变更，建议先写测试再实现 |
| Superpowers | **Anti-rationalization** — 列出 AI 可能用来跳过测试的借口，逐一封堵 | 增加 Gotchas："不允许以'简单改动不需要测试'为由跳过验证" |
| Addy Osmani `debugging-and-error-recovery` | **Reproduce → Localize → Fix → Guard** — 系统化调试流程 | 遇到执行失败时，强制按此顺序排查，不允许盲目重试 |
| GitHub Spec Kit | **Spec-implementation traceability** — 实现时持续对照 spec | 已有"对照 design.md"，可强化：每个文件修改必须能追溯到 tasks.md 中的具体任务 |
| Addy Osmani `context-engineering` | **Context refresh** — 长任务中主动 compact 或刷新上下文 | 增加提示：如果单个任务执行超过 10 次工具调用，建议检查上下文是否仍然准确 |

### 6. coding-verification-closeout（验证收口）

| 借鉴来源 | 优点 | 建议集成方式 |
|---|---|---|
| Addy Osmani `browser-testing-with-devtools` | **Runtime verification** — 不只跑测试，还要在浏览器/运行时验证 | 对 UI 类需求，verification.md 必须包含运行时验证步骤（启动服务、访问页面、检查行为） |
| Addy Osmani `security-and-hardening` | **OWASP checklist** — 安全验证不是可选项 | 增加安全检查 section：对涉及用户输入、认证、数据的变更，必须检查 OWASP Top 10 |
| Addy Osmani `performance-optimization` | **Measure first** — 性能验证要有基线对比 | 对涉及性能的需求，verification.md 必须记录 before/after 指标 |
| GitHub Spec Kit | **Spec sync** — 验证完成后反向更新 spec，保持 spec 与代码同步 | handoff.md 增加 "规范同步" section：如果实现偏离了原始设计，记录偏离原因并建议更新 design.md |
| Addy Osmani `/ship` | **Pre-launch checklist** — 部署前检查清单（监控、回滚、告警） | handoff.md 增加 "上线检查清单"：监控配置、告警规则、回滚方案、灰度策略 |

---

## 三、结构性改进建议

### A. Progressive Disclosure（渐进式披露）

**问题：** 当前每个 SKILL.md 内容较长（80-230 行），全部加载到上下文中。

**借鉴：** Anthropic 官方建议 SKILL.md 保持 < 500 行，详细内容放 `references/` 按需加载。

**建议：**
- 每个 skill 增加 `references/` 目录，存放：
  - `checklist.md` — 自检清单（按需加载）
  - `gotchas.md` — 常见错误和反合理化表（按需加载）
  - `examples.md` — 正反例（按需加载）
- SKILL.md 主体保持核心规则，通过 "Read `references/gotchas.md` when..." 指令按需加载

### B. Gotchas / Anti-rationalization Section（陷阱/反合理化）

**问题：** 当前技能没有记录 AI 常犯的错误模式。

**借鉴：** Superpowers 的 Iron Law + Anti-rationalization table；社区经验表明这是"信噪比最高的内容"。

**建议：** 每个 skill 增加 `references/gotchas.md`，格式：

```markdown
## Gotchas

| AI 常见借口 | 为什么不能接受 | 正确做法 |
|---|---|---|
| "这个改动很简单，不需要测试" | 简单改动也可能引入回归 | 至少运行相关测试套件 |
| "我已经检查过了" | 没有证据的检查等于没检查 | 必须附带命令输出或文件引用 |
```

### C. Complexity-Adaptive Workflow（复杂度自适应）

**问题：** 当前所有需求走同一套完整流程，小需求可能过重。

**借鉴：** BMAD 的 complexity profiling；Addy Osmani 的 "small tasks can be done directly"。

**建议：** 在 orchestrator 增加复杂度判断：
- **Low**（单文件 bugfix、配置修改）：可简化 investigation + design，直接进入 task + execution
- **Medium**（跨 2-3 文件的功能）：完整流程但各阶段可精简
- **High**（跨模块、涉及 DB/API/UI 的功能）：完整流程，不可省略

### D. Scripts 辅助验证（可执行脚本）

**问题：** 当前只有 `inspect_feature_state.py` 一个辅助脚本。

**借鉴：** Anthropic 建议 "Actually, Just Use Scripts"；agent-skills 用脚本消除歧义。

**建议：** 增加辅助脚本：
- `scripts/validate_task_format.py` — 验证 tasks.md 格式是否符合契约
- `scripts/check_evidence_completeness.py` — 检查各阶段 evidence 是否齐备
- `scripts/generate_verification_report.py` — 从 verification.md 生成验收报告摘要

### E. Spec 与代码的双向同步

**问题：** 当前流程是单向的（spec → code），实现后如果偏离设计，没有机制反向更新。

**借鉴：** GitHub Spec Kit Discussion #152 讨论的 "Evolving specs"；Addy Osmani 的 "update spec when scope changes"。

**建议：** 在 verification-closeout 阶段增加 "设计偏离检查"：
- 对比 design.md 的目标链路与实际实现
- 如有偏离，记录原因并建议更新 design.md（标记为 post-implementation revision）

### F. 质量门禁可视化

**问题：** 当前阶段推断逻辑复杂（23 条规则），用户难以快速了解当前状态。

**借鉴：** BMAD 的 workflow status tracker；GitHub Spec Kit 的 phase visualization。

**建议：** 在 orchestrator 的 INSPECT_FEATURES / AD_HOC_AUDIT 模式输出中，增加可视化状态：

```
需求 ✅ → 勘察 ✅ → 设计 ✅(待审批) → 任务 ⬜ → 编码 ⬜ → 验收 ⬜
```

---

## 四、优先级排序

| 优先级 | 改进项 | 理由 |
|---|---|---|
| P0 | B. Gotchas/Anti-rationalization | 信噪比最高，直接减少 AI 犯错 |
| P0 | D. 辅助验证脚本 | 减少人工检查负担，提高契约执行力 |
| P1 | A. Progressive Disclosure | 优化上下文使用，长期收益大 |
| P1 | C. 复杂度自适应 | 减少小需求的流程摩擦 |
| P2 | E. 双向同步 | 保持文档与代码一致性 |
| P2 | F. 质量门禁可视化 | 改善用户体验 |
| P2 | 各阶段具体改进 | 逐步迭代 |

---

## 五、实施建议

1. **先加 Gotchas** — 从 coding-implementation-execution 开始，记录你在实际使用中遇到的 AI 错误模式
2. **增加辅助脚本** — 扩展 inspect_feature_state.py 的能力，或新增独立脚本
3. **重构为 Progressive Disclosure** — 每个 skill 拆出 references/ 目录
4. **在 orchestrator 增加复杂度判断** — 允许 low complexity 走快速通道
5. **迭代各阶段模板** — 根据上面的表格逐步增加字段和检查项
