# ship-spec CLI 集成方案（修订版）

## 设计变更

### ❌ 废弃：JavaScript SDK
**原因**：
- 技能是 markdown 文档，AI 读取后执行 bash 命令
- JavaScript SDK 需要创建 .js 文件、执行、读取结果，过于复杂
- 不符合技能的调用模式

### ✅ 采用：Bash CLI + JSON 输出
**理由**：
- AI 可以直接在技能执行中调用 bash 命令
- 通用，任何技能都能用
- 符合 Unix 哲学：做好一件事
- JSON 输出易于解析

---

## CLI 命令设计

### 核心命令（保持不变）
```bash
ship-spec init [--template <name>]
ship-spec create <spec-id> [options]
ship-spec update <spec-id> [options]
ship-spec delete <spec-id> [options]
ship-spec validate [spec-id] [options]
ship-spec sync-index [options]
```

### 新增：集成命令

#### 1. load - 加载规范内容
```bash
ship-spec load <spec-id> [options]

Options:
  -f, --format <format>     输出格式：json | yaml | markdown（默认 json）
  --content-only            只输出正文内容
  --frontmatter-only        只输出 frontmatter

示例：
$ ship-spec load rest-api-standard --format json

输出：
{
  "spec_id": "rest-api-standard",
  "file": "backend/rest-api-standard.md",
  "projects": ["api"],
  "stages": ["design", "build"],
  "tags": ["api", "rest", "backend"],
  "status": "active",
  "description": "REST API 规范",
  "frontmatter": {
    "spec_id": "rest-api-standard",
    "description": "REST API 规范",
    "projects": ["api"],
    "stages": ["design", "build"]
  },
  "content": "# REST API Standard\n\n## 错误处理\n...",
  "body": "## 错误处理\n..."
}

$ ship-spec load rest-api-standard --content-only
# 直接输出规范正文，不包含 JSON 结构
## 错误处理
...
```

#### 2. list - 列出规范
```bash
ship-spec list [options]

Options:
  -p, --project <project>   过滤项目
  -s, --stage <stage>       过滤阶段
  -t, --type <type>         过滤类型：frontend | backend | shared
  --tags <tags>             过滤标签（逗号分隔）
  --status <status>         过滤状态：active | deprecated
  -f, --format <format>     输出格式：table | json（默认 table）

示例：
$ ship-spec list --project web --stage design --format json

输出：
{
  "total": 3,
  "filters": {
    "project": "web",
    "stage": "design"
  },
  "results": [
    {
      "spec_id": "rest-api-standard",
      "file": "backend/rest-api-standard.md",
      "projects": ["api"],
      "stages": ["design", "build"],
      "description": "REST API 规范"
    },
    {
      "spec_id": "naming-conventions",
      "file": "shared/naming-conventions.md",
      "projects": ["all"],
      "stages": ["design"],
      "description": "命名规范"
    }
  ]
}
```

#### 3. search - 搜索规范（保持，增强输出）
```bash
ship-spec search <query> [options]

Options:
  -p, --project <project>   过滤项目
  -s, --stage <stage>       过滤阶段
  -f, --format <format>     输出格式：table | json（默认 table）
  --limit <n>               结果数量限制

示例：
$ ship-spec search "api" --project web --format json

输出：
{
  "query": "api",
  "total": 2,
  "results": [
    {
      "spec_id": "rest-api-standard",
      "file": "backend/rest-api-standard.md",
      "projects": ["api"],
      "stages": ["design", "build"],
      "score": 0.95,
      "description": "REST API 规范"
    }
  ]
}
```

---

## 技能集成示例

### ship-design 技能集成

```markdown
# ship-design 技能

## 执行流程

### 1. 读取 feature meta.yml
```bash
feature_meta=$(cat feature-xxx/meta.yml)
project=$(echo "$feature_meta" | yq '.projects[0]')
```

### 2. 加载 design 阶段的相关规范
```bash
# 列出所有 design 阶段的规范
specs=$(ship-spec list --project "$project" --stage design --format json)

# 提取规范 ID 列表
spec_ids=$(echo "$specs" | jq -r '.results[].spec_id')

# 加载每个规范的内容
for spec_id in $spec_ids; do
  echo "Loading spec: $spec_id"
  spec_content=$(ship-spec load "$spec_id" --format json)
  
  # 提取规范正文
  body=$(echo "$spec_content" | jq -r '.body')
  
  # 保存到临时文件供后续使用
  echo "$body" > "/tmp/spec-${spec_id}.md"
done
```

### 3. 将规范注入到设计上下文
```bash
# 读取 API 规范
api_standard=$(cat /tmp/spec-rest-api-standard.md)

# 生成设计提示词
design_prompt="根据以下规范设计技术方案：

API 规范：
$api_standard

需求：
$(cat requirements.md)
"

# 调用 AI 生成设计
echo "$design_prompt" | ai-design > design.md
```
```

### ship-build 技能集成

```markdown
# ship-build 技能

## 执行流程

### 1. 加载 build 阶段的规范
```bash
project=$(yq '.projects[0]' feature-xxx/meta.yml)

# 列出所有 build 阶段的规范
specs=$(ship-spec list --project "$project" --stage build --format json)

# 加载代码规范
coding_standard=$(ship-spec load coding-conventions --content-only)

# 加载测试规范
test_standard=$(ship-spec load test-standards --content-only)
```

### 2. 按规范实现代码
```bash
# 在 AI prompt 中引用规范
prompt="按照以下规范实现功能：

代码规范：
$coding_standard

测试规范：
$test_standard

设计方案：
$(cat design.md)
"

echo "$prompt" | ai-code > implementation.ts
```

### 3. 完成后更新 existing-features
```bash
# 直接追加到 existing-features.md
cat >> .docs/spec/shared/existing-features.md <<EOF

## 用户模块
- **用户登录**：完成时间 $(date +%Y-%m-%d)，Feature: feature-xxx
  - 表：users, sessions
  - API：POST /api/v1/auth/login
  - 页面：/login
  - 测试：tests/e2e/login.spec.ts
EOF

# ship-spec sync-index 会在下次运行时自动索引
```
```

### ship-understand 技能集成

```markdown
# ship-understand 技能

## 执行流程

### 1. 加载 existing-features
```bash
# 列出所有 understand 阶段的规范
specs=$(ship-spec list --stage understand --format json)

# 加载已有功能索引
existing_features=$(ship-spec load existing-features --content-only)
```

### 2. 分析需求与现有功能的关系
```bash
prompt="分析需求与现有功能的关系：

已有功能：
$existing_features

新需求：
$(cat requirements.md)

输出：
1. 可复用的现有功能
2. 需要新增的功能
3. 需要修改的功能
"

echo "$prompt" | ai-analyze > analysis.md
```
```

---

## Bash 辅助库（可选）

如果多个技能需要相同的规范加载逻辑，提供轻量辅助脚本：

```bash
# skills/ship-spec/lib.sh

#!/bin/bash
# ship-spec 辅助函数库

# 加载规范内容（正文）
spec_load() {
  local spec_id=$1
  ship-spec load "$spec_id" --content-only
}

# 加载规范（JSON）
spec_load_json() {
  local spec_id=$1
  ship-spec load "$spec_id" --format json
}

# 搜索规范
spec_search() {
  local query=$1
  shift
  ship-spec search "$query" "$@" --format json
}

# 列出规范
spec_list() {
  ship-spec list "$@" --format json
}

# 加载多个规范（按项目和阶段）
spec_load_for_stage() {
  local project=$1
  local stage=$2
  
  local specs=$(ship-spec list --project "$project" --stage "$stage" --format json)
  local spec_ids=$(echo "$specs" | jq -r '.results[].spec_id')
  
  for spec_id in $spec_ids; do
    echo "=== $spec_id ==="
    ship-spec load "$spec_id" --content-only
    echo ""
  done
}

# 导出函数
export -f spec_load
export -f spec_load_json
export -f spec_search
export -f spec_list
export -f spec_load_for_stage
```

**使用**：
```bash
# 在技能中引入
source skills/ship-spec/lib.sh

# 使用辅助函数
api_standard=$(spec_load rest-api-standard)
specs=$(spec_list --project web --stage design)
```

---

## 实现简化

### 去掉的部分
- ❌ JavaScript SDK（SpecLoader 类）
- ❌ SDK 错误类（SpecNotFoundError, SpecLoaderError）
- ❌ SDK 单元测试

### 新增的部分
- ✅ `load` 命令实现
- ✅ `list` 命令实现
- ✅ 所有命令支持 `--format json`
- ✅ 可选的 bash 辅助库

### 工作量变化
- **原估算（含 SDK）**：110 小时
- **新估算（CLI only）**：102 小时
- **节省**：8 小时

---

## 命令实现伪代码

### load 命令
```javascript
function loadCommand(specId, options) {
  // 1. 读取 INDEX.md
  const index = parseIndexTable(readFile('.docs/spec/INDEX.md'));
  
  // 2. 查找规范
  const spec = index.find(s => s.spec_id === specId);
  if (!spec) {
    console.error(`Error: Spec not found: ${specId}`);
    process.exit(1);
  }
  
  // 3. 读取规范文件
  const filePath = `.docs/spec/${spec.file}`;
  const content = readFile(filePath);
  
  // 4. 解析 frontmatter
  const frontmatter = parseFrontmatter(content);
  const body = extractBody(content);
  
  // 5. 输出
  if (options.contentOnly) {
    console.log(content);
  } else if (options.frontmatterOnly) {
    console.log(JSON.stringify(frontmatter, null, 2));
  } else if (options.format === 'json') {
    console.log(JSON.stringify({
      ...spec,
      frontmatter,
      content,
      body
    }, null, 2));
  } else {
    console.log(content);
  }
}
```

### list 命令
```javascript
function listCommand(options) {
  // 1. 读取 INDEX.md
  const index = parseIndexTable(readFile('.docs/spec/INDEX.md'));
  
  // 2. 应用过滤器
  let results = index;
  
  if (options.project) {
    results = results.filter(s => 
      s.projects.includes(options.project) || s.projects.includes('all')
    );
  }
  
  if (options.stage) {
    results = results.filter(s => s.stages.includes(options.stage));
  }
  
  if (options.type) {
    results = results.filter(s => s.file.startsWith(`${options.type}/`));
  }
  
  if (options.tags) {
    const tags = options.tags.split(',');
    results = results.filter(s => 
      tags.some(tag => s.tags.includes(tag))
    );
  }
  
  if (options.status) {
    results = results.filter(s => s.status === options.status);
  }
  
  // 3. 输出
  if (options.format === 'json') {
    console.log(JSON.stringify({
      total: results.length,
      filters: options,
      results
    }, null, 2));
  } else {
    // 表格格式
    console.log('SPEC_ID\t\tPROJECT\t\tSTAGES\t\tDESCRIPTION');
    results.forEach(s => {
      console.log(`${s.spec_id}\t${s.projects.join(',')}\t${s.stages.join(',')}\t${s.description}`);
    });
  }
}
```

---

## 测试策略调整

### 去掉的测试
- SDK 单元测试
- SDK 错误处理测试

### 保留的测试
- CLI 命令集成测试
- JSON 输出格式验证
- 过滤逻辑测试

### 新增的测试
```bash
# test/cli/load.test.sh
test_load_json_output() {
  result=$(ship-spec load rest-api-standard --format json)
  
  # 验证 JSON 格式
  echo "$result" | jq . > /dev/null
  assertEquals 0 $?
  
  # 验证必需字段
  spec_id=$(echo "$result" | jq -r '.spec_id')
  assertEquals "rest-api-standard" "$spec_id"
}

test_load_content_only() {
  result=$(ship-spec load rest-api-standard --content-only)
  
  # 验证是 markdown 内容，不是 JSON
  echo "$result" | jq . > /dev/null 2>&1
  assertNotEquals 0 $?
  
  # 验证包含内容
  echo "$result" | grep -q "# REST API Standard"
  assertEquals 0 $?
}
```

---

## 文档更新清单

- [x] 08-cli-integration-approach.md（本文档）
- [ ] 修订 07-final-deliverable.md
  - 去掉 SpecLoader SDK 章节
  - 添加 load 和 list 命令
  - 更新技能集成示例
- [ ] 修订 02-command-specs.md
  - 添加 load 命令规范
  - 添加 list 命令规范
- [ ] 修订 05-final-design.md
  - 更新 SDK 章节为 CLI 章节
- [ ] 修订 06-adversarial-review-round2.md
  - 更新工作量估算（-8 小时）

---

## 最终结论

**方案变更**：JavaScript SDK → Bash CLI + JSON 输出

**优势**：
- ✅ 更简单：减少 8 小时工作量
- ✅ 更通用：任何技能都能用
- ✅ 更直接：符合技能调用模式
- ✅ 更灵活：支持管道、脚本组合

**劣势**：
- ⚠️ 需要解析 JSON（但 `jq` 已足够）
- ⚠️ 无类型检查（但命令行本就如此）

**推荐采用**：CLI 方案 ✅
