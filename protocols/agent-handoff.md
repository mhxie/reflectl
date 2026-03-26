# Agent Handoff Protocol

Defines structured contracts for agent-to-agent communication. Every handoff includes a typed envelope so the receiving agent can parse without guessing.

## Envelope Format

Every agent output that feeds another agent MUST include a metadata block:

```
---handoff---
from: <agent name>
to: <agent name>
type: research-brief | synthesis | review-check | challenge-set | perspective | evolution-report
confidence: high | medium | low
gaps: <comma-separated list of what's missing>
context_tokens: <approximate token count of payload>
---end-handoff---
```

## Contract: Researcher → Synthesizer

**Type:** `research-brief`

Required fields:
- `query`: What was searched for
- `sources`: Array of `{title, id, edited, relevance_sentence}`
- `excerpts`: Array of `{source_title, quote, language}`
- `gaps`: What was searched for but not found
- `search_strategy`: Which queries were run (text/vector, languages)
- `confidence`: How complete the coverage feels

The Synthesizer MUST NOT re-search. If gaps are critical, escalate to orchestrator.

## Contract: Synthesizer → Reviewer

**Type:** `synthesis`

Required fields:
- `output_type`: reflection | review | exploration
- `claims`: Array of `{claim, source_title, source_quote}`
- `unsourced_claims`: Array of claims made without direct source (should be empty)
- `goals_referenced`: Which goal categories were covered
- `goals_missing`: Which goal categories were not addressed
- `language_distribution`: % English vs Chinese content

## Contract: Reviewer → Orchestrator

**Type:** `review-check`

Required fields:
- `citations`: `{score: 0-10, issues: []}`
- `goal_coverage`: `{score: 0-10, missing_categories: []}`
- `honesty`: `{score: 0-10, flags: []}`
- `staleness`: `{score: 0-10, warnings: []}`
- `overall`: `{score: 0-10, verdict: "APPROVED" | "NEEDS_REVISION", summary: ""}`

Minimum passing score: 7/10 overall. Below 7 triggers revision loop.

## Contract: Challenger → User

**Type:** `challenge-set`

Required fields:
- `grounding`: What the user seems to be thinking/feeling (evidence-based)
- `affirming`: Question that validates a strength
- `probing`: Question about an assumption
- `challenging`: The uncomfortable question
- `the_one_question`: Single most important question
- `framework_used`: Which framework informed the challenge (if any)
- `emotional_register`: detected mood (excited | neutral | anxious | uncertain | overwhelmed)

## Contract: Thinker → Orchestrator

**Type:** `perspective`

Required fields:
- `reframe`: The situation stripped of the user's framing
- `frameworks_applied`: Array of `{name, insight, applicability: 0-10}`
- `cross_validation`: Where frameworks agree/disagree
- `contrarian_take`: The perspective against the grain
- `external_sources`: Any web research cited

## Escalation Protocol

If any agent encounters:
- **MCP connection failure**: Report the failure, continue with cached index data
- **Empty search results**: Try alternative queries (synonym, other language, broader terms) before reporting gap
- **Contradictory evidence**: Flag explicitly — don't resolve silently
- **Token budget exceeded**: Summarize and note truncation

## Revision Loop

When Reviewer returns `NEEDS_REVISION`:
1. Reviewer specifies which checks failed and what would fix them
2. Synthesizer receives revision request with specific issues
3. Synthesizer revises (max 2 revision rounds)
4. If still failing after 2 rounds, deliver with caveats noted
