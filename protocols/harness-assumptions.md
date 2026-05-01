# Harness Assumptions Protocol

Identifies and tracks rules in the reflectl system that depend on model capabilities, API limits, or temporal context. These assumptions go stale across model upgrades and API changes. This protocol is the registry and audit checklist; the assumptions themselves stay in their original files.

## Why This Exists

Rules like "use Opus for creative tasks, Sonnet for mechanical tasks" or "load last 3 reflections" encode a snapshot of model capabilities at a point in time. When capabilities change (new model release, context window expansion, cost reduction, new API features), these rules may become wrong, suboptimal, or unnecessary. Without a registry, they are invisible until they cause a problem.

Inspired by the "context anxiety" example from Anthropic's Managed Agents architecture: a behavioral workaround for Sonnet 4.5 became dead weight when Opus 4.5 shipped. The harness encoded a stale assumption about the model.

## Assumption Classification

| Class | Definition | Example | Staleness Signal |
|-------|-----------|---------|-----------------|
| **Model Assignment** | Which model runs which agent | Researcher=Opus | New model release, benchmark shift, cost change |
| **Token/Context Budget** | Context window sizing, loading limits | "last 3 reflections" | Context window expansion |
| **Temporal Threshold** | Time-based triggers and warnings | "7 days stale" for profile | User behavior data |
| **API Constraint** | Limits imposed by external APIs | "20KB per create_note" | API changelog |
| **Turn Budget** | maxTurns per agent | Evolver=25 | Model efficiency changes |
| **Search Strategy** | Query patterns tuned to current capability | semantic.py stub fallback | semantic.py mode change |

## Assumption Registry

### Model Assignments

`harness/models.toml` is the source of truth for which model runs which role and *why* a profile was chosen — see the `[profiles.*.rationale]` fields. `harness_lint.py` (`models-claude-drift`) catches frontmatter↔toml drift. The table below is the audit-trigger registry only: which profile each agent uses, and what staleness signal would force a re-evaluation. To learn *why* a profile fits a role, read the rationale in `harness/models.toml`.

| Agent | Profile (see `harness/models.toml`) | Re-test When |
|-------|-------------------------------------|-------------|
| Researcher | `deep_reflection` | Sonnet matches Opus on reading comprehension benchmarks |
| Synthesizer | `synthesis` | Sonnet matches Opus on synthesis quality |
| Reviewer | `mechanical_review` | Haiku becomes capable enough for rubric scoring |
| Challenger | `reflective_challenge` | Sonnet improves on open-ended question quality |
| Thinker | `framework_reasoning` | Sonnet matches on framework reasoning |
| Evolver | `system_evolution` | Sonnet matches on multi-file coherence |
| Curator | `note_operations` | Haiku becomes capable for preservation checks |
| Scout | `web_research` | Haiku becomes capable for search + format |
| Reader | `deep_reading` | Sonnet matches on analytical reading quality |
| Meeting | `meeting_extraction` | Haiku becomes capable for transcript processing |
| Librarian | `recommendations` | Haiku becomes capable for bilingual recommendations |
| Privacy Reviewer | `privacy_scan` | Haiku tier capability or cost changes; double-dispatch budget shifts |

### Token/Context Budgets

| Rule | Location | Current Value | Re-test When |
|------|----------|--------------|-------------|
| Reflections loaded at session start | session-continuity.md, reflect.md | Last 3 | Context window doubles |
| Daily notes loaded | reflect.md, session-continuity.md | Last 3-7 | Context window doubles |
| Profile token estimate | reflect.md, session-continuity.md | 3-5K identity, 5-10K directions | Profile format changes significantly |
| Agent prompt + protocols budget | reflect.md, session-continuity.md | ~2K | Agent definitions grow beyond budget |
| Session log excerpt budget | reflect.md, session-continuity.md | ~500-1K | Session logs grow in scope |

### Temporal Thresholds

| Rule | Location | Current Value | Re-test When |
|------|----------|--------------|-------------|
| Profile staleness warning | CLAUDE.md, reflect.md, review.md | 7 days | User data shows profiles change faster/slower |
| Semantic search recency window | reflect.md | 7 days for recent, 3+ months for forgotten | Embedding index makes recency less important |
| L2 staleness thresholds | staleness.py | dormant=45d, stale=90d, promote=180d+2refs | First real corpus ages past 90 days; tune with actual archival decisions |
| Meta-reflection trigger | evolver.md (principle 8 pruning trigger) | Every 5 sessions | Session volume data |

### API Constraints

| Rule | Location | Current Value | Re-test When |
|------|----------|--------------|-------------|
| create_note size limit | CLAUDE.md, curator.md | ~20KB (15KB working) | Reflect API changelog |
| No update/delete operations | CLAUDE.md | Hard constraint | Reflect API changelog |
| create_note parameter names | CLAUDE.md | contentMarkdown, subject | Reflect API changelog |
| No markdown tables in create_note | CLAUDE.md | Hard constraint | Reflect API changelog |
| Silent empty note on wrong params | CLAUDE.md | Known bug | Reflect API fix |

### Turn Budgets

| Agent | Location | Current maxTurns | Re-test When |
|-------|----------|-----------------|-------------|
| Evolver | evolver.md | 25 | Model efficiency improves |
| Researcher | researcher.md | 15 | Search strategy changes |
| Synthesizer | synthesizer.md | 15 | Model gets faster at synthesis |
| Reviewer | reviewer.md | 15 | Checklist execution speed |
| Curator | curator.md | 15 | Note operation complexity |
| Scout | scout.md | 15 | Web search patterns change |
| Librarian | librarian.md | 15 | Recommendation patterns |
| Challenger | challenger.md | 10 | Question generation needs |
| Thinker | thinker.md | 15 | Framework application depth |
| Meeting | meeting.md | 10 | Transcript complexity |
| Reader | reader.md | 15 | Reading depth needs |

### Search Strategy

| Rule | Location | Current Value | Re-test When |
|------|----------|--------------|-------------|
| semantic.py is primary for content queries | CLAUDE.md | Real embedding mode | Index is machine-local at `~/.cache/reflectl/lance/`; rebuild with `uv run scripts/semantic.py index` |
| Grep for structural queries only | CLAUDE.md | Always | semantic.py covers structural queries too |
| Retry with synonyms on empty results | error-handling.md | Manual retry | semantic.py handles synonyms natively |

## Audit Checklist

Run this checklist when any of these events occur:

- [ ] New Claude model release (Opus, Sonnet, Haiku generation change)
- [ ] Reflect API update
- [ ] Context window size change
- [ ] semantic.py mode change (stub to real)
- [ ] Cost structure change (model pricing)
- [ ] Quarterly system review

**Audit procedure:**

1. Identify which registry sections the event affects (use the "Re-test When" column)
2. For each triggered assumption, test whether the current value is still optimal
3. If stale, propose a change via the Evolver's OODA cycle
4. Log the audit result in the next session log under "Harness Assumptions Exercised"
5. Update this registry with new values and rationale after changes land

## Integration

- **Session logs** record which assumptions were load-bearing each session (the "Harness Assumptions Exercised" section in `protocols/session-log.md`)
- **Evolver** checks this registry during its Observe phase for triggered re-test conditions
- **Evolver** aggregates assumption-exercise data across session logs to spot assumptions that are never tested or always active
