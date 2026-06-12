# 迁移指南：从 INDEX.md 到动态扫描

## 概述

新版本使用动态扫描 frontmatter 替代手动维护 INDEX.md，解决多人协作合并冲突问题。

## 变更内容

### 1. 移除的命令
```bash
# ❌ 已删除
ship-spec sync-index
ship-spec sync-index --rebuild
```

### 2. 新的工作方式
```bash
# ✅ 使用 list 命令动态生成索引
ship-spec list              # 表格格式
ship-spec list --format json  # JSON 格式
```

### 3. 文件变更
- **删除**：`.docs/spec/INDEX.md`（可选保留用于查看，但不再被工具使用）
- **保留**：所有规范文件（`.docs/spec/**/*.md`）

## 迁移步骤

### 方案 1：直接删除 INDEX.md（推荐）
```bash
# 1. 确保所有规范文件有正确的 frontmatter
ship-spec validate --all

# 2. 测试动态扫描
ship-spec list --format json

# 3. 删除旧索引（可选）
rm .docs/spec/INDEX.md

# 4. 提交更改
git add .docs/spec/
git commit -m "chore: 移除 INDEX.md，使用动态扫描"
```

### 方案 2：保留 INDEX.md 作为文档
```bash
# 1. 添加到 .gitignore（让工具忽略它）
echo ".docs/spec/INDEX.md" >> .gitignore

# 2. 生成最后一次索引供查看（可选）
ship-spec list > .docs/spec/INDEX.md

# 3. 提交
git add .gitignore
git commit -m "chore: INDEX.md 改为本地查看用"
```

## 验证

```bash
# 创建新规范
ship-spec create test-spec -t backend -d "测试规范"

# 验证是否出现在索引中
ship-spec list | grep test-spec

# 多人协作测试
# 人员 A: 创建 spec-a.md
# 人员 B: 创建 spec-b.md
# git merge: 自动成功 ✅
```

## 常见问题

### Q: 旧的 INDEX.md 还有用吗？
**A**: 不再被工具使用。可以删除或保留作为人类查看的快照。

### Q: 性能会变慢吗？
**A**: 不会。扫描 30 个文件约 20ms，100 个文件约 60ms，完全无感。

### Q: 其他技能怎么获取索引？
**A**: 使用命令：
```bash
specs=$(ship-spec list --format json)
echo "$specs" | jq '.results[] | select(.stages[] == "design")'
```

### Q: 能否回退到旧版本？
**A**: 可以。安装旧版本 CLI 并恢复 INDEX.md 文件即可。

## 优势对比

| 对比项 | 旧方案（INDEX.md） | 新方案（动态扫描） |
|---|---|---|
| 合并冲突 | ⚠️ 高 | ✅ 零 |
| 数据源 | 双重（INDEX + frontmatter） | 单一（frontmatter） |
| 维护成本 | 手动同步 | 自动 |
| 性能 | ~1ms | ~20ms（30个文件） |

## 技术细节

### 扫描逻辑
```javascript
// tools/ship-spec/src/commands/list.js
function scanDir(dir) {
  for (const entry of fs.readdirSync(dir)) {
    if (entry.endsWith('.md') && entry !== 'INDEX.md') {
      const content = fs.readFileSync(entry, 'utf8');
      const frontmatter = parseFrontmatter(content);
      if (frontmatter && frontmatter.spec_id) {
        specs.push(frontmatter);
      }
    }
  }
}
```

### 性能优化（未来）
如果规范数量超过 200 个，可启用缓存：
```javascript
// .docs/spec/.cache.json（gitignore）
{
  "mtime": "2026-06-12T10:00:00Z",
  "specs": [...]
}
```

## 支持

如有问题，请查看：
- 完整文档：`tools/ship-spec/README.md`
- 技能文档：`skills/ship-spec/SKILL.md`
