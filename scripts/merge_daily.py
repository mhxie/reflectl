#!/usr/bin/env python3
"""
merge_daily.py: Merge a local daily note with Reflect's version.

Reflect returns daily notes with YAML frontmatter + H1 + bullet content. Local
files (Obsidian-style) skip the frontmatter and sometimes differ in H1. This
script strips Reflect's frontmatter, then takes a line-level union so no
captured content is lost from either side.

Output modes: write to `--output` (default: overwrite local) or `--dry-run`.
Prints a status marker on stderr: new / unchanged / identical / merged.

Only touches the files the caller passes in. Enumerating dates and calling
MCP is the orchestrator's job.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def strip_yaml_frontmatter(text: str) -> str:
    """Remove a leading YAML frontmatter block delimited by `---` lines.

    Normalizes CRLF to LF first so Reflect responses with Windows-style
    line endings are handled identically to LF-only ones.
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if not text.startswith("---\n"):
        return text
    end = text.find("\n---\n", 4)
    if end == -1:
        end = text.find("\n---", 4)
        if end == -1 or end + 4 != len(text.rstrip()):
            return text
    return text[end + 5:].lstrip("\n")


_WS = re.compile(r"\s+")
_MERGE_MARKER = "<!-- merged from Reflect -->"


def norm(line: str) -> str:
    """Normalize a line for dedup: strip, collapse whitespace."""
    return _WS.sub(" ", line.strip())


def merge(local: str, reflect: str) -> tuple[str, str]:
    """Merge local and Reflect bodies. Returns (merged_text, status)."""
    reflect_body = strip_yaml_frontmatter(reflect).rstrip()
    local_body = local.rstrip()

    if not local_body and not reflect_body:
        return "", "empty"
    if not local_body:
        return reflect_body + "\n", "new"
    if not reflect_body:
        return local_body + "\n", "unchanged"

    # Same content after normalization: prefer local (may have Obsidian-style embeds).
    if norm(local_body) == norm(reflect_body):
        return local_body + "\n", "identical"

    seen: set[str] = set()
    for line in local_body.splitlines():
        n = norm(line)
        if n:
            seen.add(n)

    extras: list[str] = []
    for line in reflect_body.splitlines():
        n = norm(line)
        if not n or n in seen:
            continue
        extras.append(line)
        seen.add(n)

    if not extras:
        return local_body + "\n", "unchanged"

    # If local already has a `<!-- merged from Reflect -->` marker from a
    # prior run, append new Reflect-only lines under it instead of adding
    # a second marker. This keeps the file tidy across repeated syncs
    # without discarding any content the user has written below the
    # marker (those lines survive via the line-union above).
    extras_text = "\n".join(extras).rstrip()
    if _MERGE_MARKER in local_body:
        merged = local_body + "\n" + extras_text + "\n"
    else:
        merged = local_body + "\n\n" + _MERGE_MARKER + "\n" + extras_text + "\n"
    return merged, "merged"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("local", help="Path to local daily note (may not exist)")
    ap.add_argument("reflect", help="Path to Reflect-sourced content file")
    ap.add_argument("-o", "--output", help="Output path (default: overwrite local)")
    ap.add_argument("--dry-run", action="store_true", help="Print merged content to stdout; do not write")
    args = ap.parse_args()

    local_path = Path(args.local)
    reflect_path = Path(args.reflect)

    local_text = local_path.read_text(encoding="utf-8") if local_path.exists() else ""
    if not reflect_path.exists():
        print(f"error: reflect file not found: {reflect_path}", file=sys.stderr)
        return 2
    reflect_text = reflect_path.read_text(encoding="utf-8")

    # Treat MCP's "No daily note found" sentinel as empty Reflect content.
    if reflect_text.strip().lower().startswith("no daily note found"):
        reflect_text = ""

    merged, status = merge(local_text, reflect_text)

    if args.dry_run:
        sys.stdout.write(merged)
        print(f"status: {status}", file=sys.stderr)
        return 0

    out = Path(args.output) if args.output else local_path

    # Skip writing if unchanged or identical to existing content.
    if out.exists():
        existing = out.read_text(encoding="utf-8")
        if existing == merged:
            print(f"{status}\t{out}", file=sys.stderr)
            return 0

    if status == "empty":
        print(f"skip (empty)\t{out}", file=sys.stderr)
        return 0

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(merged, encoding="utf-8")
    print(f"{status}\t{out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
