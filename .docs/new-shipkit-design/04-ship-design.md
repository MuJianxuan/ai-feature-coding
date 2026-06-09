# ship-design 详细设计

## 目标
基于 requirements.md 和 spec，产出完整的技术设计方案。

## 输入
- `requirements.md`（status: ready）
- 从 spec 加载：技术栈、设计规范、API 规范、数据模型规范
- 现有代码库结构

## 核心流程

```
加载 spec → 技术调研 → 方案设计 → grill-me 审查 → 生成 design.md
```

### Step 1: 加载 spec 规范
```python
def load_design_context(feature_dir):
    """加载设计相关规范"""
    spec_loader = SpecLoader(workspace_config)
    
    return {
        "api_standards": spec_loader.load_specs(["backend"]),
        "frontend_patterns": spec_loader.load_specs(["frontend"]),
        "data_model": spec_loader.load_specs(["shared", "database"]),
        "tech_stack": spec_loader.load_tech_stack()
    }
```

### Step 2: 技术调研（按需）
- 新技术选型时才做详细调研
- 熟悉技术栈直接引用 spec 规范
- 记录调研依据和选型理由

### Step 3: 方案设计
合并 API Contract + 前后端方案到一份 design.md：

**包含内容**：
- API 接口定义（path, method, request, response）
- 数据模型（表结构/Entity）
- 前端页面结构和状态管理
- 后端服务分层和调用链
- 关键流程时序图

### Step 4: grill-me 审查
在标记 `status: ready` 之前，审查：

```python
def run_design_grill_me(design_draft):
    """审查设计完整性"""
    questions = [
        # 检查契约完整性
        check_api_contract_completeness(),
        # 检查数据模型一致性
        check_data_model_consistency(),
        # 检查与现有系统的集成点
        check_integration_points(),
        # 检查性能瓶颈
        check_performance_risks()
    ]
    
    for q in questions:
        if q.is_blocking:
            answer = ask_user(q)
            update_design(answer)
    
    return "ready" if no_blocking_issues else "blocked"
```

grill-me 关注点：
- API 契约是否符合 spec 规范？
- 错误处理是否完整？
- 数据模型是否考虑扩展性？
- 前后端责任边界是否清晰？
- 性能指标如何满足？

### Step 5: 生成 design.md

```markdown
---
status: ready
updated_at: "2026-06-09T14:00:00Z"
spec_refs: ["rest-api-standard", "react-patterns", "mysql-conventions"]
---

# 技术设计：用户登录

## API 契约

### POST /api/v1/auth/login
**Request**
\`\`\`json
{
  "email": "user@example.com",
  "password": "hashed_password"
}
\`\`\`

**Response - 200 OK**
\`\`\`json
{
  "token": "jwt_token",
  "user": {
    "id": 123,
    "name": "张三",
    "email": "user@example.com"
  }
}
\`\`\`

**Response - 401 Unauthorized**
\`\`\`json
{
  "error_code": "AUTH_FAILED",
  "message": "邮箱或密码错误"
}
\`\`\`

## 数据模型

### User 表（复用现有）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigint | 主键 |
| email | varchar(255) | 邮箱（唯一） |
| password_hash | varchar(255) | bcrypt 加密 |
| login_attempts | int | 登录失败次数 |
| locked_until | datetime | 锁定截止时间 |

### Session 表（新增）
| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigint | 主键 |
| user_id | bigint | 外键 |
| token | varchar(500) | JWT token |
| expires_at | datetime | 过期时间 |

## 前端设计

### 页面：/login
- **组件**：LoginForm
- **状态管理**：zustand (auth store)
- **表单校验**：zod + react-hook-form
- **错误处理**：toast 提示

### 核心逻辑
\`\`\`typescript
const loginMutation = useMutation({
  mutationFn: (data) => api.post('/auth/login', data),
  onSuccess: (response) => {
    authStore.setUser(response.user);
    authStore.setToken(response.token);
    router.push('/dashboard');
  }
});
\`\`\`

## 后端设计

### 服务分层
\`\`\`
Controller (AuthController)
    ↓
Service (AuthService)
    ↓
Repository (UserRepository, SessionRepository)
\`\`\`

### 核心流程
1. 接收请求，校验参数格式
2. 查询 User 表，检查 locked_until
3. 验证密码（bcrypt.compare）
4. 失败：增加 login_attempts，3 次后锁定 30 分钟
5. 成功：生成 JWT token，写入 Session 表
6. 返回 token 和用户信息

## 性能考量
- Redis 缓存 user session（TTL 30 分钟）
- 数据库索引：users.email
- JWT 过期时间：7 天
```

## 输出
- `design.md`（status: ready）
- 更新 `meta.yml.current_stage = build`
- 等待用户确认："设计方案已完成，是否开始实现？"
