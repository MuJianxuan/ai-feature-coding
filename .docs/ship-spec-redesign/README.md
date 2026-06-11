# ship-spec 技能改造方案总结

## 📋 项目概览

**目标**：将 ship-spec 从模糊的规范管理技能，改造为职责清晰、易于集成的规范管理器。

**成果**：完整的可交付方案，包含架构设计、命令规范、实现细节、测试策略、迁移指南。

**文档列表**：
1. `01-architecture.md` - 架构设计
2. `02-command-specs.md` - 命令详细规范
3. `03-search-implementation.md` - 搜索功能设计
4. `04-adversarial-review-round1.md` - 第一轮对抗式审查
5. `05-final-design.md` - 最终设计方案
6. `06-adversarial-review-round2.md` - 第二轮对抗式审查
7. `07-final-deliverable.md` - 可交付版本
8. `08-cli-integration-approach.md` - CLI 集成方案（最新）

---

## 🎯 核心设计决策

### 1. 职责边界清晰 ✅
- **ship-spec**：只管理规范（CRUD + 搜索 + 验证）
- **ship-build**：完成后直接写入 existing-features.md
- **ship-spec**：自动索引 existing-features（sync-index）
- **其他技能**：通过 CLI 命令读取规范

### 2. 索引策略简化 ✅
- **INDEX.md** 为唯一真实来源（人类可读、易于 git diff）
- **.index.json** 自动生成（机器可读、快速搜索）
- 所有写操作 → 更新 INDEX.md → 重建 .index.json
- 避免双向同步的复杂性

### 3. 集成方式优化 ✅
- **废弃**：JavaScript SDK（不符合技能调用模式）
- **采用**：Bash CLI + JSON 输出（通用、简单、直接）
- **新增命令**：`load`（加载规范）、`list`（列出规范）
- **可选**：Bash 辅助库（封装常用操作）

### 4. MVP 范围收窄 ✅
- **保留**：init / create / update / delete / search / validate / sync-index / stats
- **去掉**：suggest-new-spec（推迟到 V2）、doctor（推迟到 V1.1）
- **工作量**：从 164 小时 → 102 小时（节省 62 小时）

---

## 🚀 MVP 功能清单

### 核心命令（8个）
| 命令 | 功能 | 优先级 |
|---|---|---|
| `init` | 初始化规范目录 | P0 |
| `create` | 创建新规范 | P0 |
| `update` | 更新规范 | P0 |
| `delete` | 删除/归档规范 | P0 |
| `search` | 搜索规范（元数据） | P0 |
| `list` | 列出规范（过滤） | P0 |
| `load` | 加载规范内容 | P0 |
| `validate` | 验证规范 | P0 |
| `sync-index` | 同步索引 | P0 |
| `stats` | 规范使用统计 | P1 |

### 关键实现
- ✅ **健壮的 INDEX.md 解析器**：处理转义竖线、空值、列顺序变化
- ✅ **原子性索引重建**：临时文件机制，避免数据损坏
- ✅ **并发冲突检测**：创建时检查文件和 INDEX.md，避免覆盖
- ✅ **JSON 输出支持**：所有命令支持 `--format json`
- ✅ **bash 辅助库**：可选，封装常用操作

---

## 📊 工作量估算

### 总计：102 小时（13 个工作日）

| 阶段 | 任务 | 估算 |
|---|---|---|
| Week 1 | 核心基础设施（解析器、索引、CRUD） | 30h |
| Week 2 | 命令实现（init/create/update/delete/sync-index） | 38h |
| Week 3 | 搜索和验证（search/list/load/validate） | 22h |
| Week 4 | 文档和测试（迁移指南、E2E测试） | 12h |

**相比初版节省**：
- 去掉 JavaScript SDK：-8h
- 去掉 doctor 命令：-20h
- 去掉 suggest-new-spec：-12h
- 去掉性能优化（移至 V1.1）：-12h
- 简化全文搜索（移至 V2）：-10h
- **总节省**：62 小时

---

## 🔧 技能集成示例

### ship-design 读取规范
```bash
# 列出 design 阶段的规范
specs=$(ship-spec list --project web --stage design --format json)

# 提取规范 ID
spec_ids=$(echo "$specs" | jq -r '.results[].spec_id')

# 加载规范内容
for spec_id in $spec_ids; do
  content=$(ship-spec load "$spec_id" --content-only)
  echo "规范 $spec_id 的内容：$content"
done
```

### ship-build 更新 existing-features
```bash
# 直接追加到 existing-features.md
cat >> .docs/spec/shared/existing-features.md <<EOF
## 用户模块
- **用户登录**：完成时间 $(date +%Y-%m-%d)，Feature: feature-xxx
  - 表：users, sessions
  - API：POST /api/v1/auth/login
  - 页面：/login
EOF

# ship-spec sync-index 会在下次运行时自动索引
```

### 使用 bash 辅助库（可选）
```bash
source skills/ship-spec/lib.sh

# 简化调用
api_standard=$(spec_load rest-api-standard)
specs=$(spec_list --project web --stage design)
```

---

## 📈 验收标准

### 功能完整性 ✅
- [ ] 所有 MVP 命令实现（10 个命令）
- [ ] 健壮的 INDEX.md 解析器（处理边界情况）
- [ ] 原子性索引重建（无数据损坏风险）
- [ ] 并发冲突检测（避免覆盖）
- [ ] JSON 输出格式（所有命令）

### 性能达标 ✅
- [ ] 元数据搜索 < 50ms（100 规范）
- [ ] 索引重建 < 200ms（100 规范）
- [ ] 内存占用 < 10MB

### 鲁棒性 ✅
- [ ] 通过所有单元测试
- [ ] 通过 CLI 集成测试
- [ ] INDEX.md 损坏可恢复（sync-index --rebuild）
- [ ] 规范外部修改自动检测（hash 验证）

### 用户体验 ✅
- [ ] 首次使用顺畅（init → create → search）
- [ ] 迁移指南完整（3 种场景）
- [ ] 文档完整（README、命令文档、集成示例）

---

## 🔄 版本规划

### MVP（当前方案，13 天）
- ✅ 核心 10 个命令
- ✅ CLI + JSON 输出
- ✅ 基础验证和索引
- ✅ 迁移指南

### V1.1（+2 周）
- doctor 命令（诊断和自动修复）
- 性能优化（缓存、并行）
- stats 命令增强（使用统计、归档建议）

### V2.0（+4 周）
- 全文搜索（倒排索引）
- 高级搜索语法（精确匹配、排除、正则）
- suggest-new-spec（基于统计的规范沉淀建议）
- 规范版本管理（语义化版本）
- Web UI（可视化管理）

---

## 🎨 架构亮点

### 1. 单一真实来源
- INDEX.md 是唯一源（避免同步问题）
- .index.json 只是缓存（可随时重建）

### 2. 原子性操作
- 临时文件写入 → 验证 → 原子替换
- 失败自动回滚（删除临时文件）

### 3. 健壮的解析
```javascript
// 处理转义竖线
line.split(/(?<!\\)\|/).map(c => c.replace(/\\\|/g, '|'))

// 处理空值
value === '-' ? [] : value.split(',')

// 处理列顺序变化
headers.forEach((header, i) => spec[header] = cells[i])
```

### 4. 降级策略
- 索引过期 → 采样检测 → 自动重建
- ship-spec 不可用 → bash 直接读取 INDEX.md

---

## 📝 迁移指南

### 场景 1：全新项目
```bash
ship-spec init --template standard
ship-spec create api-standard -t backend -p api --description "API 规范"
vim .docs/spec/backend/api-standard.md
ship-spec validate --all
```

### 场景 2：有散落规范文档
```bash
ship-spec init --template minimal
cp docs/api-guide.md .docs/spec/backend/api-standard.md
# 添加 frontmatter
ship-spec sync-index --auto-fix
ship-spec validate --all
```

### 场景 3：已有 .docs/spec/ 但无 INDEX.md
```bash
ship-spec sync-index --rebuild
ship-spec validate --all
```

---

## ⚠️ 风险评估

### 低风险 ✅
- **技术栈成熟**：Node.js、文件系统操作
- **依赖少**：无外部服务、无复杂算法
- **架构简单**：文件 + 索引，易于理解和维护
- **测试覆盖**：单元测试 + 集成测试 + E2E 测试

### 需关注的点
- **INDEX.md 格式兼容**：用户手动编辑可能破坏格式（通过 validate 检测）
- **并发写入**：多人同时创建规范（通过文件存在性检查）
- **迁移成本**：现有项目需要手动迁移（提供完整指南）

---

## 🏆 关键改进

相对于初版设计，本方案的改进：

1. **职责更清晰** ✅
   - 去掉 ship-spec 主动分发规范的职责
   - existing-features 由 ship-build 直接写入

2. **集成更简单** ✅
   - 废弃 JavaScript SDK
   - 采用 Bash CLI + JSON 输出
   - 符合技能调用模式

3. **实现更健壮** ✅
   - 处理边界情况（转义、空值、列顺序）
   - 原子性写入（临时文件机制）
   - 并发冲突检测

4. **范围更合理** ✅
   - 去掉非核心功能（doctor、suggest-new-spec）
   - 工作量从 164h → 102h（节省 62h）

5. **可维护性强** ✅
   - 单一真实来源（INDEX.md）
   - 自动同步（sync-index）
   - 错误可恢复（rebuild）

---

## 📚 文档结构

```
.docs/ship-spec-redesign/
├── 01-architecture.md              # 架构设计
├── 02-command-specs.md             # 命令规范（需更新）
├── 03-search-implementation.md     # 搜索实现
├── 04-adversarial-review-round1.md # 第一轮审查
├── 05-final-design.md              # 最终设计（需更新）
├── 06-adversarial-review-round2.md # 第二轮审查
├── 07-final-deliverable.md         # 可交付版本（需更新）
├── 08-cli-integration-approach.md  # CLI 集成方案（最新）
└── README.md                       # 本文档
```

**待更新**：
- [ ] 02-command-specs.md：添加 load 和 list 命令
- [ ] 05-final-design.md：去掉 SDK 章节，添加 CLI 章节
- [ ] 07-final-deliverable.md：去掉 SDK 实现，更新集成示例

---

## ✅ 最终结论

**状态**：✅ **方案可交付**

**交付物**：
1. ✅ 完整的架构设计文档
2. ✅ 详细的命令规范
3. ✅ 核心实现代码（解析器、原子性写入、冲突检测）
4. ✅ CLI 集成方案（bash + JSON）
5. ✅ 完整的迁移指南
6. ✅ 测试策略
7. ✅ 版本规划

**工作量**：102 小时（13 个工作日）

**质量保证**：
- 健壮的解析器
- 原子性写入
- 并发冲突检测
- 完整的测试覆盖
- 清晰的迁移路径

**建议下一步**：
1. Review 本方案，确认符合需求
2. 补充缺失的文档（load/list 命令规范）
3. 开始实施（按 4 周计划）
4. 持续与其他技能对接（ship-design、ship-build）

---

**方案完成日期**：2026-06-11  
**版本**：Final  
**状态**：Ready for Implementation ✅

---

## 🔄 2024-06-11 更新：单项目/多项目支持

新增 `09-single-multi-project-support.md` 文档，补充了：

### 关键补充
1. ✅ **自动检测机制**：CLI 读取 `project.yml` 或自动检测目录结构
2. ✅ **init 命令增强**：支持 `--workspace single|multi` 和 `--projects`
3. ✅ **create 命令逻辑**：根据模式和 `--project` 参数确定文件路径
4. ✅ **list/search 过滤**：多项目模式下自动过滤项目
5. ✅ **技能集成简化**：统一调用方式，CLI 内部处理差异

### 使用示例

#### 单项目初始化
```bash
ship-spec init --template standard
# 生成：.docs/spec/frontend/, backend/, shared/
```

#### 多项目初始化
```bash
ship-spec init --template standard --workspace multi --projects web,api,mobile
# 生成：.docs/spec/_shared/, web/, api/, mobile/
```

#### 技能集成（统一）
```bash
# 技能不需要关心单项目/多项目
project=$(yq '.projects[0]' feature-xxx/meta.yml)
specs=$(ship-spec list --project "$project" --stage design --format json)
# CLI 内部根据 workspace_mode 自动处理
```

### 目录结构规则

**单项目**：
- `shared/` - 通用规范
- `frontend/`, `backend/` - 按类型分类
- 所有规范 `projects=all`

**多项目**：
- `_shared/` - 跨项目通用规范
- `web/`, `api/` 等 - 项目专属规范
- 每个项目独立的 `existing-features.md`

详见：`09-single-multi-project-support.md`

---

## 💡 实现语言说明（重要）

**新增**：`10-implementation-language.md` - 澄清实现语言选择

### 核心澄清

**ship-spec 是一个 Node.js CLI 工具**

```
实现层：Node.js（处理复杂逻辑）
   ↓
接口层：CLI 命令（ship-spec list, ship-spec load ...）
   ↓
调用层：Bash 脚本（技能通过 bash 调用命令）
```

### 为什么看起来矛盾？

- ✅ 实现代码用 JavaScript（正确）
- ✅ 废弃 JavaScript SDK（正确）
- ✅ 技能用 Bash 调用（正确）

**解释**：
- **废弃的是**：JavaScript 编程接口（`import { SpecLoader }`）
- **保留的是**：JavaScript 实现 + CLI 命令
- **技能调用**：`ship-spec list --format json`（bash 命令）

### 为什么用 Node.js 而不是纯 Bash？

| 方面 | Node.js | 纯 Bash |
|---|---|---|
| INDEX.md 解析 | 50 行，清晰 | 100+ 行，复杂 |
| YAML 解析 | `yaml.parse()` | 需要安装 yq |
| 错误处理 | try/catch | 繁琐 |
| 跨平台 | ✅ 统一 | ⚠️ Windows 问题 |
| 依赖管理 | ✅ npm | ⚠️ 手动安装 |

### 使用示例

**技能开发者**（只需要知道这个）：
```bash
# 在 ship-design 技能中调用命令
specs=$(ship-spec list --project web --stage design --format json)
content=$(ship-spec load api-standard --content-only)
```

**ship-spec 开发者**（实现 CLI 工具）：
```javascript
// src/commands/list.js
async function listCommand(options) {
  const index = parseIndexTable(readFile('.docs/spec/INDEX.md'));
  const filtered = filterByProject(index, options.project);
  console.log(JSON.stringify({ total: filtered.length, results: filtered }));
}
```

详见：`10-implementation-language.md`
