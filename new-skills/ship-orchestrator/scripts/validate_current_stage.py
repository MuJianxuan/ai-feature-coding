#!/usr/bin/env python3
"""Validate current feature stage according to meta.yml.current_stage."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from _lib import feature_path, parse_loose_yaml


STAGE_TO_SCRIPT = {
    "understand": "validate_requirements.py",
    "design": "validate_design.py",
    "build": "validate_build.py",
    "done": "validate_build.py",
}


def main() -> int:
    feature_dir = feature_path(sys.argv)
    meta = parse_loose_yaml(feature_dir / "meta.yml")
    stage = meta.get("current_stage")
    if stage not in STAGE_TO_SCRIPT:
        print(f"ERROR: meta.yml.current_stage must be one of {sorted(STAGE_TO_SCRIPT)}, got {stage!r}")
        return 1
    script = Path(__file__).with_name(STAGE_TO_SCRIPT[stage])
    print(f"Current stage: {stage}; running {script.name}", flush=True)
    result = subprocess.run([sys.executable, str(script), str(feature_dir)], check=False)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
