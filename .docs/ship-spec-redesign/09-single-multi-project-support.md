# 单项目/多项目支持设计补充

## 问题

当前设计中：
- ✅ 目录结构定义了单项目和多项目的区别
- ✅ 有 `.docs/ship/project.yml` 配置文件
- ❌ **CLI 命令没有读取 project.yml 的逻辑**
- ❌ **技能调用时如何知道当前是单项目还是多项目？**

---

## 解决方案

### 1. project.yml 格式

```yaml
# .docs/ship/project.yml
workspace_mode: single_project  # single_project | project_group
workspace_name: my-workspace
projects:
  - web    # 多项目模式下的项目列表
  - api
```

**规则**：
- `single_project`：单项目模式，`projects` 可为空或只有一个项目
- `project_group`：多项目模式，`projects` 必须列出所有项目

---

### 2. 自动检测模式

如果没有 `project.yml`，CLI 自动检测：

```javascript
function detectWorkspaceMode() {
  const projectYmlPath = '.docs/ship/project.yml';
  
  // 1. 如果存在 project.yml，读取配置
  if (fileExists(projectYmlPath)) {
    const config = yaml.parse(readFile(projectYmlPath));
    return {
      mode: config.workspace_mode,
      projects: config.projects || []
    };
  }
  
  // 2. 自动检测：检查 .docs/spec/ 目录结构
  const specDir = '.docs/spec';
  const entries = fs.readdirSync(specDir, { withFileTypes: true });
  const dirs = entries.filter(e => e.isDirectory()).map(e => e.name);
  
  // 如果存在 _shared 目录，判断为多项目
  if (dirs.includes('_shared')) {
    const projects = dirs.filter(d => d !== '_shared' && !d.startsWith('.'));
    return {
      mode: 'project_group',
      projects
    };
  }
  
  // 否则判断为单项目
  return {
    mode: 'single_project',
    projects: []
  };
}
```

---

### 3. CLI 命令调整

#### init 命令
```bash
ship-spec init [options]

Options:
  --template <name>         模板：minimal | standard | comprehensive
  --workspace <mode>        工作空间模式：single | multi（默认自动检测）
  --projects <projects>     项目列表（逗号分隔，仅多项目模式）

示例：
# 单项目
ship-spec init --template standard

# 多项目
ship-spec init --template standard --workspace multi --projects web,api,mobile
```

**逻辑**：
```javascript
function initCommand(options) {
  const mode = options.workspace || 'single';
  const projects = options.projects ? options.projects.split(',') : [];
  
  // 1. 创建目录结构
  if (mode === 'single') {
    fs.mkdirSync('.docs/spec/frontend', { recursive: true });
    fs.mkdirSync('.docs/spec/backend', { recursive: true });
    fs.mkdirSync('.docs/spec/shared', { recursive: true });
  } else {
    fs.mkdirSync('.docs/spec/_shared', { recursive: true });
    projects.forEach(proj => {
      fs.mkdirSync(`.docs/spec/${proj}`, { recursive: true });
    });
  }
  
  // 2. 创建 project.yml
  const config = {
    workspace_mode: mode === 'single' ? 'single_project' : 'project_group',
    workspace_name: path.basename(process.cwd()),
    projects: mode === 'multi' ? projects : []
  };
  
  fs.writeFileSync('.docs/ship/project.yml', yaml.stringify(config));
  
  // 3. 创建 INDEX.md
  createIndexMd(mode, projects);
}
```

#### create 命令
```bash
ship-spec create <spec-id> [options]

Options:
  -p, --project <projects>  适用项目（逗号分隔）
  -t, --type <type>         规范类型：frontend | backend | shared
  
示例：
# 单项目
ship-spec create api-standard -t backend

# 多项目
ship-spec create api-standard -t backend -p api
ship-spec create naming -t shared -p web,api  # 共享规范
```

**逻辑**：
```javascript
function createCommand(specId, options) {
  const workspace = detectWorkspaceMode();
  
  // 确定文件路径
  let filePath;
  
  if (workspace.mode === 'single_project') {
    // 单项目：直接放在 type 目录下
    filePath = `.docs/spec/${options.type}/${specId}.md`;
  } else {
    // 多项目：根据 projects 判断位置
    const projects = options.project ? options.project.split(',') : ['all'];
    
    if (projects.includes('all') || projects.length > 1) {
      // 通用规范，放在 _shared
      filePath = `.docs/spec/_shared/${specId}.md`;
    } else {
      // 项目专属规范，放在项目目录下
      const project = projects[0];
      filePath = `.docs/spec/${project}/${specId}.md`;
    }
  }
  
  // 创建规范文件
  const content = generateSpecContent(specId, options);
  fs.writeFileSync(filePath, content);
  
  // 更新 INDEX.md
  updateIndexMd({
    spec_id: specId,
    file: path.relative('.docs/spec', filePath),
    projects: options.project ? options.project.split(',') : ['all'],
    // ...
  });
}
```

#### list/search 命令
```bash
ship-spec list [options]
ship-spec search <query> [options]

Options:
  -p, --project <project>   过滤项目

示例：
# 单项目：project 参数被忽略
ship-spec list

# 多项目：只列出特定项目的规范
ship-spec list --project web
ship-spec search "api" --project api
```

**逻辑**：
```javascript
function listCommand(options) {
  const workspace = detectWorkspaceMode();
  let index = parseIndexTable(readFile('.docs/spec/INDEX.md'));
  
  // 多项目模式下，应用项目过滤
  if (workspace.mode === 'project_group' && options.project) {
    index = index.filter(spec => 
      spec.projects.includes(options.project) || 
      spec.projects.includes('all')
    );
  }
  
  // 单项目模式下，忽略 project 过滤
  // (所有规范都是可见的)
  
  return formatOutput(index, options.format);
}
```

---

### 4. 技能集成调整

#### 场景：ship-design 读取规范

```bash
# 读取 feature meta.yml 获取项目信息
project=$(yq '.projects[0]' feature-xxx/meta.yml)

# 自动检测工作空间模式
workspace_mode=$(yq '.workspace_mode' .docs/ship/project.yml 2>/dev/null || echo "single_project")

# 列出规范（多项目模式下传递 project 参数）
if [ "$workspace_mode" = "project_group" ]; then
  specs=$(ship-spec list --project "$project" --stage design --format json)
else
  # 单项目模式，不需要 project 参数
  specs=$(ship-spec list --stage design --format json)
fi
```

**简化版**（推荐）：
```bash
# 技能不需要关心单项目/多项目，统一传递 project 参数
# CLI 内部自动处理
project=$(yq '.projects[0]' feature-xxx/meta.yml)
specs=$(ship-spec list --project "$project" --stage design --format json)
```

#### 场景：ship-build 更新 existing-features

```bash
# 自动检测工作空间模式
workspace_mode=$(yq '.workspace_mode' .docs/ship/project.yml 2>/dev/null || echo "single_project")

# 确定 existing-features 文件路径
if [ "$workspace_mode" = "project_group" ]; then
  # 多项目：检查是否跨项目
  project_count=$(yq '.projects | length' feature-xxx/meta.yml)
  if [ "$project_count" -gt 1 ]; then
    # 跨项目功能，写入 _shared
    features_file=".docs/spec/_shared/existing-features.md"
  else
    # 单项目功能，写入项目目录
    project=$(yq '.projects[0]' feature-xxx/meta.yml)
    features_file=".docs/spec/${project}/existing-features.md"
  fi
else
  # 单项目：统一写入 shared
  features_file=".docs/spec/shared/existing-features.md"
fi

# 追加条目
cat >> "$features_file" <<EOF
## 用户模块
- **用户登录**：完成时间 $(date +%Y-%m-%d)
EOF
```

---

### 5. 目录结构规则

#### 单项目
```
.docs/spec/
├── frontend/          # 前端规范（可选）
├── backend/           # 后端规范（可选）
└── shared/            # 通用规范（必需）
    └── existing-features.md
```

**规则**：
- 不区分项目，所有规范都在同一层级
- `shared/` 用于放置通用规范（如 existing-features、tech-stack）
- `frontend/`、`backend/` 用于分类，不表示项目边界

#### 多项目
```
.docs/spec/
├── _shared/           # 跨项目通用规范（必需）
│   ├── tech-stack.md
│   └── error-codes.md
├── web/               # web 项目的规范
│   ├── frontend/
│   └── existing-features.md
└── api/               # api 项目的规范
    ├── backend/
    └── existing-features.md
```

**规则**：
- `_shared/` 存放所有项目共用的规范
- 每个项目有独立的目录，存放项目专属规范
- 每个项目可以有自己的 `existing-features.md`

---

### 6. INDEX.md 中的 projects 字段

#### 单项目
```markdown
| spec_id | file | projects | ... |
|---|---|---|---|
| api-standard | backend/api-standard.md | all | ... |
| frontend-patterns | frontend/patterns.md | all | ... |
```

**规则**：
- 所有规范的 `projects` 都是 `all`
- 因为只有一个项目，不需要区分

#### 多项目
```markdown
| spec_id | file | projects | ... |
|---|---|---|---|
| api-standard | api/backend/api-standard.md | api | ... |
| naming | _shared/naming.md | all | ... |
| web-patterns | web/frontend/patterns.md | web | ... |
```

**规则**：
- `projects` 可以是具体项目（`web`、`api`）或 `all`
- `all` 表示所有项目都可见
- 多个项目用逗号分隔（`web,api`）

---

## 使用示例

### 初始化

#### 单项目
```bash
cd my-monorepo
ship-spec init --template standard

# 生成结构
.docs/
├── ship/
│   └── project.yml  # workspace_mode: single_project
└── spec/
    ├── INDEX.md
    ├── frontend/
    ├── backend/
    └── shared/
```

#### 多项目
```bash
cd my-monorepo
ship-spec init --template standard --workspace multi --projects web,api,mobile

# 生成结构
.docs/
├── ship/
│   └── project.yml  # workspace_mode: project_group, projects: [web, api, mobile]
└── spec/
    ├── INDEX.md
    ├── _shared/
    ├── web/
    ├── api/
    └── mobile/
```

### 创建规范

#### 单项目
```bash
# 所有规范默认 projects=all
ship-spec create api-standard -t backend --description "API 规范"
# 生成：.docs/spec/backend/api-standard.md
# INDEX.md: projects=all
```

#### 多项目
```bash
# 项目专属规范
ship-spec create api-standard -t backend -p api --description "API 规范"
# 生成：.docs/spec/api/api-standard.md
# INDEX.md: projects=api

# 跨项目通用规范
ship-spec create naming -t shared -p all --description "命名规范"
# 生成：.docs/spec/_shared/naming.md
# INDEX.md: projects=all

# 多项目共享规范
ship-spec create frontend-guide -t frontend -p web,mobile --description "前端指南"
# 生成：.docs/spec/_shared/frontend-guide.md（因为多项目）
# INDEX.md: projects=web,mobile
```

### 查询规范

#### 单项目
```bash
# 列出所有规范（project 参数被忽略）
ship-spec list
ship-spec list --project web  # 效果相同，project 参数无效
```

#### 多项目
```bash
# 列出特定项目的规范
ship-spec list --project web
# 返回：projects 包含 'web' 或 'all' 的规范

ship-spec list --project api
# 返回：projects 包含 'api' 或 'all' 的规范

# 列出所有规范
ship-spec list
# 返回：所有规范（不过滤）
```

---

## 迁移场景

### 从单项目升级到多项目

```bash
# 1. 检测当前模式
workspace_mode=$(yq '.workspace_mode' .docs/ship/project.yml)
echo "当前模式：$workspace_mode"

# 2. 执行迁移（未来可以提供 migrate 命令）
# 手动步骤：
mkdir .docs/spec/_shared
mv .docs/spec/shared/* .docs/spec/_shared/
mkdir .docs/spec/web .docs/spec/api

# 3. 更新 project.yml
cat > .docs/ship/project.yml <<EOF
workspace_mode: project_group
workspace_name: my-workspace
projects:
  - web
  - api
EOF

# 4. 重建索引
ship-spec sync-index --rebuild
```

---

## 实现优先级

### MVP（必需）
- ✅ `detectWorkspaceMode()` 函数
- ✅ `init` 命令支持 `--workspace` 和 `--projects`
- ✅ `create` 命令根据模式确定文件路径
- ✅ `list`/`search` 命令在多项目模式下过滤

### V1.1（增强）
- ✅ `migrate` 命令（单项目 ↔ 多项目）
- ✅ 自动检测模式（无需 project.yml）

---

## 总结

**关键改进**：
1. ✅ CLI 命令读取 `project.yml` 自动适配单项目/多项目
2. ✅ `init` 命令生成对应的目录结构和配置
3. ✅ `create` 命令根据模式和 `--project` 参数确定文件路径
4. ✅ `list`/`search` 命令在多项目模式下自动过滤
5. ✅ 技能集成代码统一，不需要关心单项目/多项目差异

**使用体验**：
- 单项目：简单，所有规范 `projects=all`
- 多项目：隔离，通过 `--project` 参数过滤
- 技能：统一调用方式，CLI 内部处理差异
