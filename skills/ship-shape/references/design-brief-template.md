---
stage: ship-shape
stage_status: draft
activation_mode: default_discover_shape  # default_discover_shape | uiux_material_gate_insert
uiux_gate_user_sign_off: ""
uiux_gate_signed_at: ""
browser_verified: false
browser_verified_at: ""
design_direction: ""
variations_count: 0
wireframe_index_path: "resource/wireframes/index.html"
asset_protocol_invoked: false
brand_spec_path: ""
updated_at: ""
evidence_complete: false
soft_gate_class: soft_optional
blocking_gaps: []
---

# 设计简报：[功能名称]

> 本文档由 ship-shape 阶段产出，为 ship-define 提供 UIUX 材料，为 ship-frontend-design 提供设计系统约束。
> 模板使用说明：删除所有以 `>` 开头的注释行。

## 1. 设计方向与理由

### 选定方向：[方向名]

**Pitch：**

**旗舰参考：**

**关键词：**

**对本项目的含义：**

### 被否决的方向

> 保留 2 个备选方向及否决原因。

#### [方向 B 名称]
- 否决原因：

#### [方向 C 名称]
- 否决原因：

## 2. Visual System Declaration

### Design Tokens

```yaml
tokens:
  colors:
    primary: "#"
    primary_hover: "#"
    secondary: "#"
    surface: "#"
    surface_elevated: "#"
    on_surface: "#"
    on_primary: "#"
    border: "#"
    error: "#"
    success: "#"
    warning: "#"
  typography:
    heading:
      fontFamily: ""
      weights: [400, 600, 700]
      scale: [14, 16, 20, 24, 32, 40, 48]
    body:
      fontFamily: ""
      weights: [400, 500]
      scale: [12, 14, 16, 18]
    mono:
      fontFamily: ""
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

### Rationale

> 每组 token 的设计理由。

**Colors：**

**Typography：**

**Spacing：**

**Radii & Elevation：**

## 3. 页面清单

| 页面名 | 用途 | 关联 Must Have | 关键状态 |
|--------|------|---------------|---------|
| | | | 正常/空/错误/加载 |
| | | | |

## 4. 用户流程

### 主流程

> 用户完成核心任务的步骤序列。

```
[页面 A] → 操作 → [页面 B] → 操作 → [页面 C]
```

### 关键备选路径

> 错误处理、空状态、权限不足等。

-

## 5. 线框索引

| 变体 | 文件 | 设计取向 |
|------|------|---------|
| Conservative | `resource/wireframes/variant-conservative.html` | |
| Neutral | `resource/wireframes/variant-neutral.html` | |
| Bold | `resource/wireframes/variant-bold.html` | |

## 6. 交互注释

### Hover / Active 状态

>

### 过渡动画

> 有/无/轻量，具体策略。

### 响应式断点策略

> mobile-first / desktop-first，各断点的布局变化。

## 7. 可访问性基线

| 项目 | 目标 |
|------|------|
| 文字对比度 | WCAG AA (4.5:1) |
| 焦点指示器 | 可见、高对比 |
| 键盘导航 | 主流程可完整走通 |
| 屏幕阅读器 | 关键操作有 aria-label |

## 用户确认记录

| 确认项 | 用户原话/证据 | 时间 |
|---|---|---|
| UIUX Gate 授权（B/D only） |  |  |
| 设计方向选择 |  |  |
| 浏览器验证结果确认 |  |  |

## 8. Anti-Slop Self-Check

> 列出本次刻意避免的 AI 套路，每项附替代方案。

| 避免的套路 | 替代方案 |
|-----------|---------|
| | |
| | |
