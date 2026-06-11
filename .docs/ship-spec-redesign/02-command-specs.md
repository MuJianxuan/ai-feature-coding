# ship-spec 命令详细规范

## 1. create-spec

### 用途
创建新的规范文件

### 输入
```typescript
{
  command: 'create-spec',
  spec_id: string,              // 规范唯一标识（kebab-case）
  type: 'frontend' | 'backend' | 'shared' | 'project-specific',
  projects: string[],           // 适用项目列表，['all'] 表示所有项目
  stages: ('understand' | 'design' | 'build' | 'done')[],
  tags?: string[],              // 可选标签
  template?: string,            // 可选模板名称
  description: string,          // 规范描述
  interactive?: boolean         // 是否交互式填充内容
}
```

### 输出
```typescript
{
  success: boolean,
  spec_id: string,
  file_path: string,
  next_steps: string[],         // 提示用户下一步操作
  warnings?: string[]
}
```

### 执行流程
1. 验证 spec_id 唯一性（检查 INDEX.md）
2. 确定文件路径（根据 type 和 projects）
3. 加载模板（如果指定）或创建空白模板
4. 写入规范文件
5. 更新 INDEX.md
6. 重建 .index.json
7. 返回结果

### 示例
```bash
# 命令行
ship-spec create-spec \
  --spec-id rest-api-standard \
  --type backend \
  --projects api \
  --stages design,build \
  --tags api,rest,backend \
  --template api-standard \
  --description "REST API 规范"

# API 调用
await callSkill('ship-spec', {
  command: 'create-spec',
  spec_id: 'rest-api-standard',
  type: 'backend',
  projects: ['api'],
  stages: ['design', 'build'],
  tags: ['api', 'rest', 'backend'],
  template: 'api-standard',
  description: 'REST API 规范'
});
```

---

## 2. update-spec

### 用途
更新现有规范内容

### 输入
```typescript
{
  command: 'update-spec',
  spec_id: string,
  operation: 'append' | 'replace' | 'merge' | 'edit-section',
  content?: string,             // append/replace 模式
  section?: string,             // edit-section 模式
  metadata?: {                  // 更新元数据
    projects?: string[],
    stages?: string[],
    tags?: string[],
    status?: 'draft' | 'active' | 'deprecated',
    depends_on?: string[]
  },
  reason?: string,              // 更新原因（记录到 changelog）
  create_snapshot?: boolean     // 是否创建快照
}
```

### 输出
```typescript
{
  success: boolean,
  spec_id: string,
  changes: {
    metadata_updated: boolean,
    content_updated: boolean,
    snapshot_created?: string   // 快照路径
  },
  diff?: string,                // 可选的内容 diff
  warnings?: string[]
}
```

### 执行流程
1. 验证 spec_id 存在
2. 创建快照（如果请求）
3. 根据 operation 更新内容
4. 更新元数据（如果提供）
5. 更新 INDEX.md
6. 重建 .index.json
7. 返回结果和 diff

---

## 3. delete-spec

### 用途
删除或归档规范

### 输入
```typescript
{
  command: 'delete-spec',
  spec_id: string,
  archive: boolean,             // true=归档，false=彻底删除
  force?: boolean               // 忽略依赖检查
}
```

### 输出
```typescript
{
  success: boolean,
  spec_id: string,
  action: 'deleted' | 'archived',
  archive_path?: string,        // 归档路径
  warnings?: string[],          // 依赖警告
  impacted_specs?: string[]     // 受影响的规范
}
```

### 执行流程
1. 验证 spec_id 存在
2. 检查依赖（其他规范是否依赖此规范）
3. 如果有依赖且 force=false，返回警告并阻止
4. 执行删除或归档
5. 更新 INDEX.md
6. 重建 .index.json

---

## 4. update-existing-features

### 用途
Build 完成后更新已有功能索引

### 输入
```typescript
{
  command: 'update-existing-features',
  feature_meta_path: string,    // feature meta.yml 路径
  implementation_summary: {
    module?: string,            // 功能模块
    feature: string,            // 功能名称
    tables?: string[],          // 涉及的数据表
    apis?: string[],            // 涉及的 API
    pages?: string[],           // 涉及的页面
    components?: string[],      // 涉及的组件
    tests?: string[],           // 关键测试文件
    dependencies?: string[],    // 新增的依赖
    config_changes?: string[]   // 配置变更
  }
}
```

### 输出
```typescript
{
  success: boolean,
  updated_files: string[],      // 更新的 existing-features 文件
  entry_added: {
    module: string,
    feature: string,
    completed_at: string,
    feature_dir: string
  }
}
```

### 执行流程
1. 读取 feature meta.yml 获取项目信息
2. 确定要更新的 existing-features 文件（shared 或项目专属）
3. 解析现有内容，找到对应模块
4. 追加或更新功能条目
5. 写回文件
6. 重建 .index.json（更新 keywords）

### 格式示例
```markdown
## 用户模块
- **用户登录**：完成时间 2026-06-09，Feature: feature-20260609-user-login
  - 表：users, sessions
  - API：POST /api/v1/auth/login
  - 页面：/login
  - 关键测试：tests/e2e/login.spec.ts

- **用户注册**：完成时间 2026-06-11，Feature: feature-20260611-user-register
  - 表：users, email_verifications
  - API：POST /api/v1/auth/register
  - 页面：/register
  - 关键测试：tests/e2e/register.spec.ts
```

---

## 5. sync-index

### 用途
同步 INDEX.md 和 .index.json

### 输入
```typescript
{
  command: 'sync-index',
  scan_path?: string,           // 默认 .docs/spec
  auto_fix: boolean,            // 自动修复不一致
  rebuild_json: boolean         // 强制重建 .index.json
}
```

### 输出
```typescript
{
  success: boolean,
  changes: {
    added: string[],            // 新增的 spec
    removed: string[],          // 删除的 spec
    updated: string[],          // 更新的 spec
    conflicts: Array<{
      spec_id: string,
      issue: string
    }>
  },
  index_json_rebuilt: boolean
}
```

### 执行流程
1. 扫描 .docs/spec 目录下的所有 .md 文件
2. 解析每个文件的 frontmatter（spec_id、metadata）
3. 与 INDEX.md 对比
4. 标记新增、删除、不一致
5. 如果 auto_fix=true，自动修复 INDEX.md
6. 重建 .index.json

---

## 6. search

### 用途
搜索规范

### 输入
```typescript
{
  command: 'search',
  query: string,                // 搜索关键词
  options?: {
    field?: 'metadata' | 'content' | 'all',  // 搜索范围
    project?: string,           // 过滤项目
    stage?: string,             // 过滤阶段
    type?: string,              // 过滤类型
    status?: string,            // 过滤状态
    tags?: string[],            // 按标签过滤
    format?: 'table' | 'json' | 'markdown',  // 输出格式
    limit?: number,             // 结果数量限制
    verbose?: boolean           // 是否显示匹配内容
  }
}
```

### 输出
```typescript
{
  query: string,
  filters: object,
  total: number,
  results: Array<{
    spec_id: string,
    file: string,
    projects: string[],
    stages: string[],
    tags: string[],
    status: string,
    description: string,
    score: number,              // 相关性评分
    matches?: Array<{           // verbose=true 时包含
      line: number,
      text: string,
      context_before: string[],
      context_after: string[]
    }>
  }>
}
```

### 搜索策略
1. 精确 spec_id 匹配（最高优先级）
2. 元数据搜索（.index.json）
3. 全文搜索（读取实际文件）

---

## 7. suggest-new-spec

### 用途
评估是否应该沉淀新规范

### 输入
```typescript
{
  command: 'suggest-new-spec',
  feature_history_count: number,  // 分析最近 N 个 features
  pattern_description?: string,   // 要评估的模式描述
  auto_analyze: boolean           // 自动识别重复模式
}
```

### 输出
```typescript
{
  suggestions: Array<{
    pattern_type: string,       // 模式类型（API命名、数据结构等）
    score: number,              // 评分 0-100
    evaluation: {
      reuse_count: number,      // 复用次数
      stability: string,        // 稳定性（high/medium/low）
      cross_module: boolean,    // 是否跨模块使用
      complexity: string        // 复杂度（high/medium/low）
    },
    recommendation: 'create' | 'wait' | 'reject',
    suggested_spec_id?: string,
    template_content?: string   // 建议的规范内容
  }>,
  analysis_summary: string
}
```

### 评分规则
- 复用次数 ≥ 3：+40
- 模式稳定：+30
- 跨模块使用：+20
- 中高复杂度：+10
- 总分 ≥ 60：建议创建

---

## 8. validate

### 用途
验证规范完整性和一致性

### 输入
```typescript
{
  command: 'validate',
  scope: 'single' | 'all' | 'by-project',
  spec_id?: string,             // single 模式必需
  project?: string,             // by-project 模式必需
  checks?: string[]             // 指定检查项
}
```

### 输出
```typescript
{
  valid: boolean,
  errors: Array<{
    spec_id: string,
    file: string,
    type: 'missing_field' | 'format_error' | 'sensitive_info' | 
          'broken_link' | 'naming_conflict' | 'dependency_missing',
    message: string,
    line?: number
  }>,
  warnings: Array<{
    spec_id: string,
    message: string
  }>,
  summary: {
    total_specs: number,
    valid_specs: number,
    error_count: number,
    warning_count: number
  }
}
```

### 检查项
1. **必需字段**：spec_id、description、stages、projects
2. **格式规范**：markdown 标题层级、表格格式
3. **敏感信息**：检测 password、token、secret、API key
4. **链接完整性**：depends_on 引用的规范存在
5. **命名冲突**：不同文件的相同 spec_id
6. **INDEX 一致性**：INDEX.md 与实际文件一致

---

## 9. stats

### 用途
规范使用统计

### 输入
```typescript
{
  command: 'stats',
  time_range?: '30d' | '90d' | 'all',
  sort_by?: 'usage' | 'last_updated' | 'size'
}
```

### 输出
```typescript
{
  summary: {
    total_specs: number,
    active_specs: number,
    deprecated_specs: number,
    total_size_kb: number
  },
  most_used: Array<{
    spec_id: string,
    reference_count: number,    // 被多少 features 引用
    last_used: string
  }>,
  unused: Array<{
    spec_id: string,
    last_updated: string,
    reason: string              // 为什么算未使用
  }>,
  largest: Array<{
    spec_id: string,
    size_kb: number,
    complexity: string
  }>
}
```

### 统计来源
- reference_count：从 existing-features 中的 feature 条目反向统计
- last_used：从 feature 的完成时间推断
- size：文件大小
- complexity：章节数量、代码块数量
