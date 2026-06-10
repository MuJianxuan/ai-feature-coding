#!/usr/bin/env python3
"""Requirements Validator - 验证 requirements.md 质量。"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from _lib import Check, extract_ac_sections, feature_path, has_section, require_frontmatter, section_text, summarize


def validate_requirements(feature_dir: Path) -> list[Check]:
    req_file = feature_dir / "requirements.md"
    checks, _fm, body = require_frontmatter(req_file)

    ac_sections = extract_ac_sections(body)
    checks.append(Check("至少 1 个 AC", bool(ac_sections), "requirements.md 必须包含 ### AC-1 形式的验收标准"))

    for ac_id, section in ac_sections.items():
        ok = all(token in section for token in ("Given", "When", "Then"))
        checks.append(Check(f"{ac_id} Given/When/Then", ok, f"{ac_id} 缺少 Given/When/Then 结构"))

    domain_ok = has_section(body, ["Domain 模型", "领域模型"])
    no_domain = "不涉及业务域" in body or "无 Domain" in body or "不涉及 Domain" in body
    checks.append(Check("Domain 模型", domain_ok or no_domain, "需要 Domain 模型，或明确说明不涉及业务域"))

    nfr = section_text(body, ["非功能需求", "NFR"])
    if not nfr:
        checks.append(Check("非功能需求", True, "小功能可接受未定义非功能需求", warning=True))
    else:
        has_metric = bool(re.search(r"(<|>|<=|>=|P95|P99|QPS|ms|秒|分钟|%)", nfr, flags=re.IGNORECASE))
        checks.append(Check("非功能需求量化", has_metric, "非功能需求存在但缺少量化指标", warning=not has_metric))

    return checks


def main() -> int:
    feature_dir = feature_path(sys.argv)
    return summarize(validate_requirements(feature_dir), "Requirements Validation")


if __name__ == "__main__":
    raise SystemExit(main())
