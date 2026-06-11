# ship-spec 技能架构设计

## 核心定位

**规范管理器（Spec Manager）**：专注于项目开发规范和项目信息的 CRUD 操作。

## 职责边界

### ✅ ship-spec 负责
- 创建、更新、删除规范文件
- 维护 INDEX.md 和 .index.json
- 规范验证和 lint
- 规范搜索和查询
- existing-features 索引维护
- 规范沉淀评估和建议

### ❌ ship-spec 不负责
- 主动加载规范并分发给其他技能
- 管理其他技能的 TODO
- 介入 Understand/Design/Build 流程
- 验证其他技能是否正确使用规范

### ✅ 其他技能负责
- 读取 INDEX.md 或调用搜索 API 找到需要的规范
- 根据阶段和项目范围过滤和加载规范
- 将规范内容注入到自己的工作上下文
- 调用 ship-spec 仅用于更新规范（如 Build 完成后）

## 命令架构

```
ship-spec
├── create-spec          # 创建新规范
├── update-spec          # 更新现有规范
├── delete-spec          # 删除/归档规范
├── update-existing-features  # 更新功能索引
├── sync-index           # 同步 INDEX.md 和 .index.json
├── search               # 搜索规范
├── suggest-new-spec     # 评估是否沉淀新规范
├── validate             # 验证规范完整性
└── stats                # 规范使用统计
```

## 数据结构

### INDEX.md（人类可读）
```markdown
| spec_id | file | stages | projects | tags | status | last_updated | description |
|---|---|---|---|---|---|---|---|
| rest-api-standard | backend/rest-api-standard.md | design,build | api | api,rest,backend | active | 2026-06-10 | REST API 规范 |
```

### .index.json（机器可读，自动生成）
```json
{
  "version": "1.0",
  "last_updated": "2026-06-11T10:00:00Z",
  "specs": [
    {
      "spec_id": "rest-api-standard",
      "file": "backend/rest-api-standard.md",
      "projects": ["api"],
      "stages": ["design", "build"],
      "tags": ["api", "rest", "backend"],
      "status": "active",
      "description": "REST API 规范",
      "last_modified": "2026-06-10",
      "depends_on": ["error-codes"],
      "sections": [
        {"title": "错误处理", "line": 45},
        {"title": "认证方式", "line": 102}
      ],
      "keywords": ["error", "authentication", "status code"]
    }
  ]
}
```

## 目录结构

### 单项目
```
.docs/
├── ship/
│   └── project.yml
└── spec/
    ├── INDEX.md
    ├── .index.json
    ├── frontend/
    ├── backend/
    └── shared/
        ├── tech-stack.md
        ├── existing-features.md
        └── error-codes.md
```

### 多项目
```
.docs/
├── ship/
│   └── project.yml
└── spec/
    ├── INDEX.md
    ├── .index.json
    ├── _shared/
    │   ├── tech-stack.md
    │   └── error-codes.md
    ├── web/
    │   ├── frontend/
    │   └── naming-conventions.md
    └── api/
        ├── backend/
        └── rest-api-standard.md
```

## 与其他技能的交互

### 场景 1：ship-design 读取规范
```javascript
// ship-design 调用 ship-spec 搜索
const specs = await callSkill('ship-spec', {
  command: 'search',
  query: 'api',
  options: {
    stage: 'design',
    project: 'web',
    format: 'json'
  }
});

// 读取具体规范文件
const apiStandard = await read(specs.results[0].file);
```

### 场景 2：ship-build 完成后更新 existing-features
```javascript
await callSkill('ship-spec', {
  command: 'update-existing-features',
  feature_meta_path: 'feature-20260611-xxx/meta.yml',
  implementation_summary: {
    module: '用户模块',
    feature: '用户登录',
    tables: ['users', 'sessions'],
    apis: ['POST /api/v1/auth/login'],
    pages: ['/login'],
    tests: ['tests/e2e/login.spec.ts']
  }
});
```

## 扩展性设计

### 1. 规范模板系统
内置模板库 + 用户自定义模板：
```
skills/ship-spec/templates/
├── api-standard.md
├── naming-conventions.md
└── frontend-patterns.md
```

### 2. 插件机制
支持自定义 lint 规则、搜索策略、格式化器：
```javascript
// 用户可在 .docs/ship/plugins/ 添加自定义插件
exports.lintRules = {
  'no-sensitive-info': (content) => { /* 检查逻辑 */ }
};
```

### 3. 版本化支持
关键规范支持版本管理，旧 feature 可固定到特定版本。
