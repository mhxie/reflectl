#!/usr/bin/env python3
"""Deterministic stripper + hasher for /sync.

Reads a wiki entry under zk/wiki/, strips fenced ```anchors blocks,
renders each claim's @anchor / @cite / @pass markers as a human-readable
**Sources:** bullet list, appends a synced-from footer, and prints either
the stripped body or its sha256.

Usage:
    scripts/sync_export.py hash zk/wiki/foo.md
    scripts/sync_export.py body zk/wiki/foo.md [--synced-at YYYY-MM-DD]
    scripts/sync_export.py manifest zk/wiki/   # walks dir, emits JSON per file

The LLM should never touch the bytes directly. This script is the single
source of truth for what gets hashed and what gets sent to create_note.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path

ANCHORS_FENCE = re.compile(r"^```anchors\s*\n.*?^```\s*\n", re.MULTILINE | re.DOTALL)
CLAIM_HEADING = re.compile(r"^###\s+\[C(\d+)\]", re.MULTILINE)


def parse_anchors_blocks(text: str) -> dict[str, list[str]]:
    """Return {claim_id: [marker_line, ...]} from all fenced anchors blocks."""
    blocks: dict[str, list[str]] = {}
    for match in re.finditer(
        r"^```anchors\s*\n(?P<body>.*?)^```\s*\n",
        text,
        re.MULTILINE | re.DOTALL,
    ):
        body = match.group("body")
        current: str | None = None
        for raw in body.splitlines():
            line = raw.rstrip()
            if not line:
                continue
            claim_match = re.match(r"\[C(\d+)\]\s*$", line.strip())
            if claim_match:
                current = f"C{claim_match.group(1)}"
                blocks.setdefault(current, [])
                continue
            if current is None:
                continue
            blocks.setdefault(current, []).append(line.strip())
    return blocks


def render_sources_footer(markers: list[str]) -> str:
    if not markers:
        return ""
    bullets = "\n".join(f"- {m}" for m in markers)
    return f"\n**Sources:**\n{bullets}\n"


def strip_body(path: Path, synced_at: str) -> str:
    text = path.read_text(encoding="utf-8")
    anchors = parse_anchors_blocks(text)
    # Drop all fenced anchors blocks.
    stripped = ANCHORS_FENCE.sub("", text)

    # Insert Sources footer under each claim heading if we have markers for it.
    def insert_after_claim(match: re.Match[str]) -> str:
        return match.group(0)

    # Simple pass: append markers at the end of each claim's prose by inserting
    # immediately before the next `### [C` heading or `## ` heading.
    if anchors:
        out_lines: list[str] = []
        current_claim: str | None = None
        pending_markers: list[str] = []
        for line in stripped.splitlines(keepends=False):
            heading_match = CLAIM_HEADING.match(line)
            if heading_match or line.startswith("## "):
                if current_claim and pending_markers:
                    out_lines.append(render_sources_footer(pending_markers).rstrip())
                    out_lines.append("")
                pending_markers = []
                if heading_match:
                    current_claim = f"C{heading_match.group(1)}"
                    pending_markers = list(anchors.get(current_claim, []))
                else:
                    current_claim = None
            out_lines.append(line)
        if current_claim and pending_markers:
            out_lines.append(render_sources_footer(pending_markers).rstrip())
        stripped = "\n".join(out_lines)

    # Normalize trailing whitespace and append footer.
    stripped = stripped.rstrip() + "\n"
    footer = (
        "\n---\n\n"
        f"_Synced from `{path.as_posix()}` on {synced_at}. "
        "Local is authoritative — edits here will not be pulled back._\n"
    )
    return stripped + footer


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_hash = sub.add_parser("hash", help="print sha256 of stripped body")
    p_hash.add_argument("path", type=Path)
    p_hash.add_argument("--synced-at", default=date.today().isoformat())

    p_body = sub.add_parser("body", help="print the stripped body to stdout")
    p_body.add_argument("path", type=Path)
    p_body.add_argument("--synced-at", default=date.today().isoformat())

    p_manifest = sub.add_parser(
        "manifest",
        help="walk a directory and emit JSON {slug, path, sha256, title} per file",
    )
    p_manifest.add_argument("dir", type=Path)
    p_manifest.add_argument("--synced-at", default=date.today().isoformat())

    args = parser.parse_args()

    if args.cmd == "hash":
        body = strip_body(args.path, args.synced_at)
        print(sha256_hex(body))
        return 0

    if args.cmd == "body":
        sys.stdout.write(strip_body(args.path, args.synced_at))
        return 0

    if args.cmd == "manifest":
        entries = []
        for md in sorted(args.dir.glob("*.md")):
            body = strip_body(md, args.synced_at)
            title = ""
            for line in md.read_text(encoding="utf-8").splitlines():
                if line.startswith("# "):
                    title = line[2:].strip()
                    break
            entries.append(
                {
                    "slug": md.stem,
                    "path": md.as_posix(),
                    "title": title,
                    "sha256": sha256_hex(body),
                }
            )
        print(json.dumps(entries, indent=2))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
