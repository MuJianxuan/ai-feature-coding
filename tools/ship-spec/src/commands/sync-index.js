const fs = require('fs');
const path = require('path');
const { parseIndexTable, generateIndexTable, parseFrontmatter } = require('../core/parser');

async function syncIndexCommand(options) {
  if (!fs.existsSync('.docs/spec')) {
    console.error('错误：.docs/spec 目录不存在');
    process.exit(1);
  }
  
  const specs = [];
  
  // 扫描所有 .md 文件
  function scanDir(dir, basePath = '') {
    const entries = fs.readdirSync(dir, { withFileTypes: true });
    
    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name);
      const relativePath = path.join(basePath, entry.name);
      
      if (entry.isDirectory() && !entry.name.startsWith('.')) {
        scanDir(fullPath, relativePath);
      } else if (entry.isFile() && entry.name.endsWith('.md') && entry.name !== 'INDEX.md') {
        const content = fs.readFileSync(fullPath, 'utf8');
        const frontmatter = parseFrontmatter(content);
        
        if (frontmatter && frontmatter.spec_id) {
          specs.push({
            spec_id: frontmatter.spec_id,
            file: relativePath,
            stages: frontmatter.stages || [],
            projects: frontmatter.projects || ['all'],
            tags: frontmatter.tags || [],
            status: frontmatter.status || 'active',
            description: frontmatter.description || ''
          });
        }
      }
    }
  }
  
  scanDir('.docs/spec');
  
  // 生成新的 INDEX.md
  const indexContent = `# Spec Index

${generateIndexTable(specs)}

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
  
  console.log(`✅ 索引同步完成，共 ${specs.length} 个规范`);
}

module.exports = { syncIndexCommand };
