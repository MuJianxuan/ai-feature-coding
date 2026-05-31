# Ship Orchestrator Tests

本目录保存 workflow 级 regression prompts 和人工验收场景。

可执行单元测试仍在 `skills/ship-orchestrator/scripts/`：

```bash
python3 -m unittest skills/ship-orchestrator/scripts/test_workflow_hardening.py skills/ship-orchestrator/scripts/test_spec_runtime.py
```

`regression-prompts.md` 用于验证 orchestrator 行为、gate 阻塞、artifact validator、build preflight 和 handoff evidence 是否仍符合协议。
