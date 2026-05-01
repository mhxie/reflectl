#!/usr/bin/env python3
"""
log_backlinks.py: Retrofit `[[YYYY-MM-DD]]` wikilinks in markdown table date cells.

Converts `| YYYY-MM-DD |` -> `| [[YYYY-MM-DD]] |` so each row backlinks the
daily note for that date (Obsidian unresolved-link aggregation).

Design notes:
  * Uses lookahead `(?=\\|)` so the trailing `|` is NOT consumed. This means
    consecutive date cells (`| 2025-06-13 | 2025-06-13 |`) all match — the
    sed `/g` greediness gotcha is sidestepped.
  * Negative lookbehind `(?<!\\[\\[)` is belt-and-suspenders against
    double-wrapping, though the leading `| ` literal already prevents it.
  * Single-space convention only (`| YYYY-MM-DD |`). Files with irregular
    spacing won't match — by design, to avoid silent over-rewrites.
  * YAML frontmatter `date: 2026-04-26` is safe (no surrounding `|`).
  * Inline references like `(2026-04-24)` are NOT touched (no surrounding `|`).

Usage:
    uv run scripts/log_backlinks.py --dry-run FILE [FILE ...]
    uv run scripts/log_backlinks.py FILE [FILE ...]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

PATTERN = re.compile(
    r"(?<!\[\[)"                       # not already wikilinked
    r"\| (20\d{2}-\d{2}-\d{2}) "       # | YYYY-MM-DD (single trailing space)
    r"(?=\|)"                          # followed by | (lookahead, not consumed)
)
REPLACEMENT = r"| [[\1]] "


def retrofit(path: Path, dry_run: bool) -> tuple[int, list[tuple[int, str, str]]]:
    """Return (count, list of (line_num, old_line, new_line)) for changes."""
    original = path.read_text()
    updated, count = PATTERN.subn(REPLACEMENT, original)
    if count == 0:
        return 0, []

    diffs: list[tuple[int, str, str]] = []
    old_lines = original.splitlines()
    new_lines = updated.splitlines()
    for i, (old, new) in enumerate(zip(old_lines, new_lines), 1):
        if old != new:
            diffs.append((i, old, new))

    if not dry_run:
        path.write_text(updated)

    return count, diffs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="Show diff without writing")
    ap.add_argument("--max-show", type=int, default=5, help="Max diff lines per file (default 5)")
    ap.add_argument("files", nargs="+", type=Path)
    args = ap.parse_args()

    grand_total = 0
    for f in args.files:
        if not f.exists():
            print(f"! {f}: not found", file=sys.stderr)
            continue
        count, diffs = retrofit(f, dry_run=args.dry_run)
        marker = "[dry-run]" if args.dry_run else "[applied]"
        print(f"{marker} {f}: {count} wikilinks")
        for line_num, old, new in diffs[: args.max_show]:
            print(f"    L{line_num}")
            print(f"      - {old}")
            print(f"      + {new}")
        if len(diffs) > args.max_show:
            print(f"    ... ({len(diffs) - args.max_show} more)")
        grand_total += count

    print(f"\nTotal: {grand_total} wikilinks across {len(args.files)} file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
