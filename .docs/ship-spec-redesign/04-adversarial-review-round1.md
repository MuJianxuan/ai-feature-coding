# 对抗式审查报告 Round 1

## 审查方法论

对 ship-spec 技能改造方案进行 6 个维度的审查：
1. **职责边界模糊性**：是否存在职责不清的灰色地带
2. **实现复杂度**：是否过度设计或遗漏关键细节
3. **集成可行性**：其他技能如何实际使用
4. **性能和扩展性**：大规模场景下的表现
5. **错误处理和降级**：失败场景的鲁棒性
6. **用户体验**：开发者实际使用时的痛点

---

## 1. 职责边界模糊性 ⚠️

### 问题 1.1：existing-features 的归属争议
**发现**：`update-existing-features` 命令由 ship-spec 提供，但调用时机在 ship-build 完成后。

**质疑**：
- ship-build 如何知道要调用 ship-spec？
- 如果 ship-build 忘记调用会怎样？
- existing-features 到底是"规范"还是"构建产物"？

**建议**：
```markdown
选项 A（推荐）：ship-build 负责更新 existing-features
- ship-spec 只管理"规范模板"
- ship-build 完成后直接写入 existing-features.md
- ship-spec 的 sync-index 会自动发现更新

选项 B：引入构建钩子
- ship-build 完成时触发 post-build hook
- 钩子自动调用 ship-spec update-existing-features
- 减少手动调用的遗漏风险

选项 C：existing-features 独立出去
- 不作为 spec，而是独立的 .docs/features/ 目录
- 由专门的 features-index 命令管理
```

### 问题 1.2：规范验证的责任分散
**发现**：ship-spec 有 `validate` 命令验证规范完整性，但其他技能如何确保自己读到的规范是有效的？

**质疑**：
- ship-design 读取规范后，是否需要自己再验证一次？
- 如果规范文件被手动编辑破坏了，谁负责检测？
- validate 应该在何时强制执行？

**建议**：
```markdown
引入规范版本号和校验和：
- .index.json 包含每个规范的 file_hash
- 其他技能读取时验证 hash 是否匹配
- 不匹配时警告并触发 sync-index

CI/CD 集成：
- pre-commit hook 自动运行 validate
- PR 检查强制要求 validate 通过
- 阻止破损规范进入主分支
```

---

## 2. 实现复杂度 🔴

### 问题 2.1：.index.json 和 INDEX.md 双重维护
**发现**：同时维护两个索引文件，容易不一致。

**质疑**：
- 为什么需要两个文件？
- INDEX.md 手动编辑后如何同步到 .index.json？
- 如果只保留 .index.json，人类可读性如何保证？

**建议**：
```markdown
方案 A（推荐）：INDEX.md 为唯一真实来源
- .index.json 始终从 INDEX.md 生成，不单独维护
- 解析 INDEX.md 的表格生成 .index.json
- 所有写操作都写 INDEX.md，然后重建 .index.json

方案 B：.index.json 为唯一真实来源
- INDEX.md 只是渲染视图，从 .index.json 生成
- 提供 Web UI 或 TUI 编辑 .index.json
- 自动生成 INDEX.md 供浏览

方案 C：合并为单一格式
- 使用 YAML frontmatter + Markdown 内容
- 人类可读，机器可解析
- 类似 Jekyll 的方案
```

### 问题 2.2：搜索索引构建成本
**发现**：每次更新规范都要重建 .index.json，包括提取 sections、keywords、links 等。

**质疑**：
- 大型项目（100+ 规范文件）的索引构建耗时？
- 增量更新是否真的高效？
- 索引损坏后的恢复机制？

**建议**：
```markdown
性能优化：
1. 懒加载：首次搜索时才构建索引
2. 后台异步重建：不阻塞主流程
3. 索引版本控制：支持回滚到上一个好的索引

索引分片：
- 按项目分片（web/.index.json, api/.index.json）
- 按类型分片（frontend/.index.json, backend/.index.json）
- 查询时合并分片结果

简化索引内容：
- sections/keywords/links 是否真的必需？
- 先实现基础索引（spec_id + description + metadata）
- 高级特性（全文索引）作为 V2 特性
```

### 问题 2.3：suggest-new-spec 的实现模糊
**发现**：自动识别重复模式、评分规则，缺少具体算法。

**质疑**：
- "自动识别重复模式"如何实现？需要 NLP？
- 评分规则如何量化"模式稳定性"？
- 误报率多高？开发者会信任建议吗？

**建议**：
```markdown
MVP 简化版：
- 只统计显式标记的模式引用
- 开发者手动标记：`<!-- @pattern: api-naming -->`
- 达到阈值时提示沉淀

V2 智能版：
- 基于 AST 分析代码结构相似度
- 使用 LLM 识别命名模式、数据结构模式
- 提供"试运行"模式，不直接创建规范

V3 学习版：
- 记录开发者的接受/拒绝反馈
- 调整评分权重
- 个性化建议
```

---

## 3. 集成可行性 ⚠️

### 问题 3.1：其他技能的学习成本
**发现**：每个技能都需要自己读取 INDEX.md、解析、过滤、加载规范。

**质疑**：
- 是否每个技能都要实现相同的解析逻辑？
- 如何保证所有技能的过滤逻辑一致？
- 新技能如何快速集成？

**建议**：
```markdown
提供官方 SDK：
// skills/ship-spec/sdk.js
export class SpecLoader {
  constructor(options) {
    this.project = options.project;
    this.stage = options.stage;
  }
  
  async load(specId) { /* ... */ }
  async search(query) { /* ... */ }
  async filter(criteria) { /* ... */ }
}

// 其他技能使用
import { SpecLoader } from './ship-spec/sdk.js';
const loader = new SpecLoader({ project: 'web', stage: 'design' });
const specs = await loader.search('api');
```

**或者提供通用辅助命令**：
```bash
# ship-spec 提供 load 命令，返回过滤后的规范
ship-spec load --stage design --project web --spec-ids api-standard,naming
# 输出 JSON，其他技能直接使用
```

### 问题 3.2：循环依赖风险
**发现**：ship-spec 依赖 feature meta.yml 来确定项目范围，但 meta.yml 可能依赖规范模板。

**质疑**：
- 创建新 feature 时，如何知道要用哪些规范？
- feature 模板是否应该引用规范？
- 如何避免"需要规范才能创建 feature，需要 feature 才能更新规范"的死锁？

**建议**：
```markdown
明确依赖方向：
feature meta.yml → 引用规范（读操作，无循环）
ship-spec ← 读取 meta.yml（只为了确定项目）
ship-spec ← 更新 existing-features（写操作）

启动流程：
1. 初始化项目时，先创建基础规范（无需 feature）
2. 创建 feature 时，读取现有规范
3. 完成 feature 后，更新 existing-features
```

---

## 4. 性能和扩展性 🔴

### 问题 4.1：全文搜索的性能瓶颈
**发现**：全文搜索需要读取所有候选规范文件。

**质疑**：
- 100 个规范文件，每个 5KB，全文搜索耗时？
- 并行读取是否会触发文件系统限制？
- 搜索结果缓存的失效策略是否合理？

**测试场景**：
```
项目规模：150 个规范文件，总计 800KB
搜索频率：每分钟 10 次（开发高峰期）
缓存策略：60 秒 TTL

预期性能：
- 元数据搜索：< 50ms（从 .index.json）
- 全文搜索：< 500ms（并行读取）
- 缓存命中率：> 70%

压力测试：
- 1000 次搜索，99th percentile < 1s
- 内存占用 < 100MB
```

**优化建议**：
```markdown
1. 提前终止：找到 N 个结果后停止搜索
2. 布隆过滤器：快速排除不包含关键词的文件
3. 倒排索引：构建完整的全文倒排索引（V2 特性）
```

### 问题 4.2：多项目模式的扩展性
**发现**：多项目模式下，_shared + 多个项目目录，文件分散。

**质疑**：
- 10 个项目时，目录结构会不会太深？
- 项目间的规范复用如何管理？
- 项目重命名、合并、拆分时的迁移成本？

**建议**：
```markdown
引入规范命名空间：
.docs/spec/
├── @shared/
├── @web/
├── @api/
└── @mobile/

或使用标签而非目录：
所有规范平铺在 .docs/spec/
通过 frontmatter.projects 标记归属
INDEX.md 按项目分组显示
```

---

## 5. 错误处理和降级 ⚠️

### 问题 5.1：INDEX.md 损坏的恢复
**发现**：如果 INDEX.md 被意外删除或格式破坏，系统如何恢复？

**质疑**：
- `sync-index` 能否从零重建 INDEX.md？
- 如果规范文件缺少 frontmatter，如何推断元数据？
- 部分损坏 vs 完全丢失的处理策略？

**建议**：
```markdown
自动恢复机制：
1. 检测到 INDEX.md 损坏时，自动备份到 .index.md.bak
2. 从规范文件的 frontmatter 重建 INDEX.md
3. 缺失 frontmatter 时，使用启发式规则：
   - spec_id 从文件名推断
   - projects 从目录路径推断（web/ → ['web']）
   - stages 默认为 ['design', 'build']

验证和修复命令：
ship-spec doctor
- 检查所有规范文件
- 报告缺失字段、格式错误
- 提供一键修复选项
```

### 问题 5.2：规范文件冲突
**发现**：多人协作时，同时编辑同一规范文件会导致 git 冲突。

**质疑**：
- 规范文件的合并策略？
- 如何避免覆盖他人的更新？
- 是否需要文件锁定机制？

**建议**：
```markdown
Git 友好设计：
1. 规范文件采用追加式结构（章节独立）
2. 提供规范片段（snippets）机制，多人编辑不同片段
3. 冲突时提供 merge 工具

乐观锁：
- 更新时检查 last_modified 时间戳
- 不匹配时警告用户，提供 diff 和 merge 选项
```

### 问题 5.3：规范依赖的循环检测
**发现**：规范 A 依赖 B，B 依赖 C，C 依赖 A，形成循环。

**质疑**：
- 创建/更新规范时是否检测循环依赖？
- 循环依赖是否应该完全禁止？
- 如何提示用户修复？

**建议**：
```markdown
依赖图验证：
// validate 命令包含循环检测
function detectCycles(specs) {
  const graph = buildDependencyGraph(specs);
  const cycles = findCycles(graph);
  
  if (cycles.length > 0) {
    return {
      valid: false,
      errors: cycles.map(cycle => ({
        type: 'circular_dependency',
        message: `Circular dependency detected: ${cycle.join(' → ')}`,
        specs: cycle
      }))
    };
  }
}

警告等级：
- 直接循环（A → B → A）：ERROR，阻塞操作
- 间接循环（A → B → C → A）：WARNING，允许但提示
```

---

## 6. 用户体验 🔴

### 问题 6.1：命令接口的一致性
**发现**：命令参数风格不统一。

**示例**：
```bash
ship-spec create-spec --spec-id xxx --type backend
ship-spec search "query" --stage design
ship-spec update-spec --spec-id xxx --operation append
```

**质疑**：
- 为什么有时用 `--spec-id`，有时直接位置参数？
- 为什么 search 的 query 是位置参数，其他是选项？
- 如何保证命令行和 API 调用的参数一致？

**建议**：
```markdown
统一参数风格：
ship-spec create <spec-id> [options]
ship-spec update <spec-id> [options]
ship-spec delete <spec-id> [options]
ship-spec search <query> [options]
ship-spec validate [spec-id] [options]

常用选项简写：
-p, --project
-s, --stage
-t, --type
-f, --format
```

### 问题 6.2：错误信息的可操作性
**发现**：错误信息描述不清，缺少修复建议。

**坏例子**：
```
Error: Spec validation failed
```

**好例子**：
```
Error: Spec validation failed for 'rest-api-standard'
  
  Missing required field: description
  Location: backend/rest-api-standard.md:1
  
  Fix:
  Add the following frontmatter to the file:
  ---
  spec_id: rest-api-standard
  description: "Your description here"
  ---
```

**建议**：
```markdown
错误信息模板：
1. 明确的错误类型和位置
2. 具体的错误原因
3. 可操作的修复建议
4. 相关文档链接

交互式修复：
ship-spec validate --fix
# 自动修复可自动修复的问题
# 交互式询问需要人工决策的问题
```

### 问题 6.3：首次使用体验
**发现**：新项目如何快速启动 ship-spec？

**质疑**：
- 是否提供 `ship-spec init` 命令？
- 默认创建哪些规范模板？
- 如何引导用户填充第一个规范？

**建议**：
```markdown
ship-spec init [--template <name>]

初始化流程：
1. 检测项目类型（通过 package.json, pom.xml 等）
2. 询问 workspace 模式（单项目 vs 多项目）
3. 创建目录结构和 INDEX.md
4. 根据项目类型生成初始规范：
   - Web 项目：frontend patterns, API standard
   - 后端项目：API standard, database conventions
   - 全栈项目：两者都有
5. 生成 README 说明如何使用

模板选择：
--template minimal：最少规范
--template standard：常用规范
--template comprehensive：全套规范
```

---

## 严重程度总结

### 🔴 必须修复（阻塞发布）
1. **INDEX.md 和 .index.json 双重维护**：选择唯一真实来源
2. **suggest-new-spec 实现模糊**：简化为 MVP 版本或推迟到 V2
3. **全文搜索性能**：提供性能基准测试
4. **错误信息质量**：改进为可操作的错误提示

### ⚠️ 应该改进（影响体验）
1. **existing-features 归属**：明确调用职责
2. **规范验证时机**：集成到 CI/CD
3. **其他技能集成**：提供 SDK 或辅助命令
4. **错误恢复机制**：实现 `ship-spec doctor`
5. **首次使用体验**：提供 `ship-spec init`

### ✅ 可接受（后续优化）
1. 搜索结果缓存策略
2. 多项目模式的命名空间
3. 依赖循环检测
4. 命令参数简写

---

## 改进方案建议

基于审查结果，建议分阶段实施：

### Phase 1: MVP（核心功能）
- ✅ INDEX.md 为唯一真实来源，.index.json 自动生成
- ✅ 基础 CRUD：create/update/delete
- ✅ 元数据搜索（不含全文搜索）
- ✅ 简单的 validate（必需字段检查）
- ✅ ship-spec init 初始化命令
- ✅ 明确的错误信息

### Phase 2: 增强（提升体验）
- ✅ 全文搜索（with 性能测试）
- ✅ ship-spec doctor 自动修复
- ✅ SDK 供其他技能使用
- ✅ existing-features 自动更新机制
- ✅ 依赖循环检测

### Phase 3: 高级（智能化）
- ✅ suggest-new-spec 智能建议
- ✅ 规范版本管理
- ✅ 搜索建议和自动补全
- ✅ Web UI 规范管理界面

---

下一步：根据审查结果调整设计方案。
