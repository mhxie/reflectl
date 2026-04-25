## Purpose

Recommend 3 restaurant candidates based on user-supplied context, historical preferences, and credit-burn opportunities. Read-only on catalog docs; new captures route through `/reflect` Dining Pulse.

## Quick start

`/dine` accepts optional inline context. Examples:
- `/dine` → ask all context
- `/dine 工作日午餐` → use as scene hint, ask remaining
- `/dine 朋友 4 人 川菜 dinner` → use as filters, ask remaining
- `/dine SF burn credit` → location SF + flag credit-burn priority

If args present, parse them as initial filters; only ask for slots not derivable.

## Step 1: Gather context

For missing slots, ask via `AskUserQuestion` or sequential 1-line prompts (whichever fits faster). Required slots first; optional slots only if useful.

| Slot | Options | Required |
|---|---|---|
| **Location** | Bay Area / SF / Peninsula / South Bay / East Bay / LA / NYC / Other | Y |
| **Party** | Solo / Partner / Family (N) / Friends (N) / Mixed work | Y |
| **Meal** | Lunch / Dinner / Brunch / Late night | Y |
| **Time budget** | Quick (<30min) / Standard (1-2h) / Leisurely (2h+) | Y |
| Mood / cuisine | Surprise / 中餐 / 不要中餐 / 重辣 / 清淡 / Comfort / 探索新 / Special occasion / 老人友好 | N (default any) |
| **Health filter** | balanced / 清淡 / 蔬菜多 / less oily / less salty / 高蛋白 / no preference | N (default no preference) |
| Budget cap | $20 / $50 / $100 / $150+ / no cap | N |
| Avoid recent | Last 30 / 60 / 90 days | N (default 30) |

## Step 2: Load data (parallel)

The user's vault holds these catalogs under `zk/travel/` and `zk/finance/`. Discover the actual filenames via `Grep` on those directories at runtime; do not hardcode private filenames here.

- Regional dining catalog (rotation + Michelin wishlist + 场景索引), under `zk/travel/`
- Dining log (history with 评分 + 再去 + recency), under `zk/travel/`
- Credit-perks dining catalog (Cycle Tracking + city catalogs), under `zk/travel/`
- Perks ledger (current cycle credit status, for burn signal), under `zk/finance/`
- For LA / NYC / other city: use the credit-perks catalog city section + the corresponding city Michelin guide under `zk/archive/practical/travel/`

**Missing-file fallback:** if any of these is absent, skip it silently and note the gap in the closing line ("scored without [missing source]"). The recommendation still produces; the user can decide whether to recreate the catalog.

## Step 3: Filter + score

**Hard filters** (eliminate non-matches):
- Location matches user's region
- Cuisine NOT in avoid list
- Estimated price ≤ budget cap (allow 20% margin)
- Drive time fits time budget (heuristic: 🚗 count × 15min one-way)
- For Quick lunch: ⌛ ≤ 1
- For "Special occasion": Michelin OR Exclusive Tables only
- Skip restaurants visited within `avoid recent` window (from the dining log)

**Soft scoring** (rank candidates):
| Factor | Score |
|---|---|
| Catalog 评 (legacy field) = 3 | +3 |
| Catalog 评 = 2 | +2 |
| Catalog 评 = 1 | +1 |
| Log 评分 avg (last 3 visits) ≥ 8 | +5 |
| Log avg 6-7 | +2 |
| Log avg ≤ 5 | -3 |
| 再去 = Y in last entry | +2 |
| 再去 = N in last entry | -5 (effectively eliminate unless strong override) |
| 场景索引 match (regional catalog) | +3 |
| Last visit 31-90d ago | 0 |
| Last visit > 90d (rusty miss) | +1 |
| Never visited + mood = "Surprise" or "探索" | +2 |
| **Credit-burn priority** (Exclusive Tables restaurant + relevant cycle has unused credit AND ≤ 60d to deadline) | **+5** |
| Michelin star match + mood = "Special occasion" | +4 |
| Old-favorite revisit (rotation 评 ≥ 2 + last visit > 60d) | +2 |
| **Health filter active** + recent visits (last 3) tagged 油重/盐重/肥肉多 | -3 |
| **Health filter active** + history shows balanced/清淡/蔬菜多 OR restaurant is salads/Vietnamese/Japanese clean style | +3 |
| **Health filter active** + last 5 days had ≥3 油重/重口 entries (cumulative load) | additional +2 to clean options, -2 to oily options |

## Step 4: Output

Top 3 candidates as a table:

```markdown
| # | 餐厅 | 类型 | $ | 距离·等待 | Why | Credit signal |
|---|---|---|---|---|---|---|
| 1 | 东北烧烤 | 东北/烧烤 | $30-60 | 近·中等 | 评 3 (top); fits 4 friends 晚餐; 近期没去 (last 75d) | n/a |
| 2 | Selby's | American ⭐ | $150+ | 远·订位 | Michelin 1⭐; 上次 8/10 想再去; **CSR #2 Exclusive Tables H1 deadline 6/30 ($150)** | 🔥 burn |
| 3 | Aziza | N African ⭐ | $80-120 | 中·订位 | 探索新 (never visited); Michelin 1⭐; Exclusive Tables 候选 | CSR #1 H1 ✓ available |
```

Brief reasoning paragraph (2-3 lines) below the table:
- Mention the top filter constraints applied
- Flag any credit-burn 紧迫性 in plain text
- If filter returned <3 candidates, note relaxation taken (e.g., "loosened distance to 🚗🚗")

## Step 5: Close

End with one line:
> "选哪个? (回 1/2/3) 我帮你 OpenTable / Resy 查时段, 或者 /dine + 新约束 重排"

Do NOT auto-book; just surface candidates.

## Rules

- **Read-only on catalog docs**: do NOT modify the regional dining catalog or the credit-perks catalog from `/dine`
- **Reading from the dining log is fine**; new captures only via `/reflect` Dining Pulse or explicit user "记录今天 X"
- **0 candidates after hard filter**: relax most-restrictive constraint by 1 step, retry; surface 1-2 closest matches with flag "relaxed: <constraint>"
- **Always show credit-burn opportunity** if relevant (Exclusive Tables H1/H2 ≤ 60d deadline + unused). Even if credit餐厅 doesn't match exact mood, surface as 4th line with note: "💡 Credit-burn alt: <restaurant> ($150 H1, deadline 6/30)"
- **Match user language**: Chinese-dominant if cuisine is Chinese; English if Western
- **Keep output under 30 lines** (table + 2-3 line reasoning + 1 close line)
- **No web search**: cuisine + restaurant data comes from local catalog files only
