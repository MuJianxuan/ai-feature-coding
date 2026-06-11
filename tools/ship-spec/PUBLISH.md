# npm 发布指南

## 准备工作

1. **设置 npm 账号**（如果还没有）
```bash
npm login
```

2. **检查包名是否可用**
```bash
npm view @shipkit/spec-cli
# 如果返回 404，说明包名可用
```

## 发布流程

### 1. 发布到 npm

```bash
cd tools/ship-spec

# 确保依赖已安装
npm install

# 本地测试
npm link
ship-spec -h

# 发布（首次发布）
npm publish --access public

# 后续版本发布
# 1. 更新版本号
npm version patch  # 1.0.0 -> 1.0.1
# 或
npm version minor  # 1.0.1 -> 1.1.0
# 或
npm version major  # 1.1.0 -> 2.0.0

# 2. 发布
npm publish
```

### 2. 验证发布

```bash
# 全局安装测试
npm install -g @shipkit/spec-cli

# 验证
ship-spec --version
ship-spec -h
```

## 版本管理

### 语义化版本

- **patch**（1.0.0 -> 1.0.1）：Bug 修复
- **minor**（1.0.0 -> 1.1.0）：新增功能（向后兼容）
- **major**（1.0.0 -> 2.0.0）：破坏性变更

### 发布前检查清单

- [ ] 代码通过本地测试
- [ ] README.md 已更新
- [ ] package.json 中的版本号已更新
- [ ] CHANGELOG.md 已记录变更（如果有）
- [ ] 没有提交未完成的代码

## 回滚发布

如果发布了错误的版本：

```bash
# 撤销发布（72 小时内）
npm unpublish @shipkit/spec-cli@1.0.1

# 或者立即发布修复版本
npm version patch
npm publish
```

## 持续发布

每次修改后：

1. 修改代码
2. 本地测试
3. 更新版本号（`npm version patch/minor/major`）
4. 发布（`npm publish`）
5. 验证发布成功

## 注意事项

- ⚠️ npm 不允许重复发布相同版本号
- ⚠️ 已发布的版本 72 小时后无法撤销
- ✅ 使用 `npm version` 自动更新版本号并创建 git tag
- ✅ 发布前先在本地 `npm link` 测试
