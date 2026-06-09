# 端到端使用案例

## 案例 1：小功能开发（Quick Start）

### 场景
产品经理口头说："加一个忘记密码功能，用户点击后发邮件重置"

### 完整流程

#### 1. 启动
```bash
用户：做一个忘记密码功能
```

Orchestrator 响应：
```
✓ 场景识别：快速启动（小功能，熟悉技术栈）
✓ 起点：Understand

我会快速理解需求（跳过详细质询），大约 2-3 分钟。
让我们开始吧...
```

#### 2. Understand 阶段（3 分钟）

AI 自动生成 requirements.md：
```markdown
---
status: ready
updated_at: "2026-06-09T15:00:00Z"
spec_refs: ["auth-flow", "email-service"]
---

# 需求：忘记密码

## 功能概述
用户可以通过邮箱重置密码。

## Domain 模型
- D-AUTH-003: 密码重置流程

## 验收标准

### AC-1: 发送重置链接
**Given** 用户已注册  
**When** 输入邮箱点击"忘记密码"  
**Then** 收到包含重置链接的邮件

### AC-2: 重置密码
**Given** 用户点击邮件中的链接  
**When** 输入新密码并确认  
**Then** 密码更新成功，可用新密码登录

### AC-3: 链接过期
**Given** 重置链接已发送超过 1 小时  
**When** 用户点击链接  
**Then** 提示链接已过期，需重新申请
```

AI：
```
✅ requirements.md 已生成
✅ 跳过 grill-me（quick_start 模式）

进入下一阶段：Design
```

#### 3. Design 阶段（5 分钟）

AI 加载 spec（auth-flow, email-service），生成 design.md：

```markdown
---
status: ready
spec_refs: ["auth-flow", "email-service", "rest-api-standard"]
---

# 技术设计：忘记密码

## API 契约

### POST /api/v1/auth/forgot-password
**Request**
\`\`\`json
{"email": "user@example.com"}
\`\`\`
**Response - 200**
\`\`\`json
{"message": "重置邮件已发送"}
\`\`\`

### POST /api/v1/auth/reset-password
**Request**
\`\`\`json
{
  "token": "reset_token_here",
  "new_password": "new_pass"
}
\`\`\`

## 数据模型
### password_resets 表（新增）
| 字段 | 类型 | 说明 |
|------|------|------|
| token | varchar(64) | 重置 token |
| user_id | bigint | 用户 ID |
| expires_at | datetime | 过期时间（1小时） |

## 后端设计
- AuthService.sendResetEmail()
- AuthService.resetPassword()
- EmailService.sendPasswordResetEmail()（复用现有）

## 前端设计
- 页面：/forgot-password
- 页面：/reset-password/:token
- 组件：ForgotPasswordForm, ResetPasswordForm
```

AI：
```
✅ design.md 已生成
✅ 符合规范检查通过

设计方案已完成，是否开始实现？
[yes] 开始 Build
[modify] 修改设计
```

用户：`yes`

#### 4. Build 阶段（15 分钟）

AI 自动生成 build-plan.yml：
```yaml
tasks:
  - id: T-001
    name: 创建 password_resets 表
    type: migration
    files: [migrations/003_password_resets.sql]
    
  - id: T-002
    name: 实现 AuthService 重置逻辑
    type: backend
    files: [src/services/auth.service.ts]
    dependencies: [T-001]
    
  - id: T-003
    name: 实现前端页面
    type: frontend
    files: [
      src/pages/ForgotPassword.tsx,
      src/pages/ResetPassword.tsx
    ]
```

AI 按序实现，每个任务完成后运行测试：

```
✓ T-001 完成：数据表已创建
✓ T-002 完成：后端逻辑已实现，6 个单元测试通过
✓ T-003 完成：前端页面已实现

运行集成测试...
✓ 所有测试通过（18 passed）

生成验证报告...
```

verification.md：
```markdown
# 验证报告

## AC 验证
- ✅ AC-1: 发送重置链接 (covered by: auth.service.test.ts)
- ✅ AC-2: 重置密码 (covered by: reset-password.e2e.test.ts)
- ✅ AC-3: 链接过期 (covered by: auth.service.test.ts)

## 测试覆盖
- 单元测试：6 passed
- 集成测试：10 passed
- E2E 测试：2 passed

## 代码质量
- ESLint: 0 errors, 2 warnings
- TypeScript: 0 errors

## 状态
✅ 所有 AC 已验证，功能可交付
```

AI：
```
🎉 功能开发完成！

产出文件：
- migrations/003_password_resets.sql
- src/services/auth.service.ts（新增 2 个方法）
- src/pages/ForgotPassword.tsx
- src/pages/ResetPassword.tsx
- tests/...

下一步：
- 提交代码并创建 PR
- 更新规范库（已自动更新 existing-features.md）

总用时：约 25 分钟
```

---

## 案例 2：中等复杂度（Full Flow）

### 场景
需要开发一个"订单导出"功能，涉及异步任务、权限控制、文件生成

### 完整流程

#### 1. 启动
```bash
用户：做一个订单导出功能，要支持大量数据导出
```

Orchestrator 响应：
```
✓ 场景识别：完整流程（中等复杂度）
✓ 起点：Understand

我会通过质询深入理解需求，预计 5-8 分钟。
```

#### 2. Understand 阶段（含 grill-me）

AI 先生成初步 requirements.md，然后启动 grill-me：

```
grill-me 质询开始...

问题 1/5：导出范围
当前需求未明确：用户可以导出哪些时间范围的订单？

推荐答案：支持自定义时间范围（最长 1 年）
依据：existing-features.md 显示现有"订单查询"支持时间范围筛选

你的决定？
[采纳推荐] / [自定义答案]
```

用户：`采纳推荐`

```
问题 2/5：数据量限制
当前需求未明确：单次导出最多支持多少订单？

推荐答案：单次最多 10 万条，超过则提示分批导出
依据：tech-stack.md 显示 Redis 内存限制，避免 OOM

你的决定？
```

用户：`采纳推荐`

（继续 3 个质询...）

最终生成完整 requirements.md，包含：
- 8 个 AC（权限、范围、格式、进度、通知、错误）
- 非功能需求（导出耗时 < 2 分钟/万条，并发 100）
- 约束（Excel 格式、字段脱敏）

#### 3. Design 阶段（含 grill-me）

AI 生成 design.md 后，再次 grill-me：

```
grill-me 设计审查...

问题 1/3：并发控制
设计方案使用 Redis 队列处理导出任务，但未说明如何限制并发数。

推荐方案：使用 BullMQ 的 concurrency 参数限制为 5
依据：spec/backend/queue-processing.md

是否采纳？
```

用户：`是`

（继续审查...）

最终 design.md 包含：
- 3 个 API（申请导出、查询进度、下载文件）
- 数据模型（export_tasks 表）
- 异步任务流程（BullMQ）
- 权限设计（RBAC）
- 文件存储（OSS）

#### 4. 用户确认

AI：
```
设计方案已完成并通过质量审查。

核心设计：
- 异步任务处理（BullMQ）
- 文件上传 OSS（7 天有效期）
- 进度通知（WebSocket）

是否开始实现？
[yes] / [review] / [modify]
```

用户：`yes`

#### 5. Build 阶段

生成 15 个任务，按依赖顺序实现：
1. 数据层（表、索引）
2. 后端服务（导出逻辑、队列、权限）
3. 前端页面（申请表单、进度条、下载）

总用时：约 1.5 小时

---

## 案例 3：需求拆分场景

### 场景
产品给了一个大需求："完整的用户管理系统"

### 流程

#### 1. 触发拆分
```bash
用户：这个需求太大了，帮我拆分：完整的用户管理系统，包括注册、登录、权限、个人资料管理
```

#### 2. ship-split 分析

AI 分析后生成 splits.yml：
```yaml
parent_requirement: "用户管理系统"
split_strategy: "by_user_story"
estimated_total_days: 12

splits:
  - id: REQ-001
    name: 用户注册
    priority: high
    estimated_days: 2
    dependencies: []
    
  - id: REQ-002
    name: 用户登录
    priority: high
    estimated_days: 1
    dependencies: [REQ-001]
    
  - id: REQ-003
    name: 权限管理（RBAC）
    priority: high
    estimated_days: 3
    dependencies: [REQ-002]
    
  - id: REQ-004
    name: 个人资料管理
    priority: medium
    estimated_days: 2
    dependencies: [REQ-002]
    
  - id: REQ-005
    name: 用户列表和搜索
    priority: low
    estimated_days: 2
    dependencies: [REQ-003]
    
  - id: REQ-006
    name: 用户导入导出
    priority: low
    estimated_days: 2
    dependencies: [REQ-005]
```

AI：
```
拆分方案生成完成。

建议顺序：
1. REQ-001, REQ-002（基础，3 天）
2. REQ-003, REQ-004（核心，5 天）
3. REQ-005, REQ-006（增强，4 天）

是否自动创建 6 个 feature？
[yes] 批量创建
[modify] 修改拆分方案
[tapd] 同步到 TAPD
```

用户：`yes`

#### 3. 批量创建 feature

AI 创建 6 个 feature 目录：
```
.docs/
├── feature-20260609-user-register/
│   └── meta.yml (status: pending, split_parent: user-management)
├── feature-20260609-user-login/
│   └── meta.yml (dependencies: [REQ-001])
├── feature-20260609-rbac/
├── feature-20260609-user-profile/
├── feature-20260609-user-list/
└── feature-20260609-user-import-export/
```

AI：
```
✅ 已创建 6 个 feature

当前可开始：
- REQ-001 用户注册（无依赖）

输入 "继续 REQ-001" 开始开发第一个子需求。
```

---

## 总结

这套流程的优势：
1. **快速启动**：小功能 25 分钟交付
2. **质量保证**：grill-me 确保需求和设计清晰
3. **灵活适配**：支持 quick_start / full_flow / split_first
4. **状态透明**：随时知道当前进度和阻塞点
5. **AI 友好**：简化的状态机，易于 AI 理解和执行
