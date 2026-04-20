## Purpose

Pull daily notes from Reflect into `zk/daily-notes/` and merge with any local edits, preserving both sides. One-way, Reflect to local only. `/sync` never writes to Reflect.

Sharing a wiki entry to Reflect is intentionally out of scope for this command. It is a manual per-note operation the user requests explicitly (see "Sharing a wiki entry manually" below).

## Scope

- In scope: `zk/daily-notes/YYYY-MM-DD.md`.
- Out of scope: everything else. Wiki entries under `zk/wiki/` are not synced in either direction by `/sync`. Reflections, drafts, research, etc. never cross the Reflect boundary.

## Arguments

Optional date range. Default is the last 7 days (including today). Accepted forms:

| Form | Meaning |
|---|---|
| (none) | Last 7 days |
| `last N days` | Last N calendar days, including today |
| `YYYY-MM-DD` | A single date |
| `YYYY-MM-DD..YYYY-MM-DD` | Inclusive range, earlier to later |

## Process

Single phase. No preflight, no manifest, no idempotency ledger.

1. **Resolve the date list** from the argument. Use the late-sleep rule from `CLAUDE.md` to determine "today" (before 03:00 local, "today" is the previous calendar day).

2. **For each date, fetch and merge:**
   a. Call `mcp__reflect__get_daily_note(date: "<YYYY-MM-DD>")`. Callable by the orchestrator (this command) and by the Curator when dispatched for background daily-notes sync (see Curator's "Sync Daily Notes" operation). Not callable by other subagents.
   b. If the response is the `No daily note found` sentinel (or an equivalent empty-body signal), skip the date. Do **not** create an empty local file. Empty stubs are noise.
   c. Otherwise, write the response body verbatim to `zk/cache/reflect-daily-<YYYY-MM-DD>.md`. Do not strip the YAML frontmatter or the H1 yourself; `merge_daily.py` handles that.
   d. Run:
      ```
      Bash: uv run scripts/merge_daily.py "zk/daily-notes/<YYYY-MM-DD>.md" "zk/cache/reflect-daily-<YYYY-MM-DD>.md"
      ```
      Collect the stderr status line. The script's statuses are `new`, `identical`, `merged`, `unchanged`, `empty`. A merged file has a `<!-- merged from Reflect -->` marker separating local content from Reflect-only lines.

3. **Print a summary table** after the loop:
   ```
   /sync summary (<range>)
     new:          N   (date list)
     merged:       M   (date list)
     identical:    K
     skipped:      S   (no Reflect note for those dates)
     failed:       F   (dates not attempted or merge-script error; list them)
   ```

## Failure modes

- **Reflect MCP unreachable:** stop cleanly at whichever date you were on. Report the dates that were not attempted. No partial state to clean up; `merge_daily.py` is a local-only operation and nothing was written to Reflect.
- **Merge script error on a specific date:** log the date and the stderr from `merge_daily.py`, continue with the next date. One bad date should not block the rest.
- **Cache write fails:** report the filesystem error and stop; local writes should never fail silently.

## Invariants

1. **Never create an empty local daily note.** If Reflect returns nothing, the local file stays whatever it is (possibly missing). The user just cleaned up a batch of empty stubs; do not re-introduce them.
2. **Never discard local content.** `merge_daily.py` takes a line-level union. Local content appears first; Reflect-only lines follow under the `<!-- merged from Reflect -->` marker. If something looks wrong, inspect the cache file and the merged output before re-running.
3. **One-way.** `/sync` reads from Reflect and writes to `zk/daily-notes/` and `zk/cache/`. It never calls `create_note` or `append_to_daily_note`.
4. **Re-runs fold, not stack.** When the local file already contains a `<!-- merged from Reflect -->` marker, `merge_daily.py` appends any new Reflect-only lines under the existing marker instead of inserting a second one. Everything the user has written below the marker is preserved by the line-union; the marker is never duplicated.

## Known limitations

These are trade-offs from the "no manifest, no hash" design. They are not bugs; document them so the user expects them.

- **Edited-in-place lines duplicate.** If the user edits a line that originated from Reflect (e.g., corrects a typo in a Reflect-sourced bullet), the next `/sync` sees the corrected local line and the original Reflect line as distinct after whitespace normalization and keeps both. The user is the tiebreaker: inspect the merged file and delete the Reflect-side duplicate by hand, or rewrite the line identically on both sides.
- **Provenance is unrecoverable post-merge.** Once content has been merged into `zk/daily-notes/<date>.md`, there is no record of which lines came from Reflect vs. the local file. If a line looks suspicious later, `git blame` on `zk/daily-notes/` tells you when it landed locally, not where it originated.
- **Cache files accumulate.** `zk/cache/reflect-daily-<date>.md` is overwritten on each sync of that date but never garbage-collected across dates. Over months, `zk/cache/` will grow. Clean manually if it matters; the files are gitignored.
- **No dry-run is wired into the command.** `merge_daily.py --dry-run` exists (prints merged content to stdout, no write). For a cautious first run, invoke the script directly on one date with `--dry-run` before letting the command loop overwrite files.

## Sharing a wiki entry manually

Sharing a wiki entry to Reflect is not part of `/sync`. It is a per-note manual operation:

1. The user says "share `[[Foo]]` to Reflect" (or gives a path like `zk/wiki/Foo.md`).
2. The orchestrator reads the local file at `zk/wiki/<Title>.md`.
3. The orchestrator dispatches the Curator with the file content and title.
4. The Curator calls `mcp__reflect__create_note(subject: "<H1 title>", contentMarkdown: "<body>")`.
5. The orchestrator verifies with `mcp__reflect__get_note(<returned_id>)` that the body is non-empty (the silent-empty-note guard from `CLAUDE.md`).

No manifest. No hash. No diff. If the user later edits the local wiki entry and wants the Reflect copy refreshed, they request the share again. Reflect's `create_note` with an existing title returns the existing note unchanged; the user must delete the Reflect copy by hand first if a fresh push is needed.
