## Purpose

Emergency recovery of a wiki entry from Reflect when the local file under `zk/wiki/` is lost and git history cannot help. Very rarely triggered. The only remaining Reflect copies of wiki entries are the ones the user manually shared via Curator + `create_note`; there is no automated manifest to point at them.

Do not run this command reflexively. It is not a sync verifier, not a daily check, not a health probe. The normal path when something looks wrong is `/lint` + `git status` + `git log`. `/restore` is the last resort after all of those.

## Prerequisites

- The user knows the Reflect note ID for the missing wiki entry. Reflect exposes note IDs via the URL or via its export/share UI; the user must supply them, because the system no longer tracks a local-to-Reflect mapping.
- The missing local path is under `zk/wiki/<slug>.md` (slug = filename stem, title-cased with spaces).

## The lossy-pipeline caveat

What comes back from Reflect is **degraded prose**, not a drop-in replacement. Two sources of mutation:

1. Older wiki entries pushed by the retired wiki-push `/sync` had their fenced `anchors` blocks stripped and replaced with a human-readable `**Sources:**` bullet list. Manual-share entries (via Curator + `create_note`) preserve the raw file content.
2. Reflect auto-mutates bodies on ingestion: prepends an H1, wraps bare URLs in `<...>`, normalizes `---` to `***`.

Byte-copying the Reflect body into `zk/wiki/<slug>.md` will usually fail `scripts/trust.py`'s structural-integrity check. The user is expected to read the recovered prose, reconstruct the `anchors` fences (or confirm they survived intact), and hand-author the final wiki entry.

## Process

### Phase 1: Confirm intent

Before touching anything, ask the user:

> "/restore is the last-resort recovery path for a wiki entry that is missing locally. It pulls the (possibly lossy) Reflect copy into `zk/cache/restore-<slug>.md` as a reference for hand-reconstruction. It will NOT write to `zk/wiki/`. Do you want to proceed? [y/N]"

If the user hesitates, stop. Suggest `git status` / `git log -- zk/wiki/` / `/lint` first.

### Phase 2: Collect slug + note ID pairs from the user

For each wiki entry to recover, ask the user for:

- The target slug (filename stem under `zk/wiki/`, title-cased with spaces; matches the H1 of the original entry).
- The Reflect note ID (the user can copy this from Reflect's UI).

### Phase 3: Plan

```
Bash: scripts/restore.py plan --slug "<slug>" --note-id "<id>" [--slug "<s2>" --note-id "<id2>" ...]
```

Parse the JSON. Each entry has `present_locally`. Only entries where `present_locally: false` warrant recovery. If the local file is present, stop and tell the user — use git history to inspect, not `/restore`.

### Phase 4: Fetch from Reflect

For each slug to recover:

1. Call `mcp__reflect__get_note(id: "<reflect_note_id>")`. This is an orchestrator-only MCP escape hatch (documented in `CLAUDE.md`).
2. If the note is missing or the body is empty, report the failure and skip. Either the Reflect note was never created, or the user deleted it.
3. Write the body to `zk/cache/restore-<slug>.md` with a prepended header:

   ```
   # RECOVERY SNAPSHOT — not a valid wiki entry

   Source: Reflect note <reflect_note_id>
   Fetched at: <today>

   This file is possibly-degraded prose fetched from Reflect. It is NOT
   guaranteed to be a drop-in replacement for zk/wiki/<slug>.md because
   Reflect auto-mutates bodies on ingestion (adds an H1, wraps bare URLs
   in <...>, normalizes --- to ***), and older entries pushed by the
   retired wiki-push /sync had their `anchors` fences stripped.

   To recover the wiki entry:
     1. Read the prose below.
     2. Hand-author zk/wiki/<slug>.md with proper H1, `## Claims` sections,
        `### [Cn]` headings, and `anchors` fences (reconstruct from any
        `**Sources:**` bullet list if the fences were stripped).
     3. Run `scripts/trust.py --note "zk/wiki/<slug>.md"` and
        `scripts/lint.py` to confirm the rebuilt entry parses cleanly.

   ---

   <original reflect body>
   ```

4. Never write directly to `zk/wiki/<slug>.md`. The cache file is a reference for hand-reconstruction, not an automatic restore.

### Phase 5: Report

Tell the user which cache files were written and what to do next:

> "Wrote `zk/cache/restore-<slug>.md` for N slugs. These are prose references, not valid wiki entries. Open each, reconstruct or verify the `anchors` fences, and save the result to `zk/wiki/<slug>.md`. Then run `scripts/trust.py` and `scripts/lint.py` to verify."

## Rules

1. **One-way.** `/restore` reads from Reflect, writes only to `zk/cache/`. It never writes to `zk/wiki/`.
2. **Per-slug confirmation.** Never batch-recover without explicit per-slug approval. Recovery is a reconstruction task, not an import.
3. **Prose is not schema.** What comes back may be lossy. The user must verify or re-author the `anchors` fences by hand.
4. **Covers only `zk/wiki/`.** L2 content (`zk/reflections/`, `zk/research/`, `zk/drafts/`, `zk/gtd/`, `zk/agent-findings/`, `zk/preprints/`) and `zk/daily-notes/` never had a distinct Reflect copy of the wiki kind. For daily notes, rerun `/sync`. For L2 content, use git.

## When this has fired historically

Never, as of the date this doc was written. The command exists as insurance against a failure mode the append-only Reflect archive happens to protect against. If you find yourself running this for the first time, file a note in `zk/reflections/` about what caused the loss so the system can evolve.
