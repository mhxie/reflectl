# /lint — Structural + corpus-level checks over `zk/wiki/`

Deterministic Python pass. The LLM never hand-checks structure — `scripts/lint.py` is the single source of truth, mirroring the `scripts/trust.py` pattern.

**Scope:** Three passes. (0) Harness portability and privacy checks. (1) Structural: everything under `zk/wiki/`. (2) Staleness: L2 working-layer directories (`zk/agent-findings/`, `zk/drafts/`, `zk/gtd/`, `zk/preprints/`, `zk/reflections/`, `zk/research/`). Structural lint enforces the wiki schema; staleness lint surfaces L2 notes that need attention (archival, compaction, or promotion to L4).

**What gets checked:**

| Check | Severity | Source |
|---|---|---|
| Per-note parse errors — items 1-10 of `protocols/wiki-schema.md`, plus dangling `@cite` targets (both surface under the `parse-error` code) | ERROR | `scripts/trust.py` parser + resolver |
| Duplicate titles across wiki entries (breaks `@cite` resolution) | ERROR | `scripts/lint.py` |
| Slug ↔ title alignment (filename stem matches H1 title) | WARN | `scripts/lint.py` |
| Orphan entry — no inbound `@cite` from any other wiki entry (trust cannot propagate to it) | WARN | `scripts/lint.py` graph topology |
| No outbound cite — entry does not `@cite` any other wiki entry | INFO | `scripts/lint.py` graph topology |
| Shared anchor, no cite — two entries reference the same `@anchor` but lack a `@cite` edge | INFO | `scripts/lint.py` graph topology |
| `url:` or `gist:` anchor missing `readwise:` field (`readwise-missing`) | WARN | `scripts/lint.py` — save to Readwise with `anchor-evidence` tag and backfill the document ID; fix via `uv run scripts/snapshot_anchors.py --apply --note "zk/wiki/<Title>.md"` |
| Technical term in claim body not in vocabulary allowlist and not matching any wiki entry title (`unfounded-term`) | INFO | `scripts/lint.py` — add term to `scripts/wiki_vocabulary.txt` if common knowledge, or add a wiki entry, or add a parenthetical definition inline |
| Chinese shadow missing in `zk/wiki-cn/` (`cn-shadow-missing`) | WARN | `scripts/lint.py` — run /promote Phase 4 or regenerate the CN shadow manually |
| Chinese shadow older than English source (`cn-shadow-stale`) | WARN | `scripts/lint.py` — re-translate the CN shadow to match the updated English source |
| Claude/Codex harness portability (`missing-agents-md`, `models-agent-missing`, `capability-agent-missing`, `agents-registry-entry-missing`, `commands-entry-missing`, `skill-missing`, etc.) | ERROR/WARN/INFO | `scripts/harness_lint.py` |
| Claim missing `^cn` block ID (`block-id-missing`, deferred — Phase D) | WARN | `scripts/lint.py` — regex `\^c[0-9]+$` on last line of each claim body; absent marker is a nudge, not a reject (per `protocols/wiki-schema.md` §"When `^cn` is recommended") |
| Non-`^cn` block ID inside a wiki entry (`block-id-violation`, deferred — Phase D) | ERROR | `scripts/lint.py` — any `^<token>` that does not match `\^c[0-9]+$` is a schema violation (no `^summary`, `^fig1`, `^revlog-*`, etc.) |

**Not checked:** cross-note `@anchor` date consistency. Per `protocols/wiki-schema.md`, `valid_at` is the day the marker was added to its home note, so the same source being anchored from two notes on different days is the normal case. `/lint` used to flag this and was wrong about it.

Exit code: 0 if no ERROR-level findings, 1 otherwise. WARN and INFO never fail the run.

## Process

### Phase 0: Harness health

```
Bash: python3 scripts/harness_lint.py --json
```

Parse the JSON. Shape:
```json
{
  "counts": { "error": 0, "warn": 0, "info": 0 },
  "findings": [
    { "severity": "ERROR|WARN|INFO", "code": "...", "where": "...", "message": "..." }
  ]
}
```

Any ERROR-level finding blocks the run until the harness contract is fixed. WARN and INFO findings are advisory.

```
Bash: wc -c CLAUDE.md
```

If CLAUDE.md exceeds 8,192 bytes (~2,000 tokens), emit a WARN: "CLAUDE.md is [size] bytes (target: <8KB). This file is inherited by every subagent; excess size multiplies token cost across all agent dispatches. Run a prune pass or move rules to agent definitions/protocols."

If CLAUDE.md exceeds 15,000 bytes, escalate to ERROR. The file has likely accumulated rules that belong elsewhere.

Also check for bold formatting:
```
Bash: grep -c '\*\*' CLAUDE.md
```
If count > 0, emit INFO: "CLAUDE.md contains [N] bold markers. Bold has no semantic weight for the model and wastes tokens. Consider removing."

### Phase 0b: Privacy leak scan

```
Bash: uv run scripts/privacy_check.py --json
```

Parse the JSON. Shape:
```json
{
  "zk_dir": "zk",
  "titles_scanned": N,
  "allowlist_size": N,
  "hit_count": N,
  "hits": [
    { "file": "...", "line": N, "private_title": "..." }
  ]
}
```

Any non-empty `hits` array is an ERROR: each entry is a multi-word filename stem from the private `$ZK` vault that appears as literal text in a tracked file. Present each hit verbatim with its file and line number. Remediation:

- Replace the private title with a generic placeholder (e.g., `Sample Wiki Entry`, `Topic A`).
- Or, if the exposure is deliberate (e.g., the title is fully public and appears as an illustrative example), add the stem to `scripts/privacy_allowlist.txt` and document the rationale in the commit message.

The check is a blocking quality gate for any system-evolution commit that touches tracked files. Do not proceed to structural lint if Phase 0b returns hits.

### Phase 1a: Structural lint

```
Bash: scripts/lint.py --json
```

Parse the JSON. It has the shape:

```json
{
  "wiki_dir": "zk/wiki",
  "counts": { "error": 0, "warn": 0, "info": 0 },
  "findings": [
    { "severity": "ERROR|WARN|INFO", "code": "...", "where": "...", "message": "..." }
  ]
}
```

### Phase 1b: Staleness lint

```
Bash: scripts/staleness.py --json
```

Parse the JSON. Shape:

```json
{
  "thresholds": { "stale": 90, "dormant": 45, ... },
  "counts": { "stale": N, "dormant": N, "promote": N, "active": N, "total": N },
  "notes": [{ "path": "...", "staleness": N, "category": "stale|dormant|promote|active", ... }]
}
```

Staleness findings are always advisory (no ERROR level). They surface L2 notes that have gone cold, using the formula `days_since_modified / (1 + log(1 + reference_count))`. Notes referenced from wiki entries or recent reflections decay slower.

### Phase 2: Present

Group findings by severity. If the corpus is clean, say so and stop.

For each ERROR-level finding: show the code, file path, and message verbatim. Do not rephrase the message — `scripts/trust.py` and `scripts/lint.py` emit precise line numbers that the user needs.

For WARN-level findings: show them but mark them as non-blocking.

For INFO-level findings: roll them up into a one-line summary (e.g., "4 entries with no outbound `@cite`: consider adding cross-references") unless the user asks for the full list.

**Staleness section** (from Phase 1b): present after the structural findings, under a separate heading. Group by category:
- **stale** notes: list paths, suggest archiving to `zk/archive/`
- **dormant** notes: list paths, suggest review or compaction
- **promote** candidates: list paths, suggest `/promote` to create L4 wiki entries
- If all notes are active, say so in one line and move on.

### Phase 3: Offer fixes

For each fixable category, ask the user before acting:

| Finding code | Fix | How |
|---|---|---|
| `slug-mismatch` | Rename file or edit H1 | Ask the user which side to change. Never rename without confirmation — downstream `@cite` targets key off the title. |
| `parse-error` (e.g., missing `valid_at`, non-sequential `[Cn]`) | Edit the wiki entry | Route to the user; do not auto-edit wiki entries. |
| `duplicate-title` | Edit one of the H1 titles | Ask the user which note keeps the title. |
| `dangling-cite` | Fix the `@cite` target or remove the marker | Surfaced under `parse-error` code (trust.py's resolver appends to `parse_errors`). Route to the user. |
| `orphan-entry` | Add `@cite` markers from related entries | Suggest specific claims in other entries that could cite the orphan. The `shared-anchor-no-cite` findings often point to the right pairs. |
| `shared-anchor-no-cite` | Add `@cite` between the pair | Show the shared anchor and suggest which direction the cite should flow (from the more general to the more specific claim). |

### Phase 4: Rerun (if fixes applied)

If any user-driven fixes were made, suggest rerunning `/lint` manually to confirm the state.

## Rules

1. **Never hand-check structure.** Always call `scripts/lint.py`. If the script is missing or errors, fix the script — do not re-derive the checks in the LLM.
2. **Ask before fixing.** All fixes route back to the user; `scripts/lint.py` is advisory-only.
3. **ERROR findings block further wiki work.** If a wiki entry has a parse error, do not cite it from new entries, do not score it — fix it first.
4. **WARN findings are advisory.** The system keeps working; the user decides whether to act.
