const fs = require('fs');
const path = require('path');
const { parseIndexTable, parseFrontmatter } = require('../core/parser');

async function validateCommand(specId, options) {
  if (!fs.existsSync('.docs/spec/INDEX.md')) {
    console.error('错误：INDEX.md 不存在');
    process.exit(1);
  }
  
  const indexContent = fs.readFileSync('.docs/spec/INDEX.md', 'utf8');
  const specs = parseIndexTable(indexContent);
  
  let errors = 0;
  let warnings = 0;
  
  const specsToValidate = specId ? specs.filter(s => s.spec_id === specId) : specs;
  
  if (specsToValidate.length === 0) {
    console.error(`错误：未找到规范 ${specId}`);
    process.exit(1);
  }
  
  for (const spec of specsToValidate) {
    const filePath = path.join('.docs/spec', spec.file);
    
    // 检查文件存在性
    if (!fs.existsSync(filePath)) {
      console.error(`❌ ${spec.spec_id}: 文件不存在 ${filePath}`);
      errors++;
      continue;
    }
    
    // 检查 frontmatter
    const content = fs.readFileSync(filePath, 'utf8');
    const frontmatter = parseFrontmatter(content);
    
    // 检查 frontmatter 格式完整性
    const matches = content.match(/^---$/gm);
    if (matches && matches.length !== 2) {
      console.warn(`⚠️  ${spec.spec_id}: frontmatter 格式异常（--- 标记数量不匹配）`);
      warnings++;
    }
    
    // 检查 frontmatter 格式
    const frontmatterMatch = content.match(/^---\n[\s\S]*?\n---/);
    if (frontmatterMatch && content.indexOf('---', frontmatterMatch[0].length) !== -1) {
      console.warn(`⚠️  ${spec.spec_id}: frontmatter 后可能有异常内容`);
      warnings++;
    }
    
    if (!frontmatter) {
      console.error(`❌ ${spec.spec_id}: 缺少 frontmatter`);
      errors++;
      continue;
    }
    
    // 检查必需字段
    if (!frontmatter.spec_id) {
      console.error(`❌ ${spec.spec_id}: frontmatter 缺少 spec_id`);
      errors++;
    }
    
    if (frontmatter.spec_id !== spec.spec_id) {
      console.warn(`⚠️  ${spec.spec_id}: frontmatter 中的 spec_id 与 INDEX.md 不一致`);
      warnings++;
    }
    
    if (!frontmatter.description) {
      console.warn(`⚠️  ${spec.spec_id}: 缺少 description`);
      warnings++;
    }
    
    console.log(`✅ ${spec.spec_id}: 验证通过`);
  }
  
  console.log(`\n验证完成: ${specsToValidate.length} 个规范, ${errors} 个错误, ${warnings} 个警告`);
  
  if (errors > 0) {
    process.exit(1);
  }
}

module.exports = { validateCommand };
