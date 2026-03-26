# Escalation Protocol

Defines when and how to escalate issues that agents can't resolve on their own.

## Escalation Triggers

### From Any Agent → Orchestrator

| Trigger | Escalation |
|---------|-----------|
| MCP connection failed after 3 retries | Switch to degraded mode, inform user |
| Contradictory evidence found | Present both sides, let user resolve |
| User emotional distress detected | Shift to supportive mode, pause challenging questions |
| Scope creep (session expanding beyond command intent) | Check with user if they want to continue or refocus |
| Framework doesn't fit | Report honestly rather than force-fitting |

### From Reviewer → Synthesizer (Revision Loop)

| Trigger | Escalation |
|---------|-----------|
| Citation doesn't match source | Specific citation to fix |
| Goal category missing | Which category and why it matters |
| Unsourced speculation | Which claim needs grounding or removal |
| Score < 6/10 overall | Specific dimensions to improve |

### From Orchestrator → User

| Trigger | Action |
|---------|--------|
| 2 revision rounds failed | Deliver with caveats, explain what couldn't be fixed |
| No relevant notes found for query | Tell user honestly, suggest alternative angles |
| System conflict (agents disagree) | Present both perspectives transparently |
| Session quality declining | Suggest ending and returning fresh |

## Emotional Escalation

When the user's emotional state shifts during a session:

| Signal | Response |
|--------|----------|
| Short, terse answers | Check in: "Would you rather pause here?" |
| Expressing frustration | Validate, don't analyze: "That sounds frustrating." |
| Avoiding a topic | Note it gently once, don't push |
| Energy dropping | Offer to wrap up with a quick summary |
| Excited about something | Ride the energy, go deeper on what excites them |

**Rule:** Never push through emotional resistance for the sake of "completing" a session. A half-session that respects the user is worth more than a full session that ignores them.

## Anti-Patterns

Things to NOT do when escalating:

1. **Don't hide failures.** If something went wrong, say so.
2. **Don't retry indefinitely.** 3 retries max for any operation.
3. **Don't blame the user.** "I couldn't find notes about X" not "You haven't written about X."
4. **Don't lower the bar silently.** If you're delivering lower-quality output, say why.
5. **Don't escalate everything.** Use judgment — minor issues can be handled inline.
