---
name: ship-spec
description: "ShipKit 规范管理技能。引导安装和使用 ship-spec CLI 工具，管理 .docs/spec 知识库，定义规范采集和沉淀标准。"
---

# ship-spec

## 目标

管理和维护 .docs/spec/ 知识库。spec 是项目约束，不是摆设。

---

## ship-spec CLI 工具

### 安装
```bash
# 全局安装
npm install -g @shipkit/spec-cli

# 验证安装
ship-spec -h
ship-spec --version
```

### 基本命令
```bash
ship-spec init              # 初始化目录
ship-spec create <spec-id>  # 创建规范
ship-spec list              # 列出规范（动态扫描 frontmatter）
ship-spec load <spec-id>    # 加载规范
ship-spec validate          # 验证规范
```

### 命令帮助
```bash
ship-spec -h          # 查看所有命令和示例
ship-spec create -h   # 查看具体命令帮助
```

---

## 工作模式

### 单项目（single）
- **定义**：一个仓库只有一个项目
- **规范适用**：所有规范 `projects: [all]`
- **目录结构**：`frontend/`, `backend/`, `shared/`

**何时使用**：独立应用、单体项目、小型服务

### 多项目（multi）
- **定义**：一个仓库有多个项目（web, api, mobile 等）
- **规范适用**：可指定 `projects: [web, api]` 或 `[all]`
- **目录结构**：`_shared/`, `web/`, `api/`, `mobile/`

**何时使用**：monorepo、微服务、多端应用

### 配置文件
`.docs/ship/project.yml`:
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
  - mobile
```
**初始化**：
```bash
# 单项目（默认）
ship-spec init
# 多项目
ship-spec init --mode multi --projects web,api,mobile
```
.docs/spec/
├── frontend/                   # 前端规范
├── backend/                    # 后端规范
└── shared/                     # 通用规范
    ├── tech-stack.md
    ├── existing-features.md
    └── naming-conventions.md
```

### 多项目
```
.docs/spec/
├── _shared/                    # 跨项目通用规范
│   ├── tech-stack.md
│   └── error-codes.md
├── web/                        # web 项目规范
│   ├── frontend/
│   └── existing-features.md
└── api/                        # api 项目规范
    ├── backend/
    └── existing-features.md
```

## 索引机制

- **实现**：动态扫描所有 `.md` 文件的 frontmatter
- **使用**：`ship-spec list` 生成索引
- **优势**：零合并冲突、单一数据源、自动同步

---

## 规范采集和沉淀标准 ⭐️

### 何时沉淀规范？

**评分标准**（≥ 60 分才建议新增）：
- 复用次数 ≥ 3：+40 分
- 模式稳定：+30 分
- 跨模块使用：+20 分
- 中高复杂度：+10 分

**示例**：
- ✅ REST API 标准（复用 10 次，稳定，跨模块）→ 90 分，值得沉淀
- ❌ 某个页面的布局（只用 1 次）→ 40 分，不值得
- ⚠️ 错误码定义（复用 2 次，但可能增长）→ 50 分，观察中

**原则**：低分就别污染知识库。现实里最烂的规范库就是没人敢删、没人会读。

### 规范质量要求

#### 内容要求
- ✅ **简明扼要**：不超过 200 行
- ✅ **聚焦约束**：说清楚"做什么"、"不做什么"
- ✅ **可执行**：有具体示例
- ✅ **可验证**：有检查点

#### 禁止事项
- ❌ 不写大而全的百科全书
- ❌ 不重复写已有内容
- ❌ 不写一次性的实现细节
- ❌ 不写敏感信息（密码、token、密钥、内部地址）

### spec 模板结构

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
（什么时候用这个规范）
- 设计新的 REST API
- 审查现有 API

## 核心约束

### 必须做
- 使用 RESTful 资源命名
- 统一错误格式
- 版本化（/api/v1/）

### 禁止做
- 不在 URL 中使用动词
- 不返回裸数据（必须包装）

## 示例

### 正确
GET /api/v1/users/123
POST /api/v1/orders

### 错误
GET /api/v1/getUser?id=123
POST /api/v1/createOrder

## 检查点
- [ ] URL 使用名词复数
- [ ] 错误响应包含 code/message
- [ ] 有版本号
```

### 规范命名规范

**格式**：`<scope>-<topic>[-<detail>]`

**规则**：
- 全小写，用连字符分隔
- 描述性强，一看就懂
- 不超过 4 个单词

**示例**：
- ✅ `rest-api-standard`
- ✅ `naming-conventions`
- ✅ `error-handling`
- ✅ `web-component-patterns`
- ❌ `api` (太泛)
- ❌ `myProjectRestApiDesignStandardV2` (太长)

---

## 规范对抗式审查清单 ⭐️

新规范创建后，使用此清单进行对抗式审查，确保规范可交付。

### 审查流程

```bash
# 1. 创建规范
ship-spec create <spec-id> -t <type> -d "<description>"
vim .docs/spec/<type>/<spec-id>.md

# 2. 对抗式审查
# 使用下面的检查清单逐项验证

# 3. 修复问题
# 根据审查结果修改规范

# 4. 验证通过
ship-spec validate <spec-id>
```

### 检查清单

#### ✅ 必要性检查（60 分评分）
- [ ] **复用次数**：这个规范会被复用 ≥ 3 次吗？
- [ ] **模式稳定**：这个约束在未来 6 个月内会变化吗？
- [ ] **跨模块使用**：是否被多个模块/团队使用？
- [ ] **复杂度**：是否有一定复杂度（不是显而易见的）？

**评判**：如果总分 < 60，❌ **不应该沉淀为规范**

#### ✅ 完整性检查
- [ ] **frontmatter 完整**：spec_id, description, stages, projects, status 都填写了吗？
- [ ] **有适用场景**：说明了何时使用这个规范吗？
- [ ] **有核心约束**：明确列出"必须做"和"禁止做"吗？
- [ ] **有具体示例**：提供了正确和错误的示例吗？
- [ ] **有检查点**：提供了可验证的检查清单吗？

**评判**：缺少任何一项，❌ **规范不完整**

#### ✅ 简洁性检查
- [ ] **长度适中**：规范内容 ≤ 200 行吗？
- [ ] **聚焦约束**：只写约束，没有写实现细节吗？
- [ ] **无重复**：与现有规范没有重复内容吗？
- [ ] **无废话**：每一句话都有价值吗？

**评判**：如果超过 200 行或有大量重复，⚠️ **需要精简**

#### ✅ 可执行性检查
- [ ] **示例具体**：示例是真实代码片段，不是伪代码吗？
- [ ] **约束明确**：约束是可操作的（不是"尽量"、"最好"）吗？
- [ ] **可验证**：检查点是二元的（是/否）吗？
- [ ] **无歧义**：阅读规范后，不同人的理解一致吗？

**评判**：如果有模糊表述，❌ **需要明确化**

#### ✅ 安全性检查
- [ ] **无敏感信息**：没有密码、token、密钥、内部地址吗？
- [ ] **描述来源**：如果涉及密钥，只描述"从环境变量读取"吗？
- [ ] **无生产数据**：没有真实用户数据、订单号等吗？

**评判**：如果有敏感信息，❌ **必须删除**

#### ✅ 维护性检查
- [ ] **职责单一**：这个规范只约束一个主题吗？
- [ ] **易于更新**：未来修改时，不会影响其他规范吗？
- [ ] **命名清晰**：spec_id 一看就知道是什么吗？
- [ ] **状态正确**：status 设置为 active 了吗？

**评判**：如果职责不清或命名模糊，⚠️ **需要重构**

### 审查结论

**✅ APPROVED（可交付）**：
- 所有 5 个检查类别都通过
- 没有 ❌ 标记
- ⚠️ 标记已修复或可接受

**❌ REJECTED（需修复）**：
- 必要性检查 < 60 分 → 不应该沉淀
- 有安全性问题 → 必须删除敏感信息
- 完整性缺失 → 补充缺失部分
- 可执行性不足 → 明确约束和示例

**⚠️ NEEDS IMPROVEMENT（建议改进）**：
- 长度过长 → 精简
- 有模糊表述 → 明确化
- 命名不清 → 重命名

### 审查示例

> 💡 需要查看详细示例时，读取：`./_refs/review-examples.md`（相对当前技能目录）

---

## existing-features 更新指南

### 何时更新？
功能完成后（Build done）

### 如何更新？
```bash
# 检测工作空间模式
workspace_mode=$(yq '.workspace_mode' .docs/ship/project.yml 2>/dev/null || echo "single_project")

# 确定文件路径
if [ "$workspace_mode" = "project_group" ]; then
  project=$(yq '.projects[0]' feature-xxx/meta.yml)
  features_file=".docs/spec/${project}/existing-features.md"
else
  features_file=".docs/spec/shared/existing-features.md"
fi

# 使用 cat >> 追加（不要覆盖）
cat >> "$features_file" <<EOF

## 用户模块
- **用户登录**：完成时间 $(date +%Y-%m-%d)，Feature: feature-xxx
  - 表：users, sessions
  - API：POST /api/v1/auth/login
  - 页面：/login
  - 测试：tests/e2e/login.spec.ts
EOF

# 同步索引
```

### 格式说明
```markdown
## 模块名
- **功能名**：完成时间 YYYY-MM-DD，Feature: feature-xxx
  - 表：表名列表
  - API：端点列表
  - 页面：路由列表
  - 测试：测试文件路径
```

### 注意事项
- ✅ 使用 `cat >>` 追加
- ✅ 多项目：通用能力写 `_shared`，专属写项目目录
- ❌ 不写敏感信息（密码、token、密钥）

---

## 规范维护

### 规范生命周期

#### 新建规范
```bash
# 1. 创建规范
ship-spec create <spec-id> -t <type> -d "<description>"

# 2. 编写内容
vim .docs/spec/<type>/<spec-id>.md

# 3. 对抗式审查（使用上面的检查清单）

# 4. 验证
ship-spec validate <spec-id>
```

#### 更新规范
```bash
# 1. 直接编辑规范文件
vim .docs/spec/<type>/<spec-id>.md

# 2. 更新 frontmatter（如有必要）

# 3. 同步索引
```

#### 归档规范
```bash
# 1. 修改状态
# 在 frontmatter 中设置 status: deprecated

# 2. 添加归档说明
# 在规范顶部添加：
# > ⚠️ 本规范已废弃，请使用 xxx-v2

# 3. 同步索引
```

#### 删除规范
```bash
# 1. 删除文件
rm .docs/spec/<type>/<spec-id>.md

# 2. 同步索引
```

### 规范 vs 模板 vs 代码

| 类型 | 定义 | 适用范围 | 示例 |
|---|---|---|---|
| **spec（项目规范）** | 项目长期约束 | 当前项目 | API 标准、命名规范 |
| **模板（参考模板）** | 临时检查清单 | 特定设计场景 | 技术方案模板 |
| **代码（实现）** | 具体实现 | 单个功能 | 具体 API 实现 |

**优先级**：requirements/AC > 项目 spec > 现有代码 > 参考模板 > AI 默认习惯

---

## 常见问题

```bash
```

### 规范冲突
- project 规范优先于 _shared
- 报告冲突给用户决策

### CLI 工具不可用

### 规范过期
定期审查，标记 `status: deprecated`

---

## 技能调用约定（最小化）

### 基本原则
其他技能自行决定何时、如何使用规范。

### 推荐模式
```bash
# 列出规范
specs=$(ship-spec list --project <project> --stage <stage> --format json)

# 加载规范
content=$(ship-spec load <spec-id> --content-only)
```

### 注意事项
- 不要一次加载所有规范（按需加载）
- 使用 `--project` 过滤（多项目模式）
- 使用 `--stage` 过滤（按阶段）

---

## 不做什么

- ❌ 不告诉其他技能如何集成规范（那是各技能的职责）
- ❌ 不描述 Understand/Design/Build 的工作流程
- ❌ 不定义各阶段应该加载什么规范
- ❌ 不替其他技能做决策
- ❌ 不把每次实现都沉淀成规范
- ❌ 不写大而全的规范百科全书
