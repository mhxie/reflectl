# Drive → zk Ingestion Protocol

## Roles

- **Google Drive top-level domain folders** (`~/Google Drive/My Drive/<Domain>/`) and **`~/Downloads/`** are the **raw landing zones**. New files arrive here from web downloads, exports (e.g., MyChart), scans, photo dumps, manual uploads.
- **`zk/` (the vault, currently mounted at `~/Google Drive/My Drive/zk/`)** is the **structured repository** — single source of truth for organized data.
- After ingestion, originals live only in `zk/<domain>/raw/` (or in zk's gitignored cache for entities not yet promoted). Drive top-level domain folders and Downloads are transient.

This protocol governs the flow from landing zone → repository.

## Default mode: mv

Default is **mv** (move), not cp (copy). Goal: zk is single source of truth, Drive top-level / Downloads do not duplicate.

### Exceptions where cp is correct

- **Format-conversion**: when the digested form is lossy (e.g., HEIC → jpg, DOCX → txt, video → transcript). mv the original into `zk/<domain>/raw/`, keep the transcoded version alongside as the markdown-friendly companion.
- **Uncertain completeness**: if extraction did not capture everything (e.g., a viewer skin / browser package alongside a data PDF), mv the auxiliary files into a sibling folder (`raw/<event>-viewer/`) rather than delete.
- **Explicit user request to dual-keep**: the user may say "keep the Drive copy" for a specific transition.

When uncertain → mv into zk (don't delete). zk is the destination either way.

## Two-track rule: low-value vs high-value

After mv into zk, classify each file by future utility — this determines destination subtree and whether to write a digest:

### Low-value → `zk/archive/<category>/`

Pure backup, no digest, no expectation of revisit. Categories follow existing archive structure (`career/`, `courses/`, `practical/`, `people/`, etc.). Examples:
- Old insurance applications past their effective date
- Single-bill receipts and payment confirmations
- Boilerplate compliance notices (privacy notifications, ToS confirmations)
- Past calendar invites for fulfilled appointments
- Coursework / academic artifacts past their decision window
- Application materials for closed processes

### High-value → working tier (`zk/<domain>/raw/`) **+** digest in working tier

Two artifacts together:
1. **Raw**: mv original to `zk/<domain>/raw/` for provenance and full context.
2. **Digest**: write a markdown extract in the working tier (`zk/<domain>/reports/`, `zk/<domain>/<topic>.md`) capturing the retrieval-relevant essence — key dates, structured data, cross-links, decision implications.

Rationale: without a digest, valuable raw rots unread in storage; without raw, the digest can drift from source. Both serve different purposes.

Examples:
- Lab results, scan reports, visit summaries → digest extracts findings, references raw PDF
- Lease contracts → digest captures rent / term / parties, references raw lease PDF
- Technical / strategic documents you will reference again → digest captures decision-relevant essence

### Triage decision

Ask: *would future-me grep for this file's content?*
- Yes → high-value, raw + digest.
- No, but could matter for an edge case (audit, dispute) → low-value, archive raw only.
- No → consider whether to keep at all (some files truly belong in `zk/cache/` or trash).

Don't dump raw directly into working tier subdirectories (`reports/`, `research/`). The working tier is for digests. Raw stays in `raw/` siblings.

### Lifecycle: closed domains demote to archive

When a domain is no longer an active phase of life (e.g., PhD finished, prior employer fully off-boarded with no PERM tail, retired hobby), `mv` the entire working-tier directory to `zk/archive/<domain>/`. This preserves digests (README, timeline.md) as historical snapshots while removing the implicit "active reference" status.

Example: `zk/education/` → `zk/archive/education/` after PhD completion + start of full-time work. The raw + digests come along intact.

Don't pre-archive: a domain stays in working tier as long as it has live followups, ongoing decisions, or recent file additions.

## Domain mapping

| Drive top-level | zk subdirectory | Notes |
|---|---|---|
| `Housing/` | `zk/housing/raw/` | per-residence subfolder preserved |
| `Medical/` | `zk/health/raw/` | domain name differs (Medical → health); document this in the relevant README |
| `Immigration/` | `zk/immigration/raw/` (TBD) | route per content; H1B / DS-2019 / OPT etc. |
| `Career/` | `zk/career/raw/` (TBD) | offer letters, paystubs, 401k |
| `Travel/` | `zk/travel/raw/` (TBD) | itineraries, perks ledger backing |
| `Finance/` | `zk/finance/raw/` (TBD) | tax returns, brokerage statements |
| `Education/` | `zk/education/raw/` (TBD) | degrees, transcripts |
| `Personal/` | (per content; possibly `zk/personal/raw/`) | mixed; route per file |
| `~/Downloads/<domain>/` | route per content to appropriate zk domain | transient by nature; mv into zk eagerly |

When a Drive top-level domain folder maps to a zk subdirectory with a different name (e.g., `Medical/` → `zk/health/`), document the mapping in `zk/<domain>/README.md` so future passes don't duplicate.

## Ingestion workflow

For each ingestion task (one domain or one batch):

1. **Survey** the source folder. Inventory: what's there, natural groupings (per-event subfolders, loose files, photos).
2. **Tidy at source** if needed. Group orphaned loose files into appropriate subfolders before mv. (Easier to fix structure at source than after relocation.)
3. **Mkdir destination** `zk/<domain>/raw/` if not exists. Preserve source subfolder structure verbatim where it makes sense.
4. **mv files** in. Use `mv -- "$src" "$dst"` to handle filenames with leading dashes / spaces.
5. **Extract structured data** into markdown in `zk/<domain>/` (not under `raw/`). Naming convention: `<YYYY-MM-DD>-<slug>.md` for events, `<topic>.md` for cross-cutting indexes. Cross-link related files using `[[wikilink]]`.
6. **Cross-link source raw**: structured markdown should reference its raw source (`[../raw/<subdir>/<file>]`). Unidirectional: markdown → raw, never edit raw.
7. **rmdir empty source folders**, including the Drive top-level domain folder if fully drained. Files in zk are still in Drive (zk is a Drive subpath); no data leaves the cloud.

## Per-domain README

Each `zk/<domain>/README.md` documents:

- Tier (typically L2 working).
- Drive mapping (which top-level Drive folder feeds this domain).
- Subdirectory layout (`raw/`, plus structured markdown subdirs).
- Cross-domain references (e.g., housing references health for atopic-march cluster).
- Non-principles (e.g., "no Reflect sync", "not a wiki tier").

Use `zk/health/README.md` and `zk/housing/README.md` as the templates.

## Naming hygiene in `zk/<domain>/raw/`

- **Preserve original filenames** when possible. Original names retain provenance (timestamps, source-system IDs).
- **Preserve subfolder structure** when source is well-organized (e.g., `Housing/Naya 2021_22/` → `zk/housing/raw/Naya 2021_22/`).
- **Loose / orphaned files**: group into `_search/` or by-date subfolders inside raw to avoid clutter.
- **Format-conversion siblings**: name with same stem, different extension. Example: `2024-10-28-pamf-skinprick.HEIC` (original) + `2024-10-28-pamf-skinprick.jpg` (transcode). Markdown links to the readable one.

## Privacy boundaries

- `zk/` is gitignored. Personal data (landlord names, MRNs, addresses, lease amounts, IDs) lives in zk safely. The committed repo never sees it.
- Protocols / committed files (this file included) describe the **structure** generically. No personal names, no addresses, no employer names. `scripts/privacy_check.py` enforces the filename-stem half during `/lint` and `/system-review`.
- Encrypted vaults (1Password, etc.) are **out of scope**: never extract credentials from there into zk plain text.
- Non-self entities (companion's medical, foster pets, etc.) get their own subdirectory under the domain (e.g., `zk/health/pet/`, `zk/health/jingshi/` reserved). Same protocol applies internally; cross-links from main self-line note "see also" but don't merge data.

## Audit / recovery

- After mv, verify file count at destination matches source pre-mv. `find zk/<domain>/raw -type f | wc -l`.
- Annual or per-domain pass: spot-check that raw files referenced from structured markdown are reachable.
- Drive Trash retains rm'd files for 30 days. rmdir of an empty folder also goes to Trash. Recovery is from Drive web UI, not CLI.
- Never `rm -rf` for cleanup. Use targeted `rm <file>` and `rmdir <empty-dir>` so accidents are obvious.

## Post-ingestion verification

After a Drive → zk ingestion sweep (especially a multi-domain pass), run the audit to catch gaps the protocol describes but a human eye misses:

```
uv run scripts/zk_audit.py            # human-readable report
uv run scripts/zk_audit.py --json     # machine-readable; used by /lint Phase 0b
```

The audit walks `$ZK/` and surfaces six categories of finding (advisory only; never mutates):

| # | Category | What it flags | Action |
|---|---|---|---|
| 1 | Missing READMEs | Working-tier domains with no `README.md`. Protocol mandates one per domain (see "Per-domain README" above). | Write the README using `zk/health/README.md` or `zk/housing/README.md` as a template. |
| 2 | Raw without digest | `<domain>/raw/<sub>/` clusters where no `.md` in the working tier mentions `<sub>` by name. Substring heuristic; false negatives possible if a digest references its source by a synonym. | Either write a digest, or accept low-value status and `mv` the cluster to `zk/archive/<category>/`. |
| 3 | Archive ↔ working-tier overlap | Archive subtrees whose normalized name matches a working-tier domain (e.g., `archive/practical/health-admin` ↔ `health/`). Often pre-protocol residue duplicating active tiers. | Per-subtree decision: keep as historical archive, merge into the active working tier, or rename to disambiguate. Audit surfaces; user decides. |
| 4 | Root orphans + empty `.md` | `.md` files at `$ZK/` root other than `README.md`; 0-byte `.md` files in working tiers. Empty `.md` under `archive/` aggregated as a count (pre-ingestion stubs, not new debt). | Move root orphans into a tier dir; delete or fill empty stubs. |
| 5 | Suspicious top-level dirs | Finder-duplicate names (` 2`, ` (2)`), empty dirs, skeleton dirs (no README, fewer than 3 entries). | Rename, remove, or build out. |

The audit is integrated into `/lint` as Phase 0b (advisory; never blocks). `/lint` surfaces a one-line summary per non-empty category; the full listings are read on demand via the script.

Findings are *advisory*, not auto-fixable. The audit reports gaps; consolidation, README authoring, and digest writing are user-driven follow-up work (typically a per-domain pass).

## Out of scope

- Live, actively-edited Google Docs in top-level Drive folders. Leave in place; ingest only when stable.
- Active financial / banking statements that may need original-format access for tax filing or audit. Copy (not move) into zk; original stays in source until fiscal year closed.
- Files belonging to other people (collaborators, family). Even if dropped in your Drive, route by ownership: their material → their channel.

## Cross-references

- [[local-first-architecture.md]] — L1-L5 tier model, where this protocol slots in (raw landing → L1, structured zk markdown → L2).
- [[raw-indexing.md]] — downstream pattern: cross-cutting clickable indexes over `zk/<domain>/raw/`, the navigational layer for ingested archives.
- [[epistemic-hygiene.md]] — validation-depth taxonomy applies after ingestion.
- `zk/housing/README.md`, `zk/health/README.md` — current implementations of this protocol.
- `scripts/zk_audit.py` — post-ingestion hygiene audit (see "Post-ingestion verification" above).
