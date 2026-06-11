# ship-spec 技能改造方案（最终版）

基于对抗式审查结果的改进方案。

---

## 核心设计决策

### 1. 索引策略：INDEX.md 为唯一真实来源
**决策**：采用审查建议的"方案 A"。

**理由**：
- INDEX.md 人类可读，便于手动编辑和 git diff
- .index.json 自动生成，保证一致性
- 写操作始终写 INDEX.md，然后重建 .index.json
- 避免双向同步的复杂性

**实现**：
```javascript
// 所有写操作的统一流程
function updateSpec(operation, data) {
  // 1. 执行操作（创建/更新/删除规范文件）
  performOperation(operation, data);
  
  // 2. 更新 INDEX.md
  updateIndexMd(operation, data);
  
  // 3. 从 INDEX.md 重建 .index.json
  rebuildIndexJson();
  
  // 4. 清除搜索缓存
  invalidateSearchCache();
}
```

### 2. existing-features 归属：由 ship-build 直接写入
**决策**：采用审查建议的"选项 A"。

**理由**：
- existing-features 是构建产物，不是规范
- ship-build 完成后直接写入，无需额外命令
- ship-spec 的 sync-index 会自动发现并索引
- 减少技能间的耦合

**实现**：
```javascript
// ship-build 完成后
function onBuildComplete(featureMeta, implementationSummary) {
  const featuresFile = determineFeaturesFile(featureMeta.projects);
  const entry = formatFeatureEntry(featureMeta, implementationSummary);
  
  // 直接追加到 existing-features.md
  appendToFile(featuresFile, entry);
  
  // ship-spec 的 sync-index 会在下次搜索时自动重建索引
}
```

### 3. 搜索功能：分阶段实现
**决策**：MVP 只实现元数据搜索，V2 实现全文搜索。

**理由**：
- 90% 的搜索场景元数据搜索已够用
- 全文搜索需要性能优化和测试，推迟到 V2
- 减少 MVP 复杂度，加快交付

**MVP 搜索功能**：
- 从 .index.json 搜索（< 50ms）
- 支持 spec_id、description、tags、keywords 匹配
- 支持项目、阶段、类型过滤
- 输出 table 和 json 格式

**V2 增强**：
- 全文内容搜索（with 性能基准测试）
- 高级语法（精确匹配、排除词、正则）
- 搜索建议和拼写纠正

### 4. suggest-new-spec：推迟到 V2
**决策**：MVP 不包含此功能。

**理由**：
- 自动识别模式需要复杂算法，实现成本高
- 误报率难以控制，影响开发者信任
- 非核心功能，可后续迭代

**替代方案**：
- MVP 提供手动沉淀工作流（开发者自己决定）
- V2 提供基于统计的建议（复用次数、跨模块使用）
- V3 引入 LLM 智能识别

### 5. 其他技能集成：提供 SDK
**决策**：ship-spec 提供 JavaScript SDK。

**理由**：
- 避免每个技能重复实现解析逻辑
- 保证过滤逻辑一致性
- 新技能快速集成

**SDK 设计**：
```javascript
// skills/ship-spec/sdk.js
export class SpecLoader {
  constructor(options = {}) {
    this.project = options.project;
    this.stage = options.stage;
    this.indexPath = options.indexPath || '.docs/spec/INDEX.md';
  }
  
  // 加载单个规范
  async load(specId) {
    const index = this._loadIndex();
    const spec = index.find(s => s.spec_id === specId);
    if (!spec) throw new Error(`Spec not found: ${specId}`);
    
    const content = await read(spec.file);
    return { ...spec, content };
  }
  
  // 搜索规范
  async search(query, options = {}) {
    const results = await callSkill('ship-spec', {
      command: 'search',
      query,
      options: {
        project: this.project,
        stage: this.stage,
        format: 'json',
        ...options
      }
    });
    return results.results;
  }
  
  // 过滤规范
  filter(criteria) {
    const index = this._loadIndex();
    return index.filter(spec => {
      if (criteria.project && !spec.projects.includes(criteria.project)) return false;
      if (criteria.stage && !spec.stages.includes(criteria.stage)) return false;
      if (criteria.tags && !criteria.tags.some(t => spec.tags.includes(t))) return false;
      return true;
    });
  }
  
  // 私有方法：加载索引
  _loadIndex() {
    const indexMd = readFile(this.indexPath);
    return parseIndexTable(indexMd);
  }
}
```

---

## MVP 命令清单

### 1. init - 初始化规范目录
```bash
ship-spec init [--template <name>] [--workspace <mode>]
```

**功能**：
- 创建 .docs/spec 目录结构
- 生成 INDEX.md
- 根据项目类型创建初始规范模板
- 生成 README 说明文档

**模板**：
- `minimal`：最少规范（tech-stack, existing-features）
- `standard`：常用规范（+ API standard, naming conventions）
- `comprehensive`：全套规范（+ frontend patterns, test standards）

### 2. create - 创建新规范
```bash
ship-spec create <spec-id> [options]

Options:
  -t, --type <type>         规范类型：frontend | backend | shared
  -p, --project <projects>  适用项目（逗号分隔）
  -s, --stage <stages>      适用阶段（逗号分隔）
  --tags <tags>             标签（逗号分隔）
  --template <name>         使用模板
  -d, --description <text>  规范描述
```

**流程**：
1. 验证 spec-id 唯一性
2. 确定文件路径
3. 加载模板或创建空白文件
4. 写入规范文件（带 frontmatter）
5. 更新 INDEX.md
6. 重建 .index.json

### 3. update - 更新规范
```bash
ship-spec update <spec-id> [options]

Options:
  --content <text>          新内容（append 模式）
  --file <path>             从文件读取内容
  --metadata                更新元数据（交互式）
  --status <status>         更新状态：active | deprecated
```

**流程**：
1. 验证 spec-id 存在
2. 读取当前内容
3. 根据选项更新内容/元数据
4. 写回文件
5. 更新 INDEX.md
6. 重建 .index.json

### 4. delete - 删除规范
```bash
ship-spec delete <spec-id> [options]

Options:
  --archive                 归档而非删除
  --force                   忽略依赖检查
```

**流程**：
1. 验证 spec-id 存在
2. 检查依赖（其他规范的 depends_on）
3. 如有依赖且非 --force，报错退出
4. 删除或归档文件
5. 更新 INDEX.md
6. 重建 .index.json

### 5. search - 搜索规范（元数据）
```bash
ship-spec search <query> [options]

Options:
  -p, --project <project>   过滤项目
  -s, --stage <stage>       过滤阶段
  -t, --type <type>         过滤类型
  --tags <tags>             过滤标签
  -f, --format <format>     输出格式：table | json
  --limit <n>               结果数量限制
```

**实现**：只搜索 .index.json，不读取文件内容。

### 6. validate - 验证规范
```bash
ship-spec validate [spec-id] [options]

Options:
  --all                     验证所有规范
  --fix                     自动修复可修复的问题
```

**检查项**：
- 必需字段：spec_id、description、stages、projects
- 格式规范：frontmatter 格式、markdown 标题层级
- 敏感信息：password、token、secret、API key
- 依赖完整性：depends_on 引用的规范存在
- 命名冲突：不同文件的相同 spec_id

### 7. sync-index - 同步索引
```bash
ship-spec sync-index [options]

Options:
  --auto-fix                自动修复不一致
  --rebuild                 强制重建 .index.json
```

**流程**：
1. 扫描 .docs/spec 目录
2. 解析每个 .md 文件的 frontmatter
3. 与 INDEX.md 对比
4. 报告新增/删除/不一致
5. 如 --auto-fix，更新 INDEX.md
6. 重建 .index.json

### 8. doctor - 诊断和修复
```bash
ship-spec doctor [options]

Options:
  --fix                     自动修复
```

**检查项**：
- INDEX.md 存在且格式正确
- .index.json 与 INDEX.md 一致
- 所有规范文件有效
- 无循环依赖
- 无孤儿规范（在目录中但不在 INDEX.md）

---

## 规范文件格式

### Frontmatter 必需字段
```yaml
---
spec_id: rest-api-standard
description: REST API 设计规范
projects:
  - api
stages:
  - design
  - build
tags:
  - api
  - rest
  - backend
status: active
depends_on:
  - error-codes
  - auth-standard
---
```

### INDEX.md 格式
```markdown
# Spec Index

| spec_id | file | stages | projects | tags | status | last_updated | description |
|---|---|---|---|---|---|---|---|
| rest-api-standard | backend/rest-api-standard.md | design,build | api | api,rest,backend | active | 2026-06-10 | REST API 规范 |
| existing-features | shared/existing-features.md | understand,done | all | - | active | 2026-06-11 | 已有功能索引 |
```

### .index.json 格式（自动生成）
```json
{
  "version": "1.0",
  "last_updated": "2026-06-11T10:00:00Z",
  "specs": [
    {
      "spec_id": "rest-api-standard",
      "file": "backend/rest-api-standard.md",
      "file_hash": "sha256:abc123...",
      "projects": ["api"],
      "stages": ["design", "build"],
      "tags": ["api", "rest", "backend"],
      "status": "active",
      "description": "REST API 规范",
      "last_modified": "2026-06-10T15:30:00Z",
      "depends_on": ["error-codes", "auth-standard"]
    }
  ]
}
```

---

## 错误信息改进

### 坏例子
```
Error: Validation failed
```

### 好例子
```
Error: Spec validation failed for 'rest-api-standard'

  [ERROR] Missing required field: description
  Location: backend/rest-api-standard.md
  
  Fix:
  Add the 'description' field to the frontmatter:
  
  ---
  spec_id: rest-api-standard
  description: "Your description here"
  projects: [api]
  stages: [design, build]
  ---
  
  Learn more: https://docs.shipkit.dev/specs#frontmatter

Run 'ship-spec validate --fix' to auto-fix this issue.
```

---

## 技能集成示例

### ship-design 读取规范
```javascript
import { SpecLoader } from '../ship-spec/sdk.js';

async function loadDesignSpecs(featureMeta) {
  const loader = new SpecLoader({
    project: featureMeta.projects[0],
    stage: 'design'
  });
  
  // 搜索 API 相关规范
  const apiSpecs = await loader.search('api');
  
  // 加载具体规范内容
  const apiStandard = await loader.load('rest-api-standard');
  
  // 过滤前端规范
  const frontendSpecs = loader.filter({ type: 'frontend' });
  
  return { apiStandard, frontendSpecs };
}
```

### ship-build 更新 existing-features
```javascript
async function onBuildComplete(featureMeta, summary) {
  // 确定文件路径
  const isShared = featureMeta.projects.length > 1 || summary.cross_project;
  const featuresFile = isShared
    ? '.docs/spec/_shared/existing-features.md'
    : `.docs/spec/${featureMeta.projects[0]}/existing-features.md`;
  
  // 格式化条目
  const entry = `
## ${summary.module}
- **${summary.feature}**：完成时间 ${new Date().toISOString().split('T')[0]}，Feature: ${featureMeta.feature_dir}
  - 表：${summary.tables?.join(', ') || 'N/A'}
  - API：${summary.apis?.join(', ') || 'N/A'}
  - 页面：${summary.pages?.join(', ') || 'N/A'}
  - 测试：${summary.tests?.join(', ') || 'N/A'}
`;
  
  // 追加到文件
  await appendToFile(featuresFile, entry);
  
  // ship-spec sync-index 会在下次运行时自动更新索引
}
```

---

## 性能目标

### 元数据搜索
- **延迟**：< 50ms（100 个规范）
- **吞吐量**：> 1000 次/分钟
- **内存**：< 10MB

### 索引重建
- **延迟**：< 200ms（100 个规范）
- **增量更新**：< 10ms（单个规范）

### 文件操作
- **读取规范**：< 5ms（5KB 文件）
- **更新 INDEX.md**：< 20ms
- **重建 .index.json**：< 100ms（100 个规范）

---

## 实施计划

### Sprint 1：基础设施（Week 1）
- ✅ 目录结构和文件格式定义
- ✅ INDEX.md 解析器
- ✅ .index.json 构建器
- ✅ 基础 CRUD 操作

### Sprint 2：核心命令（Week 2）
- ✅ init 命令
- ✅ create/update/delete 命令
- ✅ sync-index 命令
- ✅ 错误信息改进

### Sprint 3：搜索和验证（Week 3）
- ✅ 元数据搜索实现
- ✅ validate 命令
- ✅ doctor 命令
- ✅ 性能测试

### Sprint 4：SDK 和文档（Week 4）
- ✅ SpecLoader SDK
- ✅ 集成测试（ship-design, ship-build）
- ✅ 用户文档和示例
- ✅ 最终审查

---

## 验收标准

### 功能完整性
- [ ] 所有 MVP 命令实现
- [ ] SDK 可用，其他技能集成无障碍
- [ ] 错误信息清晰且可操作
- [ ] ship-spec init 可快速启动新项目

### 性能达标
- [ ] 元数据搜索 < 50ms
- [ ] 索引重建 < 200ms（100 规范）
- [ ] 内存占用 < 10MB

### 鲁棒性
- [ ] 通过所有错误场景测试
- [ ] INDEX.md 损坏可自动恢复
- [ ] 循环依赖检测正常
- [ ] 并发更新无冲突

### 用户体验
- [ ] 首次使用无障碍（init + create + search）
- [ ] 命令参数一致性
- [ ] 文档完整（API 文档、使用示例、最佳实践）

---

最终方案已完成，可交付。
