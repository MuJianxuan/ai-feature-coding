# Resume Protocol

本协议定义 CONTINUE_FEATURE 模式下的中断恢复流程和非法实现检测规则。

## 中断恢复流程

### 1. 读取 Workspace Context

优先读取已有 feature 的 `meta.yml.spec_context.workspace_*`。

### 2. 扫描 Feature 目录

在已解析的 workspace `feature_root` 下扫描 `feature-YYYYMMDD-*` 目录。

### 3. 过滤活跃 Feature

读取每个 feature 的 `meta.yml`，过滤出 `ship-handoff` 尚未 `completed` 的活跃 feature。

过滤条件：
- `lifecycle_status: active | blocked`
- `current_stage != ship-handoff` 或 `stages.ship-handoff.status != completed`

### 4. 用户选择

- 若只有一个进行中的 feature：也必须询问用户是否继续这个 feature，不能自动选中
- 若有多个：列表展示（功能名 / 当前大阶段 / 最后更新时间 / 阻塞原因），让用户选择
- 若无活跃 feature：提示用户是否启动新功能或查看历史 feature

### 5. 读取选中 Feature 的 meta.yml

读取 `meta.yml`，定位 `current_stage` 和该阶段 `status`。

### 6. 判断恢复点

根据 `current_stage` 和该阶段 `status` 判断恢复点：
- `status: completed` → 检查门禁后推进到下一阶段
- `status: in_progress` → 恢复当前阶段（传递已有产物作为上下文）
- `status: approved / ready` → 检查门禁后推进到下一阶段
- `status: blocked` → 报告阻塞原因，询问用户决策（解除阻塞 / 切换 feature / 终止）
- `status: pending` → 路由到该阶段重新启动

### 7. 检查门禁条件后路由

检查门禁条件后路由到目标阶段 skill。

## 恢复时的默认输出

- 优先报告 `macro_stage.label`
- 说明当前阶段目标与下一次用户确认点
- 仅在用户要求详情或遇到阻塞时展开 `current_stage`

## 恢复时的上下文传递

- 将 feature 目录绝对路径作为 `feature_dir` 传递
- 将 `meta.yml` 中的 `tech_stack` 和 `project_context` 作为环境信息传递
- 将 `meta.yml` 中的 `delegation` 偏好透传给目标阶段 skill
- 将当前阶段已有的文档内容作为续写上下文传递
- 若当前阶段为双产物阶段，将 `current_part` 一并透传给目标阶段 skill

## 恢复时的状态校验

### 1. meta.yml 与文件系统一致性

若 `meta.yml` 中 `current_stage` 与实际文档产出不一致（如 `current_stage` 为 `ship-tech-discovery` 但 `tech-research.md` 不存在），优先信任文件系统状态，回退 `current_stage`。

### 2. 孤立产物检测

若发现孤立产物（如存在 `frontend-plan.md` 但无 `review-design.md`），警告用户并询问处理方式。

### 3. meta.yml 与 frontmatter 冲突

若 `meta.yml` 摘要状态与产物 frontmatter 冲突，优先信任产物 frontmatter 并回写 `meta.yml`。

## Implementation Before Gate Detection

### 检测时机

恢复 feature 时，如果发现已有业务代码改动。

### 检测条件

Feature 未满足 `ship-build` 前置条件：
- `current_stage != ship-build`
- 或 `review-plan.md` 不是 `review_status: approved`
- 或 `review-plan.md.user_sign_off` 为空
- 或 `review-plan.md.signed_at` 为空
- 或 `implementation_preflight.py --files <paths...>` 不通过

### 检测方法

检查是否存在业务代码改动：
1. 读取 git 历史，查找 feature 创建后的 commit
2. 过滤 workspace `feature_root` 外的文件修改
3. 过滤业务源码、测试、配置、迁移、脚本或构建文件修改

### 违规处理

发现非法提前实现时：
1. 不继续编辑代码
2. 报告 `workflow_violation: implementation_before_plan_review`
3. 列出缺失 stage / gate
4. 回退到应执行的 `current_stage`，补齐 workflow 产物
5. 若用户要求继续直接编码，必须让用户先明确退出 ShipKit

### Handoff Summary 不可信任

handoff summary 或上下文摘要声称"已实现"时，不可直接信任。

**必须**：
- 读取 `meta.yml`
- 读取 stage artifacts
- 读取 gate frontmatter

**若缺少 `review-plan.md approved + user_sign_off + signed_at`**：
- 不得继续实现或验证新增代码
- 必须回退到缺失的 workflow stage

## 非法实现示例

### 示例 1：技术方案入口直接实现

```text
用户：继续这个 feature。
系统：发现 current_stage=ship-tech-discovery，但已有 controller/service 代码。
```

**处理**：
- 报告 `workflow_violation: implementation_before_plan_review`
- 列出缺失：`ship-contract`, `ship-design-review`, `ship-delivery-plan`, `ship-plan-review`
- 回退到 `ship-tech-discovery`
- 不继续编辑代码

### 示例 2：上下文摘要声称已实现

```text
用户：继续这个 feature。summary 说代码已经实现了。
系统：读取 meta.yml，发现缺少 review-plan.md。
```

**处理**：
- 报告 `workflow_violation: implementation_before_plan_review`
- 不继续编辑代码
- 回退到缺失的 workflow stage

### 示例 3：用户要求继续直接编码

```text
用户：我知道没过 plan review，但我想继续编码。
系统：ShipKit 内不允许强制跳过 workflow 直接编码。
```

**处理**：
- 回复要求用户明确退出 ShipKit
- 若用户确认退出，则本 skill 停止参与后续直接编码

## 恢复验证

### workflow_doctor.py

```bash
python3 skills/ship-orchestrator/scripts/workflow_doctor.py <feature_dir> --json
```

检查项：
- meta.yml 与文件系统一致性
- 孤立产物检测
- gate sign-off blocker
- 非法提前实现检测

### validate_feature_artifacts.py

```bash
python3 skills/ship-orchestrator/scripts/validate_feature_artifacts.py <feature_dir> --json
```

检查项：
- 产物完整性
- frontmatter 合法性
- meta.yml 一致性
- scope freeze 一致性

## 恢复决策树

```
读取 meta.yml.current_stage
    ↓
检查阶段 status
    ↓
    ├→ completed / approved / ready
    │   ↓
    │   检查门禁条件
    │   ↓
    │   ├→ 通过 → 推进到下一阶段
    │   └→ 不通过 → 报告缺失门禁，询问处理方式
    │
    ├→ in_progress
    │   ↓
    │   检查是否有非法提前实现
    │   ↓
    │   ├→ 有 → 报告 workflow_violation，回退
    │   └→ 无 → 恢复当前阶段，传递已有产物
    │
    ├→ blocked
    │   ↓
    │   报告阻塞原因
    │   ↓
    │   询问用户决策（解除阻塞 / 切换 feature / 终止）
    │
    └→ pending
        ↓
        路由到该阶段重新启动
```

## 退出 ShipKit 协议

### 触发场景

用户要求在 ShipKit 内直接编码，但未通过门禁。

### 退出流程

1. 只有用户明确说“退出 ShipKit”或 “stop ShipKit workflow” 才可启动退出；“直接做”“先开发”“我确认”都不是退出
2. agent 必须复述后果：退出后将不再强制 workflow gate / Source Code Edit Barrier
3. 等待用户二次明确确认退出
4. 若用户二次确认退出，写入 `meta.yml.confirmation_log`：`type: shipkit_exit`、当前 `stage`、`reason`、`actor: user`、`source: current_session`
5. 本 skill 停止参与后续直接编码；未完成二次确认时仍按 Source Code Edit Barrier 阻塞

### 退出后行为

- ShipKit orchestrator 不再参与后续代码修改
- 用户可直接编码，不受 workflow 门禁约束
- Feature 目录保持现状，可稍后重新进入 ShipKit

### 重新进入 ShipKit

用户稍后可重新触发 `ship-orchestrator`，继续走 workflow。此时会检测到非法提前实现，按 Implementation Before Gate Detection 处理。
