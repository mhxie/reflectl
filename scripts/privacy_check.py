#!/usr/bin/env python3
"""
privacy_check.py: Detect private-vault filename leaks in the committed repo.

Rationale: `zk/` is the user's private knowledge vault (gitignored). A
multi-word filename stem like `Note Title With Spaces` is usually a
unique topic label the user picked for a private note. If that exact
string appears as literal text in a tracked file (CLAUDE.md, a
protocol, a script, a command), the system has leaked the existence
and title of the private note to the public git history.

CLAUDE.md's privacy rule prohibits leaking org/project/internal names.
This script operationalizes the check against the vault itself: whatever
multi-word filenames live under the private dirs below are treated as
private identifiers.

What counts as private:
  - `*.md` filename stems under the PRIVATE_DIRS list.
  - 2+ words (single-word stems like `index` or `README` are skipped —
    too many false positives).
  - Explicit opt-out via `privacy_allowlist.txt` (newline-delimited
    stems, relative paths or bare stems both accepted). Use this only
    for stems the user is deliberately comfortable exposing.

CLI:
    uv run scripts/privacy_check.py            human report
    uv run scripts/privacy_check.py --json     machine-readable output

Exit code: 0 if no hits, 1 if any hit (treat as ERROR), 2 on IO error.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ZK = Path(os.environ.get("ZK", "zk"))
ALLOWLIST = Path(__file__).resolve().parent / "privacy_allowlist.txt"

PRIVATE_DIRS = [
    "wiki", "wiki-cn", "papers", "research", "agent-findings",
    "preprints", "reflections", "drafts", "gtd", "handoffs",
    "health", "finance", "luma", "travel", "planning",
    "sessions", "profile", "daily-notes", "personal",
]

SKIP_STEMS = {"index", "README"}


def load_allowlist() -> set[str]:
    if not ALLOWLIST.exists():
        return set()
    out: set[str] = set()
    for line in ALLOWLIST.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        out.add(s)
    return out


def collect_titles(root: Path, allowlist: set[str]) -> list[str]:
    titles: set[str] = set()
    for sub in PRIVATE_DIRS:
        p = root / sub
        if not p.exists():
            continue
        for f in p.rglob("*.md"):
            stem = f.stem
            if stem in SKIP_STEMS or len(stem.split()) < 2:
                continue
            if stem in allowlist:
                continue
            titles.add(stem)
    return sorted(titles)


def tracked_files() -> list[str]:
    res = subprocess.run(
        ["git", "ls-files"], capture_output=True, text=True
    )
    if res.returncode != 0:
        sys.stderr.write(
            f"privacy_check: `git ls-files` failed: {res.stderr}\n"
        )
        sys.exit(2)
    return [line for line in res.stdout.splitlines() if line.strip()]


def scan(titles: list[str], files: list[str]) -> list[dict]:
    hits: list[dict] = []
    for f in files:
        path = Path(f)
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except (OSError, UnicodeDecodeError):
            continue
        lines = content.splitlines()
        for t in titles:
            for i, line in enumerate(lines, 1):
                if t in line:
                    hits.append({
                        "file": f,
                        "line": i,
                        "private_title": t,
                    })
                    break
    return hits


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="scripts/privacy_check.py",
        description=(
            "Scan tracked files for private-vault filename leaks. Fails "
            "with exit 1 if any multi-word private filename stem appears "
            "as a literal substring in a committed file."
        ),
    )
    ap.add_argument("--json", action="store_true", help="Emit JSON output.")
    args = ap.parse_args(argv)

    if not ZK.exists():
        msg = f"privacy_check: {ZK} does not exist; nothing to check against"
        if args.json:
            print(json.dumps(
                {"zk_missing": True, "titles_scanned": 0, "hits": []},
                indent=2,
            ))
        else:
            sys.stderr.write(msg + "\n")
        return 0

    allowlist = load_allowlist()
    titles = collect_titles(ZK, allowlist)
    files = tracked_files()
    hits = scan(titles, files) if titles else []

    if args.json:
        print(json.dumps({
            "zk_dir": ZK.as_posix(),
            "titles_scanned": len(titles),
            "allowlist_size": len(allowlist),
            "hit_count": len(hits),
            "hits": hits,
        }, indent=2))
    else:
        if not hits:
            print(
                f"privacy_check: clean ({len(titles)} private titles "
                f"scanned, 0 leaks)"
            )
            return 0
        files_hit = sorted({h["file"] for h in hits})
        print(
            f"privacy_check: {len(hits)} leak(s) across "
            f"{len(files_hit)} file(s)"
        )
        for h in hits:
            print(f"  {h['file']}:{h['line']}: {h['private_title']!r}")
        print()
        print(
            "Each line shows a multi-word filename stem from your private "
            "$ZK vault appearing in a tracked file. Replace with a generic "
            "placeholder, or add the stem to scripts/privacy_allowlist.txt "
            "if the exposure is deliberate."
        )

    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
