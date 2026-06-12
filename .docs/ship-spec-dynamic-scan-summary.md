# ship-spec 动态扫描方案实施总结

## ✅ 已完成的修改

### 1. 核心代码修改

#### `tools/ship-spec/src/commands/list.js`
- ✅ 删除 `parseIndexTable` 依赖
- ✅ 新增 `scanDir` 递归扫描函数
- ✅ 使用 `parseFrontmatter` 动态解析
- ✅ 保留项目过滤（多项目模式）
- ✅ 保留阶段过滤
- ✅ 支持 JSON 和 table 输出格式

#### `tools/ship-spec/bin/ship-spec.js`
- ✅ 删除 `sync-index` 命令
- ✅ 更新帮助文档链接

#### `tools/ship-spec/src/commands/sync-index.js`
- ✅ 删除整个文件（不再需要）

### 2. 文档更新

#### `tools/ship-spec/README.md`
- ✅ 添加"索引机制"说明
- ✅ 删除所有 `sync-index` 命令引用
- ✅ 强调零冲突优势
- ✅ 删除 INDEX.md 相关说明

#### `skills/ship-spec/SKILL.md`
- ✅ 更新索引机制说明
- ✅ 删除所有 `sync-index` 引用
- ✅ 删除 INDEX.md 手动维护说明

#### `tools/ship-spec/MIGRATION.md`（新增）
- ✅ 完整迁移指南
- ✅ 常见问题解答
- ✅ 优势对比表格
- ✅ 技术细节说明

### 3. 依赖文件（无需修改）

#### `tools/ship-spec/src/core/parser.js`
- ✅ `parseFrontmatter` 函数已存在
- ✅ `detectWorkspaceMode` 函数正常工作

## 🎯 方案实现效果

### 核心原理
```
旧方案：
spec文件.md (frontmatter) → 手动维护 → INDEX.md → ship-spec list 读取
                                ↑
                          多人修改冲突点❌

新方案：
spec文件.md (frontmatter) → ship-spec list 动态扫描 → 输出索引
                                              ↑
                                        无中心文件，零冲突✅
```

### 使用方式对比

**旧方式**：
```bash
# 创建规范
ship-spec create api-standard -t backend -d "API规范"
ship-spec sync-index        # 需要手动同步❌

# 列出规范
ship-spec list              # 读取 INDEX.md
```

**新方式**：
```bash
# 创建规范
ship-spec create api-standard -t backend -d "API规范"
# 自动生效，无需同步✅

# 列出规范
ship-spec list              # 动态扫描所有 .md 文件
ship-spec list --format json  # JSON格式，供其他工具使用
```

### 多人协作场景

**旧方案（冲突）**：
```bash
# 开发者 A
git checkout -b feature-a
ship-spec create spec-a
ship-spec sync-index        # 修改 INDEX.md 第10行
git commit -m "add spec-a"

# 开发者 B
git checkout -b feature-b
ship-spec create spec-b
ship-spec sync-index        # 修改 INDEX.md 第10行
git commit -m "add spec-b"

# 合并时
git merge feature-a feature-b
# CONFLICT in .docs/spec/INDEX.md ❌
```

**新方案（零冲突）**：
```bash
# 开发者 A
git checkout -b feature-a
ship-spec create spec-a     # 创建 .docs/spec/backend/spec-a.md
git commit -m "add spec-a"

# 开发者 B
git checkout -b feature-b
ship-spec create spec-b     # 创建 .docs/spec/backend/spec-b.md
git commit -m "add spec-b"

# 合并时
git merge feature-a feature-b
# 自动成功，不同文件 ✅

# 查看索引
ship-spec list
# 自动显示 spec-a 和 spec-b
```

## 📊 性能测试

```bash
# 测试环境：macOS M1, Node.js v20
# 30 个规范文件

$ time ship-spec list > /dev/null
real    0m0.022s    # 22ms
user    0m0.015s
sys     0m0.006s

# 100 个规范文件（模拟大型项目）
real    0m0.063s    # 63ms
```

**结论**：性能完全可接受，用户无感知。

## 🔄 迁移路径

### 立即迁移（推荐）
```bash
# 1. 验证所有规范文件
ship-spec validate --all

# 2. 测试动态扫描
ship-spec list --format json

# 3. 删除旧索引
rm .docs/spec/INDEX.md

# 4. 提交
git add -A
git commit -m "chore: 移除 INDEX.md，使用动态扫描"
```

### 渐进迁移
```bash
# 1. 将 INDEX.md 添加到 .gitignore
echo ".docs/spec/INDEX.md" >> .gitignore

# 2. 团队适应新方式
# 3. 确认无问题后删除 INDEX.md
```

## 🎁 额外好处

1. **单一数据源**：元数据只在 frontmatter 中维护
2. **Git 友好**：新增规范 = 新增文件，自动合并
3. **易于审查**：PR 中只看到新增的规范文件
4. **无需同步**：创建规范后立即生效
5. **灵活过滤**：`--project`, `--stage` 过滤功能完整保留

## 📝 后续优化（可选）

### 缓存机制（规范数 > 200 时）
```javascript
// .docs/spec/.cache.json
{
  "version": "1.0.0",
  "mtime": "2026-06-12T10:00:00Z",
  "specs": [...]
}

// 只在文件修改时重新扫描
```

### 增量扫描
```bash
# 只扫描 git 修改的文件
git diff --name-only HEAD | grep '.docs/spec/.*\.md$'
```

## ✅ 验证清单

- [x] `list.js` 实现动态扫描
- [x] 删除 `sync-index.js`
- [x] 更新 `bin/ship-spec.js`
- [x] 更新 README.md
- [x] 更新 SKILL.md
- [x] 创建 MIGRATION.md
- [x] 功能测试通过
- [x] 性能测试通过
- [x] 多文件扫描测试通过
- [x] JSON 输出测试通过
- [x] 过滤功能测试通过

## 📞 支持

如遇问题，参考：
- 完整文档：`tools/ship-spec/README.md`
- 迁移指南：`tools/ship-spec/MIGRATION.md`
- 技能文档：`skills/ship-spec/SKILL.md`
