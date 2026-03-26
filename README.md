# Reflection

Reflecting on Reflect Notes with Claude Code.

A structured self-reflection system built as a [Claude Code](https://docs.anthropic.com/en/docs/claude-code) project. It connects to your [Reflect.app](https://reflect.app/) notes via MCP — helping you reflect on what you've written, structure your thoughts, track goals, and plan better.

## How It Works

```
Reflect.app  <──MCP──>  Claude Code Commands
(your notes)              /index    — build reflection context
                          /reflect  — daily reflection session
                          /review   — goal progress review
                              │
                              ▼
                     index/   — lightweight reflection context
                     reflections/  — session outputs (local, gitignored)
```

Claude Code reads your notes through the Reflect MCP server, synthesizes an index of your goals and themes, then uses that context to run reflection and review sessions. Insights are written back to your Reflect daily notes.

## Prerequisites

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI installed
- [Reflect.app](https://reflect.app/) with the MCP server enabled
- Reflect MCP server running locally (see [Reflect MCP docs](https://reflect.app/mcp))

## Setup

1. **Clone the repo:**
   ```bash
   git clone https://github.com/mhxie/Reflection.git
   cd Reflection
   ```

2. **Configure MCP** — create `.mcp.json` in the project root (gitignored):
   ```json
   {
     "mcpServers": {
       "reflect": {
         "type": "http",
         "url": "http://127.0.0.1:7676/mcp"
       }
     }
   }
   ```
   Adjust the URL if your Reflect MCP server runs on a different port.

3. **Build your reflection index:**
   ```bash
   claude
   # then inside Claude Code:
   /project:index
   ```
   This queries your Reflect notes via MCP and generates:
   - `index/meta-summary.md` — who you are, major themes, active life areas
   - `index/goals.md` — extracted goals by category with metrics

4. **Start reflecting:**
   ```
   /project:reflect    # daily reflection session
   /project:review     # goal progress review (weekly recommended)
   ```

## Commands

| Command | Purpose | Frequency |
|---------|---------|-----------|
| `/project:index` | Build or refresh your reflection context from Reflect notes | When notes change significantly |
| `/project:reflect` | Run a reflection session with questions grounded in your notes | Daily |
| `/project:review` | Review progress on goals, surface neglected areas, spot emerging interests | Weekly |

## Architecture

**MCP-first design** — instead of batch-processing thousands of notes locally, the system queries Reflect's MCP server on-the-fly using text and vector search. A lightweight local index (~15K tokens) caches only the reflection context that every session needs.

Key design decisions:
- **Two-way data flow**: reads notes via MCP, writes reflection summaries back to Reflect daily notes
- **Self-contamination guard**: AI-written content tagged `#ai-reflection` is excluded from future searches
- **Bilingual support**: handles English and Chinese notes, matches the user's language
- **Privacy by default**: all personal data (index, reflections, MCP config) is gitignored

## Customization

The persona and rules live in `CLAUDE.md`. You can customize:
- **Reflection style** — adjust the persona, question types, or tone
- **Goal categories** — the default categories are `#capacity`, `#learning`, `#identity`, `#energy`
- **Index queries** — edit `.claude/commands/index.md` to change which notes are indexed
- **Write-back behavior** — disable or modify how insights are written back to Reflect

## Project Structure

```
Reflection/
  CLAUDE.md                        # Persona and rules
  .claude/commands/
    index.md                       # Index builder command
    reflect.md                     # Daily reflection command
    review.md                      # Goal review command
  index/                           # Coaching context (gitignored)
  reflections/                     # Session outputs (gitignored)
  .mcp.json                        # MCP server config (gitignored)
```

## License

MIT
