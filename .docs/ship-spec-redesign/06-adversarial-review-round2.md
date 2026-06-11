# 对抗式审查报告 Round 2 - 可交付性验证

## 审查目标

验证最终方案是否真正可交付，从以下角度检验：
1. **实现完整性**：是否有遗漏的实现细节
2. **边界情况处理**：极端场景是否覆盖
3. **向后兼容性**：如何迁移现有项目
4. **开发成本**：工作量估算是否合理
5. **运维考虑**：上线后的维护成本
6. **测试策略**：如何验证功能正确性

---

## 1. 实现完整性检查 ✅

### 问题 1.1：INDEX.md 解析器的边界情况
**遗漏**：INDEX.md 表格解析逻辑未详细说明。

**需要明确**：
```javascript
// 如何处理这些情况？
1. 表格单元格包含逗号：tags = "api,rest,backend"
2. 表格单元格包含竖线：description = "A | B"
3. 多行表格（markdown 换行）
4. 空单元格 vs "-"
5. 列顺序变化（用户手动调整）
```

**补充设计**：
```javascript
// INDEX.md 解析器
function parseIndexTable(markdown) {
  const lines = markdown.split('\n');
  const headerLine = lines.find(l => l.includes('spec_id'));
  const separatorLine = lines[lines.indexOf(headerLine) + 1];
  
  if (!headerLine || !separatorLine.match(/^\|[-:| ]+\|$/)) {
    throw new Error('Invalid INDEX.md format');
  }
  
  // 解析表头，确定列顺序
  const headers = headerLine.split('|')
    .map(h => h.trim())
    .filter(h => h);
  
  const specs = [];
  let currentLine = lines.indexOf(separatorLine) + 1;
  
  while (currentLine < lines.length) {
    const line = lines[currentLine].trim();
    if (!line || !line.startsWith('|')) break;
    
    // 使用正则处理转义的竖线
    const cells = line.split(/(?<!\\)\|/)
      .map(c => c.trim().replace(/\\\|/g, '|'))
      .filter(c => c);
    
    const spec = {};
    headers.forEach((header, i) => {
      const value = cells[i] || '';
      
      // 处理特殊字段
      if (['projects', 'stages', 'tags'].includes(header)) {
        spec[header] = value === '-' ? [] : value.split(',').map(v => v.trim());
      } else {
        spec[header] = value;
      }
    });
    
    specs.push(spec);
    currentLine++;
  }
  
  return specs;
}
```

### 问题 1.2：.index.json 重建的原子性
**遗漏**：重建过程中如果失败（如磁盘满），如何保证不损坏现有索引？

**补充设计**：
```javascript
function rebuildIndexJson() {
  const tempPath = '.docs/spec/.index.json.tmp';
  const finalPath = '.docs/spec/.index.json';
  
  try {
    // 1. 写入临时文件
    const index = buildIndexFromIndexMd();
    writeFile(tempPath, JSON.stringify(index, null, 2));
    
    // 2. 验证临时文件有效
    const content = readFile(tempPath);
    JSON.parse(content); // 验证 JSON 格式
    
    // 3. 原子性替换
    renameFile(tempPath, finalPath);
  } catch (error) {
    // 清理临时文件
    if (fileExists(tempPath)) {
      deleteFile(tempPath);
    }
    throw new Error(`Failed to rebuild index: ${error.message}`);
  }
}
```

### 问题 1.3：SDK 的错误处理
**遗漏**：SDK 方法失败时的行为未定义。

**补充设计**：
```javascript
export class SpecLoader {
  async load(specId) {
    try {
      const index = this._loadIndex();
      const spec = index.find(s => s.spec_id === specId);
      
      if (!spec) {
        throw new SpecNotFoundError(specId);
      }
      
      const content = await read(spec.file);
      return { ...spec, content };
    } catch (error) {
      if (error instanceof SpecNotFoundError) {
        throw error;
      }
      throw new SpecLoaderError(`Failed to load spec '${specId}': ${error.message}`);
    }
  }
  
  async search(query, options = {}) {
    try {
      const results = await callSkill('ship-spec', {
        command: 'search',
        query,
        options: { ...this._defaultOptions(), ...options }
      });
      
      if (!results || !results.results) {
        throw new SpecLoaderError('Invalid search response');
      }
      
      return results.results;
    } catch (error) {
      // 降级：如果 ship-spec 不可用，直接读取 INDEX.md
      console.warn('ship-spec search failed, falling back to local search');
      return this._localSearch(query, options);
    }
  }
  
  _localSearch(query, options) {
    const index = this._loadIndex();
    return index.filter(spec => {
      const searchText = [spec.spec_id, spec.description, ...spec.tags].join(' ').toLowerCase();
      return searchText.includes(query.toLowerCase());
    });
  }
}
```

---

## 2. 边界情况处理 ⚠️

### 场景 2.1：并发创建同名规范
**问题**：两个开发者同时运行 `ship-spec create api-standard`。

**现状**：未处理，后执行的会覆盖。

**解决方案**：
```javascript
function createSpec(specId, options) {
  // 1. 检查文件是否已存在
  const filePath = determineFilePath(specId, options.type);
  if (fileExists(filePath)) {
    throw new Error(`Spec file already exists: ${filePath}\nUse 'ship-spec update' to modify it.`);
  }
  
  // 2. 检查 INDEX.md 中是否已存在
  const index = parseIndexMd();
  if (index.some(s => s.spec_id === specId)) {
    throw new Error(`Spec ID already exists in INDEX.md: ${specId}`);
  }
  
  // 3. 原子性写入
  const content = generateSpecContent(specId, options);
  writeFile(filePath, content);
  
  try {
    updateIndexMd({ operation: 'create', specId, filePath, ...options });
    rebuildIndexJson();
  } catch (error) {
    // 回滚：删除刚创建的文件
    deleteFile(filePath);
    throw error;
  }
}
```

### 场景 2.2：规范文件被外部工具修改
**问题**：开发者用 IDE 直接编辑规范文件，但忘记运行 sync-index。

**现状**：.index.json 过期，搜索结果不准确。

**解决方案**：
```javascript
// 方案 A：自动检测（推荐）
function ensureIndexFresh() {
  const indexJson = readFile('.docs/spec/.index.json');
  const index = JSON.parse(indexJson);
  
  // 检查任意规范文件的 hash
  for (const spec of index.specs.slice(0, 5)) { // 采样检查前5个
    const content = readFile(spec.file);
    const currentHash = sha256(content);
    
    if (currentHash !== spec.file_hash) {
      console.warn('Detected outdated index, rebuilding...');
      rebuildIndexJson();
      return;
    }
  }
}

// 在搜索前调用
function search(query, options) {
  ensureIndexFresh();
  // 继续搜索逻辑
}
```

```javascript
// 方案 B：文件监听（可选）
import { watch } from 'fs';

watch('.docs/spec', { recursive: true }, (event, filename) => {
  if (filename.endsWith('.md') && filename !== 'INDEX.md') {
    console.log(`Spec file changed: ${filename}, consider running 'ship-spec sync-index'`);
  }
});
```

### 场景 2.3：项目目录重构
**问题**：项目从单项目重构为多项目，或项目改名。

**现状**：需要手动迁移所有规范文件和 INDEX.md。

**解决方案**：
```bash
# 新增命令：migrate
ship-spec migrate [options]

Options:
  --from single|multi       源模式
  --to single|multi         目标模式
  --rename <old>=<new>      项目重命名
  --dry-run                 只显示变更，不执行
```

```javascript
function migrate(options) {
  const changes = [];
  
  if (options.from === 'single' && options.to === 'multi') {
    // 单项目 → 多项目
    changes.push({
      type: 'create_dir',
      path: '.docs/spec/_shared'
    });
    
    // 移动 shared 规范
    const sharedSpecs = findSpecs({ projects: ['all'] });
    sharedSpecs.forEach(spec => {
      changes.push({
        type: 'move',
        from: spec.file,
        to: spec.file.replace('shared/', '_shared/')
      });
    });
  }
  
  if (options.rename) {
    const [oldName, newName] = options.rename.split('=');
    const index = parseIndexMd();
    
    index.forEach(spec => {
      if (spec.projects.includes(oldName)) {
        changes.push({
          type: 'update_metadata',
          spec_id: spec.spec_id,
          field: 'projects',
          oldValue: spec.projects,
          newValue: spec.projects.map(p => p === oldName ? newName : p)
        });
        
        // 如果文件路径包含项目名，也要移动
        if (spec.file.startsWith(`${oldName}/`)) {
          changes.push({
            type: 'move',
            from: spec.file,
            to: spec.file.replace(`${oldName}/`, `${newName}/`)
          });
        }
      }
    });
  }
  
  if (options.dryRun) {
    console.log('Migration plan:');
    changes.forEach(c => console.log(`  ${c.type}: ${JSON.stringify(c)}`));
    return;
  }
  
  // 执行迁移
  applyChanges(changes);
  syncIndex({ autoFix: true });
}
```

---

## 3. 向后兼容性 🔴

### 问题 3.1：现有项目的迁移路径
**遗漏**：如何从无规范的项目迁移到 ship-spec？

**迁移指南**：
```markdown
## 迁移现有项目

### 场景 1：项目没有任何规范文档
1. 运行 `ship-spec init --template minimal`
2. 根据实际情况创建规范：
   ```bash
   ship-spec create tech-stack -t shared --description "技术栈说明"
   ship-spec create api-standard -t backend --description "API 规范"
   ```
3. 逐步填充规范内容

### 场景 2：项目有散落的规范文档
1. 运行 `ship-spec init --template minimal`
2. 导入现有文档：
   ```bash
   # 手动复制文档到 .docs/spec/
   cp docs/api-conventions.md .docs/spec/backend/api-standard.md
   
   # 添加 frontmatter
   ship-spec doctor --fix
   
   # 同步索引
   ship-spec sync-index --auto-fix
   ```

### 场景 3：已有 .docs/spec/ 但无 INDEX.md
1. 运行 `ship-spec sync-index --rebuild`
2. 自动扫描并生成 INDEX.md
3. 检查生成结果：`ship-spec validate --all`
```

### 问题 3.2：与旧版 ShipKit 的兼容性
**遗漏**：如果项目已在使用旧版规范管理，如何平滑升级？

**兼容性策略**：
```javascript
// 检测旧版格式并自动转换
function detectAndMigrateLegacy() {
  // 旧版可能使用 .shipkit/specs/ 目录
  if (dirExists('.shipkit/specs/')) {
    console.log('Detected legacy ShipKit specs, migrating...');
    
    // 复制文件到新位置
    copyDir('.shipkit/specs/', '.docs/spec/');
    
    // 生成 INDEX.md
    syncIndex({ autoFix: true });
    
    console.log('Migration complete. Old files preserved in .shipkit/specs/');
    console.log('Run "ship-spec validate --all" to verify.');
  }
}

// init 命令中调用
function init(options) {
  detectAndMigrateLegacy();
  // 继续初始化逻辑
}
```

---

## 4. 开发成本评估 ⚠️

### Sprint 1 工作量细化
```
任务                      估算    风险
------------------------------------
目录结构定义              2h     低
INDEX.md 解析器          8h     中（表格解析边界情况多）
.index.json 构建器       4h     低
基础 CRUD 框架           6h     低
错误类型定义             2h     低
单元测试                 8h     中
------------------------------------
总计                     30h    （约 4 天）
```

**风险点**：
- INDEX.md 解析器可能因为 markdown 格式变化需要返工
- 建议：使用成熟的 markdown 解析库（如 remark）

### Sprint 2 工作量细化
```
任务                      估算    风险
------------------------------------
init 命令                 6h     低
create 命令               8h     中（模板系统）
update 命令               8h     中（元数据更新）
delete 命令               4h     低
sync-index 命令          6h     中（文件扫描和对比）
错误信息改进             4h     低
集成测试                 10h    中
------------------------------------
总计                     46h    （约 6 天）
```

**风险点**：
- 模板系统可能需要支持变量替换，增加复杂度
- 建议：MVP 只支持静态模板

### Sprint 3 工作量细化
```
任务                      估算    风险
------------------------------------
元数据搜索实现           6h     低
搜索结果格式化           4h     低
validate 命令            10h    高（检查项多）
doctor 命令              8h     中（修复逻辑复杂）
性能测试和优化           12h    高
------------------------------------
总计                     40h    （约 5 天）
```

**风险点**：
- validate 和 doctor 的检查项可能不断增加
- 性能优化可能需要多次迭代
- 建议：MVP 先实现核心检查项，其余放 V2

### Sprint 4 工作量细化
```
任务                      估算    风险
------------------------------------
SpecLoader SDK           8h     中
ship-design 集成测试     6h     中
ship-build 集成测试      6h     中
用户文档                 8h     低
示例代码                 4h     低
Code Review              6h     中
修复 bug                 10h    高
------------------------------------
总计                     48h    （约 6 天）
```

**风险点**：
- 集成测试可能发现设计问题，需要返工
- 建议：Sprint 1-3 期间持续与其他技能对接

**总工作量**：30 + 46 + 40 + 48 = **164 小时（约 21 个工作日）**

**建议调整**：
- 如果资源有限，MVP 去掉 doctor 命令（20小时）
- 性能优化放到 V1.1（12小时）
- 总计可压缩到 **132 小时（约 17 个工作日）**

---

## 5. 运维考虑 ⚠️

### 问题 5.1：规范文件体积增长
**场景**：existing-features.md 随着项目增长不断膨胀。

**现状**：未考虑归档策略。

**解决方案**：
```markdown
## existing-features 归档策略

规则：
1. 每年归档一次旧数据
2. 归档到 .docs/spec/_archive/existing-features-2025.md
3. 当前文件只保留最近 6 个月的 features

实现：
```bash
ship-spec archive-features --before 2025-12-31
```

```javascript
function archiveFeatures(beforeDate) {
  const featuresFile = '.docs/spec/shared/existing-features.md';
  const content = readFile(featuresFile);
  const entries = parseFeatureEntries(content);
  
  const toArchive = entries.filter(e => e.completed_at < beforeDate);
  const toKeep = entries.filter(e => e.completed_at >= beforeDate);
  
  // 写入归档文件
  const year = new Date(beforeDate).getFullYear();
  const archiveFile = `.docs/spec/_archive/existing-features-${year}.md`;
  writeFile(archiveFile, formatFeatureEntries(toArchive));
  
  // 更新当前文件
  writeFile(featuresFile, formatFeatureEntries(toKeep));
  
  syncIndex({ autoFix: true });
}
```

### 问题 5.2：规范质量监控
**遗漏**：如何持续监控规范质量？

**解决方案**：
```bash
# CI/CD 集成
# .github/workflows/spec-quality.yml

name: Spec Quality Check
on:
  pull_request:
    paths:
      - '.docs/spec/**'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - run: ship-spec validate --all
      - run: ship-spec doctor
      
  report:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - run: |
          ship-spec stats > spec-stats.txt
          cat spec-stats.txt >> $GITHUB_STEP_SUMMARY
```

### 问题 5.3：多仓库规范共享
**场景**：公司有多个项目，需要共享通用规范。

**现状**：未考虑跨仓库场景。

**解决方案（V2 特性）**：
```bash
# 支持规范远程引用
# .docs/spec/INDEX.md
| spec_id | file | source | ... |
| company-api-standard | - | https://github.com/company/specs/api-standard.md | ... |
```

```javascript
// SDK 支持远程规范
class SpecLoader {
  async load(specId) {
    const spec = this._findSpec(specId);
    
    if (spec.source && spec.source.startsWith('http')) {
      // 缓存远程规范
      const cacheKey = `remote-${specId}`;
      let content = cache.get(cacheKey);
      
      if (!content) {
        content = await fetchRemoteSpec(spec.source);
        cache.set(cacheKey, content, { ttl: 3600 }); // 1小时缓存
      }
      
      return { ...spec, content };
    }
    
    // 本地规范
    const content = await read(spec.file);
    return { ...spec, content };
  }
}
```

---

## 6. 测试策略 ✅

### 单元测试覆盖
```javascript
describe('INDEX.md parser', () => {
  test('parse valid table', () => { /* ... */ });
  test('handle escaped pipes', () => { /* ... */ });
  test('handle empty cells', () => { /* ... */ });
  test('throw on invalid format', () => { /* ... */ });
});

describe('.index.json builder', () => {
  test('build from INDEX.md', () => { /* ... */ });
  test('atomic write with rollback', () => { /* ... */ });
  test('handle file hash calculation', () => { /* ... */ });
});

describe('SpecLoader SDK', () => {
  test('load existing spec', () => { /* ... */ });
  test('throw on missing spec', () => { /* ... */ });
  test('search with filters', () => { /* ... */ });
  test('fallback on ship-spec failure', () => { /* ... */ });
});
```

### 集成测试场景
```javascript
describe('ship-spec integration', () => {
  test('init → create → search → validate', async () => {
    // 1. 初始化
    await shipSpec('init', { template: 'minimal' });
    expect(fileExists('.docs/spec/INDEX.md')).toBe(true);
    
    // 2. 创建规范
    await shipSpec('create', {
      specId: 'test-spec',
      type: 'shared',
      description: 'Test'
    });
    expect(fileExists('.docs/spec/shared/test-spec.md')).toBe(true);
    
    // 3. 搜索
    const results = await shipSpec('search', { query: 'test' });
    expect(results.total).toBe(1);
    
    // 4. 验证
    const validation = await shipSpec('validate', { all: true });
    expect(validation.valid).toBe(true);
  });
  
  test('ship-design integration', async () => {
    const loader = new SpecLoader({ project: 'web', stage: 'design' });
    const specs = await loader.search('api');
    expect(specs.length).toBeGreaterThan(0);
  });
  
  test('ship-build integration', async () => {
    await onBuildComplete(
      { projects: ['web'], feature_dir: 'feature-test' },
      { module: 'Test', feature: 'Test Feature', apis: ['GET /test'] }
    );
    
    const features = readFile('.docs/spec/web/existing-features.md');
    expect(features).toContain('Test Feature');
  });
});
```

### 端到端测试
```bash
#!/bin/bash
# e2e-test.sh

# 1. 初始化新项目
mkdir test-project && cd test-project
git init
ship-spec init --template standard

# 2. 创建规范
ship-spec create api-standard -t backend -p api -s design,build --description "API 规范"

# 3. 搜索验证
result=$(ship-spec search "api" --format json)
count=$(echo $result | jq '.total')
[[ $count -gt 0 ]] || exit 1

# 4. 验证所有规范
ship-spec validate --all || exit 1

# 5. 模拟规范损坏
echo "broken" >> .docs/spec/backend/api-standard.md

# 6. doctor 修复
ship-spec doctor --fix || exit 1

echo "E2E test passed"
```

---

## 严重问题总结

### 🔴 阻塞交付（必须修复）
1. **INDEX.md 解析器边界情况未处理**：添加表格解析的健壮性
2. **.index.json 原子性写入缺失**：添加临时文件机制
3. **SDK 降级策略缺失**：添加 fallback 逻辑

### ⚠️ 影响质量（建议修复）
4. **并发创建同名规范**：添加文件存在性检查
5. **规范文件外部修改检测**：添加 hash 验证
6. **现有项目迁移指南缺失**：补充迁移文档
7. **existing-features 归档策略缺失**：V2 考虑
8. **开发工作量可能超支**：调整 MVP 范围

### ✅ 可接受（后续优化）
9. 项目重构迁移（migrate 命令）
10. 多仓库规范共享
11. CI/CD 质量监控

---

## 最终判断

**当前状态**：🟡 基本可交付，但需要补充关键实现细节

**必须补充的内容**：
1. INDEX.md 解析器的完整实现（包含边界情况处理）
2. .index.json 原子性写入的实现
3. SDK 的错误处理和降级逻辑
4. 并发创建的冲突检测
5. 现有项目的迁移指南

**建议调整的内容**：
1. 将 doctor 命令从 MVP 移到 V1.1（减少 20 小时工作量）
2. 将性能优化从 MVP 移到 V1.1（减少 12 小时工作量）
3. MVP 专注于核心 CRUD + 搜索 + 验证 + SDK

**调整后的 MVP 范围**：
- ✅ init / create / update / delete
- ✅ search（元数据搜索）
- ✅ validate（核心检查项）
- ✅ sync-index
- ✅ SpecLoader SDK
- ✅ 错误信息改进
- ✅ 迁移指南文档

**工作量**：132 小时 → **110 小时（约 14 个工作日）**

---

下一步：补充关键实现细节到最终方案。
