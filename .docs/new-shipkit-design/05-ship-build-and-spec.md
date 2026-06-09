# ship-build 和 spec 详细设计

## ship-build（实现验证）

### 目标
基于 design.md 实现代码，并验证所有 AC。

### 输入
- `design.md`（status: approved by user）
- 从 spec 加载：编码规范、测试规范

### 核心流程

```
生成任务清单 → 按序实现 → 运行测试 → AC 验证 → 生成报告
```

### Step 1: 生成任务清单
根据 design.md 自动生成：

```yaml
# build-plan.yml
tasks:
  - id: "T-001"
    name: "创建 Session 表迁移"
    type: database
    files: ["migrations/001_create_sessions.sql"]
    ac_refs: ["AC-1", "AC-2"]
    
  - id: "T-002"
    name: "实现 AuthService.login"
    type: backend
    files: ["src/services/auth.service.ts"]
    dependencies: ["T-001"]
    ac_refs: ["AC-1", "AC-2"]
    
  - id: "T-003"
    name: "实现 LoginForm 组件"
    type: frontend
    files: ["src/components/LoginForm.tsx"]
    ac_refs: ["AC-1"]
```

### Step 2: 按序实现
遵循规则：
- 先数据层（migration）
- 再后端（API）
- 最后前端（UI）
- 每个任务完成后运行相关测试

### Step 3: 持续验证
每完成一个任务：

```python
def verify_task(task_id):
    """验证任务完成"""
    task = load_task(task_id)
    
    # 运行相关测试
    test_results = run_tests(task.test_files)
    
    # 检查 AC 覆盖
    ac_coverage = check_ac_coverage(task.ac_refs)
    
    return {
        "task_id": task_id,
        "tests_passed": test_results.passed,
        "ac_covered": ac_coverage.covered
    }
```

### Step 4: 最终验证报告

```markdown
# 验证报告

## AC 验证状态
- ✅ AC-1: 正常登录 (covered by: e2e-test-login.spec.ts)
- ✅ AC-2: 密码错误 (covered by: auth.service.test.ts)

## 测试覆盖
- 单元测试：15 passed
- 集成测试：3 passed
- E2E 测试：2 passed

## 代码质量
- ESLint: 0 errors
- TypeScript: 0 errors
- 测试覆盖率：87%

## 产出文件
- migrations/001_create_sessions.sql
- src/services/auth.service.ts
- src/components/LoginForm.tsx
- tests/...

## 状态
✅ 所有 AC 已验证，可交付
```

---

## ship-spec（规范管理）增强设计

### 目标
维护项目知识库，供其他阶段加载使用。

### 核心功能

#### 1. 规范分类

```
.docs/spec/
├── INDEX.md                    # 规范索引
├── frontend/
│   ├── react-patterns.md      # React 开发规范
│   ├── state-management.md    # 状态管理规范
│   └── component-design.md    # 组件设计规范
├── backend/
│   ├── rest-api-standard.md   # API 规范
│   ├── service-layer.md       # 服务层规范
│   └── database-conventions.md # 数据库规范
└── shared/
    ├── error-codes.md         # 错误码规范
    ├── tech-stack.md          # 技术栈清单
    └── existing-features.md   # 已有功能清单
```

#### 2. 已有功能索引

```markdown
# existing-features.md

## 用户模块
- **用户注册**：完成时间 2026-05-10，Feature: feature-20260510-user-register
  - 表：users
  - API：POST /api/v1/auth/register
  - 页面：/register

- **用户登录**：进行中，Feature: feature-20260609-user-login
  - 表：users, sessions
  - API：POST /api/v1/auth/login
  - 页面：/login

## 订单模块
- **订单创建**：完成时间 2026-04-20
  - 表：orders, order_items
  - API：POST /api/v1/orders
  - 页面：/orders/create
```

#### 3. 技术栈清单

```markdown
# tech-stack.md

## 前端
- Framework: React 18.2
- Router: React Router 6
- State: Zustand 4.5
- Forms: React Hook Form + Zod
- HTTP: Axios
- UI: Ant Design 5.x

## 后端
- Runtime: Node.js 20
- Framework: Express 4.x
- ORM: Prisma 5.x
- Auth: JWT
- Cache: Redis 7.x

## 数据库
- Primary: MySQL 8.0
- Cache: Redis 7.x

## 测试
- Unit: Vitest
- E2E: Playwright
```

#### 4. 多项目支持

```yaml
# .docs/ship/project.yml
workspace_mode: project_group
workspace_name: my-workspace
projects:
  - web      # 前端项目
  - api      # 后端项目
  - admin    # 管理后台
```

目录结构：
```
workspace/
├── .docs/
│   ├── ship/project.yml
│   └── spec/
│       ├── INDEX.md           # 顶层导航
│       ├── _shared/           # 跨项目规范
│       │   ├── INDEX.md
│       │   ├── error-codes.md
│       │   └── tech-stack.md
│       ├── web/              # web 项目规范
│       │   ├── INDEX.md
│       │   └── frontend/...
│       └── api/              # api 项目规范
│           ├── INDEX.md
│           └── backend/...
├── web/
├── api/
└── admin/
```

#### 5. 加载机制

```python
class SpecLoader:
    def __init__(self, workspace_config):
        self.config = workspace_config
        self.spec_root = f"{workspace_config.root}/.docs/spec"
    
    def load_for_stage(self, stage, project=None):
        """按阶段加载相关规范"""
        index = self._parse_index(project)
        
        # 过滤适用当前阶段的规范
        specs = [
            spec for spec in index
            if stage in spec.stage_hooks
        ]
        
        return {
            spec.spec_id: self._load_spec(spec.path)
            for spec in specs
        }
    
    def load_existing_features(self):
        """加载已有功能清单"""
        return self._load_spec("shared/existing-features.md")
    
    def load_tech_stack(self):
        """加载技术栈"""
        return self._load_spec("shared/tech-stack.md")
```

#### 6. 自动更新机制

在 ship-build 完成后：

```python
def update_spec_after_build(feature_dir):
    """构建完成后更新规范"""
    feature_meta = load_meta(feature_dir)
    
    # 更新已有功能清单
    update_existing_features({
        "name": feature_meta.feature_name,
        "completed_at": feature_meta.updated_at,
        "tables": extract_tables_from_migration(),
        "apis": extract_apis_from_design(),
        "pages": extract_pages_from_frontend()
    })
    
    # 提示是否沉淀新规范
    if has_reusable_patterns(feature_dir):
        suggest_new_spec(patterns)
```

### 何时使用 spec
- **ship-understand**: 加载 existing-features, domain-glossary
- **ship-design**: 加载 api-standards, frontend-patterns, tech-stack
- **ship-build**: 加载 coding-conventions, test-standards
- **完成后**: 更新 existing-features
