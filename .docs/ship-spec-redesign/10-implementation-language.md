# 实现语言说明

## 问题澄清

文档中出现了看似矛盾的地方：
- 实现代码用 **JavaScript**
- 废弃了 **JavaScript SDK**
- 技能调用用 **Bash**

这是为什么？

---

## 架构说明

### ship-spec 是什么？

**ship-spec 是一个 Node.js CLI 工具**

```
┌─────────────────────────────────────────────┐
│  ship-spec CLI 工具                          │
│                                             │
│  - 实现语言：Node.js                         │
│  - 安装方式：npm install -g ship-spec       │
│  - 暴露接口：命令行命令                      │
│  - 输出格式：JSON / Table / Markdown        │
└─────────────────────────────────────────────┘
```

### 技能如何调用？

**技能通过 Bash 调用命令行**

```bash
# 在 ship-design 技能中（Markdown 文档）
specs=$(ship-spec list --project web --stage design --format json)
spec_ids=$(echo "$specs" | jq -r '.results[].spec_id')
content=$(ship-spec load api-standard --content-only)
```

### 为什么废弃 SDK？

**废弃的是编程接口，不是 JavaScript 实现**

❌ **废弃（不提供）**：
```javascript
// 技能作为 .js 文件，导入 SDK
import { SpecLoader } from 'ship-spec';
const loader = new SpecLoader({ project: 'web' });
const specs = await loader.search('api');
```

✅ **采用（推荐）**：
```bash
# 技能作为 Markdown，执行 bash 命令
specs=$(ship-spec search "api" --project web --format json)
```

**原因**：
- 技能是 Markdown 文档，AI 读取后执行 bash 命令
- 不需要创建 .js 文件、导入模块、执行 Node.js 脚本
- Bash 调用更直接、更通用

---

## 实现方式

### 项目结构

```
ship-spec/
├── package.json
├── bin/
│   └── ship-spec.js          # CLI 入口（Node.js）
├── src/
│   ├── commands/
│   │   ├── init.js
│   │   ├── create.js
│   │   ├── list.js
│   │   └── ...
│   ├── core/
│   │   ├── parser.js         # INDEX.md 解析器
│   │   ├── index.js          # 索引重建
│   │   └── ...
│   └── utils/
│       └── ...
└── test/
    └── ...
```

### CLI 入口

```javascript
#!/usr/bin/env node
// bin/ship-spec.js

const { Command } = require('commander');
const program = new Command();

program
  .name('ship-spec')
  .description('Ship 规范管理工具')
  .version('1.0.0');

program
  .command('list')
  .option('-p, --project <project>', '过滤项目')
  .option('-s, --stage <stage>', '过滤阶段')
  .option('-f, --format <format>', '输出格式：table | json', 'table')
  .action(async (options) => {
    const { listCommand } = require('../src/commands/list');
    await listCommand(options);
  });

program
  .command('load <spec-id>')
  .option('-f, --format <format>', '输出格式：json | yaml', 'json')
  .option('--content-only', '只输出正文')
  .action(async (specId, options) => {
    const { loadCommand } = require('../src/commands/load');
    await loadCommand(specId, options);
  });

// ... 其他命令

program.parse(process.argv);
```

### 安装和使用

```bash
# 开发时
cd ship-spec
npm install
npm link  # 创建全局命令

# 使用
ship-spec list --project web --format json
ship-spec load api-standard --content-only

# 发布后
npm install -g @your-org/ship-spec
ship-spec init --template standard
```

---

## 技能集成

### ship-design 技能示例

```markdown
# ship-design 技能

## 执行流程

### 1. 读取 feature meta.yml
```bash
project=$(yq '.projects[0]' feature-xxx/meta.yml)
```

### 2. 列出 design 阶段的规范
```bash
# 调用 ship-spec CLI（Node.js 实现，但通过 bash 调用）
specs=$(ship-spec list --project "$project" --stage design --format json)

# 解析 JSON
spec_ids=$(echo "$specs" | jq -r '.results[].spec_id')
```

### 3. 加载规范内容
```bash
for spec_id in $spec_ids; do
  content=$(ship-spec load "$spec_id" --content-only)
  echo "$content" > "/tmp/spec-${spec_id}.md"
done
```

### 4. 使用规范内容
```bash
api_standard=$(cat /tmp/spec-api-standard.md)

prompt="根据以下规范设计：

API 规范：
$api_standard

需求：
$(cat requirements.md)
"

echo "$prompt" | ai-design > design.md
```
```

---

## 为什么用 Node.js 而不是纯 Bash？

### 复杂度对比

#### INDEX.md 解析

**Node.js**：
```javascript
// 50 行，清晰易读
function parseIndexTable(markdown) {
  const lines = markdown.split('\n');
  const headerLine = lines.find(l => l.includes('spec_id'));
  const headers = parseTableRow(headerLine);
  // ...
  return specs;
}
```

**Bash**：
```bash
# 100+ 行，容易出错
parse_index_table() {
  local markdown="$1"
  local header_line=$(echo "$markdown" | grep "spec_id")
  # 手动处理转义竖线、空值、多行...
  # 需要 awk/sed 复杂正则
}
```

#### YAML 解析

**Node.js**：
```javascript
const yaml = require('yaml');
const config = yaml.parse(content);
```

**Bash**：
```bash
# 需要安装 yq
config=$(yq '.workspace_mode' project.yml)
```

#### 错误处理

**Node.js**：
```javascript
try {
  const result = operation();
  console.log(JSON.stringify(result));
} catch (error) {
  console.error(`Error: ${error.message}`);
  process.exit(1);
}
```

**Bash**：
```bash
result=$(operation 2>&1)
if [ $? -ne 0 ]; then
  echo "Error: $result" >&2
  exit 1
fi
```

---

## 跨平台兼容性

### Node.js CLI
- ✅ Windows / Linux / macOS 统一
- ✅ 文件路径处理统一（`path.join()`）
- ✅ 换行符处理统一

### Bash 脚本
- ⚠️ Windows 需要 WSL / Git Bash
- ⚠️ 不同 shell 语法差异（bash / zsh / fish）
- ⚠️ 路径分隔符（`/` vs `\`）

---

## 依赖管理

### Node.js
```json
{
  "dependencies": {
    "commander": "^11.0.0",
    "yaml": "^2.3.0",
    "chalk": "^5.3.0"
  }
}
```

- ✅ 版本锁定（package-lock.json）
- ✅ 自动安装（npm install）
- ✅ 语义化版本

### Bash
```bash
# 需要用户手动安装
brew install yq jq
apt-get install yq jq
```

- ⚠️ 不同系统安装方式不同
- ⚠️ 版本不一致
- ⚠️ 可能不存在

---

## 性能对比

### 启动时间
- **Node.js CLI**：~50ms（首次）
- **Bash 脚本**：~10ms

### 执行时间（100 规范）
- **Node.js**：解析 INDEX.md ~20ms
- **Bash**：解析 INDEX.md ~100ms（awk/sed）

### 结论
启动慢一点，但执行更快，可接受。

---

## 总结

### 最终方案

| 层面 | 技术选择 | 原因 |
|---|---|---|
| **实现语言** | Node.js | 复杂解析、跨平台、错误处理 |
| **暴露接口** | CLI 命令 | 技能调用简单 |
| **输出格式** | JSON / Table | 易于解析 |
| **技能调用** | Bash | 符合技能执行模式 |
| **不提供** | JavaScript SDK | 避免技能创建 .js 文件 |

### 用户视角

**普通用户**（命令行）：
```bash
ship-spec init --template standard
ship-spec create api-standard -t backend
ship-spec list --project web
```

**技能开发者**（Bash）：
```bash
specs=$(ship-spec list --project web --format json)
content=$(ship-spec load api-standard --content-only)
```

**ship-spec 开发者**（Node.js）：
```javascript
// 开发 ship-spec 本身
async function listCommand(options) {
  const workspace = detectWorkspaceMode();
  const index = parseIndexTable(readFile('.docs/spec/INDEX.md'));
  // ...
}
```

---

## 文档更新说明

所有设计文档中的实现代码（JavaScript）都是**正确的**：
- ✅ ship-spec 用 Node.js 实现
- ✅ 暴露为 CLI 命令
- ✅ 技能通过 Bash 调用命令
- ✅ 废弃的是 JavaScript **编程接口**（SDK），不是 JavaScript **实现**

这不是矛盾，而是**清晰的分层**：
- **实现层**：Node.js（处理复杂逻辑）
- **接口层**：CLI 命令（通用、简单）
- **调用层**：Bash 脚本（技能执行模式）
