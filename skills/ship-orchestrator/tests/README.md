# Ship Orchestrator Tests

本目录保存 workflow 级 regression prompts 和人工验收场景。

可执行单元测试仍在 `skills/ship-orchestrator/scripts/`：

```bash
python3 -m unittest skills/ship-orchestrator/scripts/test_workflow_hardening.py skills/ship-orchestrator/scripts/test_spec_runtime.py
```

`regression-prompts.md` 用于验证 orchestrator 行为、gate 阻塞、artifact validator、build preflight 和 handoff evidence 是否仍符合协议。

## Workflow Hardening Matrix

本轮 workflow hardening 的自动回归集中在 `test_workflow_hardening.py`，覆盖：

- P0 Source Code Edit Barrier：`current_stage == ship-build`、`implementation_preflight.py --files`、`allowed_files` 覆盖、非法 `allowed_files` path/glob。
- P0 Workspace Boundary：`spec_root` / `feature_root` 禁止 `../` 与绝对路径逃逸，gate/preflight/doctor 统一校验 `feature_dir` 位于 workspace `feature_root/feature-*`。
- P0/P1 Hard Gate Audit：`confirmation_log` + `confirmation_id` legacy warning / strict blocking，子代理草案不得自签。
- P1 Resume Diagnostics：`workflow_doctor.py` 报告提前实现、越界实现、worktree status 与 workflow events。
- P1 Traceability / Aggregation：`validate_traceability.py --strict --stage` 和 `validate_all.py --strict` 聚合输出。
- 既有业务规则：B/D UIUX Gate、D backend_only contract material、E technical_plan selected scope、scope freeze、raw inbox、delivery plan task schema。

推荐 preflight：

```bash
python3 -m unittest skills/ship-orchestrator/scripts/test_workflow_hardening.py skills/ship-orchestrator/scripts/test_spec_runtime.py
python3 skills/ship-orchestrator/scripts/validate_feature_artifacts.py <feature_dir> --json
python3 skills/ship-orchestrator/scripts/stage_transition_check.py <feature_dir> --target-stage ship-contract --json
python3 skills/ship-orchestrator/scripts/stage_transition_check.py <feature_dir> --target-stage ship-delivery-plan --json
```
