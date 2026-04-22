# Civilization Report

Read-only layered life dashboard with token economy. Single-pass render from vault signals. No new state files, no MCP calls.

## Design Rationale

Life domains are not peers (VanderWeele 2017, PERMA+4 2022, GFS 2025). This dashboard uses a three-layer model:
- **Foundation**: non-substitutable; collapse cascades upward
- **Enablers**: multipliers; constraints that gate how tokens can be spent
- **Expression**: where value is created and experienced

## Token Economy

Five tokens model accumulated life resources. Like Civ 6's gold counter, each shows a **real stock value** (your actual position) plus a **yield** (weekly change signal). Stocks are sourced from the most recent vault data; if the data is stale (>30 days), the system prompts the user to update.

| Token | Stock (what it measures) | Unit | How to read from vault |
|---|---|---|---|
| 金 Capital | Net worth / family assets | Dollar amount | Most recent financial plan or reflection with NW figure |
| 气 Vitality | Body state | Weight (kg) + sleep regularity | Most recent weight check-in; sleep signal from daily notes |
| 势 Momentum | Career standing | Role level + tenure + ownership count | profile/identity.md career section + career reflections |
| 识 Insight | Knowledge base | Wiki entry count + reading sessions (30d) | `ls zk/wiki/*.md \| wc -l` + reflection scan |
| 缘 Connection | Relationship health | Interaction frequency estimate (30d) | Daily notes + reflections for social events; PRM DL0 count |

**Immigration** is not a token; it is a **strategic resource** (like Civ 6's iron/niter) that gates how other tokens can be spent. Without green card progress, 金 cannot buy a house, 势 cannot switch employers, 缘 cannot advance family timeline.

### Stock Sourcing Rules

Each stock must come from a **specific vault artifact** with a known date. The Researcher records what file the value came from and when.

- **金**: Search reflections and plan files for the most recent explicit NW or asset figure. Report the value and the source date. If >30 days stale: flag `金 stale: last updated YYYY-MM-DD. Update your financial snapshot.`
- **气**: Primary: most recent weight check-in (from weight plan file, daily notes, or reflections). Secondary: sleep pattern signal (regular/drifting/unknown). If no weight data in 30 days: flag stale. If no weight data ever: report `no baseline`.
- **势**: Composite from profile: current role level + days at employer + count of distinct ownership areas claimed in career reflections (last 30d). This does not go stale quickly; update when role changes.
- **识**: Wiki count (countable, always fresh) + reading sessions in last 30d (countable from reflections). Note if wiki mtime is bulk-synced.
- **缘**: **Estimate** (collection layer not fully built). Count distinct social interactions mentioned in daily notes and reflections over last 30d (dinners, gaming, calls, meetups, partner planning sessions). Add DL0 count from most recent PRM reflection. Report as `~N interactions/30d, DL0: M`. Flag if PRM data >60 days stale.

### Yield (weekly change)

Yield is not a separate count; it is the **delta** visible when comparing the current stock to the prior reading. For tokens without numeric stocks (势, 缘), yield is qualitative: `+` (evidence of growth), `=` (maintenance), `-` (decay/neglect), `?` (insufficient signal).

### Spend Targets

The Researcher maps from directions.md what each token is currently being invested toward. These are not hardcoded; derive them from the active near-term and mid-term goals per civ.

## Civ 6 Mechanics

### Governors (♛/○)

A civ is **governed** (♛) if it has a dedicated system or plan artifact in the vault (e.g., a health plan, a finance system, a relationship management system). **Ungoverned** (○) civs lack infrastructure and are less stable. The Researcher checks for plan files referenced in directions.md or created in reflections.

### Ages (per civ)

Each civ is classified into an Age based on recent trajectory + achievement density:

| Age | Condition | Symbol |
|---|---|---|
| **Golden** | Accelerating trajectory + at least 1 wonder in window | `★` |
| **Normal** | Steady trajectory, or accelerating but no wonder | `·` |
| **Dark** | Coasting/declining/blocked, or declared goal with 0 activity | `◆` |
| **Heroic** | Was Dark last period, now accelerating with a wonder (the comeback) | `✦` |

Since the vault is young (~1 month), "last period" comparison may not be available. In that case, classify based on current signals only (no Heroic possible without a prior Dark reading).

### Era Score

Era Score measures progress toward the next Golden Age at the **era level** (not per-civ). It accumulates through the current era and is evaluated at era transitions or quarterly reviews.

**Earning Era Score:**

| Event | Points | Source |
|---|---|---|
| Wonder completed (goal achieved, system built) | +3 | Strikethrough lines, Completed Goals, milestone reflections |
| Governor established (new plan/system for a civ) | +2 | New plan file created |
| Emergency resolved before deadline | +2 | Deadline passed with evidence of action |
| Dedication alignment (quarterly focus matches top activity civ) | +1/week | 知行合一 check |
| Token stock increase (any token measurably improved) | +1 | Stock comparison vs prior reading |

**Losing Era Score:**

| Event | Points | Source |
|---|---|---|
| Stale goal (declared >1yr, no evidence) | -1 each | Stale Goals section in directions.md |
| Ungoverned Dark civ (no plan + declining) | -2 each | Governor + Age check |
| Emergency missed (deadline passed, no action) | -3 | Deadline check |
| 知行 gap (declared priority, 0 activity) | -2 | Alignment diagnostic |

**Thresholds** (calibrate over time; initial values):
- Golden Era: score >= 15
- Normal Era: 5 <= score < 15
- Dark Era: score < 5

Report: current score, trajectory to threshold, and what would move the needle most.

### Emergencies (⚡)

Time-limited critical events with hard deadlines. Triggered when a deadline from directions.md or reflections is <90 days out.

The Researcher scans directions.md and recent reflections for:
- Explicit dates (YYYY-MM-DD or month references)
- Deadline language ("by", "before", "due", "expires", "deadline")
- Expiration signals ("PTEP", "visa expires", "window closes")

Report each emergency as: `description (Nd remaining) → affected civs`

### Dedications

The quarterly focus from directions.md (`focus_this_quarter`) is the current Dedication. Activity aligned with the Dedication earns bonus Era Score (+1/week). The 知行合一 check evaluates Dedication adherence.

## Prerequisites

1. If `profile/identity.md` missing: "Run `/introspect` first." Stop.
2. If `profile/directions.md` missing: "Run `/introspect` first." Stop.
3. `Last built:` older than 7 days: warn, continue.

## Dispatch Pattern

Single pass, two dispatches:
1. **Researcher**: gathers signals, reads tokens, computes era score, returns brief.
2. **Synthesizer**: renders compact tree. No write.

## Data Contract (brief the Researcher with this)

All reads local. Grep + Read. Semantic search only for concept-shaped retrieval.

### 1. Profile Context

Read `profile/directions.md` and `profile/identity.md` in full. Extract era, goals, completed goals, stale goals, key insights, employer/start date, partner name, key people.

### 2. Term Derivation

Do NOT use hardcoded regex. For each civ:
1. Extract goal lines and life area descriptions from profile files.
2. Pull 5-10 key nouns/phrases (English + Chinese), including proper nouns.
3. Build ephemeral grep regex.

### 3. Token Stock Reading

For each of the 5 tokens, find the **current stock value** and its **source date**:

- **金**: Search reflections and plan files for most recent explicit NW/asset figure. Check financial plan files referenced in directions.md. Report: value, source, date. Flag if >30d stale.
- **气**: Check weight plan file; scan daily notes for weight/sleep. Report: weight (or "no baseline"), sleep pattern, source date. Flag if >30d stale.
- **势**: From profile: role level, employer start date, ownership areas from career reflections (30d).
- **识**: Wiki count (`ls zk/wiki/*.md | wc -l`) + reading sessions (30d). Note bulk-sync caveat.
- **缘**: Estimate: count distinct social interactions in daily notes + reflections (30d). PRM DL0 count. Flag as estimate.

### 4. Per-Civ Signals + Governor + Age

For each of the 7 civs:
1. **Goal inventory** from directions.md.
2. **Reflection scan** (30d default; 60d for Immigration, Experience).
3. **Governor check**: does a dedicated plan/system file exist for this civ? (e.g., weight plan, financial plan, PRM system, career thesis, frontier labs pipeline, travel plan). Report ♛ or ○.
4. **Age classification**: apply the Age rules based on trajectory + wonders.
5. **Supplemental sources**: plan notes referenced in goals.

### 5. Emergencies

Scan directions.md and recent reflections for deadlines <90 days from today. For each:
- What is the deadline and what happens if missed?
- Which civs are affected?
- Is there evidence of action toward it?

### 6. Era Score Calculation

Count events per the Era Score table. Sum positives and negatives. Report:
- Current score with itemized breakdown
- Distance to Golden threshold
- Single highest-leverage action to gain points

### 7. Constraints + Wonders + 知行合一

Same as before: directed edges, 3-5 wonders (60d), alignment diagnostic.

## Researcher Handoff Format

```
era: { current, theme, dedication (quarterly focus), phase_context }

tokens:
  金: { value, source, as_of, stale, spend_target }
  气: { weight, sleep, source, as_of, stale, spend_target }
  势: { level, day, ownership_areas, spend_target }
  识: { wiki, reading_sessions_30d, bulk_synced, spend_target }
  缘: { interactions_30d_est, dl0, prm_date, stale, spend_target }

civilizations:
  [per civ]: { layer, age (★·◆✦), governor (♛/○), goals, key_evidence (2-3 lines), wins }

strategic_resource:
  immigration: { status, constraints_on, evidence }

emergencies: [ { description, deadline, days_remaining, affected_civs, action_evidence } ]

era_score:
  total: N
  breakdown: { wonders: +N, governors: +N, emergencies_resolved: +N, dedication_weeks: +N, token_gains: +N, stale: -N, ungoverned_dark: -N, emergencies_missed: -N, 知行_gap: -N }
  threshold: { golden: 15, current_age_projection: "Golden/Normal/Dark" }
  highest_leverage: "..."

constraints: [directed edges]
wonders: [...]
alignment: { dedication, top_alignment, top_gap, undeclared_activity }
gaps: [...]
```

## Synthesizer Instructions

Produce a **compact tree** (~25 lines). The orchestrator handles drill-down.

### Compact Tree Template

```
## Civ Report (YYYY-MM-DD)
_Era · Phase · Dedication: [quarterly focus]_

金 $NNK (MM-DD)  气 NNkg (MM-DD)  势 LN·DayN·Nown  识 Nw·Nr  缘 ~Ni·DL0:N (est)
[stale flags if any]

Foundation
├─ Health       [age][gov]  [≤8 words]
└─ Finance      [age][gov]  [≤8 words]

Enabler
├─ Immigration  [age][gov]  [≤8 words]  ⊳ gates: [list]
└─ Relationships [age][gov]  [≤8 words]

Expression
├─ Career       [age][gov]  [≤8 words]
├─ Learning     [age][gov]  [≤8 words]
└─ Experience   [age][gov]  [≤8 words]

⚡ Emergencies: [description (Nd)] · [description (Nd)]
Era Score: N/15 → [projected age]. [+action to gain most points]
知行: [dedication] → [aligned] | gap: [gap civ]
Next: [foundation] → [enabler] → [expression]

> Name a civ, token, or "era score" to expand.
```

Format: `★♛` = Golden + governed. `◆○` = Dark + ungoverned. `·♛` = Normal + governed.

### Drill-Down: Civ

```
### [Civ] [age][gov] ([layer])
**Goals:** [list]
**Evidence:** [2-3 sentences citing [[Sources]]]
**Wins:** [list or "none"]
**Governor:** [plan name] or "none (ungoverned: +2 era score if you build one)"
**Constraints:** [edges]
**Next:** [one action]
```

### Drill-Down: Token

```
### [Token] (气/金/势/识/缘)
**Stock:** [value] (as of MM-DD)
**Spending on:** [targets from directions.md]
**Trend:** [delta vs prior or qualitative +/=/-/?]
**Bottleneck:** [what limits this token, if any]
```

### Drill-Down: Era Score

```
### Era Score: N/15
**Earning:**
  Wonders: +N ([list])
  Governors: +N ([list of governed civs])
  Emergencies resolved: +N
  Dedication alignment: +N (N weeks aligned)
  Token gains: +N ([which tokens improved])
**Costing:**
  Stale goals: -N ([list])
  Ungoverned Dark civs: -N ([list])
  Emergencies missed: -N
  知行 gap: -N ([which])
**To reach Golden (15):** [what specific actions would earn the most points]
```

Other sections (Constraint Map, Wonders list, full 知行) on request. Keep drill-downs under 15 lines.

## Style Constraints

- No em dashes. Colons, semicolons, parentheses, or restructure.
- No H1. Start with `##`.
- Citations in drill-downs only, as `[[Title]]`.
- Default English. Chinese token names (气金势识缘) inline. Civ names English.

## Frequency

Ad hoc. Identical output on unchanged vault.

## Evolution Note

Persistent era score ledger and historical token snapshots are out of scope. If repeated use shows demand, evolve toward a `zk/civ/` state directory with weekly snapshots.
