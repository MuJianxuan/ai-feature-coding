#!/usr/bin/env python3
"""Small standard-library helpers for new ShipKit validators."""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


@dataclass
class Check:
    name: str
    passed: bool
    message: str = ""
    warning: bool = False


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        raise SystemExit(f"ERROR: file not found: {path}")


def parse_value(raw: str) -> Any:
    raw = raw.strip().strip('"').strip("'")
    if raw.lower() == "true":
        return True
    if raw.lower() == "false":
        return False
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1].strip()
        if not inner:
            return []
        return [item.strip().strip('"').strip("'") for item in inner.split(",")]
    return raw


def parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    if not content.startswith("---\n"):
        return {}, content
    end = content.find("\n---", 4)
    if end == -1:
        return {}, content
    raw = content[4:end]
    body = content[end + len("\n---") :].lstrip("\n")
    data: dict[str, Any] = {}
    for line in raw.splitlines():
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = parse_value(value)
    return data, body


def strip_inline_comment(value: str) -> str:
    """Strip YAML-style inline comments without corrupting quoted # fragments."""
    in_single = False
    in_double = False
    escaped = False
    for idx, ch in enumerate(value):
        if ch == "\\" and in_double and not escaped:
            escaped = True
            continue
        if ch == '"' and not in_single and not escaped:
            in_double = not in_double
        elif ch == "'" and not in_double:
            in_single = not in_single
        elif ch == "#" and not in_single and not in_double:
            return value[:idx]
        escaped = False
    return value


def parse_block_value(lines: list[str]) -> Any:
    """Parse the small YAML subset used by ShipKit meta/project files."""
    entries = [line.strip() for line in lines if line.strip() and not line.strip().startswith("#")]
    if not entries:
        return []

    if any(entry.startswith("- ") for entry in entries):
        items: list[Any] = []
        current: dict[str, Any] | None = None
        for entry in entries:
            if entry.startswith("- "):
                raw_item = entry[2:].strip()
                if not raw_item:
                    current = {}
                    items.append(current)
                    continue
                if ":" in raw_item:
                    key, value = raw_item.split(":", 1)
                    current = {key.strip(): parse_value(strip_inline_comment(value))}
                    items.append(current)
                else:
                    current = None
                    items.append(parse_value(strip_inline_comment(raw_item)))
                continue
            if current is not None and ":" in entry:
                key, value = entry.split(":", 1)
                current[key.strip()] = parse_value(strip_inline_comment(value))
        return items

    data: dict[str, Any] = {}
    for entry in entries:
        if ":" not in entry:
            continue
        key, value = entry.split(":", 1)
        data[key.strip()] = parse_value(strip_inline_comment(value))
    return data


def parse_meta_yaml(path: Path) -> dict[str, Any]:
    """Parse ShipKit meta/project YAML without external dependencies.

    Supported subset: top-level scalars, inline lists, nested maps, lists of
    scalars, and lists of maps. This intentionally avoids pretending to be a
    full YAML parser while covering meta.yml and .docs/ship/project.yml.
    """
    if not path.exists():
        return {}

    raw_lines = path.read_text(encoding="utf-8").splitlines()
    data: dict[str, Any] = {}
    idx = 0
    while idx < len(raw_lines):
        line = raw_lines[idx]
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or line.startswith((" ", "\t")) or ":" not in stripped:
            idx += 1
            continue

        key, value = stripped.split(":", 1)
        key = key.strip()
        value = strip_inline_comment(value)
        if value.strip():
            data[key] = parse_value(value)
            idx += 1
            continue

        block: list[str] = []
        idx += 1
        while idx < len(raw_lines):
            child = raw_lines[idx]
            child_stripped = child.strip()
            if child_stripped and not child.startswith((" ", "\t")):
                break
            block.append(child)
            idx += 1
        data[key] = parse_block_value(block)
    return data


def parse_loose_yaml(path: Path) -> dict[str, Any]:
    return parse_meta_yaml(path)


def extract_ac_ids(content: str) -> list[str]:
    ids = re.findall(r"^###\s*(AC-\d+)\b", content, flags=re.MULTILINE)
    if ids:
        return sorted(set(ids), key=lambda x: int(x.split("-")[1]))
    ids = re.findall(r"\bAC-\d+\b", content)
    return sorted(set(ids), key=lambda x: int(x.split("-")[1]))


def extract_ac_sections(content: str) -> dict[str, str]:
    matches = list(re.finditer(r"^###\s*(AC-\d+)\b.*$", content, flags=re.MULTILINE))
    sections: dict[str, str] = {}
    for idx, match in enumerate(matches):
        start = match.start()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(content)
        sections[match.group(1)] = content[start:end]
    return sections


def has_section(content: str, names: Iterable[str]) -> bool:
    for name in names:
        if re.search(rf"^##+\s+.*{re.escape(name)}", content, flags=re.MULTILINE | re.IGNORECASE):
            return True
    return False


def has_top_section(content: str, names: Iterable[str]) -> bool:
    """Return True only for stable top-level design sections (`## Title`)."""
    for name in names:
        if re.search(rf"^##\s+.*{re.escape(name)}", content, flags=re.MULTILINE | re.IGNORECASE):
            return True
    return False


def section_text(content: str, names: Iterable[str]) -> str:
    lines = content.splitlines()
    start = None
    level = None
    for i, line in enumerate(lines):
        m = re.match(r"^(##+)\s+(.*)$", line)
        if not m:
            continue
        title = m.group(2)
        if any(name.lower() in title.lower() for name in names):
            start = i + 1
            level = len(m.group(1))
            break
    if start is None:
        return ""
    end = len(lines)
    for j in range(start, len(lines)):
        m = re.match(r"^(##+)\s+", lines[j])
        if m and len(m.group(1)) <= (level or 2):
            end = j
            break
    return "\n".join(lines[start:end]).strip()


def require_frontmatter(path: Path) -> tuple[list[Check], dict[str, Any], str]:
    content = read_text(path)
    fm, body = parse_frontmatter(content)
    checks = [Check("frontmatter 存在", bool(fm), f"{path.name} 缺少 YAML frontmatter")]
    status = fm.get("status")
    checks.append(
        Check(
            "status 字段",
            status in {"draft", "ready", "approved"},
            f"status 必须是 draft/ready/approved，实际: {status!r}",
        )
    )
    return checks, fm, body


def summarize(checks: list[Check], title: str) -> int:
    errors = [c for c in checks if not c.passed and not c.warning]
    warnings = [c for c in checks if c.warning or (c.passed and c.message.startswith("WARNING:"))]
    print(title)
    print("Checks:")
    for check in checks:
        if check.warning:
            icon = "⚠️"
        elif check.passed:
            icon = "✅"
        else:
            icon = "❌"
        detail = f" - {check.message}" if (check.message and (not check.passed or check.warning)) else ""
        print(f"  {icon} {check.name}{detail}")
    print(f"Summary: {len([c for c in checks if c.passed])} passed, {len(errors)} errors, {len(warnings)} warnings")
    return 0 if not errors else 1


def feature_path(argv: list[str]) -> Path:
    if len(argv) != 2:
        raise SystemExit(f"Usage: {Path(argv[0]).name} <feature_dir>")
    return Path(argv[1])
