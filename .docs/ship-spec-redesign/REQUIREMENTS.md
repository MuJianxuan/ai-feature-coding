# ship-spec CLI 工具实现需求

## 目标
实现一个 Node.js CLI 工具，用于管理 ShipKit 项目的规范文件。

## 核心需求

### 1. 工作空间模式支持
- [ ] 支持单项目模式（single_project）
- [ ] 支持多项目模式（project_group）
- [ ] 读取 `.docs/ship/project.yml` 配置
- [ ] 自动检测工作空间模式（当 project.yml 不存在时）

### 2. init 命令
- [ ] 创建目录结构（单项目：frontend/backend/shared，多项目：_shared/project1/project2）
- [ ] 生成 `.docs/ship/project.yml`
- [ ] 生成 `.docs/spec/INDEX.md` 空索引
- [ ] 创建 `existing-features.md` 模板
- [ ] 支持 `--workspace single|multi` 参数
- [ ] 支持 `--projects <list>` 参数（多项目模式）

### 3. create 命令
- [ ] 创建新规范文件（带 frontmatter）
- [ ] 根据工作空间模式确定文件路径
- [ ] 单项目：按 type 放置（frontend/backend/shared）
- [ ] 多项目：单项目规范放项目目录，多项目规范放 _shared
- [ ] 检查文件是否已存在（避免覆盖）
- [ ] 更新 INDEX.md
- [ ] 支持 `-p, --project` 参数
- [ ] 支持 `-t, --type` 参数
- [ ] 支持 `-s, --stages` 参数
- [ ] 支持 `-d, --description` 参数

### 4. list 命令
- [ ] 列出所有规范
- [ ] 支持 `--project` 过滤（多项目模式）
- [ ] 支持 `--stage` 过滤
- [ ] 支持 `--format table|json` 输出
- [ ] JSON 输出包含 total、filters、results

### 5. load 命令
- [ ] 加载指定规范的完整内容
- [ ] 支持 `--format json|yaml` 输出
- [ ] 支持 `--content-only` 只输出正文
- [ ] 支持 `--frontmatter-only` 只输出 frontmatter
- [ ] JSON 输出包含 spec 元数据、frontmatter、content、body

### 6. sync-index 命令
- [ ] 扫描所有 .md 文件
- [ ] 从 frontmatter 提取元数据
- [ ] 重建 INDEX.md
- [ ] 支持 `--rebuild` 参数

### 7. validate 命令
- [ ] 验证 INDEX.md 存在
- [ ] 验证规范文件存在
- [ ] 验证 frontmatter 完整性
- [ ] 验证 spec_id 一致性
- [ ] 统计错误和警告数量
- [ ] 支持验证单个规范或全部规范

### 8. 核心解析器（parser.js）
- [ ] detectWorkspaceMode()：检测工作空间模式
- [ ] parseIndexTable()：解析 INDEX.md 表格
- [ ] generateIndexTable()：生成 INDEX.md 表格
- [ ] parseFrontmatter()：解析 YAML frontmatter
- [ ] extractBody()：提取正文内容
- [ ] 处理转义竖线（\|）
- [ ] 处理空值（-）
- [ ] 处理数组字段（stages, projects, tags）

## 测试场景

### 场景 1：单项目初始化和使用
```bash
ship-spec init --template standard
ship-spec create api-standard -t backend -d "API 规范"
ship-spec list --format json
ship-spec load api-standard --content-only
ship-spec validate --all
```

### 场景 2：多项目初始化和使用
```bash
ship-spec init --workspace multi --projects web,api
ship-spec create web-patterns -p web -d "Web 模式"
ship-spec create api-standard -p api -d "API 规范"
ship-spec create naming -p all -d "命名规范"
ship-spec list --project web --format json
ship-spec validate --all
```

### 场景 3：索引同步
```bash
# 手动修改规范文件的 frontmatter
ship-spec sync-index --rebuild
ship-spec validate --all
```

## 非功能需求
- [ ] 错误处理：文件不存在、解析失败等
- [ ] 用户友好的错误信息
- [ ] 命令执行成功提示
- [ ] 跨平台兼容（Windows/Linux/macOS）
- [ ] npm 可安装（npm install -g ship-spec）

## 不在范围内
- update 命令（V1.1）
- delete 命令（V1.1）
- search 命令（V1.1）
- stats 命令（V1.1）
- doctor 命令（V1.1）
- Web UI（V2.0）
- 全文搜索（V2.0）
