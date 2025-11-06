#!/usr/bin/env python3
"""ASCII compliance checker for source code and documentation.

This script scans Python source files and Markdown documentation for non-ASCII
characters (byte values > 0x7F). It's designed to prevent Windows encoding
issues and ensure cross-platform compatibility.

Usage:
    python scripts/check_ascii.py

    Or from VS Code task / GitHub Actions:
    python scripts/check_ascii.py --fail-fast

Exit codes:
    0: All files are ASCII-compliant
    1: Non-ASCII characters found in active files
    2: Script error (missing dependencies, permissions, etc.)

Configuration:
    - Default scan scope: src/
    - Optional: include docs/ via --scan-dirs src docs
    - Excludes: _archive/, legacy/, __pycache__, *.pyc, .git/
    - File types: .py, .md, .txt, .yaml, .yml, .toml, .ini, .cfg

Example output:
    [ERROR] Non-ASCII in src/main.py:42: print("Success!")
    [ERROR] Non-ASCII in README.md:10: - Checkmark emoji
    [FAIL] Found 2 files with non-ASCII characters
"""

import argparse
import sys
from pathlib import Path
from typing import NamedTuple


class NonAsciiMatch(NamedTuple):
    """A non-ASCII character match."""

    file: Path
    line_num: int
    line_content: str
    char_position: int
    char_value: int


class AsciiChecker:
    """Scanner for non-ASCII characters in text files."""

    def __init__(
        self,
        scan_dirs: list[str] | None = None,
        exclude_dirs: list[str] | None = None,
        file_extensions: list[str] | None = None,
        fail_fast: bool = False,
    ):
        """Initialize the ASCII checker.

        Args:
            scan_dirs: Directories to scan (default: src/)
            exclude_dirs: Directories to exclude (default: _archive/, legacy/, __pycache__)
            file_extensions: File types to scan (default: .py, .md, .txt, .yaml, .yml)
            fail_fast: Stop on first non-ASCII file (default: False)
        """
        self.scan_dirs = scan_dirs or ["src"]
        self.exclude_dirs = exclude_dirs or ["_archive", "legacy", "__pycache__", ".git"]
        self.file_extensions = file_extensions or [
            ".py",
            ".md",
            ".txt",
            ".yaml",
            ".yml",
            ".toml",
            ".ini",
            ".cfg",
        ]
        self.fail_fast = fail_fast
        self.matches: list[NonAsciiMatch] = []

    def is_excluded(self, path: Path) -> bool:
        """Check if a path should be excluded from scanning.

        Args:
            path: Path to check

        Returns:
            True if path should be excluded, False otherwise
        """
        parts = path.parts
        return any(excluded in parts for excluded in self.exclude_dirs)

    def scan_file(self, file_path: Path) -> list[NonAsciiMatch]:
        """Scan a single file for non-ASCII characters.

        Args:
            file_path: Path to file to scan

        Returns:
            List of non-ASCII character matches
        """
        matches: list[NonAsciiMatch] = []

        try:
            with open(file_path, encoding="utf-8", errors="replace") as f:
                for line_num, line in enumerate(f, start=1):
                    for char_pos, char in enumerate(line):
                        if ord(char) > 0x7F:
                            matches.append(
                                NonAsciiMatch(
                                    file=file_path,
                                    line_num=line_num,
                                    line_content=line.rstrip(),
                                    char_position=char_pos,
                                    char_value=ord(char),
                                )
                            )
                            if self.fail_fast:
                                return matches

        except (OSError, UnicodeDecodeError) as e:
            print(f"[WARNING] Could not read {file_path}: {e}", file=sys.stderr)

        return matches

    def scan_directory(self, directory: str | Path) -> int:
        """Scan a directory tree for non-ASCII characters.

        Args:
            directory: Directory to scan

        Returns:
            Number of files with non-ASCII characters
        """
        dir_path = Path(directory)
        if not dir_path.exists():
            print(f"[WARNING] Directory not found: {directory}, skipping", file=sys.stderr)
            return 0

        files_with_issues = 0

        for file_path in dir_path.rglob("*"):
            # Skip directories and excluded paths
            if not file_path.is_file() or self.is_excluded(file_path):
                continue

            # Check file extension
            if file_path.suffix not in self.file_extensions:
                continue

            # Scan the file
            file_matches = self.scan_file(file_path)
            if file_matches:
                files_with_issues += 1
                self.matches.extend(file_matches)

                if self.fail_fast:
                    return files_with_issues

        return files_with_issues

    def run(self) -> int:
        """Run the ASCII compliance check.

        Returns:
            Exit code (0 = success, 1 = non-ASCII found, 2 = error)
        """
        print("[INFO] Starting ASCII compliance check...")
        print(f"[INFO] Scanning directories: {', '.join(self.scan_dirs)}")
        print(f"[INFO] Excluding: {', '.join(self.exclude_dirs)}")
        print()

        total_files_with_issues = 0

        for scan_dir in self.scan_dirs:
            files_with_issues = self.scan_directory(scan_dir)
            total_files_with_issues += files_with_issues

            if self.fail_fast and total_files_with_issues > 0:
                break

        # Report results
        if self.matches:
            print(f"\n[FAIL] Found {len(self.matches)} non-ASCII characters in {total_files_with_issues} files:\n")

            for match in self.matches:
                # Produce ASCII-safe line preview using backslash escapes
                safe_line = match.line_content.encode("ascii", "backslashreplace").decode("ascii")
                if len(safe_line) > 80:
                    safe_line = safe_line[:80] + "..."

                print(f"  {match.file}:{match.line_num}:{match.char_position} " f"(U+{match.char_value:04X})")
                print(f"    {safe_line}")
                print()

            return 1

        print("[OK] All files are ASCII-compliant!")
        return 0


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Check source files for non-ASCII characters",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop scanning after first non-ASCII file",
    )
    parser.add_argument(
        "--scan-dirs",
        nargs="+",
        default=["src"],
        help="Directories to scan (default: src) - add docs explicitly if desired",
    )
    parser.add_argument(
        "--exclude-dirs",
        nargs="+",
        default=["_archive", "legacy", "__pycache__", ".git"],
        help="Directories to exclude (default: _archive legacy __pycache__ .git)",
    )

    args = parser.parse_args()

    try:
        checker = AsciiChecker(
            scan_dirs=args.scan_dirs,
            exclude_dirs=args.exclude_dirs,
            fail_fast=args.fail_fast,
        )
        return checker.run()

    except KeyboardInterrupt:
        print("\n[WARNING] Interrupted by user", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"\n[ERROR] Script error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
