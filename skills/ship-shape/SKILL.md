---
name: ship-shape
description: "Optional Ship support skill for UI/UX shaping. Use for UI tasks without sufficient design direction, screenshots, or prototypes; produces lightweight design direction, states, and optional HTML wireframes."
---

# Ship Shape

`ship-shape` 是支持 skill，不是默认 runtime stage。它只在 UI 任务需要视觉/交互方向时插入。

## Use When

- 用户要做页面、组件、dashboard、landing、交互改造。
- 没有 Figma/截图/原型，或现有材料不足以实现。
- 需要比较 2-3 个设计方向。

## Process

1. 读取 `brief.md` 和现有 UI 代码/截图（如有）。
2. 提出 2-3 个差异明确的方向，并推荐一个。
3. 定义页面状态：default、loading、empty、error、success、permission。
4. 必要时产出 HTML wireframe 或静态原型。
5. 把选定方向写成可供 `ship-contract` / `ship-build` 消费的 UI evidence。

## Output

- `resource/ui-shape.md`
- 可选：`resource/wireframes/index.html`

## Boundaries

- 不替代 `ship-define` 的需求澄清。
- 不在没有用户确认的情况下把大胆视觉方向当成最终设计。
- 不使用通用 AI slop：无意义渐变、emoji bullets、模板化卡片堆叠。
