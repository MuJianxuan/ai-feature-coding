# Ship Solo Stage Routing

新版 runtime 只有 8 个 canonical stages：

| Order | Stage | Macro | Artifact |
|---|---|---|---|
| 01 | `ship-discover` | Discover | `intent.md` |
| 02 | `ship-define` | Define | `brief.md` |
| 03 | `ship-tech-discovery` | Understand | `context-map.md` |
| 04 | `ship-contract` | Design | `contract.md` |
| 05 | `ship-delivery-plan` | Plan | `plan.md` |
| 06 | `ship-build` | Build | `build-log.md` |
| 07 | `ship-verify` | Verify | `verification.md` |
| 08 | `ship-handoff` | Close | `handoff.md` |

## Support Skills

以下 skills 是可选支持工具，不进入 `current_stage`：

- `ship-shape`
- `ship-frontend-design`
- `ship-backend-design`
- `ship-define-review`
- `ship-design-review`
- `ship-plan-review`
- `ship-grill-me`
- `ship-spec`

## Routing Rules

- 目标不清：从 `ship-discover` 开始。
- 需求基本清楚：从 `ship-define` 开始。
- bugfix/refactor：通常从 `ship-tech-discovery` 开始。
- UI 无方向：插入 `ship-shape`，产物作为 evidence 回到 define/contract。
- docs/release：按证据自动跳过不必要阶段。
- 实现前必须进入 `ship-build`，且有一个 DOING slice。

## Transition Principle

只强制已完成的前置 runtime stages 有足够 artifact；当前阶段可以 in progress，未来阶段不得阻塞当前 transition。
