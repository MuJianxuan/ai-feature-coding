# ship-orchestrator 入口工作流草案

更新时间：2026-05-27T17:15:47+08:00

## 背景

当前 `ship-*` 技能套件已经有四种 NEW_FEATURE 场景：

- A 零到一：`greenfield`
- B 产品提供：`product_provided`
- C 迭代增强：`evolve`
- D PRD 直通：`prd_direct`

现有协议主要覆盖“用户已经携带资料”或“直接进入阶段”的情况。需要补充的是：当用户调用 `ship-orchestrator`，但没有指定需求目录、也没有携带资料时，orchestrator 应先识别是否存在未完成需求，再决定是继续、选择模式，还是创建资料准备目录。

本草案的目标是补齐入口体验与资料准备态，同时不破坏现有 canonical stage、stage status 和下游阶段合同。

## 已确认原则

1. `ship-orchestrator` 是 `ship-*` 工作流的统一入口。
2. 用户未指定 `feature_dir` 时，必须先扫描 `.docs/feature-*` 下未完成 feature。
3. 即使只存在一个未完成 feature，也必须询问用户是否继续，不能自动进入。
4. 没有未完成 feature 时，直接列出四种新建模式供用户选择，不先猜测。
5. PRD 直通和产品提供都允许用户把完整 PRD 原文粘贴到 `requirements.md`。
6. 初始 `requirements.md` 可以作为 raw PRD inbox，但不能被下游设计、计划、实现阶段直接消费。
7. `ship-define` normalize 后，`requirements.md` 必须回归结构化 requirements contract。
8. normalize 后，原始 PRD 迁移或保留到 `resource/raw-prd.md`，用于追溯。
9. 资料准备态不新增 canonical stage，也不新增 stage status 枚举。
10. 资料准备态使用 `stages.ship-define.status: blocked` + `block_reason: awaiting_materials`。
11. 零到一模式也先创建 feature 目录，但不创建 raw `requirements.md` inbox，不等待资料，直接进入 `ship-discover`。
12. 迭代增强必须有现状基线；没有已有 feature 目录或代码路径时，不创建目录，先询问基于哪个对象增强。

## 入口决策流程

```text
用户调用 ship-orchestrator
  -> 是否指定 feature_dir？
     -> 是：按 Resume Protocol 恢复指定 feature
     -> 否：扫描 .docs/feature-* 未完成 feature
        -> 多个：列表展示，让用户选择继续哪个，或选择新建
        -> 一个：询问“是否继续这个 feature，还是新建？”
        -> 没有：列出四种新建模式
```

未完成 feature 的判断应以 `meta.yml.lifecycle_status` 和各阶段状态为主：

- `active` / `blocked` 视为未完成。
- `completed` / `abandoned` 不进入默认继续列表。
- 若 `meta.yml` 与阶段产物 frontmatter 冲突，仍沿用现有协议：阶段产物 frontmatter 是事实源，`meta.yml` 是索引层。

## 新建模式选择

当没有未完成 feature，或用户明确选择新建时，orchestrator 直接列出四种模式：

```text
请选择进入方式：
1. PRD 直通：你已有完整 PRD，想直接粘贴/放资料，不做需求采访。
2. 产品提供：你有 PRD/原型/设计稿，但允许我继续澄清缺口。
3. 零到一：你只有想法，需要先头脑风暴产出需求。
4. 迭代增强：基于已有功能、feature 目录或代码路径做增强。
```

不要在“用户未携带资料”的入口里自行猜测模式。模式选择是用户显式决策点。

## 四种模式行为

### 1. PRD 直通

适用条件：

- 用户已有完整 PRD。
- 用户希望直接使用 PRD，不做需求采访。
- 可能有原型、设计稿、截图、接口文档等补充资料。

目录初始化：

```text
.docs/feature-YYYYMMDD-<short-name>/
├── meta.yml
├── requirements.md
└── resource/
    └── README.md
```

初始化状态：

```yaml
current_stage: ship-define
scenario: prd_direct
stages:
  ship-discover:
    status: skipped
  ship-shape:
    status: skipped
  ship-define:
    status: blocked
    block_reason: awaiting_materials
    generation_mode: prd_direct
    evidence_complete: false
```

`requirements.md` 初始化为 raw PRD inbox。用户可以把完整 PRD 原文直接粘贴进去，格式不限。

用户说“资料放好了”后：

1. 检查 `requirements.md` 是否不是空模板，或 `resource/` 下是否存在至少一个非 `README.md` 文件。
2. 若两者都为空，继续保持 `blocked + awaiting_materials`，提示用户补资料。
3. 若存在资料，清空 `block_reason`，将 `stages.ship-define.status` 改为 `pending`。
4. 路由到 `ship-define`，按 `prd_direct` 执行 normalize。
5. `ship-define` 尽量零提问，只做提取、结构化、标记 `[GAP]`。

### 2. 产品提供

适用条件：

- 用户有 PRD、原型、设计稿、会议纪要或其他产品资料。
- 用户允许根据资料继续澄清阻塞缺口。

目录初始化与 PRD 直通相同，也创建 raw `requirements.md` inbox 和 `resource/README.md`。

初始化状态：

```yaml
current_stage: ship-define
scenario: product_provided
stages:
  ship-discover:
    status: skipped
  ship-shape:
    status: skipped
  ship-define:
    status: blocked
    block_reason: awaiting_materials
    generation_mode: interview
    evidence_complete: false
```

用户说“资料放好了”后的解除等待规则与 PRD 直通一致。区别是路由到 `ship-define` 后走 `interview`，会基于资料继续提问，直到阻塞性需求缺口清零，或保持 `stage_status: draft`。

### 3. 零到一

适用条件：

- 用户只有想法，没有 PRD、原型或设计稿。
- 需要先通过头脑风暴、事实核查、方案对比，把想法转成 `product-brief.md`。

目录初始化：

```text
.docs/feature-YYYYMMDD-<short-name>/
├── meta.yml
└── resource/
```

不创建 raw `requirements.md` inbox。

初始化状态：

```yaml
current_stage: ship-discover
scenario: greenfield
stages:
  ship-discover:
    status: pending
    discovery_mode: greenfield
  ship-define:
    generation_mode: interview
```

创建目录后直接进入 `ship-discover`，不进入 `awaiting_materials`。

### 4. 迭代增强

适用条件：

- 用户基于已有 feature 目录、已有代码路径或明确现有功能做增强。

入口规则：

1. 用户已指定已有 `feature_dir`：
   - 创建新的增强 feature 目录。
   - `scenario: evolve`。
   - 记录 `parent_feature_dir`。
   - 进入 `ship-discover` evolve。
2. 用户已指定代码路径：
   - 创建新的增强 feature 目录。
   - `scenario: evolve`。
   - 记录 `source_code_paths`。
   - 进入 `ship-discover` evolve。
3. 用户没有指定基线：
   - 不创建目录。
   - 先询问：这是基于哪个已有功能、feature 目录或代码路径增强？

迭代增强不应在缺少现状基线时创建空目录，因为 `ship-discover` evolve 必须先读取现有实现或过往 feature 产物。

## raw requirements.md inbox 协议

PRD 直通和产品提供模式允许 `requirements.md` 在最初作为 raw PRD inbox。

初始化模板建议：

```markdown
---
stage: ship-define
stage_status: draft
generation_mode: raw_prd_input
input_kind: raw_prd
evidence_complete: false
updated_at: ""
---

# Raw PRD Input

请将完整 PRD 原文粘贴到下方。格式不限，可以包含标题、表格、流程说明、验收规则、会议纪要等。

补充资料请放入 `resource/`，例如原型、设计稿、截图、接口文档、会议纪要附件。

---

[在这里粘贴 PRD 原文]
```

raw inbox 约束：

- 允许格式不统一。
- 允许缺少 Domain ID、AC、NFR、In/Out Scope。
- 不允许下游 `ship-tech-discovery`、`ship-contract`、`ship-frontend-design`、`ship-backend-design`、`ship-delivery-plan`、`ship-build` 直接消费。
- `ship-define` 启动后必须先 normalize。

normalize 后的 `requirements.md` 必须恢复为结构化 requirements contract：

- `stage: ship-define`
- `stage_status: draft | ready`
- `generation_mode: prd_direct | interview`
- Domain ID 体系
- Acceptance Criteria
- In Scope / Out of Scope
- MoSCoW
- NFR
- 约束与假设
- 待确认问题清单
- 需求资料索引

原始 PRD 处理：

- normalize 前，如果 `requirements.md` 含 raw PRD 原文，应迁移或保留到 `resource/raw-prd.md`。
- normalize 后的 `requirements.md` 不再承载完整原文，只保留结构化 contract 和来源摘要。

## 资料准备态协议

不新增 canonical stage，不新增 stage status 枚举。

统一表达：

```yaml
current_stage: ship-define
stages:
  ship-define:
    status: blocked
    block_reason: awaiting_materials
    evidence_complete: false
```

解除条件：

```text
requirements.md 不是空模板
或
resource/ 下存在至少一个非 README.md 文件
```

解除动作：

```yaml
stages:
  ship-define:
    status: pending
    block_reason: ""
```

`ship-define` 真正开始处理资料时，再将自身状态置为 `in_progress`。

## 需要修改的文件

### `ship-orchestrator/SKILL.md`

- 增加“未携带资料入口”处理流程。
- 调整 Resume Protocol：单个 active feature 也必须询问是否继续。
- 增加无 active feature 时的四种新建模式选择文案。
- 增加 PRD 直通 / 产品提供的资料准备态。
- 明确迭代增强无基线时不创建目录。

### `ship-define/SKILL.md`

- 增加 raw `requirements.md` inbox 输入模式。
- 明确 raw input 到 structured contract 的 normalize 流程。
- PRD 直通和产品提供都可读取 raw `requirements.md`。
- normalize 后将原始 PRD 迁移或保留到 `resource/raw-prd.md`。
- 防止 raw inbox 被误判为可进入下游的 `ready` contract。

### `ship-orchestrator/_templates/meta/meta.yml.template`

- 在 `stages.ship-define` 下增加 `block_reason` 字段。
- 注释说明 `awaiting_materials` 的语义。

### `ship-orchestrator/scripts/feature_meta_runtime.py`

- 初始化 PRD 直通 / 产品提供时支持写入 `blocked + awaiting_materials`。
- 资料解除等待时支持将 `ship-define.status` 改为 `pending` 并清空 `block_reason`。
- 不改变 canonical stage id。

### 新增模板

建议新增：

```text
ship-orchestrator/_templates/requirements/raw-prd-inbox.md.template
ship-orchestrator/_templates/resource/README.md.template
```

## 复查清单

- [x] 未指定 `feature_dir` 时先扫描未完成 feature。
- [x] 单个未完成 feature 也必须询问是否继续。
- [x] 没有未完成 feature 时直接列四种模式。
- [x] PRD 直通允许粘贴完整 PRD 原文到 `requirements.md`。
- [x] 产品提供也允许复用 raw `requirements.md` inbox。
- [x] raw `requirements.md` 不作为下游 contract。
- [x] normalize 后 `requirements.md` 回归结构化 contract。
- [x] 原始 PRD 迁移或保留到 `resource/raw-prd.md`。
- [x] 资料准备态使用 `blocked + block_reason: awaiting_materials`。
- [x] 零到一先建目录，但直接进入 `ship-discover`。
- [x] 迭代增强无基线时不创建目录，先询问。
- [x] 不新增 canonical stage。
- [x] 不新增 stage status 枚举。
