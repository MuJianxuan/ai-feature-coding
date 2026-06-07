# Ship Orchestrator Tests

本目录保存 workflow 级 regression prompts 和人工验收场景。

可执行单元测试仍在 `skills/ship-orchestrator/scripts/`：

```bash
python3 -m unittest skills/ship-orchestrator/scripts/test_workflow_hardening.py skills/ship-orchestrator/scripts/test_spec_runtime.py
```

`regression-prompts.md` 用于验证 orchestrator 行为、gate 阻塞、artifact validator、build preflight 和 handoff evidence 是否仍符合协议。

## Workflow Hardening Matrix

本轮 workflow hardening 的自动回归集中在 `test_workflow_hardening.py`，覆盖：

- B/D UIUX Gate inserted `ship-shape` transition。
- D + `backend_only` contract material hard gate。
- E technical_plan derived requirements AC/source completeness。
- `project_scope` design-review 后冻结。
- scenario/scope forbidden artifacts、raw inbox、delivery plan task schema。

推荐 preflight：

```bash
python3 -m unittest skills/ship-orchestrator/scripts/test_workflow_hardening.py skills/ship-orchestrator/scripts/test_spec_runtime.py
python3 skills/ship-orchestrator/scripts/validate_feature_artifacts.py <feature_dir> --json
python3 skills/ship-orchestrator/scripts/stage_transition_check.py <feature_dir> --target-stage ship-contract --json
python3 skills/ship-orchestrator/scripts/stage_transition_check.py <feature_dir> --target-stage ship-delivery-plan --json
```
