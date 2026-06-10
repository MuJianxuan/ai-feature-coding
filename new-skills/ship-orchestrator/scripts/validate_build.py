#!/usr/bin/env python3
"""Build Validator - 验证 Build 产物、测试记录和 AC 覆盖。"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from _lib import Check, extract_ac_ids, feature_path, read_text, require_frontmatter, section_text, summarize


def validate_build(feature_dir: Path) -> list[Check]:
    verification_file = feature_dir / "verification.md"
    requirements_file = feature_dir / "requirements.md"
    build_plan_file = feature_dir / "build-plan.yml"

    checks, fm, body = require_frontmatter(verification_file)

    checks.append(Check("build-plan.yml 存在", build_plan_file.exists(), "缺少 build-plan.yml"))
    if build_plan_file.exists():
        plan = read_text(build_plan_file)
        checks.append(Check("构建任务含 AC 引用", "ac_refs" in plan and "AC-" in plan, "build-plan.yml 任务必须关联 ac_refs"))

    req_content = read_text(requirements_file) if requirements_file.exists() else ""
    ac_ids = extract_ac_ids(req_content)
    checks.append(Check("requirements.md 存在", requirements_file.exists(), "缺少 requirements.md，无法验证 AC 覆盖"))

    all_ac_passed = fm.get("all_ac_passed") is True or "所有 AC 已验证" in body or "所有 AC 已验证，功能可交付" in body
    checks.append(Check("all_ac_passed", all_ac_passed, "verification.md frontmatter 需要 all_ac_passed: true，或正文明确所有 AC 已验证"))

    uncovered = []
    for ac_id in ac_ids:
        evidence_lines = [line for line in body.splitlines() if ac_id in line]
        has_evidence = any(re.search(r"(✅|passed|covered by:)", line, flags=re.IGNORECASE) for line in evidence_lines)
        if not has_evidence:
            uncovered.append(ac_id)
    checks.append(Check("AC 测试覆盖", not uncovered, f"verification.md 未证明这些 AC: {', '.join(uncovered)}" if uncovered else ""))

    test_section = section_text(body, ["测试覆盖", "测试", "Test"])
    has_failure = bool(re.search(r"\b([1-9]\d*)\s*(failed|failures|errors)\b|失败|❌", test_section, flags=re.IGNORECASE))
    has_success = bool(re.search(r"\b(passed|通过)\b|0\s*(failed|failures|errors)", test_section, flags=re.IGNORECASE))
    tests_passed = has_success and not has_failure
    checks.append(Check("测试通过记录", tests_passed, "verification.md 缺少真实测试通过记录，或记录了 failed/errors"))

    quality_section = section_text(body, ["代码质量", "质量", "Lint", "Typecheck"])
    no_lint_errors = bool(re.search(r"(0\s*errors|Typecheck:\s*passed|类型检查.*通过|Lint:\s*0)", quality_section, flags=re.IGNORECASE))
    checks.append(Check("代码质量记录", no_lint_errors, "verification.md 缺少 lint/typecheck 无错误记录", warning=not no_lint_errors))

    outputs = section_text(body, ["产出文件", "输出文件"])
    checks.append(Check("产出文件记录", bool(outputs), "verification.md 需要列出产出文件"))

    return checks


def main() -> int:
    feature_dir = feature_path(sys.argv)
    return summarize(validate_build(feature_dir), "Build Validation")


if __name__ == "__main__":
    raise SystemExit(main())
