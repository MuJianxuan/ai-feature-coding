const fs = require('fs');
const { detectWorkspaceMode, parseIndexTable } = require('../core/parser');

async function listCommand(options) {
  if (!fs.existsSync('.docs/spec/INDEX.md')) {
    console.error('错误：INDEX.md 不存在');
    process.exit(1);
  }
  
  const workspace = detectWorkspaceMode();
  const content = fs.readFileSync('.docs/spec/INDEX.md', 'utf8');
  let specs = parseIndexTable(content);
  
  // 多项目模式下应用项目过滤
  if (workspace.mode === 'project_group' && options.project) {
    specs = specs.filter(s => 
      s.projects.includes(options.project) || s.projects.includes('all')
    );
  }
  
  // 应用阶段过滤
  if (options.stage) {
    specs = specs.filter(s => s.stages.includes(options.stage));
  }
  
  // 输出
  if (options.format === 'json') {
    console.log(JSON.stringify({
      total: specs.length,
      filters: { project: options.project, stage: options.stage },
      results: specs
    }, null, 2));
  } else {
    console.log('SPEC_ID\t\tFILE\t\tPROJECTS\t\tSTAGES\t\tDESCRIPTION');
    specs.forEach(s => {
      console.log(`${s.spec_id}\t${s.file}\t${s.projects.join(',')}\t${s.stages.join(',')}\t${s.description}`);
    });
  }
}

module.exports = { listCommand };
