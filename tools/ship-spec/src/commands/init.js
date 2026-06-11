const fs = require('fs');
const path = require('path');
const yaml = require('yaml');
const { detectWorkspaceMode, generateIndexTable } = require('../core/parser');

async function initCommand(options) {
  const mode = options.workspace || 'single';
  const projects = options.projects ? options.projects.split(',').map(p => p.trim()) : [];
  
  // 创建目录结构
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
  
  // 创建 project.yml
  fs.mkdirSync('.docs/ship', { recursive: true });
  const config = {
    workspace_mode: mode === 'single' ? 'single_project' : 'project_group',
    workspace_name: path.basename(process.cwd()),
    projects: mode === 'multi' ? projects : []
  };
  fs.writeFileSync('.docs/ship/project.yml', yaml.stringify(config));
  
  // 创建 INDEX.md
  const indexContent = `# Spec Index

${generateIndexTable([])}

## 使用说明

- **spec_id**: 规范唯一标识
- **file**: 规范文件路径（相对 .docs/spec/）
- **stages**: 适用阶段（understand, design, build, done）
- **projects**: 适用项目（all 或具体项目名）
- **tags**: 标签
- **status**: 状态（active, deprecated）
- **description**: 规范描述
`;
  
  fs.writeFileSync('.docs/spec/INDEX.md', indexContent);
  
  // 创建 existing-features.md
  const featuresPath = mode === 'single' 
    ? '.docs/spec/shared/existing-features.md'
    : '.docs/spec/_shared/existing-features.md';
  
  const featuresContent = `---
spec_id: existing-features
description: 已有功能索引
stages: [understand, done]
projects: [all]
---

# 已有功能索引

此文件记录项目中已完成的功能模块，供 ship-understand 和其他阶段参考。

## 功能列表

（待补充）
`;
  
  fs.writeFileSync(featuresPath, featuresContent);
  
  console.log('✅ ship-spec 初始化完成');
  console.log(`   模式: ${config.workspace_mode}`);
  if (mode === 'multi') {
    console.log(`   项目: ${projects.join(', ')}`);
  }
  console.log('   目录: .docs/spec/');
  console.log('   索引: .docs/spec/INDEX.md');
}

module.exports = { initCommand };
