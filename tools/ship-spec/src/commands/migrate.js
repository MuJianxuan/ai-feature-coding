#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const yaml = require('yaml');

async function migrateCommand() {
  const configPath = '.docs/ship/project.yml';
  
  if (!fs.existsSync(configPath)) {
    console.log('❌ 配置文件不存在，跳过迁移');
    return;
  }

  const content = fs.readFileSync(configPath, 'utf8');
  const oldConfig = yaml.parse(content);

  // 已经是新格式
  if (oldConfig.mode) {
    console.log('✅ 已是新格式，无需迁移');
    return;
  }

  // 转换格式
  const newConfig = {
    mode: oldConfig.workspace_mode === 'single_project' ? 'single' : 'multi'
  };

  if (newConfig.mode === 'single') {
    newConfig.project = { 
      name: oldConfig.workspace_name || path.basename(process.cwd()) 
    };
  } else {
    newConfig.projects = oldConfig.projects || [];
  }

  // 备份
  fs.copyFileSync(configPath, `${configPath}.bak`);
  console.log('📦 已备份: .docs/ship/project.yml.bak');

  // 写入新格式
  fs.writeFileSync(configPath, yaml.stringify(newConfig), 'utf8');
  
  console.log('✅ 迁移完成');
  console.log(`   模式: ${newConfig.mode}`);
  if (newConfig.mode === 'single') {
    console.log(`   项目: ${newConfig.project.name}`);
  } else {
    console.log(`   项目: ${newConfig.projects.join(', ')}`);
  }
}

module.exports = { migrateCommand };

if (require.main === module) {
  migrateCommand().catch(console.error);
}
