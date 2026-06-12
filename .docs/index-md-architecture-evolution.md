# INDEX.md 架构演进分析

## 当前架构：INDEX.md 单文件索引

### 设计原理
```
.docs/spec/
├── INDEX.md                    # 所有规范的元数据中心
├── frontend/
│   ├── component-patterns.md
│   └── state-management.md
└── backend/
    └── rest-api-standard.md
```

**INDEX.md 结构**：
```markdown
| spec_id | file | stages | projects | tags | status | description |
|---------|------|--------|----------|------|--------|-------------|
| rest-api-standard | backend/rest-api-standard.md | design,build | all | api,rest,backend | active | REST API 设计规范 |
| component-patterns | frontend/component-patterns.md | build | web | frontend,react | active | 组件设计模式 |
| state-management | frontend/state-management.md | design,build | web | frontend,state | active | 状态管理规范 |
```

### 为什么说是"权宜之计"？

**优点（短期）**：
- ✅ 零依赖：纯文本，任何工具可读
- ✅ Git 友好：Markdown diff 直观
- ✅ AI 友好：LLM 直接理解，无需解析
- ✅ 实现简单：不需要数据库或额外服务

**架构债务（长期）**：
- ❌ 并发写入冲突
- ❌ 查询性能瓶颈
- ❌ 元数据不可扩展
- ❌ 缺少关系表达能力

---

## 问题 1：并发写入冲突（典型场景）

### 场景：两个开发者同时创建规范

**时间线**：
```
T0: INDEX.md 有 50 个规范

T1: Alice 创建 error-handling.md
    - ship-spec create error-handling
    - 读取 INDEX.md（50 行）
    - 追加 1 行
    - 写入 INDEX.md（51 行）

T2: Bob 创建 logging-standard.md（并发）
    - ship-spec create logging-standard
    - 读取 INDEX.md（50 行）← 还没看到 Alice 的变更
    - 追加 1 行
    - 写入 INDEX.md（51 行）← 覆盖了 Alice 的变更
```

**结果**：
```bash
git status
# modified: INDEX.md

git diff INDEX.md
# <<<<<<< HEAD
# | error-handling | ... |
# =======
# | logging-standard | ... |
# >>>>>>> refs/heads/feature-logging
```

### 为什么会发生？

**单文件索引的本质问题**：
```
Read → Modify → Write（非原子操作）

线程 A: Read(50) → Modify(+1) → Write(51)
线程 B: Read(50) → Modify(+1) → Write(51) ← 丢失了 A 的修改
```

### 现实影响

**小团队（< 5人）**：
- 规范创建频率低（周均 < 2 次）
- 冲突概率 < 5%
- 手动解决冲突可接受

**中型团队（10-20人）**：
- 规范创建频率高（周均 5-10 次）
- 冲突概率 20-30%
- 手动解决冲突成本高

**大型团队（> 50人）**：
- Monorepo，多团队并行开发
- 冲突概率 > 50%
- **INDEX.md 成为瓶颈**

### Git 冲突解决的痛苦

```bash
# Alice 提交
git add INDEX.md
git commit -m "Add error-handling spec"
git push
# ✅ Push 成功

# Bob 提交（晚 10 秒）
git add INDEX.md
git commit -m "Add logging-standard spec"
git push
# ❌ rejected: non-fast-forward

git pull
# CONFLICT (content): Merge conflict in .docs/spec/INDEX.md
```

**INDEX.md 冲突内容**：
```markdown
| spec_id | file | stages | projects | tags | status | description |
|---------|------|--------|----------|------|--------|-------------|
| ... | ... | ... | ... | ... | ... | ... |
<<<<<<< HEAD
| error-handling | backend/error-handling.md | build | all | error,backend | active | 错误处理规范 |
=======
| logging-standard | shared/logging-standard.md | build | all | logging,observability | active | 日志规范 |
>>>>>>> origin/main
```

**问题**：
- Markdown 表格冲突极难手动合并（列对齐、分隔符）
- 即使合并了，`ship-spec sync-index` 可能再次覆盖
- 新人不敢解决冲突，直接放弃

---

## 问题 2：查询性能瓶颈

### 场景：随着规范增长，查询变慢

**规范数量演进**：
```
第 1 个月: 5 个规范   → INDEX.md 200 行
第 6 个月: 30 个规范  → INDEX.md 1,200 行
第 12 个月: 80 个规范 → INDEX.md 3,200 行
第 24 个月: 150 个规范 → INDEX.md 6,000 行
```

### 查询操作的时间复杂度

**当前实现（伪代码）**：
```javascript
// ship-spec list --project web --stage design --tags api

function listSpecs(filters) {
  // 1. 读取整个 INDEX.md
  const content = fs.readFileSync('.docs/spec/INDEX.md', 'utf-8');
  
  // 2. 解析 Markdown 表格（O(n)）
  const rows = parseMarkdownTable(content);
  
  // 3. 线性扫描过滤（O(n)）
  return rows.filter(row => {
    return (
      row.projects.includes(filters.project) &&
      row.stages.includes(filters.stage) &&
      row.tags.some(tag => filters.tags.includes(tag))
    );
  });
}
```

**时间复杂度**：
- 读取文件：O(n)，n = 文件大小
- 解析表格：O(m)，m = 规范数量
- 过滤：O(m × k)，k = 过滤条件数
- **总复杂度**：O(n + m × k)

### 性能实测（模拟）

| 规范数量 | INDEX.md 大小 | 查询耗时 | 影响 |
|---------|--------------|---------|------|
| 10 | 4 KB | 5 ms | ✅ 无感知 |
| 50 | 20 KB | 25 ms | ✅ 可接受 |
| 100 | 40 KB | 60 ms | ⚠️ 开始感知 |
| 200 | 80 KB | 150 ms | ⚠️ 明显延迟 |
| 500 | 200 KB | 500 ms | ❌ 无法接受 |

### 真实场景的复合查询

```bash
# 开发者常见操作
ship-spec list --project web --stage build --tags api,rest
ship-spec search "error handling"
ship-spec suggest backend/api/users.ts  # 基于文件路径推荐
```

**每次查询都要**：
1. 读取整个 INDEX.md
2. 解析全部规范元数据
3. 线性扫描匹配

**问题**：
- 没有索引结构（如 B-tree、倒排索引）
- 无法利用缓存（文件内容改变频繁）
- 复杂查询（多条件 AND/OR）性能差

---

## 问题 3：元数据不可扩展

### 场景：需要新增元数据字段

**需求 1：规范依赖关系**
```yaml
# error-handling.md 依赖 logging-standard.md
---
spec_id: error-handling
depends_on:
  - logging-standard
  - monitoring-setup
---
```

**问题**：INDEX.md 表格如何表达？
```markdown
| spec_id | file | stages | projects | tags | status | depends_on | description |
|---------|------|--------|----------|------|--------|------------|-------------|
| error-handling | ... | ... | ... | ... | active | logging-standard,monitoring-setup | ... |
```

**问题**：
- 表格列越来越多（横向膨胀）
- 数组字段用逗号分隔（无法表达复杂结构）
- Markdown 表格不支持嵌套

**需求 2：规范版本历史**
```yaml
---
spec_id: rest-api-standard
version: 2.1.0
changelog:
  - version: 2.0.0
    date: 2025-01-15
    breaking: true
    changes: ["移除 XML 支持"]
  - version: 1.5.0
    date: 2024-10-20
    changes: ["新增分页规范"]
---
```

**问题**：INDEX.md 表格完全无法表达版本历史（二维结构 vs 树形结构）。

**需求 3：规范使用统计**
```yaml
---
spec_id: rest-api-standard
usage_stats:
  referenced_by: [feature-001, feature-005, feature-012]
  last_used: 2025-06-12
  usage_count: 47
  compliance_rate: 0.85
---
```

**问题**：
- 统计数据频繁变化
- 每次更新都会导致 INDEX.md 的 Git diff 噪音
- 表格无法表达复杂的统计对象

### 根本问题：Markdown 表格的表达能力

**Markdown 表格擅长**：
- ✅ 二维数据（行列结构）
- ✅ 简单字段（字符串、数字）
- ✅ 人类阅读

**Markdown 表格不擅长**：
- ❌ 复杂嵌套结构（数组、对象）
- ❌ 关系表达（依赖、引用）
- ❌ 频繁变化的数据（统计、缓存）
- ❌ 高效查询（需要解析后才能过滤）

---

## 问题 4：缺少关系表达能力

### 场景 1：规范依赖图

**真实需求**：
```
rest-api-standard
├── depends on: error-handling
│   └── depends on: logging-standard
├── depends on: naming-conventions
└── depends on: versioning-strategy
```

**当前架构**：无法表达依赖关系
```bash
ship-spec load rest-api-standard
# ❌ 不知道需要先阅读哪些依赖规范
```

**理想情况**：
```bash
ship-spec load rest-api-standard --with-deps
# 输出：
# 检测到依赖规范，建议按顺序阅读：
# 1. logging-standard
# 2. error-handling
# 3. naming-conventions
# 4. versioning-strategy
# 5. rest-api-standard ← 当前规范
```

### 场景 2：规范演进关系

**版本演进**：
```
rest-api-standard-v1 (deprecated)
└── replaced by: rest-api-standard-v2 (active)
    └── extended by: rest-api-graphql-migration (active)
```

**当前架构**：只能在规范内容中手动写：
```markdown
> ⚠️ 本规范已废弃，请使用 rest-api-standard-v2
```

**问题**：
- 无法自动追踪演进链
- 无法生成"迁移路径图"
- 旧代码引用旧规范，无法自动提示升级

### 场景 3：规范与代码的关联

**真实需求**：
```yaml
---
spec_id: rest-api-standard
code_references:
  - path: backend/api/users.ts
    lines: [15, 23, 45]
    compliance: true
  - path: backend/api/orders.ts
    lines: [8]
    compliance: false
    violation: "未使用复数名词"
---
```

**当前架构**：INDEX.md 表格无法表达这种复杂关联。

---

## 解决方案：分层索引架构演进

### 阶段 1：INDEX.md + 内存缓存（当前 + 优化）

**适用规模**：< 100 个规范，< 20 人团队

**改进点**：
```javascript
// ship-spec CLI 内部实现缓存
const cache = new Map();

function listSpecs(filters) {
  const cacheKey = JSON.stringify(filters);
  if (cache.has(cacheKey)) {
    return cache.get(cacheKey);
  }
  
  const result = parseAndFilter('.docs/spec/INDEX.md', filters);
  cache.set(cacheKey, result);
  return result;
}
```

**优点**：
- ✅ 无架构变更
- ✅ 查询性能提升 10-50 倍
- ✅ 零学习成本

**仍然无法解决**：
- ❌ 并发写入冲突
- ❌ 元数据扩展性

---

### 阶段 2：INDEX.md + .meta/ 分片索引（推荐）

**架构设计**：
```
.docs/spec/
├── INDEX.md                          # 保留，用于人类阅读和降级
├── .meta/                            # 新增：机器可读的结构化索引
│   ├── index.json                    # 主索引
│   ├── by-project/
│   │   ├── web.json                  # 按项目分片
│   │   └── api.json
│   ├── by-stage/
│   │   ├── design.json               # 按阶段分片
│   │   └── build.json
│   ├── by-tag/
│   │   ├── api.json                  # 按标签分片（倒排索引）
│   │   └── frontend.json
│   └── specs/
│       ├── rest-api-standard.json    # 单个规范的完整元数据
│       └── error-handling.json
└── backend/
    └── rest-api-standard.md          # 规范内容不变
```

**index.json 结构**：
```json
{
  "version": "1.0.0",
  "generated_at": "2025-06-12T14:30:00Z",
  "total_specs": 50,
  "specs": [
    {
      "spec_id": "rest-api-standard",
      "file": "backend/rest-api-standard.md",
      "stages": ["design", "build"],
      "projects": ["all"],
      "tags": ["api", "rest", "backend"],
      "status": "active",
      "description": "REST API 设计规范",
      "version": "2.1.0",
      "depends_on": ["error-handling", "naming-conventions"],
      "created_at": "2025-01-15",
      "updated_at": "2025-06-10"
    }
  ]
}
```

**单规范元数据（specs/rest-api-standard.json）**：
```json
{
  "spec_id": "rest-api-standard",
  "file": "backend/rest-api-standard.md",
  "version": "2.1.0",
  "changelog": [
    {
      "version": "2.0.0",
      "date": "2025-01-15",
      "breaking": true,
      "changes": ["移除 XML 支持"]
    }
  ],
  "depends_on": [
    {
      "spec_id": "error-handling",
      "min_version": "1.0.0",
      "required": true
    }
  ],
  "usage_stats": {
    "referenced_by": ["feature-001", "feature-005"],
    "last_used": "2025-06-12",
    "usage_count": 47,
    "compliance_rate": 0.85
  },
  "code_references": [
    {
      "path": "backend/api/users.ts",
      "lines": [15, 23],
      "compliance": true
    }
  ]
}
```

**查询优化**：
```javascript
// 查询：project=web, stage=design, tags=api
function listSpecs(filters) {
  // 1. 根据过滤条件选择最优索引
  if (filters.project) {
    // 读取分片索引：.meta/by-project/web.json
    const projectSpecs = JSON.parse(
      fs.readFileSync('.docs/spec/.meta/by-project/web.json')
    );
    return projectSpecs.filter(/* 其他条件 */);
  }
  
  // 2. 如果没有索引命中，读取主索引
  const mainIndex = JSON.parse(
    fs.readFileSync('.docs/spec/.meta/index.json')
  );
  return mainIndex.specs.filter(/* 过滤条件 */);
}
```

**性能对比**：
| 操作 | INDEX.md | .meta/ 分片索引 | 提升 |
|------|----------|----------------|------|
| 查询单项目规范 | 150ms | 5ms | 30x |
| 查询多条件 | 200ms | 10ms | 20x |
| 获取规范详情 | 150ms | 2ms | 75x |

**并发写入优化**：
```bash
# 创建规范时，只写入单个文件
ship-spec create error-handling

# 写入操作：
# 1. 创建 backend/error-handling.md
# 2. 创建 .meta/specs/error-handling.json  ← 独立文件，无冲突
# 3. 更新 .meta/index.json（后台异步，带锁机制）
# 4. 同步 INDEX.md（可选，后台异步）
```

**优点**：
- ✅ 解决并发写入冲突（单规范独立文件）
- ✅ 解决查询性能（分片索引 + JSON）
- ✅ 解决元数据扩展（JSON 支持嵌套）
- ✅ 保持向后兼容（INDEX.md 仍存在）

**缺点**：
- ⚠️ 增加存储空间（约 2-3 倍）
- ⚠️ 需要同步机制（INDEX.md ↔ .meta/）

---

### 阶段 3：SQLite 索引数据库（可选，大型项目）

**适用规模**：> 500 个规范，> 100 人团队

**架构设计**：
```
.docs/spec/
├── INDEX.md                    # 保留（只读，工具生成）
├── .meta/
│   └── index.db                # SQLite 数据库
└── backend/
    └── rest-api-standard.md
```

**数据库 Schema**：
```sql
CREATE TABLE specs (
  spec_id TEXT PRIMARY KEY,
  file TEXT NOT NULL,
  version TEXT,
  status TEXT DEFAULT 'active',
  description TEXT,
  created_at DATETIME,
  updated_at DATETIME
);

CREATE TABLE spec_stages (
  spec_id TEXT,
  stage TEXT,
  FOREIGN KEY (spec_id) REFERENCES specs(spec_id)
);

CREATE TABLE spec_projects (
  spec_id TEXT,
  project TEXT,
  FOREIGN KEY (spec_id) REFERENCES specs(spec_id)
);

CREATE TABLE spec_tags (
  spec_id TEXT,
  tag TEXT,
  FOREIGN KEY (spec_id) REFERENCES specs(spec_id)
);

CREATE TABLE spec_dependencies (
  spec_id TEXT,
  depends_on TEXT,
  min_version TEXT,
  required BOOLEAN,
  FOREIGN KEY (spec_id) REFERENCES specs(spec_id),
  FOREIGN KEY (depends_on) REFERENCES specs(spec_id)
);

-- 索引优化
CREATE INDEX idx_spec_status ON specs(status);
CREATE INDEX idx_spec_projects ON spec_projects(project);
CREATE INDEX idx_spec_tags ON spec_tags(tag);
```

**查询性能**：
```javascript
// 复杂查询：project=web AND stage=design AND tags IN (api, rest)
const db = new SQLite('.docs/spec/.meta/index.db');

const specs = db.prepare(`
  SELECT DISTINCT s.*
  FROM specs s
  JOIN spec_projects sp ON s.spec_id = sp.spec_id
  JOIN spec_stages ss ON s.spec_id = ss.spec_id
  JOIN spec_tags st ON s.spec_id = st.spec_id
  WHERE sp.project = ?
    AND ss.stage = ?
    AND st.tag IN (?, ?)
    AND s.status = 'active'
`).all('web', 'design', 'api', 'rest');
```

**性能对比**：
| 操作 | INDEX.md | SQLite | 提升 |
|------|----------|--------|------|
| 查询 500 规范 | 500ms | 3ms | 166x |
| 复杂多表 JOIN | 800ms | 5ms | 160x |
| 依赖图查询 | N/A | 10ms | ∞ |

**优点**：
- ✅ 极致查询性能（B-tree 索引）
- ✅ 支持复杂关系查询（JOIN、递归 CTE）
- ✅ 事务支持（ACID）

**缺点**：
- ❌ 二进制文件（Git diff 不可读）
- ❌ 需要数据库工具
- ❌ 学习曲线增加

---

## 推荐演进路径

### 当前阶段判断

| 团队规模 | 规范数量 | 推荐架构 | 理由 |
|---------|---------|---------|------|
| < 10人 | < 50 | 阶段 1：INDEX.md + 缓存 | 简单够用，冲突率低 |
| 10-50人 | 50-200 | 阶段 2：.meta/ 分片 | 平衡性能和复杂度 |
| > 50人 | > 200 | 阶段 3：SQLite | 性能优先 |

### 渐进式迁移策略

**第 1 步：加缓存（无痛，1 天）**
```javascript
// 在 ship-spec CLI 内部加缓存，外部无感知
const cachedIndex = memoize(() => parseIndexMd());
```

**第 2 步：生成 .meta/（兼容，1 周）**
```bash
# 用户无感知，CLI 自动生成
ship-spec sync-index
# → 生成 INDEX.md
# → 生成 .meta/index.json（新增）
# → 生成 .meta/by-project/*.json（新增）
```

**第 3 步：CLI 优先读 .meta/（性能提升，1 天）**
```javascript
// ship-spec 内部实现
function getIndex() {
  if (fs.existsSync('.meta/index.json')) {
    return JSON.parse(fs.readFileSync('.meta/index.json'));  // 快速路径
  }
  return parseMarkdownTable('INDEX.md');  // 降级路径
}
```

**第 4 步：独立规范元数据（解决冲突，2 周）**
```bash
# 创建规范时，写独立文件
ship-spec create new-spec
# → 写入 backend/new-spec.md
# → 写入 .meta/specs/new-spec.json  ← 关键：无并发冲突
# → 异步更新 .meta/index.json（带文件锁）
```

**第 5 步：淘汰 INDEX.md 写入（可选，长期）**
```bash
# INDEX.md 变为只读，从 .meta/ 生成
ship-spec sync-index --readonly
# → INDEX.md 成为"导出格式"，不再是主索引
```

---

## 总结：为什么需要演进？

### INDEX.md 的定位应该是

**不是**：数据库（高性能查询、复杂关系）
**而是**：人类可读的规范目录（类似书的"目录页"）

### 演进的核心思想

```
INDEX.md（人类可读）
    ↓
.meta/（机器可读）
    ↓
查询/统计/关系分析（高性能）
```

**类比**：
- INDEX.md = 书的目录（给人看）
- .meta/index.json = 图书馆的电子检索系统（给机器用）
- .meta/specs/*.json = 每本书的详细信息卡片

### 关键原则

1. **向后兼容**：INDEX.md 永远存在，工具降级时仍可用
2. **渐进式演进**：从缓存 → 分片 → 数据库，逐步升级
3. **透明迁移**：用户无感知，CLI 内部自动选择最优方案

### 何时启动演进？

**立即行动的信号**：
- ✅ 团队 > 10 人，规范 > 30 个
- ✅ 每周出现 INDEX.md 冲突 > 1 次
- ✅ `ship-spec list` 查询耗时 > 100ms
- ✅ 需要规范依赖、版本管理等高级功能

**观望等待的信号**：
- 团队 < 5 人，规范 < 20 个
- 冲突罕见（月均 < 1 次）
- 查询速度可接受

---

## 附录：实现参考

### .meta/ 目录结构完整示例

```
.docs/spec/.meta/
├── index.json              # 主索引（所有规范摘要）
├── by-project/
│   ├── web.json            # web 项目的规范 ID 列表
│   ├── api.json
│   └── mobile.json
├── by-stage/
│   ├── design.json
│   ├── build.json
│   └── test.json
├── by-tag/
│   ├── api.json            # 包含 "api" 标签的规范列表
│   ├── frontend.json
│   └── backend.json
├── by-status/
│   ├── active.json
│   └── deprecated.json
├── specs/                  # 单个规范的详细元数据
│   ├── rest-api-standard.json
│   ├── error-handling.json
│   └── ...
├── relations/
│   ├── dependencies.json   # 规范依赖图
│   └── evolution.json      # 规范演进链
└── stats/
    ├── usage.json          # 使用统计
    └── compliance.json     # 合规性统计
```

### 同步脚本示例

```bash
#!/bin/bash
# sync-meta.sh - 同步 INDEX.md ↔ .meta/

# 1. 扫描所有规范文件
specs=$(find .docs/spec -name "*.md" -not -name "INDEX.md")

# 2. 提取 frontmatter，生成 JSON
for spec in $specs; do
  spec_id=$(yq '.spec_id' "$spec")
  # 生成 .meta/specs/${spec_id}.json
  yq -o=json '.' "$spec" > ".meta/specs/${spec_id}.json"
done

# 3. 聚合生成主索引
jq -s '.' .meta/specs/*.json > .meta/index.json

# 4. 生成分片索引
jq '[.[] | select(.projects[] == "web")]' .meta/index.json > .meta/by-project/web.json

# 5. 从 .meta/ 重新生成 INDEX.md（可选）
ship-spec generate-index --from-meta
```

---

**结论**：INDEX.md 是优秀的起点，但不是终点。当团队和规范增长时，分层索引架构能在保持简单性的同时，提供工业级的性能和扩展性。
