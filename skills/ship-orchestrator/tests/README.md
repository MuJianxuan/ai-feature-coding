# Ship Orchestrator Tests

本目录保存新版 Ship Solo workflow 的 regression prompts 和人工验收场景。

可执行单元测试在 `skills/ship-orchestrator/scripts/`：

```bash
python3 skills/ship-orchestrator/scripts/test_solo_workflow.py
python3 skills/ship-orchestrator/scripts/test_workflow_hardening.py
python3 skills/ship-orchestrator/scripts/test_spec_runtime.py
```

`regression-prompts.md` 用于验证 orchestrator 行为、轻量门禁、artifact validator、build preflight 和 handoff evidence 是否符合新版协议。

## Workflow Hardening Matrix

新版 hardening 自动回归集中在 `test_workflow_hardening.py`，覆盖：

- Runtime stages：只保留 8 个 canonical stages，review / shape / design support skills 不进入 `current_stage`。
- Source edit barrier：`current_stage == ship-build`、一个 DOING slice、`allowed_files` 覆盖、`verification_command` 存在。
- Workspace boundary：schema v3 支持 `.docs/ship/<work-id>`，旧 `feature-*` 目录仍可兼容读取。
- Review checklist：`ship-define-review`、`ship-design-review`、`ship-plan-review` 是可选 checklist，不再要求默认签字才能推进。
- Artifact validation：新版文件名为 `brief.md`、`context-map.md`、`contract.md`、`plan.md`、`build-log.md`、`verification.md`、`handoff.md`。
- Regression prompts：覆盖 bugfix、feature、refactor、UI、docs、close 和 support skill 场景。

推荐 preflight：

```bash
python3 skills/ship-orchestrator/scripts/validate_workflow_docs.py
python3 skills/ship-orchestrator/scripts/test_solo_workflow.py
python3 skills/ship-orchestrator/scripts/test_workflow_hardening.py
python3 skills/ship-orchestrator/scripts/test_spec_runtime.py
```
