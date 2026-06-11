# 搜索功能详细设计

## 索引结构

### .index.json 格式
```json
{
  "version": "1.0",
  "last_updated": "2026-06-11T10:00:00Z",
  "build_metadata": {
    "total_specs": 15,
    "total_size_kb": 234,
    "build_duration_ms": 45
  },
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
      "size_bytes": 5420,
      "depends_on": ["error-codes", "auth-standard"],
      "sections": [
        {
          "title": "错误处理",
          "level": 2,
          "line": 45,
          "keywords": ["error", "exception", "status code"]
        },
        {
          "title": "认证方式",
          "level": 2,
          "line": 102,
          "keywords": ["authentication", "jwt", "token"]
        }
      ],
      "keywords": ["error", "authentication", "status code", "response", "request"],
      "code_blocks": 8,
      "links": [
        {"type": "internal", "target": "error-codes#http-status"},
        {"type": "external", "url": "https://tools.ietf.org/html/rfc7231"}
      ]
    }
  ]
}
```

## 索引构建

### 触发时机
1. 创建规范时（create-spec）
2. 更新规范时（update-spec）
3. 删除规范时（delete-spec）
4. 手动同步时（sync-index）
5. 首次搜索时（如果 .index.json 不存在）

### 增量更新策略
```javascript
function updateIndex(specId, operation) {
  const index = loadIndex();
  
  switch (operation) {
    case 'create':
    case 'update':
      // 只重建变更的规范
      const specData = buildSpecMetadata(specId);
      const existingIndex = index.specs.findIndex(s => s.spec_id === specId);
      if (existingIndex >= 0) {
        index.specs[existingIndex] = specData;
      } else {
        index.specs.push(specData);
      }
      break;
      
    case 'delete':
      index.specs = index.specs.filter(s => s.spec_id !== specId);
      break;
  }
  
  index.last_updated = new Date().toISOString();
  saveIndex(index);
}
```

### 元数据提取
```javascript
function buildSpecMetadata(specFile) {
  const content = readFile(specFile);
  const frontmatter = parseFrontmatter(content);
  const sections = extractSections(content);
  const keywords = extractKeywords(content, sections);
  const codeBlocks = countCodeBlocks(content);
  const links = extractLinks(content);
  
  return {
    spec_id: frontmatter.spec_id || deriveSpecId(specFile),
    file: specFile,
    file_hash: sha256(content),
    projects: frontmatter.projects || ['all'],
    stages: frontmatter.stages || [],
    tags: frontmatter.tags || [],
    status: frontmatter.status || 'active',
    description: frontmatter.description || extractFirstParagraph(content),
    last_modified: getFileModifiedTime(specFile),
    size_bytes: content.length,
    depends_on: frontmatter.depends_on || [],
    sections,
    keywords,
    code_blocks: codeBlocks,
    links
  };
}
```

## 搜索实现

### 搜索策略选择
```javascript
function smartSearch(query, options) {
  // 策略 1：精确 spec_id 匹配
  if (isSpecIdFormat(query)) {
    const exact = findBySpecId(query);
    if (exact) {
      return { strategy: 'exact', results: [exact] };
    }
  }
  
  // 策略 2：元数据快速搜索
  if (options.field !== 'content') {
    const metaResults = searchMetadata(query, options);
    
    // 结果少且未强制全文搜索，返回元数据结果
    if (metaResults.length <= 20 && options.field !== 'content') {
      return { strategy: 'metadata', results: metaResults };
    }
  }
  
  // 策略 3：全文搜索
  return { 
    strategy: 'fulltext', 
    results: searchContent(query, options) 
  };
}
```

### 元数据搜索
```javascript
function searchMetadata(query, options) {
  const index = loadIndex();
  const queryLower = query.toLowerCase();
  const queryTerms = queryLower.split(/\s+/);
  
  let candidates = index.specs;
  
  // 应用过滤器
  if (options.project) {
    candidates = candidates.filter(s => 
      s.projects.includes(options.project) || s.projects.includes('all')
    );
  }
  
  if (options.stage) {
    candidates = candidates.filter(s => s.stages.includes(options.stage));
  }
  
  if (options.type) {
    candidates = candidates.filter(s => s.file.startsWith(`${options.type}/`));
  }
  
  if (options.status) {
    candidates = candidates.filter(s => s.status === options.status);
  }
  
  if (options.tags && options.tags.length > 0) {
    candidates = candidates.filter(s => 
      options.tags.some(tag => s.tags.includes(tag))
    );
  }
  
  // 计算相关性评分
  const results = candidates.map(spec => {
    const searchText = [
      spec.spec_id,
      spec.description,
      ...spec.tags,
      ...spec.keywords,
      ...spec.sections.map(s => s.title)
    ].join(' ').toLowerCase();
    
    let score = 0;
    
    // 精确匹配 spec_id：最高分
    if (spec.spec_id === query) {
      score = 1.0;
    }
    // spec_id 部分匹配
    else if (spec.spec_id.includes(queryLower)) {
      score = 0.9;
    }
    // description 匹配
    else if (spec.description.toLowerCase().includes(queryLower)) {
      score = 0.8;
    }
    // 所有查询词都出现
    else if (queryTerms.every(term => searchText.includes(term))) {
      score = 0.7;
    }
    // 部分查询词出现
    else if (queryTerms.some(term => searchText.includes(term))) {
      const matchCount = queryTerms.filter(term => searchText.includes(term)).length;
      score = 0.3 + (matchCount / queryTerms.length) * 0.4;
    }
    
    // 标签匹配加分
    if (spec.tags.some(tag => tag.toLowerCase().includes(queryLower))) {
      score += 0.1;
    }
    
    return { ...spec, score };
  })
  .filter(spec => spec.score > 0)
  .sort((a, b) => b.score - a.score);
  
  // 应用结果限制
  const limit = options.limit || 20;
  return results.slice(0, limit);
}
```

### 全文搜索
```javascript
function searchContent(query, options) {
  // 先通过元数据过滤缩小范围
  const candidates = options.field === 'content'
    ? loadIndex().specs
    : searchMetadata(query, { ...options, field: 'metadata' });
  
  const results = [];
  const queryLower = query.toLowerCase();
  
  for (const spec of candidates) {
    const content = readFile(spec.file);
    const lines = content.split('\n');
    const matches = [];
    
    lines.forEach((line, index) => {
      if (line.toLowerCase().includes(queryLower)) {
        matches.push({
          line: index + 1,
          text: line.trim(),
          context_before: lines.slice(Math.max(0, index - 2), index)
            .map(l => l.trim()),
          context_after: lines.slice(index + 1, index + 3)
            .map(l => l.trim())
        });
      }
    });
    
    if (matches.length > 0) {
      results.push({
        ...spec,
        match_count: matches.length,
        matches: options.verbose ? matches : undefined
      });
    }
  }
  
  return results;
}
```

## 高级搜索语法

### 语法解析
```javascript
function parseSearchQuery(query) {
  const parsed = {
    include: [],    // 必须包含的词
    exclude: [],    // 必须排除的词
    exact: [],      // 精确短语
    regex: null     // 正则表达式
  };
  
  // 精确短语："error handling"
  const exactMatches = query.match(/"([^"]+)"/g);
  if (exactMatches) {
    parsed.exact = exactMatches.map(m => m.slice(1, -1));
    query = query.replace(/"[^"]+"/g, '');
  }
  
  // 排除词：-deprecated
  const excludeMatches = query.match(/-(\w+)/g);
  if (excludeMatches) {
    parsed.exclude = excludeMatches.map(m => m.slice(1));
    query = query.replace(/-\w+/g, '');
  }
  
  // 正则表达式：/API-\d+/
  const regexMatch = query.match(/\/(.+)\//);
  if (regexMatch) {
    parsed.regex = new RegExp(regexMatch[1], 'i');
    query = query.replace(/\/.+\//, '');
  }
  
  // 剩余词为包含词
  parsed.include = query.trim().split(/\s+/).filter(w => w);
  
  return parsed;
}

function advancedSearch(query, options) {
  const parsed = parseSearchQuery(query);
  const index = loadIndex();
  
  return index.specs.filter(spec => {
    const searchText = buildSearchText(spec).toLowerCase();
    
    // 精确短语匹配
    if (parsed.exact.length > 0) {
      if (!parsed.exact.every(phrase => searchText.includes(phrase.toLowerCase()))) {
        return false;
      }
    }
    
    // 排除词
    if (parsed.exclude.length > 0) {
      if (parsed.exclude.some(word => searchText.includes(word.toLowerCase()))) {
        return false;
      }
    }
    
    // 正则表达式
    if (parsed.regex) {
      if (!parsed.regex.test(searchText)) {
        return false;
      }
    }
    
    // 包含词（AND）
    if (parsed.include.length > 0) {
      if (!parsed.include.every(word => searchText.includes(word.toLowerCase()))) {
        return false;
      }
    }
    
    return true;
  });
}
```

## 搜索结果格式化

### 表格格式
```javascript
function formatAsTable(results) {
  const headers = ['SPEC_ID', 'PROJECT', 'STAGES', 'DESCRIPTION'];
  const rows = results.map(r => [
    r.spec_id,
    r.projects.join(','),
    r.stages.join(','),
    truncate(r.description, 40)
  ]);
  
  return formatTable(headers, rows);
}
```

### 详细格式
```javascript
function formatVerbose(results) {
  return results.map((r, index) => {
    let output = `[${index + 1}] ${r.spec_id} (${r.file})\n`;
    output += `    Projects: ${r.projects.join(', ')} | Stages: ${r.stages.join(', ')}\n`;
    output += `    Score: ${r.score.toFixed(2)}\n\n`;
    
    if (r.matches) {
      r.matches.slice(0, 3).forEach(m => {
        output += `    Line ${m.line}: ${m.text}\n`;
        if (m.context_before.length > 0) {
          output += `    ${m.context_before.join('\n    ')}\n`;
        }
        if (m.context_after.length > 0) {
          output += `    ${m.context_after.join('\n    ')}\n`;
        }
        output += '\n';
      });
      
      if (r.matches.length > 3) {
        output += `    ... and ${r.matches.length - 3} more matches\n\n`;
      }
    }
    
    return output;
  }).join('\n');
}
```

### JSON 格式
```javascript
function formatAsJson(results, query, filters) {
  return JSON.stringify({
    query,
    filters,
    total: results.length,
    results: results.map(r => ({
      spec_id: r.spec_id,
      file: r.file,
      projects: r.projects,
      stages: r.stages,
      tags: r.tags,
      status: r.status,
      description: r.description,
      score: r.score,
      matches: r.matches
    }))
  }, null, 2);
}
```

## 性能优化

### 缓存策略
```javascript
const searchCache = new Map();
const CACHE_TTL = 60000; // 1分钟

function cachedSearch(query, options) {
  const cacheKey = JSON.stringify({ query, options });
  const cached = searchCache.get(cacheKey);
  
  if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
    return cached.results;
  }
  
  const results = smartSearch(query, options);
  searchCache.set(cacheKey, {
    results,
    timestamp: Date.now()
  });
  
  return results;
}

// 索引更新时清除缓存
function invalidateSearchCache() {
  searchCache.clear();
}
```

### 并行全文搜索
```javascript
async function parallelFulltextSearch(candidates, query, options) {
  const chunkSize = 10;
  const chunks = [];
  
  for (let i = 0; i < candidates.length; i += chunkSize) {
    chunks.push(candidates.slice(i, i + chunkSize));
  }
  
  const results = await Promise.all(
    chunks.map(chunk => 
      Promise.resolve(searchContentInChunk(chunk, query, options))
    )
  );
  
  return results.flat();
}
```

### 索引预热
```javascript
// 首次搜索时自动构建索引
function ensureIndexExists() {
  const indexPath = '.docs/spec/.index.json';
  
  if (!fileExists(indexPath)) {
    console.log('Building search index for the first time...');
    syncIndex({ auto_fix: true, rebuild_json: true });
    console.log('Index built successfully.');
  }
}
```

## 搜索建议

### 拼写纠正和建议
```javascript
function suggestCorrections(query, specs) {
  const allSpecIds = specs.map(s => s.spec_id);
  const allKeywords = [...new Set(specs.flatMap(s => s.keywords))];
  
  const suggestions = [];
  
  // Levenshtein 距离计算相似度
  for (const specId of allSpecIds) {
    const distance = levenshteinDistance(query, specId);
    if (distance <= 3 && distance > 0) {
      suggestions.push({ 
        type: 'spec_id', 
        value: specId, 
        distance 
      });
    }
  }
  
  for (const keyword of allKeywords) {
    const distance = levenshteinDistance(query, keyword);
    if (distance <= 3 && distance > 0) {
      suggestions.push({ 
        type: 'keyword', 
        value: keyword, 
        distance 
      });
    }
  }
  
  return suggestions
    .sort((a, b) => a.distance - b.distance)
    .slice(0, 5);
}
```

### 热门搜索
```javascript
function getPopularSearches() {
  return [
    'existing-features',
    'api-standard',
    'naming-conventions',
    'error-codes',
    'auth-standard'
  ];
}
```

## 搜索 API 示例

### 其他技能集成
```javascript
// ship-design 查找 API 相关规范
const specs = await callSkill('ship-spec', {
  command: 'search',
  query: 'api',
  options: {
    stage: 'design',
    project: currentProject,
    format: 'json'
  }
});

// 读取第一个匹配的规范
if (specs.results.length > 0) {
  const apiStandard = await read(specs.results[0].file);
  // 使用规范内容
}
```

### 命令行使用
```bash
# 基础搜索
ship-spec search "authentication"

# 带过滤器
ship-spec search "api" --stage design --project web

# 全文搜索
ship-spec search "error handling" --field content --verbose

# 高级语法
ship-spec search '"REST API" -deprecated' --format json

# 标签搜索
ship-spec search --tags security,api
```
