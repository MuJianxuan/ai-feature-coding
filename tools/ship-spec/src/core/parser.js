const fs = require('fs');
const path = require('path');
const yaml = require('yaml');

/**
 * 加载配置文件
 */
function loadConfig() {
  const projectYmlPath = '.docs/ship/project.yml';
  
  if (fs.existsSync(projectYmlPath)) {
    const content = fs.readFileSync(projectYmlPath, 'utf8');
    const config = yaml.parse(content);
    
    // 兼容旧格式
    if (config.workspace_mode) {
      return {
        mode: config.workspace_mode === 'single_project' ? 'single' : 'multi',
        project: { name: config.workspace_name || path.basename(process.cwd()) },
        projects: config.projects || []
      };
    }
    
    return config;
  }
  
  // 默认配置
  return { mode: 'single', project: { name: path.basename(process.cwd()) } };
}

/**
 * 获取规范基础路径
 */
function getSpecBasePath(config, projectName) {
  if (config.mode === 'single') {
    return '.docs/spec';
  } else {
    return projectName ? `.docs/spec/${projectName}` : '.docs/spec';
  }
}

/**
 * 解析 INDEX.md 表格
 */
function parseIndexTable(markdown) {
  const lines = markdown.split('\n').filter(l => l.trim());
  
  const headerLine = lines.find(l => l.includes('spec_id'));
  if (!headerLine) return [];
  
  const separatorIdx = lines.indexOf(lines.find(l => /^\|[\s:-|]+\|$/.test(l)));
  if (separatorIdx === -1) return [];
  
  const headers = headerLine
    .split(/(?<!\\)\|/)
    .map(h => h.trim())
    .filter((_, i, arr) => i > 0 && i < arr.length - 1);
  
  const dataLines = lines.slice(separatorIdx + 1).filter(l => l.startsWith('|'));
  
  return dataLines.map(line => {
    const values = line
      .split(/(?<!\\)\|/)
      .map(v => v.trim())
      .filter((_, i, arr) => i > 0 && i < arr.length - 1);
    
    const obj = {};
    headers.forEach((h, i) => {
      obj[h] = values[i] || '';
    });
    return obj;
  });
}

/**
 * 生成 INDEX.md 表格
 */
function generateIndexTable(specs) {
  if (!specs || specs.length === 0) {
    return `| spec_id | file | stages | projects | tags | status | description |
|---------|------|--------|----------|------|--------|-------------|
<!-- 此表格由 ship-spec 自动维护 -->`;
  }
  
  let table = `| spec_id | file | stages | projects | tags | status | description |\n`;
  table += `|---------|------|--------|----------|------|--------|-------------|\n`;
  
  specs.forEach(spec => {
    table += `| ${spec.spec_id || ''} | ${spec.file || ''} | ${spec.stages || ''} | ${spec.projects || ''} | ${spec.tags || ''} | ${spec.status || ''} | ${spec.description || ''} |\n`;
  });
  
  return table;
}

/**
 * 解析 frontmatter
 */
function parseFrontmatter(content) {
  const match = content.match(/^---\n([\s\S]*?)\n---/);
  if (!match) return null;
  
  try {
    return yaml.parse(match[1]);
  } catch (e) {
    return null;
  }
}

/**
 * 提取正文
 */
function extractBody(content) {
  const match = content.match(/^---\n[\s\S]*?\n---\n([\s\S]*)/);
  return match ? match[1].trim() : content;
}

module.exports = {
  loadConfig,
  getSpecBasePath,
  parseIndexTable,
  parseFrontmatter,
  generateIndexTable,
  extractBody
};
