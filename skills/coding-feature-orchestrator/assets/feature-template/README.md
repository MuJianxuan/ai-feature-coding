---
template: coding-feature-workflow
doc_type: overview
doc_status: ready
updated_at: ""
---

# Feature 目录说明

本目录由 `coding-feature-orchestrator` 创建，默认位置为仓库根目录的 `.docs/feature-YYYYMMDD-short-name/`。

## 文件职责

- `investigation.md`：先记录仓库证据、真实代码链路、数据来源、相似实现和必要外部调研。
- `requirements.md`：基于勘查证据沉淀业务目标、范围边界、验收标准。
- `design.md`：技术方案 brainstorming、澄清问题、影响范围、接口/数据变更、风险和回滚。
- `tasks.md`：唯一编码驱动文件，按任务状态推进。
- `verification.md`：验收标准到验证证据的映射。
- `handoff.md`：交付摘要、复核入口、残余风险。
- `resource/`：需求资料、原型、会议纪要、接口草案。
- `sql/`：需求阶段 SQL 草案，最终脚本按项目规范落正式目录。

## 使用原则

- 先仓库勘查和外部调研，后需求澄清；先证据，后方案；先任务，后编码；先验证，后收口。
- 需求澄清和技术设计必须识别模糊之处、边界情况和未明确行为，并提出具体问题。
- 文档用中文写，保留 technical English names。
- 不确定内容必须标为 `待确认`、`推断` 或 `未验证`，不能伪装成结论。
- 初始模板中的空表格和 `UNSET` 不代表有效阶段内容，阶段 skill 必须写入真实证据后再更新 `stage_status`。
