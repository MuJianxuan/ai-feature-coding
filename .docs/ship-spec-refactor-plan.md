# ship-spec 混合式改造方案

## 核心变更

### 配置格式
```yaml
# 旧格式
workspace_mode: single_project | project_group
workspace_name: xxx
projects: [...]

# 新格式
mode: single | multi
project:
  name: xxx  # 单项目，可选
projects:    # 多项目
  - web
  - api
```

### 目录结构不变
```
# 单项目
.docs/spec/{frontend,backend,shared}/

# 多项目
.docs/spec/{_shared,web,api}/
```

## 修改文件清单

### 1. skills/ship-spec/SKILL.md
**变更**：
- L43-68: 工作空间模式章节
- L59-77: 配置文件示例和初始化命令
- L80-105: 目录结构示例

**改为**：
```markdown
## 工作模式

### 单项目（single）
- **定义**：一个仓库一个项目
- **路径**：.docs/spec/{frontend,backend,shared}/
- **配置**：mode: single

### 多项目（multi）
- **定义**：monorepo，多个项目
- **路径**：.docs/spec/{_shared,web,api}/
- **配置**：mode: multi, projects: [...]

### 配置文件
```yaml
# 单项目
mode: single
project:
  name: my-app  # 可选，默认目录名

# 多项目
mode: multi
projects:
  - web
  - api
```

**初始化**：
```bash
# 单项目
ship-spec init

# 多项目
ship-spec init --mode multi --projects web,api,mobile
```
```

### 2. tools/ship-spec/README.md
**变更**：
- L40-49: 命令选项
- L82-125: 配置文件和目录结构

**改为**：
```markdown
## 快速开始

```bash
# 单项目
ship-spec init

# 多项目
ship-spec init --mode multi --projects web,api,mobile
```

## 配置

`.docs/ship/project.yml`:
```yaml
mode: single  # single | multi

# 单项目
project:
  name: my-app  # 可选

# 多项目
projects:
  - web
  - api
```
```

### 3. tools/ship-spec/src/commands/init.js
**核心改动**：

```javascript
// 旧
const workspace = program.workspace || 'single';
const workspaceMode = workspace === 'multi' ? 'project_group' : 'single_project';

// 新
const mode = program.mode || 'single';

// 配置生成
if (mode === 'single') {
  config = {
    mode: 'single',
    project: {
      name: program.name || path.basename(process.cwd())
    }
  };
} else {
  config = {
    mode: 'multi',
    projects: program.projects.split(',').map(p => p.trim())
  };
}

// 目录创建逻辑不变
if (mode === 'single') {
  fs.mkdirSync('.docs/spec/frontend', { recursive: true });
  fs.mkdirSync('.docs/spec/backend', { recursive: true });
  fs.mkdirSync('.docs/spec/shared', { recursive: true });
} else {
  fs.mkdirSync('.docs/spec/_shared', { recursive: true });
  projects.forEach(p => {
    fs.mkdirSync(`.docs/spec/${p}`, { recursive: true });
  });
}
```

**选项更新**：
```javascript
program
  .option('--mode <type>', 'mode: single or multi', 'single')
  .option('--name <name>', 'project name (single mode)')
  .option('--projects <list>', 'project list (multi mode, comma-separated)')
  .option('--template <name>', 'template name', 'standard');
```

### 4. tools/ship-spec/src/core/parser.js
**配置读取兼容**：

```javascript
function loadConfig() {
  const configPath = '.docs/ship/project.yml';
  if (!fs.existsSync(configPath)) {
    return { mode: 'single', project: { name: path.basename(process.cwd()) } };
  }
  
  const config = yaml.load(fs.readFileSync(configPath, 'utf8'));
  
  // 兼容旧格式
  if (config.workspace_mode) {
    return {
      mode: config.workspace_mode === 'single_project' ? 'single' : 'multi',
      project: { name: config.workspace_name },
      projects: config.projects || []
    };
  }
  
  return config;
}

function getSpecBasePath(config, projectName) {
  if (config.mode === 'single') {
    return '.docs/spec';
  } else {
    return projectName ? `.docs/spec/${projectName}` : '.docs/spec';
  }
}
```

### 5. tools/ship-spec/src/commands/list.js
**过滤逻辑调整**：

```javascript
const config = loadConfig();

// 扫描路径
let scanPaths = [];
if (config.mode === 'single') {
  scanPaths = ['.docs/spec'];
} else {
  scanPaths = ['.docs/spec/_shared'];
  if (program.project) {
    scanPaths.push(`.docs/spec/${program.project}`);
  } else {
    config.projects.forEach(p => scanPaths.push(`.docs/spec/${p}`));
  }
}
```

### 6. tools/ship-spec/src/commands/create.js
**路径生成调整**：

```javascript
const config = loadConfig();

let basePath;
if (config.mode === 'single') {
  basePath = '.docs/spec';
} else {
  if (program.type === '_shared') {
    basePath = '.docs/spec/_shared';
  } else if (program.project) {
    basePath = `.docs/spec/${program.project}`;
  } else {
    throw new Error('Multi mode requires --project or --type _shared');
  }
}

const specPath = path.join(basePath, program.type, `${specId}.md`);
```

### 7. 迁移工具
**新增**：`tools/ship-spec/src/commands/migrate.js`

```javascript
#!/usr/bin/env node
const fs = require('fs');
const yaml = require('js-yaml');

const configPath = '.docs/ship/project.yml';
if (!fs.existsSync(configPath)) {
  console.log('No config found, skip migration');
  process.exit(0);
}

const oldConfig = yaml.load(fs.readFileSync(configPath, 'utf8'));

// 已经是新格式
if (oldConfig.mode) {
  console.log('Already new format');
  process.exit(0);
}

// 转换
const newConfig = {
  mode: oldConfig.workspace_mode === 'single_project' ? 'single' : 'multi'
};

if (newConfig.mode === 'single') {
  newConfig.project = { name: oldConfig.workspace_name };
} else {
  newConfig.projects = oldConfig.projects || [];
}

// 备份
fs.copyFileSync(configPath, `${configPath}.bak`);

// 写入
fs.writeFileSync(configPath, yaml.dump(newConfig), 'utf8');

console.log('✅ Migrated to new format');
console.log('📦 Backup saved to .docs/ship/project.yml.bak');
```

**添加到 package.json**：
```json
{
  "bin": {
    "ship-spec": "./bin/ship-spec.js",
    "ship-spec-migrate": "./src/commands/migrate.js"
  }
}
```

## 执行步骤

1. **修改 SKILL.md**（文档）
2. **修改 README.md**（文档）
3. **修改 init.js**（核心）
4. **修改 parser.js**（配置读取）
5. **修改 list.js, create.js, load.js**（路径逻辑）
6. **添加 migrate.js**（迁移工具）
7. **测试验证**
8. **发布新版本**

## 兼容性

- **配置读取**：parser.js 自动识别旧格式
- **迁移命令**：`ship-spec-migrate` 一键升级
- **路径逻辑**：根据 mode 自动适配

## 测试用例

```bash
# 单项目初始化
ship-spec init
# 验证：.docs/spec/{frontend,backend,shared}/ 存在
# 验证：project.yml mode=single

# 多项目初始化
ship-spec init --mode multi --projects web,api
# 验证：.docs/spec/{_shared,web,api}/ 存在
# 验证：project.yml mode=multi

# 旧配置迁移
ship-spec-migrate
# 验证：workspace_mode 转为 mode

# 创建规范
ship-spec create test -t frontend -d "test"
# 单项目：.docs/spec/frontend/test.md
# 多项目（需 --project）：.docs/spec/web/frontend/test.md
```

## 破坏性变更

- ⚠️ 配置格式变化（自动兼容）
- ⚠️ CLI 选项名变化（--workspace → --mode）
- ✅ 目录结构不变
- ✅ 规范文件格式不变
