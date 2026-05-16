#!/usr/bin/env python3
"""
Coding Feature Workflow — Metrics Aggregator

扫描所有 .docs/feature-*/metrics.json，输出聚合分析报告。
stdlib-only，无外部依赖。

用法：
    python aggregate_metrics.py [project_root]

    project_root 默认为当前目录。脚本会在 project_root 下查找
    .docs/feature-*/metrics.json 文件。
"""

import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


def find_metrics_files(project_root: str) -> list[Path]:
    docs_dir = Path(project_root) / ".docs"
    if not docs_dir.exists():
        return []
    results = []
    for feature_dir in sorted(docs_dir.iterdir()):
        if feature_dir.is_dir() and feature_dir.name.startswith("feature-"):
            metrics_file = feature_dir / "metrics.json"
            if metrics_file.exists():
                results.append(metrics_file)
    return results


def parse_metrics(path: Path) -> dict | None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not data.get("events"):
            return None
        return data
    except (json.JSONDecodeError, OSError):
        return None


def parse_timestamp(ts: str) -> datetime | None:
    if not ts:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%dT%H:%M%z"):
        try:
            return datetime.strptime(ts, fmt)
        except ValueError:
            continue
    return None


def compute_stage_durations(events: list[dict]) -> dict[str, list[float]]:
    durations: dict[str, list[float]] = defaultdict(list)
    enter_times: dict[str, datetime] = {}

    for event in events:
        etype = event.get("type", "")
        stage = event.get("stage", "")
        ts = parse_timestamp(event.get("timestamp", ""))
        if not ts or not stage:
            continue

        if etype == "stage_enter":
            enter_times[stage] = ts
        elif etype == "stage_complete":
            if stage in enter_times:
                delta = (ts - enter_times[stage]).total_seconds() / 60.0
                durations[stage].append(delta)
                del enter_times[stage]
            elif "duration_minutes" in event:
                durations[stage].append(event["duration_minutes"])

    return durations


def aggregate(metrics_list: list[dict]) -> dict:
    total_features = len(metrics_list)
    pipeline_modes = Counter()
    all_stage_durations: dict[str, list[float]] = defaultdict(list)
    blocker_types = Counter()
    error_types = Counter()
    composition_call_types = Counter()
    total_completed = 0
    total_blocked_stages = 0
    total_error_recoveries = 0

    for data in metrics_list:
        pipeline_modes[data.get("pipeline_mode", "unknown")] += 1

        events = data.get("events", [])
        stage_durations = compute_stage_durations(events)
        for stage, durs in stage_durations.items():
            all_stage_durations[stage].extend(durs)

        for event in events:
            etype = event.get("type", "")
            if etype == "stage_blocked":
                blocker_types[event.get("blocker", "unknown")] += 1
                total_blocked_stages += 1
            elif etype == "error_recovery":
                error_types[event.get("error_type", "unknown")] += 1
                total_error_recoveries += 1
            elif etype == "composition_call":
                call_type = event.get("call_type", "unknown")
                callee = event.get("callee", "unknown")
                composition_call_types[f"{call_type}:{callee}"] += 1

        summary = data.get("summary", {})
        if summary.get("total_duration_hours") is not None:
            total_completed += 1

    avg_stage_durations = {}
    for stage, durs in sorted(all_stage_durations.items()):
        if durs:
            avg_stage_durations[stage] = {
                "avg_minutes": round(sum(durs) / len(durs), 1),
                "min_minutes": round(min(durs), 1),
                "max_minutes": round(max(durs), 1),
                "count": len(durs),
            }

    return {
        "total_features": total_features,
        "completed_features": total_completed,
        "pipeline_modes": dict(pipeline_modes.most_common()),
        "avg_stage_durations": avg_stage_durations,
        "top_blockers": dict(blocker_types.most_common(5)),
        "total_blocked_stages": total_blocked_stages,
        "top_error_types": dict(error_types.most_common(5)),
        "total_error_recoveries": total_error_recoveries,
        "composition_calls": dict(composition_call_types.most_common(10)),
    }


def format_report(result: dict) -> str:
    lines = []
    lines.append("=" * 60)
    lines.append("Coding Feature Workflow — Metrics Report")
    lines.append("=" * 60)
    lines.append("")

    lines.append(f"总 Feature 数：{result['total_features']}")
    lines.append(f"已完成 Feature 数：{result['completed_features']}")
    lines.append("")

    lines.append("--- Pipeline 模式分布 ---")
    for mode, count in result["pipeline_modes"].items():
        lines.append(f"  {mode}: {count}")
    lines.append("")

    lines.append("--- 平均阶段耗时 ---")
    for stage, stats in result["avg_stage_durations"].items():
        lines.append(
            f"  {stage}: 平均 {stats['avg_minutes']}min "
            f"(最短 {stats['min_minutes']}min, 最长 {stats['max_minutes']}min, "
            f"样本数 {stats['count']})"
        )
    lines.append("")

    lines.append(f"--- 阻塞统计 (总计 {result['total_blocked_stages']} 次) ---")
    if result["top_blockers"]:
        for blocker, count in result["top_blockers"].items():
            lines.append(f"  {blocker}: {count}")
    else:
        lines.append("  无阻塞记录")
    lines.append("")

    lines.append(f"--- 错误恢复统计 (总计 {result['total_error_recoveries']} 次) ---")
    if result["top_error_types"]:
        for etype, count in result["top_error_types"].items():
            lines.append(f"  {etype}: {count}")
    else:
        lines.append("  无错误恢复记录")
    lines.append("")

    lines.append("--- 组合调用统计 ---")
    if result["composition_calls"]:
        for call, count in result["composition_calls"].items():
            lines.append(f"  {call}: {count}")
    else:
        lines.append("  无组合调用记录")
    lines.append("")

    return "\n".join(lines)


def main():
    project_root = sys.argv[1] if len(sys.argv) > 1 else "."
    project_root = os.path.abspath(project_root)

    metrics_files = find_metrics_files(project_root)
    if not metrics_files:
        print(f"未找到 metrics 文件。搜索路径：{project_root}/.docs/feature-*/metrics.json")
        sys.exit(0)

    metrics_list = []
    for path in metrics_files:
        data = parse_metrics(path)
        if data:
            metrics_list.append(data)

    if not metrics_list:
        print("找到 metrics 文件但均为空或格式错误。")
        sys.exit(0)

    result = aggregate(metrics_list)
    report = format_report(result)
    print(report)

    output_path = Path(project_root) / ".docs" / "metrics-report.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"JSON 报告已写入：{output_path}")


if __name__ == "__main__":
    main()
