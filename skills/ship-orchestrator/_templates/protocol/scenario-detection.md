# Ship Solo Scenario Detection

`ship-orchestrator` 先判断 work mode，再选择最小必要阶段。

## Modes

| Mode | Signals | Default Start |
|---|---|---|
| `feature` | 新功能、MVP、增强 | `ship-discover` / `ship-define` |
| `bugfix` | 报错、失败、回归 | `ship-tech-discovery` |
| `refactor` | 不改变行为、结构调整 | `ship-tech-discovery` |
| `ui` | 页面、组件、交互、视觉 | `ship-define` + optional `ship-shape` |
| `docs` | README、文档、规范 | `ship-define` |
| `release` | 验证、交付、发布说明 | `ship-verify` |

## Compression Rules

- 用户已给清晰目标和 AC：可跳过 `ship-discover`。
- bugfix：brief 可压缩为现象 / 期望 / 复现。
- refactor：contract 写 invariant，不写新功能。
- docs：contract 可写 `contract_forms: [none]` 或跳过。
- UI：无设计方向时调用 `ship-shape`，但不把它写入 runtime stage。

## Safety Rules

- 不能因为 technical plan 存在就直接编码；仍需 repository reality check。
- 不能因为用户说“直接改”就跳过文件读取和 allowed_files。
- 能从仓库获得的事实先查，不问用户。
