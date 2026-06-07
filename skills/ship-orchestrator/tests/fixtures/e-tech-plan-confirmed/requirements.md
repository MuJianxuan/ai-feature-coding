---
stage: ship-define
stage_status: ready
generation_mode: technical_plan
selected_scope_ac_confirmed: true
source_documents:
  - path: resource/tech.md
selected_scope:
  - 3.2 Export
updated_at: "2026-06-07T00:00:00+08:00"
evidence_complete: true
blocking_gaps: []
---
# Requirements
## In Scope
D-EXP-001 export orders.
## Out of Scope
Import.
## Acceptance Criteria
- AC-EXP-001 D-EXP-001 selected scope: 3.2 Export source: resource/tech.md#3.2 In Scope Given a user requests export, When the job is submitted, Then an export job is created.
## Open Questions
None.
## 需求资料索引
technical_plan_source selected scope resource/tech.md
## 非功能需求 / NFR
performance P95 < 1s. security auth required. availability retry. accessibility N/A.
