---
doc_type: implementation_plan
doc_status: complete
updated_at: 2026-05-23T00:00:00+08:00
---

# Ship Skills 精简方案

## 1. 摘要

目标不是减少实际治理动作，而是降低对外认知负担。

方案核心：

- 对外只展示 `4` 个大阶段：`Define → Design → Build → Close`
- 内部继续保留 `14` 个 canonical stages、三道硬门禁、现有产物和 fast-track 规则
- 默认用户只和 `ship-orchestrator` 交互
- `meta.yml` 新增 `macro_stage`，承载默认展示视图

预期收益：

- 新用户不再需要先学习一长串阶段名
- 内部流程不丢失，可继续精确恢复、诊断和门禁控制
- 文档、协议、模板与示例在同一套阶段语义下对齐

## 2. 关键改动

### 2.1 对外展示模型

默认对外只展示：

- 当前大阶段
- 当前目标
- 下一次需要用户确认的动作

默认不展示完整内部阶段序列。只有在以下场景展开 `current_stage`：

- 恢复断点
- 排查阻塞
- 直接调用具体阶段 skill
- 高级模式诊断

### 2.2 双层阶段模型

新增双层语义：

- `current_stage`：内部 canonical stage id，继续作为恢复与路由事实源
- `macro_stage`：默认对外展示视图

映射关系：

| `macro_stage.current` | `macro_stage.label` | 包含的 `current_stage` |
| --- | --- | --- |
| `define` | `Define` | `ship-intake`, `ship-intake-review` |
| `design` | `Design` | `ship-research`, `ship-stack`, `ship-contract`, `ship-frontend-design`, `ship-backend-design`, `ship-design-review` |
| `build` | `Build` | `ship-frontend-plan`, `ship-backend-plan`, `ship-plan-review`, `ship-build`, `ship-verify` |
| `close` | `Close` | `ship-handoff` |

### 2.3 元数据与接口

`meta.yml` 新增：

```yaml
macro_stage:
  current: ""              # define | design | build | close
  label: ""                # Define | Design | Build | Close
  summary: ""              # 面向用户的阶段摘要
  next_user_decision: ""   # 下一次需要用户确认的动作
```

约束：

- `current_stage` 仍然只允许 canonical stage id
- `macro_stage` 是索引与展示层字段，不替代 `current_stage`
- 每次 `current_stage` 切换时，必须同步刷新 `macro_stage`

### 2.4 文档与模板

需要同步收敛的对象：

- 根 `README.md`
- `skills/README.md`
- `ship-orchestrator/SKILL.md`
- `workflow-protocol.md`
- `meta.yml.template`
- `todo-app-example` 示例说明

原则：

- 首屏只讲 `4` 个大阶段
- `14` 个细阶段下沉到 advanced / internal / protocol 视图
- 维护说明必须挂接到可执行校验命令

### 2.5 可执行校验与最小 runtime

补一层最小可执行能力，避免 `macro_stage` 只存在于文档：

- `workflow_stage_map.py`
  - 固化 `current_stage -> macro_stage` 映射
  - 可输出列表或单阶段映射结果
- `validate_workflow_docs.py`
  - 校验协议、模板、README、示例说明是否一致
- `feature_meta_runtime.py`
  - `init`：创建 feature 时初始化 `meta.yml`，并写入 `macro_stage`
  - `refresh`：恢复 feature 时根据 `current_stage` 自动刷新 `macro_stage`

## 3. 实施步骤

1. 收敛根 README 与 `skills/README.md`
   - verify: 默认视图统一为 `Define → Design → Build → Close`
2. 更新 `ship-orchestrator/SKILL.md`
   - verify: 默认对外响应改为大阶段摘要，细阶段退到高级模式
3. 扩展 `workflow-protocol.md` 与 `meta.yml.template`
   - verify: `macro_stage` 成为正式协议字段
4. 修复示例与模板说明
   - verify: `todo-app-example` 能说明 `macro_stage` / `current_stage` 双层视图
5. 增加可执行脚本
   - verify: 可通过脚本输出映射、自动检查文档一致性、并在 init/refresh 时写入 `macro_stage`

## 4. 测试与验收

需要验证的场景：

- 新用户阅读主 README 时，只看到 `4` 个大阶段
- CONTINUE 场景默认显示 `macro_stage.label`
- INSPECT 场景默认显示当前大阶段，内部阶段只在高级视图展开
- `meta.yml.template`、协议和 orchestrator 文档对 `macro_stage` 字段定义一致
- 示例文档不再误导为完整运行时快照
- 校验脚本可通过
- `feature_meta_runtime.py init` 创建的 `meta.yml` 自动带有正确的 `macro_stage`
- `feature_meta_runtime.py refresh` 会根据 `current_stage` 自动重算 `macro_stage`

本次实现的最小验收命令：

```bash
python3 skills/ship-orchestrator/scripts/validate_workflow_docs.py
python3 skills/ship-orchestrator/scripts/workflow_stage_map.py --list
python3 skills/ship-orchestrator/scripts/feature_meta_runtime.py init .docs/feature-YYYYMMDD-demo --feature-name "Demo Feature" --feature-id "feature-YYYYMMDD-demo"
python3 skills/ship-orchestrator/scripts/feature_meta_runtime.py refresh .docs/feature-YYYYMMDD-demo/meta.yml
```

## 5. 假设与默认决策

- 不合并内部 skill，只先精简对外呈现
- 三道硬门禁全部保留
- 现有产物文件名不变
- fast-track 规则不变
- `macro_stage` 只作为索引/展示字段，不改变 canonical routing
- 本轮优先处理文档、协议、模板和最小 runtime helper，不实现完整 runtime orchestrator

## 6. 已落地结果

当前已完成：

- 文档层收敛为 `4` 个大阶段
- 协议层补齐 `macro_stage`
- `meta.yml.template` 补齐 `macro_stage`
- 示例层补齐 `meta-view-example.md`
- 可执行层新增映射脚本、校验脚本和 `feature_meta_runtime.py`

后续若继续推进，优先项是：

- 增加真正的 orchestrator runtime 或 inspect/resume helper
- 让创建、恢复、状态汇总都直接消费同一套 runtime 脚本
