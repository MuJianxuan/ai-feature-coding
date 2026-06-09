# Ship Solo Routing Protocol

本协议描述 orchestrator 如何在主上下文、支持 skill、子代理之间路由。

## Default

主上下文负责状态推进和用户决策。支持 skill 和子代理只提供证据、草案或检查结果。

## Support Skill Routing

- `ship-shape`：UI 方向、状态、wireframe。
- `ship-frontend-design`：复杂前端页面/组件/状态设计。
- `ship-backend-design`：复杂后端数据/事务/服务设计。
- `ship-*-review`：可选 checklist。
- `ship-grill-me`：一次一个阻塞问题。
- `ship-spec`：规范读取或 proposal。

## Subagent Routing

适合委派：

- 仓库探索
- 官方文档调研
- 测试缺口分析
- code review
- 多方案比较

不适合委派：

- 用户风险接受
- 正式状态推进
- 合并多个互斥方案的最终决定
- 修改同一事实源文件的并行任务

## Grill Rule

`ship-grill-me` 只能输出问题、推荐答案、证据和分支影响。它不替用户批准风险，也不替 review checklist 写通过结论。
