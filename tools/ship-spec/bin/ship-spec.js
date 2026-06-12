#!/usr/bin/env node

const { Command } = require('commander');
const program = new Command();

program
  .name('ship-spec')
  .description('ShipKit 规范管理工具 - 管理 .docs/spec 知识库')
  .version('1.0.0')
  .addHelpText('after', `
示例:
  # 初始化单项目
  $ ship-spec init --template standard
  
  # 初始化多项目
  $ ship-spec init --workspace multi --projects web,api
  
  # 创建规范
  $ ship-spec create api-standard -t backend -d "REST API 规范"
  
  # 列出规范
  $ ship-spec list --project web --stage design --format json
  
  # 加载规范内容
  $ ship-spec load api-standard --content-only
  
  # 验证规范
  $ ship-spec validate --all
  
更多信息: https://github.com/shipkit/spec-cli
`);

  program
  .command('init')
  .description('初始化规范目录')
  .option('--template <name>', '模板：minimal | standard | comprehensive', 'standard')
  .option('--workspace <mode>', '工作空间模式：single | multi')
  .option('--projects <projects>', '项目列表（逗号分隔）')
  .action(async (options) => {
    const { initCommand } = require('../src/commands/init');
    await initCommand(options);
  });

program
  .command('create <spec-id>')
  .description('创建新规范')
  .option('-p, --project <projects>', '适用项目（逗号分隔）')
  .option('-t, --type <type>', '规范类型：frontend | backend | shared')
  .option('-s, --stages <stages>', '适用阶段（逗号分隔）', 'design,build')
  .option('-d, --description <desc>', '规范描述')
  .action(async (specId, options) => {
    const { createCommand } = require('../src/commands/create');
    await createCommand(specId, options);
  });

program
  .command('list')
  .description('列出规范')
  .option('-p, --project <project>', '过滤项目')
  .option('-s, --stage <stage>', '过滤阶段')
  .option('-f, --format <format>', '输出格式：table | json', 'table')
  .action(async (options) => {
    const { listCommand } = require('../src/commands/list');
    await listCommand(options);
  });

program
  .command('load <spec-id>')
  .description('加载规范内容')
  .option('-f, --format <format>', '输出格式：json | yaml', 'json')
  .option('--content-only', '只输出正文')
  .option('--frontmatter-only', '只输出 frontmatter')
  .action(async (specId, options) => {
    const { loadCommand } = require('../src/commands/load');
    await loadCommand(specId, options);
  });


program
  .command('validate')
  .description('验证规范')
  .argument('[spec-id]', '规范 ID（留空验证所有）')
  .option('--all', '验证所有规范')
  .action(async (specId, options) => {
    const { validateCommand } = require('../src/commands/validate');
    await validateCommand(specId, options);
  });

program.parse(process.argv);
