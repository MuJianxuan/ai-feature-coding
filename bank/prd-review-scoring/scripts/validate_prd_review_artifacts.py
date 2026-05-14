#!/usr/bin/env python3
"""Validate the PRD review scoring skill and generated review reports."""

from __future__ import annotations

from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parents[3]
SKILL_ROOT = ROOT / "skills" / "prd-review-scoring"

SKILL_REQUIRED = [
    "PRD 解析",
    "当前仓库勘查",
    "业界类似产品调研",
    "多维度评分",
    "多角色评审",
    "结论与行动项",
    "自检",
]

REPORT_REQUIRED = [
    "## 1. 评审结论",
    "## 2. 证据来源",
    "## 3. PRD 摘要",
    "## 4. 当前仓库相关能力勘查",
    "## 5. 业界类似产品调研",
    "## 6. 多维度评分",
    "## 7. 多角色评审",
    "## 8. 关键问题",
    "## 9. 进入下一阶段前的行动项",
]


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def validate_skill(errors: list[str]) -> None:
    skill_path = SKILL_ROOT / "SKILL.md"
    template_path = SKILL_ROOT / "assets" / "report-template.md"

    if not skill_path.exists():
        fail(errors, f"missing {skill_path}")
        return
    if not template_path.exists():
        fail(errors, f"missing {template_path}")

    text = skill_path.read_text()
    if not text.startswith("---\n"):
        fail(errors, "SKILL.md missing YAML frontmatter")
    if "name: prd-review-scoring" not in text:
        fail(errors, "SKILL.md missing expected skill name")
    if "description:" not in text:
        fail(errors, "SKILL.md missing description")

    for marker in SKILL_REQUIRED:
        if marker not in text:
            fail(errors, f"SKILL.md missing required marker: {marker}")

    if template_path.exists():
        template = template_path.read_text()
        for marker in REPORT_REQUIRED:
            if marker not in template:
                fail(errors, f"report template missing required marker: {marker}")


def validate_report(path: Path, errors: list[str]) -> None:
    if not path.exists():
        fail(errors, f"report not found: {path}")
        return

    text = path.read_text()
    for marker in REPORT_REQUIRED:
        if marker not in text:
            fail(errors, f"{path}: missing report section {marker}")

    if "总分" not in text or not re.search(r"\b\d+(?:\.\d)?/10\b", text):
        fail(errors, f"{path}: missing 0-10 overall score")
    if text.count("https://") < 4:
        fail(errors, f"{path}: expected at least 4 official external links")
    if "未发现相关业务能力证据" not in text:
        fail(errors, f"{path}: repository investigation boundary is not explicit")
    if "Critical" not in text or "Major" not in text:
        fail(errors, f"{path}: missing severity sections")


def main(argv: list[str]) -> int:
    errors: list[str] = []
    validate_skill(errors)

    for raw_path in argv[1:]:
        validate_report(Path(raw_path), errors)

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print("prd-review-scoring artifacts OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
