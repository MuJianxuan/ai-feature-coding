const fs = require('fs');
const path = require('path');
const yaml = require('yaml');
const { parseIndexTable, parseFrontmatter, extractBody } = require('../core/parser');

async function loadCommand(specId, options) {
  if (!fs.existsSync('.docs/spec/INDEX.md')) {
    console.error('错误：INDEX.md 不存在');
    process.exit(1);
  }
  
  const indexContent = fs.readFileSync('.docs/spec/INDEX.md', 'utf8');
  const specs = parseIndexTable(indexContent);
  
  const spec = specs.find(s => s.spec_id === specId);
  if (!spec) {
    console.error(`错误：规范不存在: ${specId}`);
    process.exit(1);
  }
  
  const filePath = path.join('.docs/spec', spec.file);
  if (!fs.existsSync(filePath)) {
    console.error(`错误：规范文件不存在: ${filePath}`);
    process.exit(1);
  }
  
  const content = fs.readFileSync(filePath, 'utf8');
  const frontmatter = parseFrontmatter(content);
  const body = extractBody(content);
  
  if (options.contentOnly) {
    console.log(content);
  } else if (options.frontmatterOnly) {
    console.log(JSON.stringify(frontmatter, null, 2));
  } else if (options.format === 'yaml') {
    const output = { ...spec, frontmatter, content, body };
    console.log(yaml.stringify(output));
  } else if (options.format === 'json') {
    console.log(JSON.stringify({
      ...spec,
      frontmatter,
      content,
      body
    }, null, 2));
  } else {
    console.log(content);
  }
}

module.exports = { loadCommand };
