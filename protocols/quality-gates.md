# Quality Gates

Defines checkpoints that must pass before output reaches the user. Each gate has clear pass/fail criteria and a remediation path.

## Gate Architecture

```
[Research] → Gate 1 → [Synthesis] → Gate 2 → [Review] → Gate 3 → [User]
                                       ↑                    |
                                       └── Revision Loop ←──┘
```

## Gate 1: Research Completeness

**When:** After Researcher finishes, before Synthesizer starts.

| Check | Pass Criteria | Fail Action |
|-------|--------------|-------------|
| Source count | >= 5 relevant notes found | Try alternative search queries |
| Language coverage | Both Chinese and English searched | Run missing language queries |
| Recency | At least 2 notes from last 30 days | Expand time range, note staleness |
| Gap acknowledgment | Gaps explicitly listed | Researcher must document gaps |
| Handoff format | Valid `---handoff---` block present | Researcher must format output |

**Gate keeper:** Orchestrator (main agent)
**Max retries:** 1 (if fail, proceed with degraded flag)

## Gate 2: Synthesis Quality

**When:** After Synthesizer finishes, before Reviewer starts.

| Check | Pass Criteria | Fail Action |
|-------|--------------|-------------|
| Citation density | >= 80% of claims have [[citations]] | Flag unsourced claims for review |
| Insight level | At least 1 Pattern/Tension/Implication level insight | Synthesizer must deepen |
| Goal coverage | All active categories mentioned or explained | Address missing categories |
| Language matching | Chinese sources → Chinese sections | Fix language mismatches |
| Source audit | Source audit block present at end | Synthesizer must add it |

**Gate keeper:** Orchestrator (main agent)
**Max retries:** 1

## Gate 3: Review Pass

**When:** After Reviewer scores, before presenting to user.

| Overall Score | Action |
|--------------|--------|
| 8-10 | APPROVED — deliver to user |
| 6-7.9 | APPROVED_WITH_NOTES — deliver with caveats |
| 4-5.9 | NEEDS_REVISION — send back to Synthesizer with specific fixes (max 2 rounds) |
| 0-3.9 | REJECTED — start over or deliver with major caveats |

**Gate keeper:** Reviewer
**Max revision rounds:** 2 (after 2 failed revisions, deliver with all caveats noted)

## Bypass Conditions

Gates can be bypassed when:
- MCP is unavailable (degraded mode — skip Gates 1 and portions of Gate 3)
- User explicitly asks for a quick/rough reflection
- Session is interactive and user is actively participating (lower bar for completeness)

## Gate Metrics

Track over time (stored in session output):
- Gate 1 pass rate
- Gate 2 pass rate
- Gate 3 average score
- Revision loop frequency
- Bypass frequency
