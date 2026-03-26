# Daily Reflection

Run a reflection session grounded in your Reflect notes and goals.

## Prerequisites

1. Check if `index/meta-summary.md` exists. If not, tell the user: "No reflection index found. Run `/project:index` first to build your profile." and stop.
2. Read `index/meta-summary.md`. Check the `Last built:` date. If older than 7 days, warn: "Your reflection index is stale (built on [date]). Consider running `/project:index` to refresh. Continuing with current index."

## Context Loading

1. **Read index files:**
   - `index/meta-summary.md` — your reflection context
   - `index/goals.md` — your goals and metrics

2. **Read recent reflections** (last 3 files from `reflections/` directory, sorted by date). If none exist, this is the first session — note that.

3. **Query MCP for fresh context:**
   - `get_daily_note(date: "<today>")` — what you've done today
   - `get_daily_note(date: "<yesterday>")` — what you did yesterday
   - `search_notes(query: "<a theme from meta-summary>", searchType: "vector", limit: 5, editedAfter: "<7 days ago>")` — recent activity related to your themes

## Coaching Session

Based on the loaded context, run an interactive reflection:

1. **Open with a grounding observation.** Reference something specific from today's daily note or recent activity. Example: "I see you wrote about [topic] today in your daily note. How does that connect to your [[goal note title]]?"

2. **Ask 2-3 reflective questions**, one at a time. Each question should:
   - Reference a specific note or goal by title in [[brackets]]
   - Connect current activity to longer-term patterns or goals
   - Be open-ended (not yes/no)
   - Match the user's language (Chinese for Chinese goals)

3. **Surface a forgotten connection.** Use `search_notes(searchType: "vector")` to find a semantically related note the user may have forgotten. Example: "This reminds me of something you wrote in [[old note title]] — [brief quote]. Do you see a connection?"

4. **Close with one concrete prompt.** Based on the conversation, suggest one specific thing to reflect on or do next. Keep it actionable and tied to a specific goal.

## Output

After the interactive session, write a reflection file:

**File:** `reflections/YYYY-MM-DD-reflection.md`
```markdown
# Reflection — YYYY-MM-DD

## Context
[Brief summary of what was discussed, with note citations]

## Key Insights
[Bullet points of insights from the conversation]

## Connections Made
[Notes or themes that were connected during the session]

## Next Action
[The concrete prompt or action suggested]

## Notes Referenced
[List of all notes cited during this session, as [[Note Title]] links]
```

## Write-Back to Reflect

After writing the reflection file, check if today's daily note already contains content tagged `#ai-reflection`.

- If **no existing AI content**: Use `append_to_daily_note` to add a brief summary:
  ```
  ## AI Reflection #ai-reflection
  [2-3 sentence summary of key insights from today's reflection session]
  ```
  Use today's date in YYYY-MM-DD format.

- If **AI content already exists**: Skip write-back to avoid duplicates. Tell the user: "Already wrote to today's daily note earlier — skipping duplicate write-back."

## Wrap Up

Tell the user the reflection has been saved and suggest committing to git:
"Reflection saved to `reflections/YYYY-MM-DD-reflection.md`. You can commit it with: `git add reflections/ && git commit -m 'reflection: YYYY-MM-DD'`"
