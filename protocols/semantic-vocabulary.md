## Purpose

Documents the small set of tags that carry **semantic meaning for agents**. Tags listed here are not navigation; they tell agents how to interpret the content that follows.

Agents that parse `$ZK` markdown must recognize these tags. Free-form tags outside this list are user-defined and not interpreted.

## Why tags, not wikilinks

Wikilinks (`[[Foo]]`) only resolve to other notes. Semantic markers like "Side Notes" are not notes — they label sections inline. Tags (`#side-notes`) render in most markdown viewers and on GitHub, are search-indexable, and don't pollute the link graph.

The `scripts/wikilink_to_md.py` converter rewrites unresolved `[[Foo]]` to `#foo-slug` automatically; semantic markers fall out as tags by virtue of having no target file.

## Documented semantic tags

| Tag | Meaning |
|-----|---------|
| `#side-notes` | Section: voice-transcribed bullets follow |
| `#decisions` | Section: decision log entries follow |
| `#open-questions` | Section: unresolved questions follow |
| `#todo` | Section: actionable items follow |
| `#action-items` | Section: assigned next-steps follow |
| `#references` | Section: citations follow |
| `#followups` | Section: deferred items requiring later attention |
| `#evidence` | Section: supporting evidence for a claim follows |
| `#anomalies` | Session log section: things that broke or surprised |
| `#continuity` | Session log section: handoff context for next session |

Add new entries when a tag is reused across 3+ files and an agent needs to interpret it. Drop entries that no agent ever reads.

## Naming rules (forward-going)

- **Tag slug**: lowercase ASCII or unicode; spaces → `-`; punctuation stripped (`#side-notes`, `#心流`).
- **No pure-number tags**: `[[2025]]` → strip to plain text `2025`. A tag must contain at least one non-digit character.
- **Dates**: only ISO `YYYY-MM-DD`. Wikilinks like `[[2024-08-08]]` resolve to `daily-notes/2024-08-08.md` if present, else strip to plain text. Legacy formats (`Thu, August 8th, 2024`, `8/8/2024`, `2024年8月8日`) get normalized to ISO during conversion; do not introduce new ones.

## Backlink categories (canonical reference)

| Pattern | Source intent | Converter target |
|---------|---------------|-------------------|
| `[[Foo]]` resolves to a `.md` file | navigation | `[Foo](relative/Foo.md)` |
| `[[Foo\|Bar]]` resolves | aliased navigation | `[Bar](relative/Foo.md)` |
| `[[Foo#Section]]` resolves | section anchor | `[Foo](relative/Foo.md#section-slug)` |
| `[[Foo#^block]]` resolves | block ref (wikilink-native) | `[Foo](relative/Foo.md)` (block id dropped) |
| `[[<full-date>]]` | daily-note ref | `[YYYY-MM-DD](daily-notes/YYYY-MM-DD.md)` if file exists, else plain ISO |
| `[[<pure-digits>]]` | bare year/number | strip to plain text |
| `[[]]` | empty | strip entirely |
| `[[Foo]]` unresolved | semantic marker (or broken) | `#foo-slug` tag |
| `![[image.png]]` (wikilink embed) | inline image | `![](image.png)` standard markdown |
