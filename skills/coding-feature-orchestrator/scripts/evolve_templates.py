#!/usr/bin/env python3
"""
Coding Feature Workflow — Template Evolution Analyzer

分析已完成 feature 的阶段文档，识别模板中从未使用的 section 和经常手动添加的 section，
输出模板改进建议。

stdlib-only，无外部依赖。

用法：
    python evolve_templates.py [project_root]

    project_root 默认为当前目录。脚本会在 project_root 下查找
    .docs/feature-*/  目录并与模板对比。
"""

import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path


ORCHESTRATOR_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_DIR = ORCHESTRATOR_ROOT / "assets" / "feature-template"
FAST_TRACK_TEMPLATE_DIR = ORCHESTRATOR_ROOT / "assets" / "fast-track-template"

STAGE_DOCS = [
    "discovery.md",
    "requirements.md",
    "design.md",
    "tasks.md",
    "verification.md",
    "handoff.md",
]

FAST_TRACK_DOCS = [
    "brief.md",
    "implementation.md",
    "verification.md",
]


def extract_sections(text: str) -> list[str]:
    """提取 markdown 中所有 ## 和 ### 级别的 section 标题。"""
    sections = []
    for match in re.finditer(r"^(#{2,3})\s+(.+)$", text, re.MULTILINE):
        sections.append(match.group(2).strip())
    return sections


def extract_template_sections(template_dir: Path, doc_name: str) -> list[str]:
    """从模板文件中提取 section 标题。"""
    path = template_dir / doc_name
    if not path.is_file():
        return []
    return extract_sections(path.read_text())


def find_completed_features(project_root: str) -> list[Path]:
    """查找所有已完成的 feature 目录（handoff.md 存在且 stage_status 为 complete）。"""
    docs_dir = Path(project_root) / ".docs"
    if not docs_dir.exists():
        return []
    results = []
    for feature_dir in sorted(docs_dir.iterdir()):
        if not feature_dir.is_dir() or not feature_dir.name.startswith("feature-"):
            continue
        handoff = feature_dir / "handoff.md"
        if handoff.is_file():
            text = handoff.read_text()
            if "stage_status: complete" in text:
                results.append(feature_dir)
    return results


def find_all_features(project_root: str) -> list[Path]:
    """查找所有 feature 目录。"""
    docs_dir = Path(project_root) / ".docs"
    if not docs_dir.exists():
        return []
    return sorted(
        d for d in docs_dir.iterdir()
        if d.is_dir() and d.name.startswith("feature-")
    )


def detect_pipeline_mode(feature_dir: Path) -> str:
    """检测 feature 使用的 pipeline 模式。"""
    brief = feature_dir / "brief.md"
    if brief.is_file():
        text = brief.read_text()
        if "pipeline_mode: fast_track" in text:
            return "fast_track"
    discovery = feature_dir / "discovery.md"
    if discovery.is_file():
        return "standard"
    return "unknown"


def analyze_section_usage(
    features: list[Path],
    template_dir: Path,
    doc_names: list[str],
) -> dict:
    """分析 section 使用情况。"""
    template_sections: dict[str, list[str]] = {}
    for doc_name in doc_names:
        template_sections[doc_name] = extract_template_sections(template_dir, doc_name)

    section_usage: dict[str, Counter] = defaultdict(Counter)
    extra_sections: dict[str, Counter] = defaultdict(Counter)

    for feature_dir in features:
        for doc_name in doc_names:
            doc_path = feature_dir / doc_name
            if not doc_path.is_file():
                continue
            actual_sections = extract_sections(doc_path.read_text())
            expected = set(template_sections.get(doc_name, []))

            for section in actual_sections:
                if section in expected:
                    section_usage[doc_name][section] += 1
                else:
                    extra_sections[doc_name][section] += 1

    return {
        "template_sections": template_sections,
        "section_usage": section_usage,
        "extra_sections": extra_sections,
        "feature_count": len(features),
    }


def generate_recommendations(analysis: dict) -> list[dict]:
    """基于分析结果生成模板改进建议。"""
    recommendations = []
    feature_count = analysis["feature_count"]
    if feature_count == 0:
        return recommendations

    threshold_unused = 0.2
    threshold_add = 0.5

    for doc_name, template_secs in analysis["template_sections"].items():
        usage = analysis["section_usage"].get(doc_name, Counter())
        for section in template_secs:
            use_rate = usage.get(section, 0) / feature_count
            if use_rate < threshold_unused:
                recommendations.append({
                    "type": "mark_optional",
                    "doc": doc_name,
                    "section": section,
                    "usage_rate": round(use_rate * 100, 1),
                    "reason": f"仅 {round(use_rate * 100, 1)}% 的 feature 使用了此 section",
                })

    for doc_name, extras in analysis["extra_sections"].items():
        for section, count in extras.most_common(10):
            add_rate = count / feature_count
            if add_rate >= threshold_add:
                recommendations.append({
                    "type": "add_to_template",
                    "doc": doc_name,
                    "section": section,
                    "usage_rate": round(add_rate * 100, 1),
                    "reason": f"{round(add_rate * 100, 1)}% 的 feature 手动添加了此 section",
                })

    return recommendations


def format_report(
    standard_analysis: dict,
    fast_track_analysis: dict,
    recommendations: list[dict],
) -> str:
    """格式化输出报告。"""
    lines = []
    lines.append("=" * 60)
    lines.append("Coding Feature Workflow — Template Evolution Report")
    lines.append("=" * 60)
    lines.append("")

    lines.append(f"Standard pipeline features 分析数：{standard_analysis['feature_count']}")
    lines.append(f"Fast-track pipeline features 分析数：{fast_track_analysis['feature_count']}")
    lines.append("")

    if not recommendations:
        lines.append("暂无改进建议（样本不足或模板使用率良好）。")
        return "\n".join(lines)

    add_recs = [r for r in recommendations if r["type"] == "add_to_template"]
    optional_recs = [r for r in recommendations if r["type"] == "mark_optional"]

    if add_recs:
        lines.append("--- 建议添加到模板的 Section ---")
        for rec in sorted(add_recs, key=lambda r: -r["usage_rate"]):
            lines.append(f"  [{rec['doc']}] {rec['section']}")
            lines.append(f"    原因：{rec['reason']}")
        lines.append("")

    if optional_recs:
        lines.append("--- 建议标记为 Optional 的 Section ---")
        for rec in sorted(optional_recs, key=lambda r: r["usage_rate"]):
            lines.append(f"  [{rec['doc']}] {rec['section']}")
            lines.append(f"    原因：{rec['reason']}")
        lines.append("")

    return "\n".join(lines)


def main():
    project_root = sys.argv[1] if len(sys.argv) > 1 else "."
    project_root = os.path.abspath(project_root)

    all_features = find_all_features(project_root)
    if not all_features:
        print(f"未找到 feature 目录。搜索路径：{project_root}/.docs/feature-*/")
        sys.exit(0)

    standard_features = [f for f in all_features if detect_pipeline_mode(f) == "standard"]
    fast_track_features = [f for f in all_features if detect_pipeline_mode(f) == "fast_track"]

    standard_analysis = analyze_section_usage(standard_features, TEMPLATE_DIR, STAGE_DOCS)
    fast_track_analysis = analyze_section_usage(fast_track_features, FAST_TRACK_TEMPLATE_DIR, FAST_TRACK_DOCS)

    recommendations = []
    recommendations.extend(generate_recommendations(standard_analysis))
    recommendations.extend(generate_recommendations(fast_track_analysis))

    report = format_report(standard_analysis, fast_track_analysis, recommendations)
    print(report)


if __name__ == "__main__":
    main()
