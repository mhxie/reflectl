#!/usr/bin/env python3
"""Split daily-notes/YYYY-MM-DD.md into daily-notes/YYYY/YYYY-MM/YYYY-MM-DD.md.

Per protocols/repo-conventions.md fission rule (32-entry threshold). Two-level
grouping (year then year-month) keeps every directory under threshold:
  - daily-notes/        : 8 year subdirs (2018-2026)
  - daily-notes/YYYY/   : up to 12 month subdirs
  - daily-notes/YYYY/YYYY-MM/ : up to 31 daily files

Also rewrites markdown refs across all tracked .md to point at the new path.

Usage:
  uv run scripts/fission_daily_notes.py --dry-run
  uv run scripts/fission_daily_notes.py --apply
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OV = (REPO_ROOT / "zk").resolve()
DAILY = OV / "daily-notes"

ISO_FILENAME_RE = re.compile(r"^(\d{4})-(\d{2})-\d{2}\.md$")
SKIP_DIRS = {"secure", "personal", "cache", ".obsidian", ".trash", "raw", "assets"}

# Markdown link patterns referencing daily-notes/YYYY-MM-DD.md (any prefix path)
DAILY_LINK_RE = re.compile(
    r"(\]\(<?(?:[^)>]*?/)?)daily-notes/(\d{4})-(\d{2})-(\d{2})\.md(#[^)>]*)?(>?\))"
)
# Wrap path in <> when it contains a space — but no daily-note path has spaces
# under the new YYYY/YYYY-MM/ scheme, so we always emit plain (path).


def plan_moves() -> list[tuple[Path, Path]]:
    """Return list of (src, dst) pairs for every YYYY-MM-DD.md at top of daily-notes/.
    Target: daily-notes/YYYY/YYYY-MM/YYYY-MM-DD.md (two-level grouping)."""
    moves: list[tuple[Path, Path]] = []
    for f in sorted(DAILY.iterdir()):
        if not f.is_file():
            continue
        m = ISO_FILENAME_RE.match(f.name)
        if not m:
            continue
        year, month = m.group(1), m.group(2)
        dst_dir = DAILY / year / f"{year}-{month}"
        dst = dst_dir / f.name
        moves.append((f, dst))
    return moves


def update_links_in_file(path: Path, dry_run: bool) -> int:
    """Rewrite daily-notes/YYYY-MM-DD.md → daily-notes/YYYY-MM/YYYY-MM-DD.md
    in this file. Returns count of replacements."""

    def _sub(m: re.Match) -> str:
        prefix = m.group(1)
        year, month, day = m.group(2), m.group(3), m.group(4)
        anchor = m.group(5) or ""
        suffix = m.group(6)
        return f"{prefix}daily-notes/{year}/{year}-{month}/{year}-{month}-{day}.md{anchor}{suffix}"

    text = path.read_text(encoding="utf-8")
    new_text, n = DAILY_LINK_RE.subn(_sub, text)
    if n and not dry_run:
        path.write_text(new_text, encoding="utf-8")
    return n


def main() -> None:
    ap = argparse.ArgumentParser()
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    if not DAILY.is_dir():
        print(f"[error] {DAILY} not found", file=sys.stderr)
        sys.exit(1)

    moves = plan_moves()
    print(f"[plan] {len(moves)} files to move", file=sys.stderr)

    months_touched = sorted({m[1].parent.name for m in moves})
    print(f"[plan] {len(months_touched)} month subdirs: {months_touched[0]} … {months_touched[-1]}",
          file=sys.stderr)

    # Move files
    if args.apply:
        for src, dst in moves:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))
        print(f"[apply] moved {len(moves)} files", file=sys.stderr)
    else:
        print(f"[dry-run] would move {len(moves)} files", file=sys.stderr)
        for src, dst in moves[:3]:
            print(f"          {src.relative_to(OV)} → {dst.relative_to(OV)}", file=sys.stderr)
        if len(moves) > 3:
            print(f"          ... +{len(moves) - 3} more", file=sys.stderr)

    # Rewrite refs across all .md
    print(f"\n[refs] scanning all .md for daily-notes/ refs...", file=sys.stderr)
    total_files_changed = 0
    total_replacements = 0
    for f in OV.rglob("*.md"):
        rel = f.relative_to(OV)
        if any(p in SKIP_DIRS for p in rel.parts):
            continue
        n = update_links_in_file(f, dry_run=not args.apply)
        if n:
            total_files_changed += 1
            total_replacements += n

    action = "applied" if args.apply else "dry-run"
    print(f"[refs] {total_files_changed} files would change, {total_replacements} replacements ({action})",
          file=sys.stderr)


if __name__ == "__main__":
    main()
