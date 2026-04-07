#!/usr/bin/env python3
"""
restore.py: Diagnose wiki entries that exist in the sync manifest but are
missing from zk/wiki/ on disk. Emergency-only.

This script does NOT call MCP or write to Reflect. It only inspects local
state and prints a JSON plan. The /restore command is responsible for the
MCP `get_note` calls that follow and for staging recovered bodies into
zk/cache/restore-<slug>.md.

**Critical limitation — read before running /restore.**

The /sync pipeline is LOSSY for wiki entries:

  1. `sync_export.py` strips the fenced ```anchors``` blocks (the
     machine-readable @anchor / @cite / @pass markers that trust.py scores
     on) and replaces them with a human-readable **Sources:** bullet list.
  2. Reflect mutates the body on ingestion: auto-prepends an H1, wraps
     bare URLs in <...>, normalizes --- to ***.

What comes back from Reflect is therefore **degraded prose**, not a
drop-in replacement for the original `zk/wiki/<slug>.md`. You cannot
restore a valid wiki entry by byte-copying the Reflect body into place —
trust.py will fail the parse (missing `anchors` fences, structural
integrity items 5/6/7), and /sync will be blocked.

The correct recovery workflow is:

  1. /restore fetches the Reflect body into `zk/cache/restore-<slug>.md`.
  2. You read the prose, the claim titles, and the Sources footer.
  3. You re-author `zk/wiki/<slug>.md` by hand, reconstructing the
     `anchors` fences from the Sources bullets and filling in any
     details the lossy pipeline dropped.
  4. You rerun `scripts/trust.py` and `scripts/lint.py` to confirm the
     reconstructed entry parses cleanly before /sync.

This is a very rare emergency path: an AI-driven operation (or a finger
slip) deleted or corrupted a wiki entry locally, and the Reflect copy is
the only surviving snapshot. In the common case of working-copy churn,
git + the local file is the right answer — not this script.

CLI:
    scripts/restore.py diagnose            JSON plan of missing slugs
    scripts/restore.py diagnose --all      include present slugs too

Exit code 0 if the diagnose pass ran, 2 on IO / manifest error.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

MANIFEST_PATH = Path("zk/.sync-manifest.json")
WIKI_DIR = Path("zk/wiki")
CACHE_DIR = Path("zk/cache")


def load_manifest() -> dict:
    if not MANIFEST_PATH.exists():
        sys.stderr.write(
            f"restore: {MANIFEST_PATH} does not exist — nothing to restore from.\n"
        )
        sys.exit(2)
    try:
        data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        sys.stderr.write(f"restore: cannot parse manifest: {e}\n")
        sys.exit(2)
    if not isinstance(data, dict) or not isinstance(data.get("entries"), dict):
        sys.stderr.write("restore: manifest missing or malformed `entries` dict\n")
        sys.exit(2)
    return data


def diagnose(include_present: bool) -> int:
    manifest = load_manifest()
    entries = manifest["entries"]

    plan = []
    for slug, row in sorted(entries.items()):
        wiki_path = WIKI_DIR / f"{slug}.md"
        present = wiki_path.exists()
        if present and not include_present:
            continue
        plan.append(
            {
                "slug": slug,
                "wiki_path": wiki_path.as_posix(),
                "present_locally": present,
                "reflect_note_id": row.get("reflect_note_id"),
                "synced_at": row.get("synced_at"),
                "content_sha256": row.get("content_sha256"),
                "cache_path": (CACHE_DIR / f"restore-{slug}.md").as_posix(),
            }
        )

    payload = {
        "manifest_path": MANIFEST_PATH.as_posix(),
        "wiki_dir": WIKI_DIR.as_posix(),
        "cache_dir": CACHE_DIR.as_posix(),
        "missing_count": sum(1 for e in plan if not e["present_locally"]),
        "total_count": len(plan),
        "plan": plan,
    }
    print(json.dumps(payload, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="scripts/restore.py",
        description="Diagnose wiki entries missing from zk/wiki/ (emergency recovery only).",
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_diag = sub.add_parser(
        "diagnose",
        help="Print a JSON plan of slugs in the manifest that are missing locally.",
    )
    p_diag.add_argument(
        "--all",
        action="store_true",
        help="Include slugs that ARE present locally (full manifest view).",
    )

    args = parser.parse_args(argv)

    if args.cmd == "diagnose":
        return diagnose(include_present=args.all)

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
