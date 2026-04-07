# /sync — Push `zk/wiki/` entries to Reflect for mobile display

One-way sync from the local wiki layer to Reflect. Wiki entries live under `zk/wiki/*.md` and are the authoritative L4 knowledge layer (see `protocols/local-first-architecture.md`). Reflect is a display surface for mobile reading — not a source of truth and not pulled back.

**Scope:** only `zk/wiki/*.md`. Daily notes, reflections, drafts, and everything else in `zk/` do not sync. `/sync` does not pull edits from Reflect back into the vault.

## What to sync

| Source | Target in Reflect | Title |
|---|---|---|
| `zk/wiki/<slug>.md` | standalone note via `create_note` | H1 of the wiki file |

## Process

### Phase 1: Preflight

1. Check that `.mcp.json` is configured and the Reflect MCP is reachable. If not, stop cleanly: "Reflect MCP not reachable. Skipping sync. Nothing is lost — wiki entries are authoritative on disk."
2. Read the sync manifest at `zk/.sync-manifest.json` (gitignored). If it doesn't exist, treat every wiki entry as new.
   ```json
   {
     "schema": 1,
     "entries": {
       "<slug>": {
         "reflect_note_id": "<id returned by create_note>",
         "synced_at": "YYYY-MM-DD",
         "content_sha256": "<hash of stripped body at last sync>"
       }
     }
   }
   ```
3. Run `Bash: scripts/sync_export.py manifest zk/wiki/ --synced-at <today>` to get the list of wiki entries with deterministic sha256 hashes and titles. **The LLM must never compute hashes or strip markdown itself** — `sync_export.py` is the single source of truth for the stripped body and its hash (Gemini flagged LLM non-determinism here as a blocker). For each entry in the JSON output, compare `sha256` with `entries[slug].content_sha256` in the manifest.
4. Categorize:
   - **new** — slug not in manifest
   - **changed** — slug in manifest, hash differs
   - **unchanged** — slug in manifest, hash matches → skip
5. Run `Bash: scripts/trust.py --json` and filter entries where `integrity_ok: false` (or with non-empty `parse_errors`). Do not sync failing entries; warn the user.

### Phase 2: Obtain the stripped body (deterministic)

Do not strip markdown in the LLM. Instead call:

```
Bash: scripts/sync_export.py body zk/wiki/<slug>.md --synced-at <today>
```

`sync_export.py` does the following deterministically, and the LLM never re-derives it:

1. Keeps: H1 title, intro prose, `## Claims` heading, each `### [Cn]` heading and its prose body, `## Revision Log`.
2. For each claim, collects its `@anchor`, `@cite`, and `@pass` lines from the fenced `anchors` block and renders them under the claim as a human-readable `**Sources:**` bullet list.
3. Drops the fenced ` ```anchors ` blocks entirely.
4. Appends a top-level "Synced from ... Local is authoritative" footer.

The output of `sync_export.py body` is the exact byte stream whose sha256 was computed in Phase 1 and is what you pass to `create_note` in Phase 3. Capture it to a temporary file under `zk/cache/sync-<slug>.md` so the LLM can feed it into the MCP call without re-encoding.

### Phase 3: Write to Reflect

For each **new** entry:
1. `create_note(subject: "<H1 title>", contentMarkdown: "<stripped body>")`
2. **Verify:** immediately `get_note(id)` and confirm the body is non-empty. If empty, the parameter name was wrong — stop and report. This is the silent-empty-note failure mode CLAUDE.md warns about.
3. Record in manifest under the slug: `reflect_note_id`, `synced_at`, `content_sha256`.

For each **changed** entry:

Reflect MCP has no update API. The user is expected to have deleted the old Reflect note by hand before re-running `/sync`. We attempt `create_note` and verify whether we got a fresh copy or hit the stale stub:

1. Call `create_note(subject: "<H1 title>", contentMarkdown: "<stripped body>")`.
2. **Verify:** immediately `get_note(id)` on the returned ID.
   - **Empty body:** the parameter name was wrong — stop and report (same silent-empty-note check as the new-entry path).
   - **Body matches the stripped body we just sent:** the user successfully deleted the old note; `create_note` created a fresh one. **Update the manifest** (`reflect_note_id`, `synced_at`, `content_sha256`) and treat as success.
   - **Body does not match (stale stub):** the user forgot to delete the old Reflect note, so `create_note` returned the existing one unchanged. Skip this entry, do **not** update the manifest hash, and report:
     > "<slug> has local edits but the old Reflect note is still present. Delete it by hand in Reflect and re-run `/sync`."

### Phase 4: Report

Present a summary:
```
/sync summary
  New entries synced:    N
  Unchanged (skipped):   M
  Changed (needs manual replace): K — [list slugs]
  Failing trust parse (skipped):  F — [list slugs with errors]
  Reflect MCP reachable:  yes/no
```

## Error handling

- **Reflect MCP down:** exit cleanly in Phase 1. No partial writes, no manifest mutation.
- **`create_note` empty-body detected:** stop the loop, do not update the manifest, report the slug that failed.
- **Title collision (existing Reflect note with same title but no manifest entry):** `create_note` returns the existing note. Verify the returned body matches the stripped body we just computed. If they match, record it in the manifest and treat as idempotent success. If they don't match, skip it and report: manual resolution needed.
- **Structural-integrity failure:** already filtered in Phase 1. Print the file path and parse errors so the user can fix the source.
- **`scripts/trust.py` missing or errors:** skip the trust filter but still perform the sync. Warn: "Trust engine unavailable — syncing without parse verification."

## Idempotency

Re-running `/sync` with no changes must be a no-op. The manifest is the idempotency ledger. Deleting the manifest forces a full re-sync attempt (which will hit title collisions on everything already in Reflect — use the collision path to reconcile).

## Rules

1. **One-way.** Never read from Reflect to update `zk/wiki/`. Manual edits in Reflect are lost on the next `/sync` of a changed entry.
2. **Markers are for the trust engine, not for humans.** The Sources footer is the human-readable rendering; the markers stay only in the local file.
3. **Manifest is gitignored.** Add `zk/.sync-manifest.json` to `.gitignore` if it isn't already.
4. **Ask before destructive action.** If a collision requires asking the user to delete a Reflect note by hand, stop and tell them — don't guess.
