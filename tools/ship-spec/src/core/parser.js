const fs = require('fs');
const path = require('path');
const yaml = require('yaml');

/**
 * 检测工作空间模式
 */
function detectWorkspaceMode() {
  const projectYmlPath = '.docs/ship/project.yml';
  
  if (fs.existsSync(projectYmlPath)) {
    const content = fs.readFileSync(projectYmlPath, 'utf8');
    const config = yaml.parse(content);
    return {
      mode: config.workspace_mode || 'single_project',
      projects: config.projects || []
    };
  }
  
  // 自动检测
  const specDir = '.docs/spec';
  if (!fs.existsSync(specDir)) {
    return { mode: 'single_project', projects: [] };
  }
  
  const entries = fs.readdirSync(specDir, { withFileTypes: true });
  const dirs = entries.filter(e => e.isDirectory()).map(e => e.name);
  
  if (dirs.includes('_shared')) {
    const projects = dirs.filter(d => d !== '_shared' && !d.startsWith('.'));
    return { mode: 'project_group', projects };
  }
  
  return { mode: 'single_project', projects: [] };
}

/**
 * 解析 INDEX.md 表格
 */
function parseIndexTable(markdown) {
  const lines = markdown.split('\n').filter(l => l.trim());
  
  const headerLine = lines.find(l => l.includes('spec_id'));
  if (!headerLine) return [];
  
  const separatorIdx = lines.indexOf(lines.find(l => /^\|[\s\-:|]+\|$/.test(l)));
  if (separatorIdx === -1) return [];
  
  const headers = headerLine
    .split(/(?<!\\)\|/)
    .map(c => c.replace(/\\\|/g, '|').trim())
    .filter(Boolean);
  
  const dataLines = lines.slice(separatorIdx + 1).filter(l => l.startsWith('|'));
  
  return dataLines.map(line => {
    const cells = line
      .split(/(?<!\\)\|/)
      .map(c => c.replace(/\\\|/g, '|').trim())
      .filter((_, i, arr) => i > 0 && i < arr.length - 1);
    
    const spec = {};
    headers.forEach((header, i) => {
      const value = cells[i] || '';
      if (header === 'projects' || header === 'stages' || header === 'tags') {
        spec[header] = value === '-' || value === '' ? [] : value.split(',').map(s => s.trim());
      } else {
        spec[header] = value === '-' ? '' : value;
      }
    });
    
    return spec;
  });
}

/**
 * 生成 INDEX.md 表格
 */
function generateIndexTable(specs) {
  if (specs.length === 0) {
    return '| spec_id | file | stages | projects | tags | status | description |\n|---|---|---|---|---|---|---|\n';
  }
  
  const headers = ['spec_id', 'file', 'stages', 'projects', 'tags', 'status', 'description'];
  const headerLine = '| ' + headers.join(' | ') + ' |';
  const separatorLine = '|' + headers.map(() => '---').join('|') + '|';
  
  const dataLines = specs.map(spec => {
    const cells = headers.map(h => {
      const value = spec[h];
      if (Array.isArray(value)) {
        return value.length === 0 ? '-' : value.join(',');
      }
      const stringValue = (value || '-').toString();
      return stringValue.replace(/\|/g, '\\|');
    });
    return '| ' + cells.join(' | ') + ' |';
  });
  
  return [headerLine, separatorLine, ...dataLines].join('\n');
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
  detectWorkspaceMode,
  parseIndexTable,
  generateIndexTable,
  parseFrontmatter,
  extractBody
};
