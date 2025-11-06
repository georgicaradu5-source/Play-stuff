#!/usr/bin/env python3
"""Scrub non-ASCII characters from docs with consistent ASCII replacements."""

import sys
from pathlib import Path

# Character replacement map
REPLACEMENTS = {
    # Emoji -> ASCII labels
    "\U0001f680": "[ROCKET]",
    "\U0001f3af": "[TARGET]",
    "\u26a1": "[LIGHTNING]",
    "\U0001f6e0\ufe0f": "[TOOLS]",
    "\U0001f6e0": "[TOOLS]",
    "\ufe0f": "",  # variation selector, remove
    "\U0001f3ae": "[GAME]",
    "\U0001f510": "[LOCK]",
    "\U0001f4cb": "[CLIPBOARD]",
    "\U0001f50d": "[SEARCH]",
    "\u2705": "[OK]",
    "\U0001f6a8": "[ALERT]",
    "\u274c": "[X]",
    "\U0001f4ca": "[CHART]",
    "\U0001f6e1\ufe0f": "[SHIELD]",
    "\U0001f6e1": "[SHIELD]",
    "\U0001f4dd": "[MEMO]",
    "\U0001f389": "[PARTY]",
    "\u26a0\ufe0f": "[WARN]",
    "\u26a0": "[WARN]",
    "\U0001f7e2": "[GREEN]",
    # Em dash -> hyphen
    "\u2014": " - ",
    # Non-breaking hyphen -> regular hyphen
    "\u2011": "-",
    # Arrows -> ASCII
    "\u2192": "->",
    # Box drawing -> equals
    "\u2550": "=",
    # Not equal -> !=
    "\u2260": "!=",
}


def scrub_file(file_path: Path) -> tuple[bool, int]:
    """Scrub non-ASCII from a file.

    Returns:
        (changed, replacement_count)
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"[ERROR] Could not read {file_path}: {e}", file=sys.stderr)
        return False, 0

    original = content
    replacements = 0

    for old, new in REPLACEMENTS.items():
        if old in content:
            count = content.count(old)
            content = content.replace(old, new)
            replacements += count

    if content != original:
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"[OK] Scrubbed {file_path}: {replacements} replacements")
            return True, replacements
        except Exception as e:
            print(f"[ERROR] Could not write {file_path}: {e}", file=sys.stderr)
            return False, 0

    return False, 0


def main():
    """Scrub all docs."""
    docs_dir = Path("docs")
    if not docs_dir.exists():
        print("[ERROR] docs/ directory not found", file=sys.stderr)
        return 1

    total_files = 0
    total_changed = 0
    total_replacements = 0

    for file_path in docs_dir.rglob("*.md"):
        # Skip archived/legacy
        if "_archive" in file_path.parts or "legacy" in file_path.parts:
            continue

        total_files += 1
        changed, count = scrub_file(file_path)
        if changed:
            total_changed += 1
            total_replacements += count

    print(f"\n[SUMMARY] Processed {total_files} files")
    print(f"[SUMMARY] Changed {total_changed} files")
    print(f"[SUMMARY] Made {total_replacements} total replacements")

    return 0


if __name__ == "__main__":
    sys.exit(main())
