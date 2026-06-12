const fs = require('fs');
const path = require('path');
const { loadConfig, parseFrontmatter } = require('../core/parser');

async function listCommand(options) {
  if (!fs.existsSync('.docs/spec')) {
    console.error('错误：.docs/spec 目录不存在');
    process.exit(1);
  }
  
  const config = loadConfig();
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
  
  // 应用项目过滤（多项目模式）
  let filteredSpecs = specs;
  if (config.mode === 'multi' && options.project) {
    filteredSpecs = filteredSpecs.filter(s => 
      s.projects.includes(options.project) || s.projects.includes('all')
    );
  }
  
  // 应用阶段过滤
  if (options.stage) {
    filteredSpecs = filteredSpecs.filter(s => s.stages.includes(options.stage));
  }
  
  // 输出
  if (options.format === 'json') {
    console.log(JSON.stringify({
      total: filteredSpecs.length,
      filters: { project: options.project, stage: options.stage },
      results: filteredSpecs
    }, null, 2));
  } else {
    console.log('SPEC_ID\t\tFILE\t\tPROJECTS\t\tSTAGES\t\tDESCRIPTION');
    filteredSpecs.forEach(s => {
      console.log(`${s.spec_id}\t${s.file}\t${s.projects.join(',')}\t${s.stages.join(',')}\t${s.description}`);
    });
  }
      }
  module.exports = { listCommand };
