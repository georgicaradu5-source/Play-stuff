#!/usr/bin/env python3
"""
Fail CI if any Jupyter notebook (*.ipynb) in the repo contains executed outputs or execution counts.
- Exits with code 1 on any violations and prints a concise report.
- Skips files in common ignored directories (e.g., .venv, venv, .git, node_modules, _archive/ if desired?).
- Pure stdlib, no external deps.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SKIP_DIRS = {
    ".git",
    "venv",
    ".venv",
    "env",
    ".mypy_cache",
    "__pycache__",
    "node_modules",
}

# Allow outputs in archived snapshots if needed? Keep strict by default.
ALLOWED_PATH_SUBSTRINGS = set()


def notebook_has_outputs(nb_path: Path) -> tuple[bool, list[str]]:
    problems: list[str] = []
    try:
        with nb_path.open("r", encoding="utf-8") as f:
            nb = json.load(f)
    except Exception as e:
        return True, [f"{nb_path}: Failed to parse JSON: {e}"]

    cells = nb.get("cells", [])
    for idx, cell in enumerate(cells, start=1):
        if cell.get("cell_type") != "code":
            continue
        outputs = cell.get("outputs")
        exec_count = cell.get("execution_count")
        if outputs:
            problems.append(f"{nb_path} [cell {idx}]: has outputs ({len(outputs)})")
        if exec_count not in (None, 0):
            problems.append(f"{nb_path} [cell {idx}]: has execution_count={exec_count}")
    return (len(problems) > 0), problems


def should_skip(path: Path) -> bool:
    parts = set(p.name for p in path.parents) | {path.name}
    if parts & SKIP_DIRS:
        return True
    for sub in ALLOWED_PATH_SUBSTRINGS:
        if sub in str(path).replace("\\", "/"):
            return True
    return False


def main() -> int:
    root = Path.cwd()
    violations: list[str] = []
    for nb_path in root.rglob("*.ipynb"):
        if should_skip(nb_path):
            continue
        has_outputs, probs = notebook_has_outputs(nb_path)
        if has_outputs:
            violations.extend(probs)
    if violations:
        print("Notebook output check: FAIL", file=sys.stderr)
        for v in violations:
            print(f" - {v}", file=sys.stderr)
        print("\nHint: Run 'nbstripout --install' once and commit stripped notebooks.", file=sys.stderr)
        return 1
    print("Notebook output check: PASS - no outputs found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
