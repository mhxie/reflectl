# Build Coaching Index

Build or refresh the reflection context index by querying Reflect notes via MCP.

## Prerequisites

Verify the Reflect MCP server is accessible by calling `list_tags`. If it fails with a connection error, tell the user: "Cannot reach Reflect MCP server. Make sure Reflect is running and the MCP server is enabled."

## Pipeline

### Step 1: Discover Goals

Search for goal-related notes using multiple queries to cover both languages:

1. `search_notes(query: "目标", limit: 20)` — Chinese goal notes
2. `search_notes(query: "goal", limit: 20)` — English goal notes
3. `search_notes(query: "小目标", limit: 20)` — Annual goal notes (e.g., "2026小目标")
4. `search_notes(query: "objective", limit: 10)` — Additional goal notes

Deduplicate results by note ID. Prioritize recent notes — use `editedAfter` filter to weight notes edited in the last 12 months. Also fetch older goal notes but flag them as potentially stale.

### Step 2: Discover Themes and Context

1. `list_tags()` — Get all available tags to understand the user's categorization system
2. `search_notes(query: "career", limit: 10)` — Career trajectory
3. `search_notes(query: "learning", limit: 10)` — Learning interests
4. `search_notes(query: "职业", limit: 10)` — Chinese career notes
5. `search_notes(query: "学习", limit: 10)` — Chinese learning notes

### Step 3: Get Recent Context

1. `get_daily_note(date: "<today's date>")` — Today's daily note
2. `get_daily_note(date: "<yesterday's date>")` — Yesterday's daily note
3. `search_notes(query: "plan", editedAfter: "<30 days ago>", limit: 10)` — Recent planning notes

### Step 4: Read Full Content

For the top ~30-40 most relevant notes from Steps 1-3, read their full content using `get_note(noteId: "<id>")`. Focus on:
- All goal notes (these are critical)
- Recent daily notes
- Top career/learning notes

### Step 5: Synthesize Index Files

Using all gathered content, create two files:

**`index/meta-summary.md`** (~3-5K tokens max):
```markdown
# Meta Summary
Last built: YYYY-MM-DD

## Who You Are
[2-3 sentence summary of the user based on their notes — role, interests, life stage]

## Active Life Areas
[Bullet points for each major area: career, learning, health, relationships, finance, etc.]

## Major Themes
[Recurring topics across notes — what does this person think about most?]

## Key People
[Important people referenced frequently in notes — mentors, collaborators, family]

## Recent Focus
[What the user has been writing about in the last 30 days]
```

**`index/goals.md`** (~5-10K tokens max):
```markdown
# Goals Index
Last built: YYYY-MM-DD

## Near-term (next 1-3 months)
[Goals with specific metrics, sourced from recent notes]
- Goal: [description] — Source: [[Note Title]]

## Mid-term (3-12 months)
[Goals from annual planning notes]
- Goal: [description] — Source: [[Note Title]]

## Long-term (1-3 years)
[Career/life direction from strategic planning notes]
- Goal: [description] — Source: [[Note Title]]

## Stale Goals (>1 year old, may need review)
[Goals from notes not edited recently]
- Goal: [description] — Source: [[Note Title]] — Last edited: YYYY-MM-DD
```

### Step 6: Write Build State

Write `index/.build-state.json`:
```json
{
  "lastBuilt": "YYYY-MM-DDTHH:MM:SSZ",
  "notesProcessed": <count>,
  "goalsFound": <count>,
  "tagsFound": <count>
}
```

### Step 7: Report

Tell the user what you found:
- How many notes were queried
- How many goals were extracted
- Key themes identified
- Any gaps or concerns (e.g., "No goal notes found for 2026 — do you have annual goals set?")
- Suggest running `/project:reflect` to start using the index
