# Workflow Fixture Map

本目录保存可读 regression fixtures；大型 golden path 目前由 `scripts/test_workflow_hardening.py` 的 fixture helper 动态生成，避免维护重复的完整 feature 树。

## Existing Fixtures

- `b-uiux-gate-inserted-shape/`：覆盖 B/D UIUX Material Gate 插入 `ship-shape`。
- `e-tech-plan-confirmed/`：覆盖 technical_plan selected scope AC 已确认路径。
- `e-tech-plan-missing-ac-confirmation/`：覆盖 selected scope AC 缺失阻塞。
- `evolve-missing-baseline/`：覆盖 evolve baseline 缺失。
- `raw-inbox-past-define/`：覆盖 raw PRD inbox 不得越过 define。
- `verification-shared-ownership/`：覆盖 verification / handoff 共享 ownership。

## Golden Path Coverage

- `a-greenfield-happy-path`：由 `WorkflowHardeningTest.prepare_ready_contract_stage` 和 build-ready helper 动态覆盖。
- `c-evolve-happy-path`：由 evolve baseline / source validation tests 覆盖。
- `fullstack-build-ready`：由 stage transition + implementation preflight tests 覆盖。
- `frontend-only-happy-path`：由 frontend plan / frontend-only build preflight tests 覆盖。
- `backend-only-happy-path`：由 backend-only delivery plan、design review、implementation preflight tests 覆盖。
- `implementation-preflight-file-scope-violation`：由 `test_implementation_preflight_blocks_files_outside_doing_task` 覆盖。
- `workspace-path-escape`：由 `test_project_config_rejects_workspace_path_escape` 与 `test_preflight_rejects_feature_dir_outside_feature_root` 覆盖。
