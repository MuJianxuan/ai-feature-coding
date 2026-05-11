---
template: coding-feature-workflow
doc_type: overview
doc_status: ready
updated_at: ""
---

# Feature 目录说明

本目录由 `coding-feature-orchestrator` 创建，默认位置为仓库根目录的 `.docs/feature-YYYYMMDD-short-name/`。

## 文件职责

- `requirements.md`：业务目标、范围边界、验收标准。
- `investigation.md`：仓库证据、真实代码链路、数据来源。
- `design.md`：技术方案、影响范围、接口/数据变更、风险和回滚。
- `tasks.md`：唯一编码驱动文件，按任务状态推进。
- `verification.md`：验收标准到验证证据的映射。
- `handoff.md`：交付摘要、复核入口、残余风险。
- `resource/`：需求资料、原型、会议纪要、接口草案。
- `sql/`：需求阶段 SQL 草案，最终脚本按项目规范落正式目录。

## 使用原则

- 先证据，后方案；先任务，后编码；先验证，后收口。
- 文档用中文写，保留 technical English names。
- 不确定内容必须标为 `待确认`、`推断` 或 `未验证`，不能伪装成结论。
- 初始模板中的空表格和 `UNSET` 不代表有效阶段内容，阶段 skill 必须写入真实证据后再更新 `stage_status`。
