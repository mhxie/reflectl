#!/usr/bin/env python3
"""
auto_memory_audit.py: Audit pass over Claude Code auto-memory.

atelier's auto-memory lives at:
    ~/.claude-personal/projects/<encoded-cwd>/memory/

with a flat layout:
    MEMORY.md          (index — one wikilink per line)
    feedback_*.md      (system-correcting notes)
    user_*.md          (stable user-fact notes)

This is a *capability-side* check: surface entries that may have
gone poison (stale, orphaned, dead-linked, or self-flagged
provisional) so the human can decide invalidation. The script is
the (A) path of the bi-temporal forgetting design — it produces
data without yet imposing schema. Frontmatter-level expiry
(verified_at / invalidates_when) is left to (B).

Audit categories (all advisory; never mutates):

  [1] dead-link    — MEMORY.md links to a file that does not exist.
  [2] orphan       — .md file under memory/ has no MEMORY.md entry.
  [3] stale        — file mtime older than --threshold days
                     (default 90). mtime is the proxy for
                     verified_at while the schema is unversioned.
  [4] provisional  — body contains an explicit self-flag
                     ("provisional", "promote after N sessions",
                     "N-day window") that the index does not
                     surface.
  [5] frontmatter  — file is missing one of name/description/type.
  [6] index-bloat  — MEMORY.md exceeds 200 lines (Claude truncates
                     beyond that — entries past line 200 become
                     invisible silently).

CLI:
    uv run scripts/auto_memory_audit.py            human report
    uv run scripts/auto_memory_audit.py --json     machine-readable
    uv run scripts/auto_memory_audit.py --threshold 60   custom stale window
    uv run scripts/auto_memory_audit.py --dir <path>     custom memory dir

Exit code: 0 always (audit is advisory). Missing memory dir is
reported as a `memory-dir-missing` INFO finding so callers
parsing --json never see a non-zero exit on first-run setup.

Design notes:
  - Stdlib only. Mirrors scripts/zk_audit.py / privacy_check.py style.
  - Memory dir is auto-discovered from CWD using Claude Code's
    project encoding ("/" → "-"); override via --dir or
    CLAUDE_MEMORY_DIR.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_STALE_DAYS = 90
INDEX_TRUNCATION_LIMIT = 200
INDEX_FILENAME = "MEMORY.md"
REQUIRED_FRONTMATTER = ("name", "description", "type")

# Match lines in MEMORY.md of the form:
#   - [Title](file.md) - description
#   - [Title](file.md) — description
#   - [Title](file.md)             (description optional)
_INDEX_ENTRY_RE = re.compile(r'^-\s*\[([^\]]+)\]\(([^\)]+)\)(?:\s*[-—]\s*(.+))?$')

# Self-flagged provisional markers in body text. Conservative —
# only literal phrases the user has actually used in prior memories.
_PROVISIONAL_RE = re.compile(
    r'\b(provisional|tentative|'
    r'(?:after|across|in)\s+\d+\+?\s*(?:more\s+)?'
    r'(?:independent\s+)?(?:sessions?|applications?)|'
    r'\d+\+?\s+(?:more\s+)?independent\s+(?:sessions?|applications?)|'
    r'\d+[-\s]?day\s+window|'
    r'durab\w+\s+pending|'
    r'promote\s+(?:to|after)\b)',
    re.IGNORECASE,
)


@dataclass
class Finding:
    severity: str  # "WARN" | "INFO"
    code: str
    where: str
    message: str

    def to_dict(self) -> dict:
        return {
            "severity": self.severity,
            "code": self.code,
            "where": self.where,
            "message": self.message,
        }


@dataclass
class AuditResult:
    memory_dir: str
    threshold_days: int
    findings: list[Finding] = field(default_factory=list)
    total_files: int = 0
    indexed_files: int = 0


def _discover_memory_dir() -> Path:
    """Resolve the auto-memory directory.

    Priority:
      1. --dir arg (passed in by main, not this function)
      2. $CLAUDE_MEMORY_DIR
      3. Claude Code convention: ~/.claude-personal/projects/<encoded-cwd>/memory/
         where encoded-cwd is the absolute CWD path with '/' → '-'.
    """
    env = os.environ.get("CLAUDE_MEMORY_DIR")
    if env:
        return Path(env).expanduser()
    cwd = Path.cwd().resolve()
    encoded = str(cwd).replace("/", "-")
    return Path.home() / ".claude-personal" / "projects" / encoded / "memory"


def _parse_index(index_path: Path) -> tuple[dict[str, str], int]:
    """Parse MEMORY.md → {filename: title}, line_count."""
    entries: dict[str, str] = {}
    if not index_path.is_file():
        return entries, 0
    line_count = 0
    for raw in index_path.read_text(encoding="utf-8").splitlines():
        line_count += 1
        m = _INDEX_ENTRY_RE.match(raw.strip())
        if m:
            title = m.group(1).strip()
            filename = m.group(2).strip()
            entries[filename] = title
    return entries, line_count


def _read_frontmatter(path: Path) -> tuple[dict[str, str], str]:
    """Return (frontmatter_dict, body_text). Empty dict if none."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    fm_text, body = parts[1], parts[2]
    fm: dict[str, str] = {}
    for line in fm_text.strip().splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip()
    return fm, body


def _days_since_mtime(path: Path) -> int:
    """Days since file mtime, rounded down. Floor at 0."""
    age_seconds = time.time() - path.stat().st_mtime
    return max(0, int(age_seconds // 86400))


def audit(memory_dir: Path, threshold_days: int) -> AuditResult:
    result = AuditResult(memory_dir=str(memory_dir), threshold_days=threshold_days)
    if not memory_dir.is_dir():
        # Advisory: missing dir on first-run setup is normal. Emit a
        # synthetic finding so the JSON parse path stays uniform and
        # callers can decide what to surface.
        print(f"warning: memory directory does not exist: {memory_dir}",
              file=sys.stderr)
        result.findings.append(Finding(
            severity="INFO",
            code="memory-dir-missing",
            where=str(memory_dir),
            message="memory directory does not exist; auto-memory not in use yet",
        ))
        return result

    # 1. Parse index.
    index_path = memory_dir / INDEX_FILENAME
    indexed, line_count = _parse_index(index_path)
    indexed_files_set = set(indexed.keys())

    # 2. Index-bloat check.
    if line_count > INDEX_TRUNCATION_LIMIT:
        result.findings.append(Finding(
            severity="WARN",
            code="index-bloat",
            where=str(index_path),
            message=(
                f"{INDEX_FILENAME} is {line_count} lines (Claude truncates "
                f"after {INDEX_TRUNCATION_LIMIT}). "
                f"Entries past line {INDEX_TRUNCATION_LIMIT} are silently invisible."
            ),
        ))

    # 3. Walk memory dir; classify each file.
    on_disk: set[str] = set()
    for entry in sorted(memory_dir.iterdir()):
        if not entry.is_file() or entry.suffix != ".md":
            continue
        if entry.name == INDEX_FILENAME:
            continue
        on_disk.add(entry.name)
        result.total_files += 1
        if entry.name in indexed_files_set:
            result.indexed_files += 1
        else:
            result.findings.append(Finding(
                severity="WARN",
                code="orphan-file",
                where=str(entry),
                message=(
                    f"file exists under memory/ but is not linked from "
                    f"{INDEX_FILENAME} — recall pipeline cannot find it"
                ),
            ))

        # mtime staleness
        days = _days_since_mtime(entry)
        if days > threshold_days:
            result.findings.append(Finding(
                severity="INFO",
                code="stale-mtime",
                where=str(entry),
                message=(
                    f"unchanged for {days} days (>{threshold_days}). "
                    f"mtime is a proxy for verified_at while schema is unversioned."
                ),
            ))

        # frontmatter sanity + provisional scan
        try:
            fm, body = _read_frontmatter(entry)
        except OSError as e:
            result.findings.append(Finding(
                severity="WARN",
                code="read-error",
                where=str(entry),
                message=f"cannot read file: {e}",
            ))
            continue

        missing = [k for k in REQUIRED_FRONTMATTER if k not in fm]
        if missing:
            result.findings.append(Finding(
                severity="INFO",
                code="frontmatter-missing",
                where=str(entry),
                message=f"frontmatter missing field(s): {', '.join(missing)}",
            ))

        m = _PROVISIONAL_RE.search(body)
        if m:
            result.findings.append(Finding(
                severity="INFO",
                code="provisional-marker",
                where=str(entry),
                message=(
                    f"body self-flags as provisional ('{m.group(0)}'). "
                    f"Has the validation horizon passed?"
                ),
            ))

    # 4. Dead-link check (index points to file that does not exist).
    for filename, title in indexed.items():
        if filename not in on_disk:
            result.findings.append(Finding(
                severity="WARN",
                code="dead-link",
                where=f"{index_path}::{filename}",
                message=(
                    f"index entry '{title}' → {filename}, but file does not exist"
                ),
            ))

    return result


def _counts(findings: list[Finding]) -> dict[str, int]:
    out: dict[str, int] = {}
    for f in findings:
        out[f.code] = out.get(f.code, 0) + 1
    return out


def emit_json(result: AuditResult) -> None:
    payload = {
        "memory_dir": result.memory_dir,
        "thresholds": {"stale_days": result.threshold_days,
                       "index_truncation": INDEX_TRUNCATION_LIMIT},
        "counts": {
            "total_files": result.total_files,
            "indexed_files": result.indexed_files,
            **_counts(result.findings),
        },
        "findings": [f.to_dict() for f in result.findings],
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def emit_human(result: AuditResult) -> None:
    print(f"auto-memory audit  ({result.memory_dir})")
    print(f"  total files: {result.total_files}")
    print(f"  indexed:     {result.indexed_files}")
    print(f"  threshold:   {result.threshold_days} days")
    print()

    if not result.findings:
        print("  no findings — auto-memory is clean.")
        return

    by_code: dict[str, list[Finding]] = {}
    for f in result.findings:
        by_code.setdefault(f.code, []).append(f)

    order = [
        "index-bloat",
        "dead-link",
        "orphan-file",
        "frontmatter-missing",
        "stale-mtime",
        "provisional-marker",
        "read-error",
    ]
    seen = set()
    for code in order + sorted(by_code.keys()):
        if code in seen or code not in by_code:
            continue
        seen.add(code)
        items = by_code[code]
        sev = items[0].severity
        print(f"  [{sev}] {code}  ({len(items)})")
        for f in items:
            print(f"    - {f.where}")
            print(f"        {f.message}")
        print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit Claude Code auto-memory: stale, orphan, dead-link, "
                    "provisional, frontmatter, index-bloat checks."
    )
    parser.add_argument(
        "--dir",
        type=Path,
        default=None,
        help="Override memory directory path (default: auto-discover via CWD).",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=DEFAULT_STALE_DAYS,
        help=f"Stale mtime threshold in days (default: {DEFAULT_STALE_DAYS}).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of human text.",
    )
    args = parser.parse_args()

    memory_dir = (args.dir.expanduser() if args.dir else _discover_memory_dir())
    result = audit(memory_dir, args.threshold)

    if args.json:
        emit_json(result)
    else:
        emit_human(result)


if __name__ == "__main__":
    main()
