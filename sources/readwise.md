# Readwise

Content ingestion and normalization layer. Captures web articles, PDFs, newsletters, tweets, YouTube transcripts, and EPUBs. Provides AI summaries and highlight management.

## Setup

- Install: `npm install -g @readwise/cli`
- Auth: `readwise login` (browser OAuth) or `readwise login-with-token <token>`
- Persona: run `/build-persona` to create `reader_persona.md` for personalized triage

## Installed Skills

These are pre-built Claude Code skills (installed via `readwise skills install claude`):

- `/triage` — walk through inbox one doc at a time with personalized pitches
- `/build-persona` — build reading profile from your library
- `/feed-catchup` — catch up on RSS feed
- `/reader-recap` — briefing on recent reading activity
- `/quiz` — test retention on recently read documents
- `/surprise-me` — surface surprising patterns in your reading history

## Key CLI Commands

### List and search
```bash
# Inbox (most recent saves)
readwise reader-list-documents --location new --limit 20 \
  --response-fields title,author,summary,category,word_count,saved_at,tags

# Search across all saved documents
readwise reader-search-documents --query "distributed training"

# Filter by category and location
readwise reader-list-documents --location later --category article --tag research

# Semantic search across highlights
readwise readwise-search-highlights --vector-search-term "compounding knowledge"
```

### Read content
```bash
# Full document as markdown (the "page fault" — only load when needed)
readwise reader-get-document-details --document-id <id>

# Highlights on a document
readwise reader-get-document-highlights --document-id <id>
```

### Organize
```bash
# Move between locations: new → later → shortlist → archive
readwise reader-move-documents --document-ids <id1>,<id2> --location archive

# Tag documents
readwise reader-add-tags-to-document --document-id <id> --tag-names deep-read,ml-infra

# List all tags
readwise reader-list-tags
```

### Save
```bash
# Save a URL (Readwise scrapes and snapshots it)
readwise reader-create-document --url "https://example.com/article" --tags research
```

## Locations

| Location | Purpose |
|----------|---------|
| `new` | Inbox — unsorted saves |
| `later` | Worth reading but not now |
| `shortlist` | High priority |
| `archive` | Done or skipped |
| `feed` | RSS feed items |

## Tagging Convention (for pipeline integration)

| Tag | Meaning |
|-----|---------|
| `#deep-read` | Queued for a reflectl `/reflect → Read` session |
| `#digest` | Include in weekly reading digest |
| `#auto-triaged` | Processed by the curate pipeline |

## Output

All commands support `--json` for machine-readable output. Pipe through `jq` for filtering.
