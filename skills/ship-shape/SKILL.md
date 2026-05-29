---
name: ship-shape
description: "ShipKit pre-Define stage. Produces design system tokens, HTML wireframe prototypes, and multi-variant design directions when no external UIUX materials exist. Use when feature has UI but no Figma/prototype/design."
---

# UIUX 原型设计 (Design Shaping)

## Overview

UIUX 原型设计是开发工作流的条件性前置阶段，在无外部设计稿时产出**设计系统 + HTML 原型 + 多方案变体**，质量足以让 `ship-define` 把 UIUX 部分当作"已有材料"解析。

核心目标：
- 产出可在浏览器中查看的 HTML 线框原型，而非纯文字描述
- 声明设计系统（token-as-code），为后续 `ship-frontend-design` 提供机器可读的设计约束
- 提供 3+ 设计变体（保守到大胆光谱），帮助用户做出视觉方向决策
- 严格遵守 Anti-Slop 纪律，避免 AI 生成的通用视觉套路

## When to Use

- `product-brief.md` 已 ready（来自 ship-discover）
- feature 涉及 UI（有页面、组件、交互）
- 用户未提供外部 UIUX 材料（无 Figma/Sketch/墨刀/设计稿）
- orchestrator 判定需要进入 ship-shape

## When NOT to Use

- 用户已提供 Figma/原型/UIUX 设计稿——直接进 `ship-define`
- feature 是纯后端/CLI/API，无 UI——跳过本阶段
- `project_scope = backend_only`——本阶段自动跳过，orchestrator 将 `stages.ship-shape.status = skipped`
- fast-track 模式下——默认跳过，UI 由 build 阶段现场处理
- 用户明确说"不需要设计，直接开始"——尊重用户意图

## Process

```
┌─────────────────────────────────────────────────────────────┐
│                  UIUX 原型设计流程                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 读取 product-brief.md，提取 UI 相关信息                   │
│       │                                                     │
│       ▼                                                     │
│  2. 设计方向探索 (Design Direction Advisor)                   │
│       │                                                     │
│       ▼                                                     │
│  3. 声明 Visual System (token-as-code)                       │
│       │                                                     │
│       ▼                                                     │
│  4. 页面清单与用户流程                                         │
│       │                                                     │
│       ▼                                                     │
│  5. 产出 HTML 线框原型 (3+ 变体)                              │
│       │                                                     │
│       ▼                                                     │
│  6. 浏览器验证                                               │
│       │                                                     │
│       ▼                                                     │
│  7. 用户选定方向 → 编写 design-brief.md                       │
│       │                                                     │
│       ▼                                                     │
│  8. Anti-Slop Self-Check                                    │
│       │                                                     │
│       ▼                                                     │
│  9. stage_status: ready                                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Step 2: Design Direction Advisor

当 product-brief 的视觉方向不明确时，从 10 种设计语言中挑 3 个**不同流派**的方向：

**设计语言库（5 学派 × 2 流派）：**

| 学派 | 流派 A | 流派 B |
|------|--------|--------|
| 结构现代主义 | Swiss Editorial（瑞士国际风格） | Bauhaus Geometric（包豪斯几何） |
| 安静极简 | Kenya Hara "Emptiness"（原研哉空白美学） | Dieter Rams Industrial（迪特·拉姆斯工业设计） |
| 编辑叙事 | Magazine Editorial（杂志编辑排版） | Zine / Risograph（独立出版/孔版印刷） |
| 动态数字原生 | Field.io Motion Poetics（动态诗学） | Brutalist Web（野兽派网页） |
| 表现实验 | Sagmeister Experimental（实验表现主义） | Y2K / Futurist-Retro（千禧未来复古） |

每个方向呈现：
- 一句话 pitch
- 旗舰参考（知名产品/网站）
- 3 个关键词
- 对本项目意味着什么（一句话）

用户选定方向后（或混合多个方向），进入下一步。

### Step 3: Visual System Declaration

声明设计系统，采用 design.md 的双层思想（YAML 机器可读 + Markdown 人类可读）：

```yaml
tokens:
  colors:
    primary: "#..."
    primary_hover: "#..."
    secondary: "#..."
    surface: "#..."
    surface_elevated: "#..."
    on_surface: "#..."
    on_primary: "#..."
    border: "#..."
    error: "#..."
    success: "#..."
  typography:
    heading:
      fontFamily: "..."
      weights: [400, 600, 700]
      scale: [14, 16, 20, 24, 32, 40, 48]
    body:
      fontFamily: "..."
      weights: [400, 500]
      scale: [12, 14, 16, 18]
    mono:
      fontFamily: "..."
  spacing:
    unit: 8
    scale: [4, 8, 12, 16, 24, 32, 48, 64, 96]
  radii: [0, 4, 8, 12, 16, 9999]
  elevation:
    - "0 1px 2px rgba(0,0,0,0.05)"
    - "0 4px 8px rgba(0,0,0,0.1)"
    - "0 8px 24px rgba(0,0,0,0.15)"
  breakpoints:
    mobile: 375
    tablet: 768
    desktop: 1280
```

每个 token 组附 Markdown 旁注说明 rationale（为什么选这个值、与设计方向的关系）。

### Step 4: 页面清单与用户流程

基于 product-brief 的范围，列出：
- 所有页面/视图（名称 + 用途 + 关联的 Must Have 功能）
- 主流程（用户完成核心任务的步骤序列）
- 关键备选路径（错误处理、空状态、权限不足等）

### Step 5: HTML 线框原型

产出至少 3 个变体，覆盖保守到大胆光谱：

**变体命名规范：**
- `variant-conservative.html`：安全、熟悉、低风险
- `variant-neutral.html`：平衡、现代、主流
- `variant-bold.html`：大胆、创新、有辨识度

**技术骨架：**
- React 18.3.1 + ReactDOM 18.3.1 + Babel 7.29.0（CDN，带 integrity hash）
- 每个变体一个独立 HTML 入口
- `index.html` 是导航页（变体对比 canvas，并排展示关键页面截图）
- 使用真实占位文案（不用 lorem ipsum）
- 响应式：至少覆盖 mobile (375px) 和 desktop (1280px)

**内容要求：**
- 覆盖 product-brief 中所有 Must Have 功能的关键页面
- 包含主流程的完整交互路径（可点击导航）
- 包含至少 1 个空状态和 1 个错误状态
- 使用 placeholder 图片（灰色色块 + 尺寸标注），不用 AI 生成的假图

### Step 6: 浏览器验证

每个 HTML 变体必须：
- 在真实浏览器中打开
- 控制台无 JS 错误、无 404、无 React warning
- 在 375px 和 1280px 宽度下布局不崩溃
- 主流程可点击走通

### Step 7: Core Asset Protocol（涉及品牌时）

当 product-brief 涉及具体品牌时，强制走资产收集流程：

1. 向用户索要 6 类资产：logo、产品截图、UI 截图、品牌色、字体、设计规范
2. 搜索官方渠道获取缺失资产
3. 验证资产质量（分辨率、版权、品牌一致性）
4. 将结果冻结到 `resource/brand-spec.md`

关键规则：**logo / 产品截图 / UI 截图是一等公民**。颜色和字体是辅助。跳过前者会产出通用结果。

## Anti-Slop Discipline

以下视觉模式**明确禁止**，除非用户主动要求：

| 禁止模式 | 为什么禁止 |
|---------|-----------|
| 渐变 orb/blob 代表"AI"或"创新" | AI 生成的通用视觉隐喻，无信息量 |
| 圆角卡片 + 左侧色条 accent | 过度使用的 dashboard 套路 |
| CSS 画的产品图/设备框 | 应使用真实截图或明确的 placeholder |
| Emoji 作为 bullet/icon | 除非品牌风格明确使用 emoji |
| "3 列特性网格"作为默认页面结构 | 懒惰的信息架构，不思考内容层次 |
| 装饰性渐变背景（无功能意义） | 视觉噪音，分散注意力 |
| 假数据/假统计数字 | 使用明确标注的 placeholder |
| Inter/Roboto/Arial 作为默认字体 | 应根据设计方向选择有辨识度的字体 |
| SVG 剪影代替真实产品图 | 降低可信度 |
| 过度 iconified 的列表 | 不是所有列表都需要图标 |

**Self-Check**：`design-brief.md` 最后一章必须列出本次刻意避免了哪些 AI 套路。

## Delegation Boundary

本阶段只允许**辅助委派**。

允许委派的子任务：
- 素材收集（品牌资产、参考图、竞品截图）
- 参考图分析（提取配色、排版模式）
- Token 提取（从参考图推导 token 值）
- 单个变体的 HTML 草稿（主上下文给出设计系统后）

禁止委派的动作：
- 设计方向选择
- Visual System 最终声明
- 变体筛选与推荐
- `design-brief.md` 的正式定稿
- Anti-Slop Self-Check

## Output: design-brief.md

### Frontmatter

```yaml
---
stage: ship-shape
stage_status: draft  # draft | ready
design_direction: ""              # 选定方向名
variations_count: 0               # 已产出的变体数量（≥3）
wireframe_index_path: "resource/wireframes/index.html"
asset_protocol_invoked: false     # 是否走了 Core Asset Protocol
brand_spec_path: ""               # 走了的话，resource/brand-spec.md
updated_at: ""
evidence_complete: false
---
```

### 章节结构

#### 1. 设计方向与理由
- 选定流派名称与 pitch
- 被否决的备选方向及原因
- 对本项目的具体含义

#### 2. Visual System Declaration
- YAML token 块（完整，可被 ship-frontend-design 直接引用）
- 每组 token 的 Markdown rationale

#### 3. 页面清单
- 每页：名称、用途、关联的 Must Have 功能、关键状态（正常/空/错误/加载）

#### 4. 用户流程
- 主流程（步骤序列，标注页面跳转）
- 关键备选路径

#### 5. 线框索引
- 指向 `resource/wireframes/` 下各变体的链接
- 每个变体一句话描述其设计取向

#### 6. 交互注释
- Hover/Active 状态策略
- 过渡动画策略（有/无/轻量）
- 响应式断点策略

#### 7. 可访问性基线
- 对比度目标（WCAG AA 4.5:1 / AAA 7:1）
- 焦点管理策略
- 屏幕阅读器关键路径

#### 8. Anti-Slop Self-Check
- 本次刻意避免的 AI 套路清单
- 每项附"替代方案是什么"

## Output: resource/wireframes/

```text
resource/wireframes/
├── index.html                    # 变体导航页（并排对比 canvas）
├── variant-conservative.html     # 保守变体
├── variant-neutral.html          # 中性变体
├── variant-bold.html             # 大胆变体
└── shared/                       # 共享资源（如有）
    ├── reset.css
    └── tokens.css                # 从 design-brief token 生成的 CSS 变量
```

## Exit Condition

- `design-brief.md.stage_status: ready`
- 至少 3 个 HTML 变体在浏览器中验证通过（控制台干净、布局不崩）
- 用户在变体中选定了主方案（写入 `design_direction`）
- Anti-Slop Self-Check 已完成

## Transition Rules

- 完成后进入 `ship-define`
- `ship-define` 将 `design-brief.md` + `resource/wireframes/` 视为等同 Figma/原型的输入材料
- `ship-frontend-design` 阶段可引用 `design-brief.md` 中的 Visual System token 作为设计约束起点
