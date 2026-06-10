# Design Reference Templates

| id | file | priority | 说明 |
|---|---:|---:|---|
| async-task | async-task.md | 90 | MQ / 定时 / 批处理 / 重试 |
| integration | integration.md | 80 | 第三方 API / Webhook / 外部系统 |
| data-migration | data-migration.md | 70 | 表结构 / 回填 / 数据清洗 |
| fullstack-feature | fullstack-feature.md | 60 | UI + API + 数据 |
| backend-service | backend-service.md | 50 | API / 服务层 / 权限 / 数据模型 |
| frontend-ui | frontend-ui.md | 40 | 页面 / 组件 / 状态管理 |
| config-change | config-change.md | 30 | 配置 / 灰度 / 开关 / 权限矩阵 |

规则：模板只提供 Design 阶段 checklist。`design.md` 顶层章节仍使用 ShipKit 稳定骨架，专项内容写进对应基础章节的小节。
