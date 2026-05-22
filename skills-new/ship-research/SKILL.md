---
name: ship-research
description: "ShipKit stage. Researches latest technical information using source-driven approach. Use after ship-intake-review gate passes."
---

# 技术调研 (Tech Research)

## Overview

本阶段基于 requirements.md 中明确的技术需求，通过 Source-Driven 模式获取最新、可靠的技术信息。核心原则：**不依赖训练数据中的过时信息，一切结论必须有可追溯来源**。

产出物：`tech-research.md`

## When to Use

- requirements.md 已通过 `ship-intake-review` gate
- 需要评估新技术栈、框架、库的适用性
- 需要确认技术方案的可行性和最新状态
- 项目涉及不熟悉的技术领域

## When NOT to Use

- requirements.md 尚未完成或未通过评审
- 技术栈已确定且无需调研（纯业务逻辑变更）
- 仅涉及已有项目内部代码重构，无新技术引入

## Source-Driven Protocol

### DETECT（识别调研点）

从 requirements.md 提取需要调研的技术关注点：

1. 读取 requirements.md 中的技术约束和非功能需求
2. 识别所有涉及的技术领域（语言/框架/数据库/基础设施/第三方服务）
3. 列出每个领域需要回答的关键问题
4. 确定调研优先级（P0: 阻塞性选型 / P1: 重要但有备选 / P2: 锦上添花）

### FETCH（获取信息）

针对每个调研点，按优先级获取信息：

1. **官方文档**：框架/库的官方网站、API 文档
2. **Release Notes**：最新版本的变更日志、升级指南
3. **GitHub Repository**：star 数、最近提交频率、issue 活跃度
4. **官方博客/公告**：路线图、废弃计划、重大变更预告
5. **Package Registry**：npm/PyPI/Maven Central 上的下载量和版本历史

工具使用优先级：
- `mcp__context7` — 获取库的最新文档和代码示例（首选，权威性高）
- `mcp__tavily__tavily_search` — 搜索最新版本信息和社区动态
- `mcp__tavily__tavily_extract` — 提取官方文档页面内容
- `mcp__tavily__tavily_crawl` — 批量抓取文档站点（多页面调研）

信息可信度排序（高到低）：
1. 官方文档 / 官方 GitHub Release
2. 官方博客 / 核心维护者发布
3. 主流技术媒体（InfoQ / The New Stack 等）
4. 社区博客 / Stack Overflow 高赞回答
5. AI 训练数据中的旧记忆（最低优先级，必须通过其他来源验证）

### SUMMARIZE（提炼信息）

对每项技术产出结构化摘要：

```markdown
### [技术名称]
- **当前稳定版本**：x.y.z（发布日期）
- **LTS 状态**：是否有长期支持版本
- **关键特性**：与项目需求相关的核心能力
- **适用场景**：官方推荐的使用场景
- **已知限制**：性能瓶颈、兼容性问题、已知 bug
- **学习曲线**：入门难度评估
- **生态系统**：插件/中间件/社区资源丰富度
```

### CITE（标注来源）

每条信息必须附带来源标注：

```markdown
> 来源：[官方文档标题](URL) | 获取时间：YYYY-MM-DD
```

如果无法获取最新信息：

```markdown
> ⚠️ 信息可能过时，需人工确认。最后已知版本：x.y.z（训练数据截止）
```

## Process

```
1. 读取 requirements.md → 提取技术关注点列表
   verify: 关注点列表覆盖所有技术领域，无遗漏
2. 对关注点分级（P0/P1/P2）
   verify: P0 项不超过 5 个，聚焦核心决策
3. 按优先级逐项执行 FETCH
   verify: P0 每项至少 2 个独立来源，P1 至少 1 个官方来源
4. 执行 SUMMARIZE，产出结构化摘要
   verify: 每项摘要字段完整，无空白项
5. 构建对比矩阵（如有多个备选方案）
   verify: 对比维度覆盖非功能需求，至少 5 个维度
6. 评估社区活跃度和生态
   verify: 有量化指标（star/下载量/提交频率/最近提交时间）
7. 分析与项目需求的匹配度
   verify: 逐条对照 requirements.md 非功能需求
8. 汇总信息来源清单
   verify: 所有 URL 已列出，附获取时间
9. 写入 tech-research.md
   verify: frontmatter 完整，章节齐全，无 TODO 遗留
```

### 对比矩阵模板

当同一领域有多个候选方案时，使用以下格式：

```markdown
| 维度 | 方案 A | 方案 B | 方案 C | 权重 |
|------|--------|--------|--------|------|
| 性能 | ... | ... | ... | 高 |
| 生态 | ... | ... | ... | 中 |
| 学习曲线 | ... | ... | ... | 中 |
| 社区活跃度 | ... | ... | ... | 中 |
| 长期维护 | ... | ... | ... | 高 |
| **综合评分** | x/10 | x/10 | x/10 | — |
```

评分标准：
- 9-10：完全满足，无明显短板
- 7-8：基本满足，有小缺陷但可接受
- 5-6：勉强满足，需要额外工作弥补
- 3-4：不太满足，风险较高
- 1-2：不满足，不推荐

## Research Dimensions (调研维度)

每项技术至少覆盖以下维度：

| 维度 | 关注点 | 信息来源 |
|------|--------|----------|
| 成熟度 | 版本号、发布历史、是否 GA | Release Notes |
| 性能 | Benchmark 数据、已知瓶颈 | 官方文档/第三方评测 |
| 安全性 | CVE 历史、安全更新频率 | GitHub Security Advisories |
| 兼容性 | 与现有技术栈的集成难度 | 官方集成指南 |
| 社区 | GitHub stars、npm 下载量、Stack Overflow 活跃度 | 各平台统计 |
| 维护状态 | 最近提交时间、核心维护者数量、是否有商业支持 | GitHub Insights |
| 文档质量 | 文档完整度、示例丰富度、中文文档可用性 | 官方文档站 |
| 许可证 | License 类型、商用限制 | GitHub/npm |

### 健康度判断信号

调研时关注以下"健康度"信号，识别潜在风险：

**正面信号**：
- 最近 90 天内有发布或合并 PR
- Issue 平均响应时间在合理范围（< 14 天）
- 多个核心维护者（避免单点故障）
- 有商业公司或基金会背书
- 完整的迁移指南和废弃说明

**负面信号**：
- 超过 6 个月无提交
- 大量未关闭的关键 issue
- 仅有一个维护者（bus factor = 1）
- README 中有"unmaintained"或"deprecated"声明
- 大量未回复的安全告警

## Output: tech-research.md

```yaml
---
stage: ship-research
stage_status: draft  # draft / ready
updated_at: ""
evidence_complete: false
---
```

### 核心章节

1. **调研范围** — 从 requirements.md 提取的技术关注点清单
2. **技术调研结果** — 每项含：技术名称/当前版本/官方文档链接/关键特性/适用场景/已知限制
3. **框架/库对比矩阵** — 多维度对比表格
4. **社区活跃度和生态评估** — 量化指标 + 定性判断
5. **与项目需求的匹配度分析** — 逐条对照非功能需求
6. **信息来源清单** — 所有引用的 URL，附获取时间

### stage_status 流转规则

- `draft`：调研进行中，信息不完整
- `ready`：所有 P0/P1 调研点已完成，来源已标注，可进入选型阶段

### evidence_complete 判定标准

- 所有 P0 调研点有至少 2 个独立来源
- 所有 P1 调研点有至少 1 个官方来源
- 无"信息可能过时"标注未解决的 P0 项
- 所有引用 URL 已实际访问验证（非凭记忆构造）

### tech-research.md 模板片段

```markdown
## 1. 调研范围

| 关注点 | 优先级 | 关键问题 |
|--------|--------|----------|
| Web 框架 | P0 | 是否支持 SSR？性能如何？ |
| ORM | P0 | 类型安全？迁移工具？ |
| 缓存 | P1 | 集群支持？持久化？ |

## 2. 技术调研结果

### Next.js
- 当前稳定版本：x.y.z
- LTS：N/A（持续滚动更新）
- 关键特性：App Router / Server Components / ...
- 适用场景：...
- 已知限制：...
> 来源：[Next.js Docs](https://nextjs.org/docs) | 获取时间：2026-05-22
```

## Anti-Rationalizations

1. **"我知道这个技术，不需要查"** — 不行。训练数据可能过时，版本可能已更新，API 可能已变更。必须 FETCH 确认。
2. **"官方文档太长了，我概括一下"** — 概括可以，但必须附带原文链接。读者需要能验证你的概括是否准确。
3. **"这个技术很流行，肯定没问题"** — 流行不等于适合。必须验证与项目具体需求的匹配度。
4. **"找不到最新信息，用我知道的版本吧"** — 必须明确标注信息可能过时。不标注等于误导。
5. **"对比太多维度太麻烦"** — 维度不全等于决策依据不足。至少覆盖 Research Dimensions 表中的前 5 项。

## Red Flags

- 调研结果中没有任何 URL 来源 → 信息不可信
- 所有技术都被描述为"优秀"且无缺点 → 调研不客观
- 版本号与官方最新版本不一致 → 信息过时
- 对比矩阵中某项技术所有维度都优于其他 → 可能存在偏见
- 调研范围遗漏了 requirements.md 中明确提到的技术领域 → 覆盖不全

## Verification

完成 tech-research.md 后，执行以下检查：

```
□ 调研范围是否覆盖 requirements.md 所有技术关注点？
□ 每项技术是否有官方文档 URL？
□ 版本信息是否为当前最新稳定版？
□ 对比矩阵维度是否覆盖非功能需求？
□ 是否有未解决的"信息可能过时"标注？
□ 信息来源清单是否完整？
□ evidence_complete 字段是否准确反映当前状态？
```

全部通过后，将 `stage_status` 设为 `ready`。
