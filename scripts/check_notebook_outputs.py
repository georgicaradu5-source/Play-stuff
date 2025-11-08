#!/usr/bin/env python3
"""
Lightweight notebook output checker for CI.

Exits with code 1 if any .ipynb contains outputs; otherwise 0.
Intended for use in GitHub Actions to enforce clean notebooks.
"""

import json
import sys
from pathlib import Path


def has_outputs(nb_path: Path) -> bool:
    """Return True if the notebook contains any cell outputs."""
    try:
        with nb_path.open("r", encoding="utf-8") as f:
            nb = json.load(f)
        for cell in nb.get("cells", []):
            if cell.get("outputs"):
                return True
            # Also check execution_count (non-None means executed)
            if cell.get("cell_type") == "code" and cell.get("execution_count") is not None:
                return True
    except Exception as e:
        print(f"Error reading {nb_path}: {e}", file=sys.stderr)
        return False
    return False


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    notebooks = list(repo_root.glob("notebooks/**/*.ipynb"))

    dirty = []
    for nb in notebooks:
        if has_outputs(nb):
            dirty.append(nb.relative_to(repo_root))

    if dirty:
        print("❌ The following notebooks contain outputs or execution counts:", file=sys.stderr)
        for path in dirty:
            print(f"   - {path}", file=sys.stderr)
        print("\nRun 'nbstripout <file>' or 'nbstripout notebooks/**/*.ipynb' to strip outputs.", file=sys.stderr)
        return 1

    print("✅ All notebooks are clean (no outputs).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
