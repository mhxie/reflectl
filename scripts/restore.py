#!/usr/bin/env python3
"""
restore.py: Emergency-only helper for /restore.

Given a list of Reflect note IDs and their target slugs, this script does
two things:

  1. Confirms whether a local wiki file at `zk/wiki/<slug>.md` is missing
     (the only case where recovery from Reflect is warranted).
  2. Prints the intended cache path `zk/cache/restore-<slug>.md` where the
     /restore command will stage the Reflect body after calling the MCP
     `get_note(id)` escape hatch.

This script does NOT call MCP. It does not write to Reflect, it does not
write to zk/wiki/, and it does not maintain any idempotency ledger. The
former sync manifest is gone; /restore now requires the user to supply
the Reflect note IDs (which the user can find in Reflect itself).

**Critical limitation — read before running /restore.**

Wiki entries that were ever pushed to Reflect (via the retired wiki-push
`/sync` or via a manual share) have been mutated on ingestion:

  1. Fenced ```anchors``` blocks were stripped at push time and replaced
     with a human-readable **Sources:** bullet list (if the push was the
     old /sync flow). Direct shares via the manual Curator path preserve
     the raw file content.
  2. Reflect itself auto-prepends an H1, wraps bare URLs in <...>, and
     normalizes --- to ***.

What comes back from Reflect may therefore be **degraded prose**, not a
drop-in replacement for the original `zk/wiki/<slug>.md`. You cannot
restore a valid wiki entry by byte-copying the Reflect body into place —
trust.py will fail the parse if the anchors fences are missing.

The correct recovery workflow is:

  1. /restore fetches the Reflect body into `zk/cache/restore-<slug>.md`.
  2. You read the prose, the claim titles, and the Sources footer.
  3. You re-author `zk/wiki/<slug>.md` by hand, reconstructing the
     `anchors` fences and filling in anything the lossy pipeline dropped.
  4. You rerun `scripts/trust.py` and `scripts/lint.py` to confirm the
     reconstructed entry parses cleanly.

This is a very rare emergency path. In the common case of working-copy
churn, git + the local file is the right answer — not this script.

CLI:
    scripts/restore.py plan --slug <slug> --note-id <id> [--slug <s2> --note-id <id2> ...]
        Print a JSON plan of (slug, note_id, cache_path, present_locally)
        tuples for the /restore command to execute against.

Exit code 0 on success, 2 on IO / CLI error.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

WIKI_DIR = Path("zk/wiki")
CACHE_DIR = Path("zk/cache")


def plan(pairs: list[tuple[str, str]]) -> int:
    entries = []
    for slug, note_id in pairs:
        wiki_path = WIKI_DIR / f"{slug}.md"
        entries.append(
            {
                "slug": slug,
                "reflect_note_id": note_id,
                "wiki_path": wiki_path.as_posix(),
                "present_locally": wiki_path.exists(),
                "cache_path": (CACHE_DIR / f"restore-{slug}.md").as_posix(),
            }
        )
    payload = {
        "wiki_dir": WIKI_DIR.as_posix(),
        "cache_dir": CACHE_DIR.as_posix(),
        "missing_count": sum(1 for e in entries if not e["present_locally"]),
        "total_count": len(entries),
        "plan": entries,
    }
    print(json.dumps(payload, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="scripts/restore.py",
        description=(
            "Stage a /restore plan given user-supplied (slug, reflect_note_id) pairs. "
            "Emergency recovery only. Does not call MCP or write to Reflect."
        ),
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_plan = sub.add_parser(
        "plan",
        help=(
            "Print a JSON plan for /restore to execute. Requires matched "
            "--slug / --note-id pairs (can be specified multiple times)."
        ),
    )
    p_plan.add_argument(
        "--slug",
        action="append",
        default=[],
        help="Wiki entry slug (filename stem under zk/wiki/, e.g. 'Sample Wiki Entry').",
    )
    p_plan.add_argument(
        "--note-id",
        action="append",
        default=[],
        help="Reflect note ID returned by an earlier create_note or visible in the Reflect UI.",
    )

    args = parser.parse_args(argv)

    if args.cmd == "plan":
        if len(args.slug) != len(args.note_id):
            sys.stderr.write(
                f"restore: --slug count ({len(args.slug)}) must equal --note-id count "
                f"({len(args.note_id)})\n"
            )
            return 2
        if not args.slug:
            sys.stderr.write(
                "restore: at least one --slug / --note-id pair is required\n"
            )
            return 2
        return plan(list(zip(args.slug, args.note_id)))

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
