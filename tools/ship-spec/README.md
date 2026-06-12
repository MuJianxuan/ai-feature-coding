# @shipkit/spec-cli

ShipKit 规范管理 CLI 工具。管理 `.docs/spec/` 知识库。

## 安装

```bash
npm install -g @shipkit/spec-cli
```

## 验证安装

```bash
ship-spec -h
ship-spec --version
```

## 快速开始

```bash
# 单项目初始化
ship-spec init

# 多项目初始化
ship-spec init --mode multi --projects web,api,mobile

# 创建规范
ship-spec create rest-api-standard -t backend -d "REST API 设计规范"

# 列出规范（动态扫描）
ship-spec list --format json

# 加载规范
ship-spec load rest-api-standard --content-only

# 验证规范
ship-spec validate --all
```

## 命令说明

### init
初始化 `.docs/spec/` 目录结构

**选项**：
- `--mode <mode>`: 工作模式（single/multi，默认 single）
- `--name <name>`: 项目名称（单项目模式，可选）
- `--projects <list>`: 项目列表（多项目模式，逗号分隔）

### create
创建新规范

**选项**：
- `-t, --type <type>`: 规范类型（frontend/backend/shared/_shared）
- `-d, --description <desc>`: 规范描述
- `-p, --project <name>`: 项目名称（多项目模式）
- `--stages <list>`: 适用阶段（默认 design,build）
- `--tags <list>`: 标签（逗号分隔）

### list
列出规范（动态扫描 frontmatter）

**选项**：
- `--project <name>`: 按项目过滤
- `--stage <name>`: 按阶段过滤（design/build/test）
- `--tag <name>`: 按标签过滤
- `--format <format>`: 输出格式（table/json/yaml，默认 table）

### load
加载规范内容

**选项**：
- `--content-only`: 只输出规范内容（不含元数据）
- `--format <format>`: 输出格式（json/yaml，默认 json）

### validate
验证规范格式

**选项**：
- `--all`: 验证所有规范
- `--strict`: 严格模式（检查内容完整性）

## 索引机制

索引信息存储在每个规范文件的 frontmatter 中，通过 `ship-spec list` 动态生成。

**优势**：
- ✅ 零合并冲突（无中心索引文件）
- ✅ 单一数据源（frontmatter）
- ✅ 自动同步（无需手动维护）

## 目录结构

### 单项目
```
.docs/spec/
├── frontend/
├── backend/
└── shared/
    ├── tech-stack.md
    └── existing-features.md
```

### 多项目
```
.docs/spec/
├── _shared/
├── web/
│   ├── frontend/
│   └── existing-features.md
└── api/
    ├── backend/
    └── existing-features.md
```

## 配置迁移

旧版本配置格式（`workspace_mode`）自动兼容，也可手动迁移：
```bash
ship-spec migrate
```
projects:
  - web
  - api
```

## 规范格式

```markdown
---
spec_id: rest-api-standard
description: REST API 设计规范
stages: [design, build]
projects: [all]
tags: [api, rest, backend]
status: active
---

# REST API 设计规范

## 适用场景
...

## 核心约束
### 必须做
...

### 禁止做
...

## 示例
...

## 检查点
- [ ] ...
```

## 许可证

MIT
