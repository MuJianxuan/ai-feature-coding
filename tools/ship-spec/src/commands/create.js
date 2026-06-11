const fs = require('fs');
const path = require('path');
const yaml = require('yaml');
const { detectWorkspaceMode, parseIndexTable, generateIndexTable } = require('../core/parser');

async function createCommand(specId, options) {
  const workspace = detectWorkspaceMode();
  
  if (!fs.existsSync('.docs/spec/INDEX.md')) {
    console.error('错误：INDEX.md 不存在，请先运行 ship-spec init');
    process.exit(1);
  }
  
  // 确定文件路径
  let filePath;
  const projects = options.project ? options.project.split(',').map(p => p.trim()) : ['all'];
  
  if (workspace.mode === 'single_project') {
    const type = options.type || 'shared';
    filePath = `.docs/spec/${type}/${specId}.md`;
  } else {
    if (projects.includes('all') || projects.length > 1) {
      filePath = `.docs/spec/_shared/${specId}.md`;
    } else {
      filePath = `.docs/spec/${projects[0]}/${specId}.md`;
    }
  }
  
  // 检查文件是否已存在
  if (fs.existsSync(filePath)) {
    console.error(`错误：规范文件已存在: ${filePath}`);
    process.exit(1);
  }
  
  // 创建目录
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  
  // 生成规范内容
  const stages = options.stages ? options.stages.split(',').map(s => s.trim()) : ['design', 'build'];
  const description = options.description || `${specId} 规范`;
  
  const content = `---
spec_id: ${specId}
description: ${description}
stages: [${stages.join(', ')}]
projects: [${projects.join(', ')}]
tags: []
status: active
---

# ${description}

## 概述

（待补充）

## 规范内容

（待补充）
`;
  
  fs.writeFileSync(filePath, content);
  
  // 更新 INDEX.md
  const indexContent = fs.readFileSync('.docs/spec/INDEX.md', 'utf8');
  const specs = parseIndexTable(indexContent);
  
  specs.push({
    spec_id: specId,
    file: path.relative('.docs/spec', filePath),
    stages,
    projects,
    tags: [],
    status: 'active',
    description
  });
  
  const newIndexContent = indexContent.replace(
    /\|[\s\S]*?\n\n/,
    generateIndexTable(specs) + '\n\n'
  );
  
  fs.writeFileSync('.docs/spec/INDEX.md', newIndexContent);
  
  console.log('✅ 规范创建成功');
  console.log(`   规范 ID: ${specId}`);
  console.log(`   文件路径: ${filePath}`);
  console.log(`   适用项目: ${projects.join(', ')}`);
  console.log(`   适用阶段: ${stages.join(', ')}`);
}

module.exports = { createCommand };
