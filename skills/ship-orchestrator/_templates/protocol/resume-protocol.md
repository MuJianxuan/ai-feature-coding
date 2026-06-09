# Ship Solo Resume Protocol

恢复工作时，先定位 `.docs/ship/<work-id>/meta.yml`，再读取当前阶段 artifact。

## Resume Steps

1. 读取 `meta.yml.current_stage`。
2. 用 `workflow_stage_map.py --json <stage>` 获取 macro view。
3. 读取当前阶段 artifact 和前一个 runtime artifact。
4. 检查 `blocking_gaps`、当前 DOING slice、验证证据。
5. 只向用户汇报下一步必要决策。

## Source Edit Resume

继续修改源码前必须满足：

- `current_stage == ship-build`
- `plan.md` 或 `meta.yml.slices` 中只有一个 `DOING` slice
- 当前 slice 有 `allowed_files`
- 当前 slice 有 `verification_command`
- 目标文件被 `allowed_files` 覆盖

推荐命令：

```bash
python3 skills/ship-orchestrator/scripts/implementation_preflight.py .docs/ship/<work-id> --files <paths...>
```

## If Blocked

- 仓库事实不足：回到 `ship-tech-discovery`。
- 范围不清：回到 `ship-define`。
- 文件范围不足：更新 `ship-delivery-plan`，不要直接越界修改。
- 验证失败：留在 `ship-verify` 或回到 `ship-build` 修当前 slice。
