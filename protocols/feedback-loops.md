# Feedback Loops

Defines how the system learns from each session and improves over time.

## Three Feedback Loops

### Loop 1: Within-Session (Real-time)

During a session, calibrate based on user signals:

| User Signal | Interpretation | Adjustment |
|-------------|---------------|------------|
| Long, detailed response | Engaged, go deeper | Ask follow-up questions |
| "Yes" / "That's right" | Confirmed, move on | Don't belabor the point |
| "Not really" / "That's not quite it" | Missed, recalibrate | Ask clarifying question |
| Question back to you | Wants more detail | Provide evidence |
| Changes subject | Done with this topic | Follow their lead |
| Silence / minimal response | Disengaged or thinking | Ask if they want to continue |

### Loop 2: Between-Sessions (Session-over-session)

After each session, capture what worked:

**In the session output file, include:**
```markdown
## Session Meta
- Duration: [approximate]
- User engagement: high / medium / low (based on response patterns)
- Questions that landed: [which questions got thoughtful responses]
- Questions that didn't land: [which got deflected or minimal response]
- Frameworks used: [which frameworks, if any]
- Surprise factor: [did we surface something genuinely new?]
```

**The Evolver reads this to:**
- Identify question types that consistently land vs. fall flat
- Track which frameworks the user responds to
- Notice if certain goal categories get more engagement
- Adjust the system to do more of what works

### Loop 3: Cross-Session (Systemic)

Monthly or every 10 sessions, the Evolver should:

1. **Read all session score cards** from the past month
2. **Identify patterns:**
   - Which dimensions consistently score low?
   - Which session types (reflect/review/weekly/etc.) score highest?
   - Is the trend improving, stable, or declining?
3. **Propose system changes** based on evidence
4. **Request codex review** on proposed changes for external perspective

## Feedback Collection

### Implicit Feedback (always captured)
- User response length and depth
- Which questions get followed up vs. dropped
- Topics that get repeated across sessions (important to user)
- Topics that get avoided across sessions (sensitive or boring)

### Explicit Feedback (when offered)
If the user says:
- "That was helpful" → Note what worked in session meta
- "That wasn't useful" → Note what didn't work, consider why
- "Don't do X" → Save as feedback memory immediately
- "Keep doing Y" → Save as positive feedback memory

## Calibration Signals

Over time, the system should learn:

| Signal | What It Teaches |
|--------|----------------|
| User engages more with Chinese content | Increase Chinese-language reflection |
| User skips energy audit | Maybe not valuable, or wrong timing |
| User always asks follow-up on career topics | Career is highest priority |
| User loves the "forgotten thread" section | Invest more in semantic discovery |
| User ignores framework applications | Frameworks may feel too abstract — make more specific |
| Decision journal gets used frequently | User values structured decision-making |

## Anti-Feedback Patterns

Things that look like feedback but aren't:

1. **Recency bias**: One great session doesn't mean the approach is always right
2. **Politeness signal**: "Thanks" doesn't mean it was helpful
3. **Topic interest ≠ question quality**: User may engage with a topic despite poor questions
4. **Absence ≠ rejection**: Not using a command doesn't mean it's bad — might not be the right time
