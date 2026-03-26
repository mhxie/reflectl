# Error Handling & Graceful Degradation

Defines how agents handle failures without blocking sessions.

## Failure Hierarchy

Failures are ranked by severity. Handle at the lowest level possible.

### Level 1: Recoverable (handle silently)
- Single MCP search returns empty → try alternative query
- Note content is shorter than expected → use what's available
- Framework file missing → skip framework, use first principles
- Previous reflection file missing → treat as first session

### Level 2: Degraded (warn and continue)
- MCP server unreachable → fall back to cached index files only
- Index files stale (>7 days) → warn user, proceed with stale data
- Multiple searches return empty → report coverage gap, continue with available data
- Write-back to Reflect fails → save locally, inform user

### Level 3: Blocking (stop and inform)
- No index files AND no MCP connection → cannot proceed, guide user to fix
- All goal data missing → cannot run review, suggest `/project:index`
- Fundamental prompt misunderstanding → ask user to clarify

## Agent-Specific Fallbacks

### Researcher
- **MCP down**: Read `index/meta-summary.md` and `index/goals.md` as sole sources. Prefix output with `[DEGRADED: MCP unavailable, using cached index only]`
- **Empty results**: Try 3 alternative queries before reporting gap. Query strategy: exact → semantic → broader category
- **Rate limited**: Batch remaining queries, report partial results

### Synthesizer
- **No research brief received**: Read index files directly (bypass normal contract). Note: `[DEGRADED: No research brief, synthesizing from index only]`
- **Research brief has critical gaps**: Acknowledge gaps explicitly in output rather than filling with speculation
- **Write failure**: Save to `reflections/` locally, skip Reflect write-back

### Reviewer
- **Cannot verify citation**: Mark as `UNVERIFIED` rather than `FAIL`. Distinguish "wrong" from "couldn't check"
- **Index goals.md missing**: Skip goal coverage check, note in output
- **MCP down during spot-check**: Use grep on local files as fallback

### Challenger
- **No recent daily notes**: Use latest reflection file as context instead
- **No contradictions found**: This is fine — not every session has contradictions. Don't force them.
- **User emotional state unclear**: Default to neutral register

### Thinker
- **Framework files missing**: Use built-in knowledge of frameworks (they're well-known models)
- **Web search fails**: Proceed without external sources, note the limitation
- **No clear framework fit**: Use first principles thinking — always available

### Evolver
- **Cannot write to files**: Report proposed changes as text diff for manual application
- **Git operations fail**: Propose changes without committing
- **Conflicting improvement signals**: Document the tension, don't force resolution

## Session Continuity

If a session is interrupted:
1. Check `reflections/` for partial output from today
2. Check daily note for `#ai-reflection` content already written
3. Resume from the last completed step rather than restarting
4. If unclear what was done, ask the user

## Timeout Policy

- MCP calls: 30 seconds before fallback
- Web searches: 15 seconds before skip
- Agent handoffs: No timeout (rely on maxTurns)
- Write operations: 10 seconds, then save locally
