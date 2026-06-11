# ship-spec 技能改造方案 - 可交付版本（Final）

基于两轮对抗式审查的最终可交付方案。

---

## 变更摘要

### 相对于初版的关键调整
1. ✅ **索引策略明确**：INDEX.md 为唯一真实来源，.index.json 自动生成
2. ✅ **职责边界清晰**：existing-features 由 ship-build 直接写入
3. ✅ **MVP 范围收窄**：去掉 suggest-new-spec、doctor（移至 V1.1）
4. ✅ **实现细节补充**：INDEX.md 解析器、原子性写入、SDK 错误处理
5. ✅ **迁移路径明确**：提供现有项目的迁移指南

### 工作量
- **原估算**：164 小时（21 工作日）
- **调整后**：110 小时（14 工作日）
- **节省**：54 小时（通过去掉非核心功能）

---

## MVP 功能清单

### 核心命令（8个）
| 命令 | 功能 | 优先级 | 估算 |
|---|---|---|---|
| `init` | 初始化规范目录 | P0 | 6h |
| `create` | 创建新规范 | P0 | 8h |
| `update` | 更新规范 | P0 | 8h |
| `delete` | 删除/归档规范 | P0 | 4h |
| `search` | 搜索规范（元数据） | P0 | 6h |
| `validate` | 验证规范 | P0 | 10h |
| `sync-index` | 同步索引 | P0 | 6h |
| `stats` | 规范使用统计 | P1 | 4h |

### SDK
- SpecLoader 类（load / search / filter）
- 错误处理和降级
- 估算：8h

### 文档
- 用户指南
- 迁移指南
- API 文档
- 估算：8h

### 测试
- 单元测试
- 集成测试
- E2E 测试
- 估算：18h

**总计**：110 小时

---

## 核心实现

### 1. INDEX.md 解析器（健壮版）

```javascript
/**
 * 解析 INDEX.md 表格
 * 支持：
 * - 转义的竖线（\|）
 * - 空单元格（解析为空字符串）
 * - "-" 表示空数组
 * - 逗号分隔的数组字段
 */
function parseIndexTable(markdown) {
  const lines = markdown.split('\n');
  
  // 查找表头行
  const headerLine = lines.find(l => l.trim().startsWith('|') && l.includes('spec_id'));
  if (!headerLine) {
    throw new Error('INDEX.md: Cannot find header row with "spec_id"');
  }
  
  const headerIndex = lines.indexOf(headerLine);
  const separatorLine = lines[headerIndex + 1];
  
  // 验证分隔行格式
  if (!separatorLine || !separatorLine.match(/^\s*\|[\s\-:|]+\|\s*$/)) {
    throw new Error('INDEX.md: Invalid table separator row');
  }
  
  // 解析表头，确定列顺序
  const headers = parseTableRow(headerLine);
  
  // 验证必需列
  const requiredColumns = ['spec_id', 'file', 'stages', 'projects', 'description'];
  const missingColumns = requiredColumns.filter(col => !headers.includes(col));
  if (missingColumns.length > 0) {
    throw new Error(`INDEX.md: Missing required columns: ${missingColumns.join(', ')}`);
  }
  
  // 解析数据行
  const specs = [];
  let currentLine = headerIndex + 2;
  
  while (currentLine < lines.length) {
    const line = lines[currentLine].trim();
    
    // 空行或非表格行，结束解析
    if (!line || !line.startsWith('|')) {
      break;
    }
    
    const cells = parseTableRow(line);
    
    // 跳过列数不匹配的行（可能是格式错误）
    if (cells.length !== headers.length) {
      console.warn(`INDEX.md line ${currentLine + 1}: Column count mismatch, skipping`);
      currentLine++;
      continue;
    }
    
    // 构建 spec 对象
    const spec = {};
    headers.forEach((header, i) => {
      const value = cells[i];
      spec[header] = parseTableCell(header, value);
    });
    
    specs.push(spec);
    currentLine++;
  }
  
  return specs;
}

/**
 * 解析表格行，处理转义的竖线
 */
function parseTableRow(line) {
  // 移除首尾空格和竖线
  line = line.trim().replace(/^\|/, '').replace(/\|$/, '');
  
  // 分割单元格，处理转义的竖线
  const cells = [];
  let currentCell = '';
  let i = 0;
  
  while (i < line.length) {
    if (line[i] === '\\' && line[i + 1] === '|') {
      // 转义的竖线，添加到当前单元格
      currentCell += '|';
      i += 2;
    } else if (line[i] === '|') {
      // 未转义的竖线，单元格分隔符
      cells.push(currentCell.trim());
      currentCell = '';
      i++;
    } else {
      currentCell += line[i];
      i++;
    }
  }
  
  // 添加最后一个单元格
  cells.push(currentCell.trim());
  
  return cells;
}

/**
 * 解析单元格值，根据列名转换类型
 */
function parseTableCell(columnName, value) {
  // 空值处理
  if (!value || value === '-') {
    if (['projects', 'stages', 'tags', 'depends_on'].includes(columnName)) {
      return [];
    }
    return '';
  }
  
  // 数组字段：逗号分隔
  if (['projects', 'stages', 'tags', 'depends_on'].includes(columnName)) {
    return value.split(',').map(v => v.trim()).filter(v => v);
  }
  
  // 其他字段：原样返回
  return value;
}

/**
 * 将 spec 对象序列化为表格行
 */
function formatTableRow(spec, headers) {
  const cells = headers.map(header => {
    const value = spec[header];
    
    // 数组字段
    if (Array.isArray(value)) {
      return value.length > 0 ? value.join(',') : '-';
    }
    
    // 字符串字段，转义竖线
    if (typeof value === 'string') {
      return value.replace(/\|/g, '\\|');
    }
    
    return value || '-';
  });
  
  return '| ' + cells.join(' | ') + ' |';
}
```

### 2. .index.json 原子性重建

```javascript
const fs = require('fs');
const crypto = require('crypto');

/**
 * 从 INDEX.md 重建 .index.json
 * 使用临时文件保证原子性
 */
function rebuildIndexJson() {
  const indexMdPath = '.docs/spec/INDEX.md';
  const indexJsonPath = '.docs/spec/.index.json';
  const tempPath = '.docs/spec/.index.json.tmp';
  
  try {
    // 1. 读取并解析 INDEX.md
    if (!fs.existsSync(indexMdPath)) {
      throw new Error('INDEX.md not found');
    }
    
    const markdown = fs.readFileSync(indexMdPath, 'utf-8');
    const specs = parseIndexTable(markdown);
    
    // 2. 增强每个 spec 的元数据
    const enhancedSpecs = specs.map(spec => {
      const filePath = `.docs/spec/${spec.file}`;
      
      if (!fs.existsSync(filePath)) {
        console.warn(`Warning: Spec file not found: ${filePath}`);
        return {
          ...spec,
          file_hash: null,
          last_modified: null,
          error: 'file_not_found'
        };
      }
      
      const content = fs.readFileSync(filePath, 'utf-8');
      const stats = fs.statSync(filePath);
      
      return {
        ...spec,
        file_hash: sha256(content),
        last_modified: stats.mtime.toISOString(),
        size_bytes: stats.size
      };
    });
    
    // 3. 构建索引对象
    const index = {
      version: '1.0',
      last_updated: new Date().toISOString(),
      build_metadata: {
        total_specs: enhancedSpecs.length,
        total_size_kb: Math.round(
          enhancedSpecs.reduce((sum, s) => sum + (s.size_bytes || 0), 0) / 1024
        ),
        errors: enhancedSpecs.filter(s => s.error).length
      },
      specs: enhancedSpecs
    };
    
    // 4. 写入临时文件
    fs.writeFileSync(tempPath, JSON.stringify(index, null, 2), 'utf-8');
    
    // 5. 验证临时文件
    const tempContent = fs.readFileSync(tempPath, 'utf-8');
    JSON.parse(tempContent); // 验证 JSON 格式
    
    // 6. 原子性替换
    fs.renameSync(tempPath, indexJsonPath);
    
    return { success: true, specs_count: enhancedSpecs.length };
    
  } catch (error) {
    // 清理临时文件
    if (fs.existsSync(tempPath)) {
      fs.unlinkSync(tempPath);
    }
    
    throw new Error(`Failed to rebuild index: ${error.message}`);
  }
}

/**
 * 计算文件内容的 SHA-256 哈希
 */
function sha256(content) {
  return 'sha256:' + crypto.createHash('sha256').update(content).digest('hex');
}

/**
 * 检查索引是否过期（采样检查）
 */
function isIndexStale() {
  const indexJsonPath = '.docs/spec/.index.json';
  
  if (!fs.existsSync(indexJsonPath)) {
    return true;
  }
  
  try {
    const index = JSON.parse(fs.readFileSync(indexJsonPath, 'utf-8'));
    
    // 采样检查前 5 个规范文件
    const samplesToCheck = Math.min(5, index.specs.length);
    
    for (let i = 0; i < samplesToCheck; i++) {
      const spec = index.specs[i];
      const filePath = `.docs/spec/${spec.file}`;
      
      if (!fs.existsSync(filePath)) continue;
      
      const content = fs.readFileSync(filePath, 'utf-8');
      const currentHash = sha256(content);
      
      if (currentHash !== spec.file_hash) {
        return true; // 发现过期
      }
    }
    
    return false; // 所有采样都匹配
    
  } catch (error) {
    return true; // 读取失败，视为过期
  }
}
```

### 3. SpecLoader SDK（完整版）

```javascript
/**
 * SpecLoader SDK
 * 供其他技能使用，封装规范加载逻辑
 */
export class SpecLoader {
  constructor(options = {}) {
    this.project = options.project;
    this.stage = options.stage;
    this.indexPath = options.indexPath || '.docs/spec/INDEX.md';
    this.cache = new Map();
  }
  
  /**
   * 加载单个规范
   * @param {string} specId - 规范 ID
   * @returns {Object} 规范对象（包含 content）
   * @throws {SpecNotFoundError} 规范不存在
   */
  async load(specId) {
    try {
      const index = this._loadIndex();
      const spec = index.find(s => s.spec_id === specId);
      
      if (!spec) {
        throw new SpecNotFoundError(specId);
      }
      
      // 读取规范内容
      const content = await this._readFile(`.docs/spec/${spec.file}`);
      
      return {
        ...spec,
        content,
        frontmatter: this._parseFrontmatter(content),
        body: this._extractBody(content)
      };
      
    } catch (error) {
      if (error instanceof SpecNotFoundError) {
        throw error;
      }
      throw new SpecLoaderError(`Failed to load spec '${specId}': ${error.message}`);
    }
  }
  
  /**
   * 搜索规范
   * @param {string} query - 搜索关键词
   * @param {Object} options - 搜索选项
   * @returns {Array} 搜索结果
   */
  async search(query, options = {}) {
    try {
      // 优先使用 ship-spec 命令
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
      
      if (!results || !results.results) {
        throw new Error('Invalid search response');
      }
      
      return results.results;
      
    } catch (error) {
      // 降级：本地搜索
      console.warn('ship-spec search failed, falling back to local search');
      return this._localSearch(query, options);
    }
  }
  
  /**
   * 过滤规范
   * @param {Object} criteria - 过滤条件
   * @returns {Array} 符合条件的规范
   */
  filter(criteria) {
    const index = this._loadIndex();
    
    return index.filter(spec => {
      // 项目过滤
      if (criteria.project) {
        if (!spec.projects.includes(criteria.project) && !spec.projects.includes('all')) {
          return false;
        }
      }
      
      // 阶段过滤
      if (criteria.stage) {
        if (!spec.stages.includes(criteria.stage)) {
          return false;
        }
      }
      
      // 类型过滤
      if (criteria.type) {
        if (!spec.file.startsWith(`${criteria.type}/`)) {
          return false;
        }
      }
      
      // 标签过滤
      if (criteria.tags && criteria.tags.length > 0) {
        if (!criteria.tags.some(tag => spec.tags.includes(tag))) {
          return false;
        }
      }
      
      // 状态过滤
      if (criteria.status) {
        if (spec.status !== criteria.status) {
          return false;
        }
      }
      
      return true;
    });
  }
  
  /**
   * 获取所有规范 ID
   */
  listSpecIds() {
    const index = this._loadIndex();
    return index.map(s => s.spec_id);
  }
  
  /**
   * 私有方法：加载索引
   */
  _loadIndex() {
    const cacheKey = 'index';
    
    if (this.cache.has(cacheKey)) {
      return this.cache.get(cacheKey);
    }
    
    const markdown = fs.readFileSync(this.indexPath, 'utf-8');
    const index = parseIndexTable(markdown);
    
    this.cache.set(cacheKey, index);
    return index;
  }
  
  /**
   * 私有方法：本地搜索（降级）
   */
  _localSearch(query, options) {
    const index = this._loadIndex();
    const queryLower = query.toLowerCase();
    
    return index.filter(spec => {
      const searchText = [
        spec.spec_id,
        spec.description,
        ...(spec.tags || [])
      ].join(' ').toLowerCase();
      
      return searchText.includes(queryLower);
    });
  }
  
  /**
   * 私有方法：读取文件
   */
  async _readFile(path) {
    // 使用 read 工具
    return await read(path);
  }
  
  /**
   * 私有方法：解析 frontmatter
   */
  _parseFrontmatter(content) {
    const match = content.match(/^---\n([\s\S]+?)\n---/);
    if (!match) return {};
    
    // 简单的 YAML 解析（MVP 版本）
    const yaml = match[1];
    const result = {};
    
    yaml.split('\n').forEach(line => {
      const colonIndex = line.indexOf(':');
      if (colonIndex === -1) return;
      
      const key = line.slice(0, colonIndex).trim();
      const value = line.slice(colonIndex + 1).trim();
      
      // 处理数组
      if (value.startsWith('[') && value.endsWith(']')) {
        result[key] = value.slice(1, -1).split(',').map(v => v.trim().replace(/['"]/g, ''));
      } else {
        result[key] = value.replace(/['"]/g, '');
      }
    });
    
    return result;
  }
  
  /**
   * 私有方法：提取正文
   */
  _extractBody(content) {
    return content.replace(/^---\n[\s\S]+?\n---\n/, '');
  }
}

/**
 * 自定义错误类
 */
export class SpecNotFoundError extends Error {
  constructor(specId) {
    super(`Spec not found: ${specId}`);
    this.name = 'SpecNotFoundError';
    this.specId = specId;
  }
}

export class SpecLoaderError extends Error {
  constructor(message) {
    super(message);
    this.name = 'SpecLoaderError';
  }
}
```

### 4. 并发冲突检测

```javascript
/**
 * 创建规范，带并发冲突检测
 */
function createSpec(specId, options) {
  // 1. 确定文件路径
  const filePath = determineFilePath(specId, options.type, options.projects);
  
  // 2. 检查文件是否已存在
  if (fs.existsSync(filePath)) {
    throw new ConflictError(
      `Spec file already exists: ${filePath}\n\n` +
      `Use 'ship-spec update ${specId}' to modify it, or choose a different spec_id.`
    );
  }
  
  // 3. 检查 INDEX.md 中是否已存在
  const index = parseIndexTable(fs.readFileSync('.docs/spec/INDEX.md', 'utf-8'));
  const existing = index.find(s => s.spec_id === specId);
  
  if (existing) {
    throw new ConflictError(
      `Spec ID already exists in INDEX.md: ${specId}\n` +
      `File: ${existing.file}\n\n` +
      `Choose a different spec_id or delete the existing spec first.`
    );
  }
  
  // 4. 生成规范内容
  const content = generateSpecContent(specId, options);
  
  // 5. 原子性写入
  try {
    fs.writeFileSync(filePath, content, 'utf-8');
    
    // 6. 更新 INDEX.md
    updateIndexMd({
      operation: 'create',
      spec_id: specId,
      file: path.relative('.docs/spec', filePath),
      projects: options.projects || ['all'],
      stages: options.stages || ['design', 'build'],
      tags: options.tags || [],
      status: 'active',
      description: options.description,
      last_updated: new Date().toISOString().split('T')[0]
    });
    
    // 7. 重建 .index.json
    rebuildIndexJson();
    
    return {
      success: true,
      spec_id: specId,
      file_path: filePath,
      next_steps: [
        `Edit the spec file: ${filePath}`,
        `Add content to the spec`,
        `Verify: ship-spec validate ${specId}`
      ]
    };
    
  } catch (error) {
    // 回滚：删除刚创建的文件
    if (fs.existsSync(filePath)) {
      fs.unlinkSync(filePath);
    }
    throw error;
  }
}

class ConflictError extends Error {
  constructor(message) {
    super(message);
    this.name = 'ConflictError';
  }
}
```

---

## 迁移指南

### 场景 1：全新项目
```bash
# 1. 初始化
cd your-project
ship-spec init --template standard

# 2. 创建第一个规范
ship-spec create api-standard \
  -t backend \
  -p api \
  -s design,build \
  --description "REST API 设计规范"

# 3. 编辑规范
vim .docs/spec/backend/api-standard.md

# 4. 验证
ship-spec validate --all
```

### 场景 2：有散落规范文档
```bash
# 1. 初始化
ship-spec init --template minimal

# 2. 复制现有文档
cp docs/api-guide.md .docs/spec/backend/api-standard.md

# 3. 添加 frontmatter
# 在文件开头添加：
---
spec_id: api-standard
description: REST API 设计规范
projects: [api]
stages: [design, build]
tags: [api, rest]
status: active
---

# 4. 同步索引
ship-spec sync-index --auto-fix

# 5. 验证
ship-spec validate --all
```

### 场景 3：已有 .docs/spec/ 但无 INDEX.md
```bash
# 自动扫描并生成 INDEX.md
ship-spec sync-index --rebuild

# 检查生成结果
ship-spec validate --all

# 如有问题，手动修正后再次同步
ship-spec sync-index --auto-fix
```

---

## 验收标准（最终版）

### 功能完整性 ✅
- [ ] 所有 MVP 命令实现（init/create/update/delete/search/validate/sync-index）
- [ ] SpecLoader SDK 可用
- [ ] INDEX.md 解析健壮（处理转义、空值、列顺序变化）
- [ ] .index.json 原子性写入
- [ ] 并发冲突检测
- [ ] 错误信息清晰可操作

### 性能达标 ✅
- [ ] 元数据搜索 < 50ms（100 规范）
- [ ] 索引重建 < 200ms（100 规范）
- [ ] 内存占用 < 10MB

### 鲁棒性 ✅
- [ ] 通过所有单元测试
- [ ] 通过集成测试（ship-design, ship-build）
- [ ] 通过 E2E 测试
- [ ] INDEX.md 损坏可自动恢复（sync-index --rebuild）
- [ ] 规范文件外部修改自动检测（hash 验证）

### 用户体验 ✅
- [ ] 首次使用顺畅（init → create → search → validate）
- [ ] 迁移指南完整（3 种场景）
- [ ] 文档完整（README、API 文档、示例）

---

## 实施计划（最终版）

### Week 1: 核心基础设施
- Day 1-2: INDEX.md 解析器 + .index.json 构建器
- Day 3: 基础 CRUD 框架 + 错误类型
- Day 4: 单元测试

### Week 2: 命令实现
- Day 1: init + create 命令
- Day 2: update + delete 命令
- Day 3: sync-index 命令
- Day 4: 集成测试

### Week 3: 搜索和验证
- Day 1-2: 元数据搜索 + 格式化
- Day 3: validate 命令
- Day 4: 性能测试

### Week 4: SDK 和文档
- Day 1: SpecLoader SDK
- Day 2: 集成测试（ship-design, ship-build）
- Day 3: 用户文档 + 迁移指南
- Day 4: Code Review + Bug 修复

---

## 后续版本规划

### V1.1（+2周）
- doctor 命令（诊断和修复）
- 性能优化（缓存、并行）
- stats 命令增强

### V2.0（+4周）
- 全文搜索
- 高级搜索语法
- suggest-new-spec（智能建议）
- 规范版本管理
- Web UI

---

## 最终结论

**状态**：✅ 可交付

**交付物**：
1. ship-spec 技能实现（8 个命令）
2. SpecLoader SDK
3. 用户文档和迁移指南
4. 完整测试套件

**工作量**：110 小时（14 个工作日）

**质量保证**：
- 健壮的解析器（处理边界情况）
- 原子性写入（无数据损坏风险）
- 错误处理和降级（SDK fallback）
- 并发冲突检测（避免覆盖）
- 完整的测试覆盖

**风险**：低
- 技术栈成熟（Node.js、文件系统操作）
- 依赖少（无外部服务）
- 架构简单（文件 + 索引）

方案可交付。✅
