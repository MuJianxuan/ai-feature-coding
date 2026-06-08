# Routing Protocol

本协议定义 ship-orchestrator 的路由分发机制、委派模型和辅助质询（Assistive Questioning）规则。

## 路由分发机制

### 上下文传递包

调度器路由到阶段 skill 时传递的上下文包：
- `feature_dir`：feature 目录绝对路径
- `current_stage`：当前阶段标识
- `macro_stage`：当前大阶段标识与摘要
- `delegation`：当前 feature 的子代理偏好（default_mode / ask flags / node_overrides）
- `project_context`：unknown / existing_project / new_project
- `project_scope`：fullstack / backend_only / frontend_only
- `tech_stack`：已确定的技术栈信息（可能为空）
- `spec_context`：最近一次规范解析结果摘要（index_status / referenced_spec_ids / warnings / pending_proposals）
- `upstream_docs`：上游阶段产出文档路径列表
- `current_part`：双产物阶段内的子段索引（如 `research` / `selection` / `frontend` / `backend` / `sync`）

### 路由后回调

阶段 skill 完成后必须回调调度器：
1. 先读取对应产物 frontmatter，确认事实状态
2. 将 `meta.yml` 中对应阶段状态回写为摘要状态
3. 更新 `current_stage` 为下一阶段 canonical stage id
4. 若当前阶段为双产物阶段，同步刷新对应 `current_part`
5. 同步刷新 `macro_stage.current`、`macro_stage.label`、`macro_stage.summary`、`macro_stage.next_user_decision`
6. 若发现 `meta.yml` 与产物 frontmatter 不一致，优先修正 `meta.yml`
7. 若进入特定阶段，先刷新 `meta.yml.spec_context` 再传递上下文
8. 若命中配置驱动节点或子代理决策节点，先读取 `meta.yml.delegation` 判定执行方式
9. 若当前阶段存在 unresolved blocking `ship-grill-me` question，不得推进下一阶段；若只剩 non-blocking grill question，必须作为 Open Questions / Risk 传递并写清影响范围

## Delegation Model

### 核心原则

**orchestrator 是唯一状态推进者。子代理只是执行策略，不是额外阶段。**

### 委派模式

| 模式 | 适用场景 | 说明 |
|------|---------|------|
| `parallel_owned_outputs` | 只用于 `ship-frontend-design` / `ship-backend-design` | 两个子代理各自拥有独立产物 |
| `gate_check_switchable` | 只用于 `ship-define-review` / `ship-design-review` / `ship-plan-review` | 子代理执行 gate 检查并起草正式 review 文档 |
| `assistive_only` | research 取证、计划审计、测试分轨、证据整理等辅助工作 | 子代理不改正式产物状态 |
| `forbidden` | 共享契约、正式 gate、正式状态推进点 | 不委派 |
| `user_gate_only` | `approved / rejected / revision_needed`、`ship-build` 是否继续、`ship-handoff` 是否关闭等决策 | 必须由用户作出 |

### Delegation 配置结构

```yaml
delegation:
  default_mode: current_context  # 或 assistive_subagent / parallel_subagent / gate_check_subagent
  ask_on_parallel_stage: true    # 是否在并行阶段询问
  ask_on_assistive_node: true    # 是否在辅助节点询问
  node_overrides:
    ship-frontend-design: parallel_subagent
    ship-backend-design: parallel_subagent
    ship-define-review: gate_check_subagent
    # ... 更多节点覆盖
  warnings: []  # 委派解析告警
```

### Node Overrides 合法值

固定为以下四种：
- `current_context`：主上下文执行
- `assistive_subagent`：辅助子代理（不改正式产物状态）
- `parallel_subagent`：并行子代理（各自拥有独立产物）
- `gate_check_subagent`：gate 检查子代理（起草正式 review 文档）

### Canonical Node ID

#### Stage 级

- pre-Define stage 级（条件性）：`ship-discover`、`ship-shape`
- stage 级：`ship-define`、`ship-define-review`、`ship-contract`、`ship-frontend-design`、`ship-backend-design`、`ship-design-review`、`ship-delivery-plan`、`ship-plan-review`

#### Substage 级

- `ship-tech-discovery.research`
- `ship-tech-discovery.selection`

#### Build 辅助节点

- `ship-build.read-next-task`
- `ship-build.spec-scan`
- `ship-build.env-precheck`
- `ship-build.evidence-pack`

#### Verify 测试轨

- `ship-verify.backend-unit`
- `ship-verify.backend-integration`
- `ship-verify.backend-contract`
- `ship-verify.frontend-component`
- `ship-verify.frontend-e2e`

#### Handoff 辅助节点

- `ship-handoff.ac-evidence`
- `ship-handoff.deploy-materials`
- `ship-handoff.spec-proposals`

### 自动委派解析规则

1. `forbidden` 节点不可启动任何子代理；若存在 override，记录 warning 后强制回退 `current_context`
2. `parallel_owned_outputs` 只接受 `current_context | parallel_subagent`
3. `assistive_subagent` 不得在 `parallel_owned_outputs` 节点上被解释成 `parallel_subagent`
4. `assistive_only` 只接受 `current_context | assistive_subagent`
5. 当 `ask_on_parallel_stage = false` 时，只有显式 `node_overrides[node_id] = parallel_subagent` 才能自动委派；否则回退 `current_context`
6. 当 `ask_on_assistive_node = false` 时，`assistive_only` 节点可在 override 缺失时回落到 `default_mode`
7. 用户对某个节点的临时回答写入 `node_overrides[node_id]`；只有用户明确说"以后默认都这样"时才更新 `default_mode`

### Hard Gate 的运行时模型

#### 执行方式

- `current_context`：主代理直接执行 gate 检查并写正式 `review-*.md`
- `gate_check_subagent`：子代理执行 gate 检查并直接写正式 `review-*.md` 草案

#### 解析规则

- hard gate 的执行方式先读 `node_overrides[stage]`，再读 `default_mode`，最后回退 `current_context`
- 对 hard gate 而言，`assistive_subagent` 解释为 `gate_check_subagent`
- 对 hard gate 而言，`parallel_subagent` 是无效值；记录 warning 后回退

#### 写权限约束

- 无论哪种方式，主代理都必须重新读取正式 gate 文档并复核
- 只有主代理可以把 `review_status` 从 `pending` 改成终态
- 等待用户批准时正式 frontmatter 仍保持 `pending`，可在正文记录 `recommended_status`
- 若主代理判断可通过，只有在用户明确批准后，才能一次性写入 `review_status: approved`、`user_sign_off` 和 `signed_at`
- 三个 hard gate 的执行方式复用 `node_overrides` 与 `default_mode`，不再每次进入都单独询问

### 写权限约束

- 子代理不得修改 `meta.yml`
- 子代理可以起草正式 `review-*.md`，但 gate frontmatter 的最终结论必须由主代理确认
- 子代理起草正式 gate 文档时，必须保持 `review_status: pending`，且 `user_sign_off`、`signed_at` 为空
- `assistive_only` 子代理不得直接改正式产物的正文、`stage_status` / `review_status`
- 只有主上下文可以合并子代理结果并推进 `current_stage`

### 节点级行为

#### 1. ship-contract 完成后

默认询问是否并行启动前后端设计子代理。

#### 2. ship-plan-review 通过后

默认询问是否开启 build 辅助委派模式。

#### 3. ship-build 每个 verified slice 完成后

默认询问下一个正式任务继续由当前上下文执行，还是附带启动只读准备/验证子代理。

#### 4. ship-verify 入口

默认询问是否按测试轨道分派子代理。

#### 5. ship-handoff 收尾前

只询问 accept / follow-up / proposal 处理，不委派关闭判定。

## Assistive Questioning

### 定位

`ship-grill-me` 是辅助质询 hook，**不是 delegation mode 的新取值**：
- 不写入 `node_overrides`
- 不改变 5 个 macro stages 或 14 个 canonical stages
- orchestrator 在进入允许节点时，可根据用户请求、阶段风险或未关闭的 blocking gap 使用它做逐题压力测试

### 推荐接入点

1. `ship-discover.pre-ready`：方案选择后、`product-brief.md` ready 前
2. `ship-shape.pre-selection`：3+ wireframe / design variants 产出并浏览器验证后、用户选定方向前
3. `ship-define.pre-ready`：`requirements.md` 成稿后、ready 前
4. `ship-tech-discovery.selected-scope-ac-confirmation`：selected scope AC 确认前（场景 E）
5. `ship-tech-discovery.research-alignment`：Research Alignment Check 发现影响 contract / design 的 unknown 时
6. `ship-frontend-design.pre-ready` / `ship-backend-design.pre-ready`：各自设计文档 ready 前；因这两个阶段是 `parallel_owned_outputs`，grill 由当前产物 owner 内部执行，不能另启 `assistive_subagent` 修改同一正式文档
7. `ship-design-review.pre-signoff`：`review-design.md` 草案完成后、用户 approved 前

### 禁止接入点

- `ship-contract`
- `ship-tech-discovery.selection`
- `ship-delivery-plan`
- 任何正式状态推进动作

### 执行规则

1. 一次只问一个问题，并给出 recommended answer
2. 能从仓库、已有 feature 文档、API、DB、页面、权限或测试命令确认的问题，先探索证据，不问用户
3. grill 输出只能进入当前产物正文的 Grill Notes / Open Questions / Risk section，或 hard gate 正文中的 sign-off questions / risk acceptance candidates / conditions candidates
4. `ship-grill-me` 不替代 `review-*.md`，不得写 `review_status: approved`
5. `user_sign_off` 和 `signed_at` 仍必须由主上下文在用户明确批准后写入
6. blocking grill question 未 resolved 时，不得推进下一阶段
7. non-blocking question 必须进入 Open Questions / 假设并标注影响范围

### Grill Question 状态

- `blocking`：必须解决才能推进
- `non-blocking`：记录为 Open Questions / Risk，可推进但必须标注影响范围
- `resolved`：已确认答案
- `accepted`：用户接受风险

## Spec Hook Model

### Ownership 采用 Hybrid 模式

- **orchestrator**：
  - 负责 workspace resolution
  - 调用 `spec_runtime.py` / `feature_meta_runtime.py sync-spec`
  - 维护 `meta.yml.spec_context`
  - 把规范摘要透传给阶段 skill
- **阶段 skill**：
  - 根据 `spec_context` 和本阶段输入实际读取规范
  - 把 `referenced_spec_ids`、`spec_warnings`、`spec_checked_at` 写入产物或任务证据
- **ship-handoff**：
  - 只记录 proposal，不直接写回 workspace `spec_root`
  - 真正沉淀由用户确认后执行

### Workspace Resolution 规则

1. NEW_FEATURE 创建 feature 前必须先通过 Workspace Config Gate
2. NEW_FEATURE / CONTINUE_FEATURE / `sync-spec` 都以 workspace 为边界，而不是当前 cwd
3. 显式配置源是 workspace `.docs/ship/project.yml`
4. project_group 下 feature 目录写入 workspace `feature_root`
5. CONTINUE_FEATURE 优先信任已有 `meta.yml.spec_context.workspace_*` 字段，不重新按 cwd 猜测
6. 无法确定 workspace 时阻塞；workspace 已确定但 spec 缺失时只 warning
7. feature `projects` 是默认执行范围，不是硬安全边界
8. single_project 下读取 `.docs/spec/INDEX.md`；project_group 下读取 `.docs/spec/_shared/INDEX.md`，并按当前目标项目读取 `.docs/spec/<project>/INDEX.md`
9. project_group 下 `ship-build` 必须由任务 `project:` 显式提供目标项目，不从 `allowed_files` 路径反推

### 默认缺规策略

- 缺少 `INDEX.md`、找不到匹配规范、规范 frontmatter 不合法时，记录 warning 并继续
- 只有用户显式要求严格模式时，缺规才升级为阻塞条件
- `ship-build` 和 `ship-handoff` 都需要汇总规范引用与待沉淀 proposal，不能因为需求较小而跳过规范检查
