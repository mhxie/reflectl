# reflectl

A personal reflection system that reads your notes and helps you think.

Built on [Claude Code](https://docs.anthropic.com/en/docs/claude-code) with a **local-first** Zettelkasten under `zk/` as the data layer. [Reflect.app](https://reflect.app/) is one of several capture surfaces (alongside Readwise, voice, mobile); the authoritative knowledge layer lives on disk and is scored by a deterministic TrustRank engine. A team of AI agents reads from `zk/`, helps you reflect, read deeply, make decisions, and take action.

## What It Does

**Reflect** — Daily check-ins grounded in what you actually wrote. Surfaces forgotten connections, challenges assumptions, tracks your goals across life chapters.

**Read** — Deep-reads articles, saved notes, and transcripts through multiple lenses (critical, structural, practical, dialectical). Multiple readers analyze in parallel, then you discuss what they found.

**Plan** — Goal reviews, decision journals, and energy audits. Tracks what's progressing, what's neglected, and what's emerging. Uses 23 thinking frameworks with cross-validation.

**Act** — Compact redundant notes, deep-dive into a topic with 4 agents working in parallel, or triage your notes for cleanup.

**Learn** — Get reading recommendations or introspect to rebuild your self-model.

**Wiki** — Crystallize validated thinking into `zk/wiki/` entries with structured claims, external anchors, and bi-temporal markers. A TrustRank pass (`scripts/trust.py`) scores each claim via Personalized PageRank with external anchors as trust seeds. `/lint` enforces corpus-level structure; `/sync` pushes wiki entries to Reflect for mobile reading.

Session insights write back to your Reflect daily notes (with your approval). Compiled knowledge lives locally in `zk/wiki/` and syncs out one-way.

## Getting Started

### Prerequisites

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI
- [Reflect.app](https://reflect.app/) with the [MCP server](https://reflect.app/mcp) running locally

**Optional — external reviewers:**
- [Codex CLI](https://github.com/openai/codex) — `npm i -g @openai/codex` — OpenAI's coding agent, used for independent code review and adversarial audits
- [Gemini CLI](https://github.com/google-gemini/gemini-cli) — `npm i -g @google/gemini-cli` — Google's coding agent, used as a second external perspective

The system works without these, but external reviewers from different AI models catch blind spots that internal agents miss.

### Install

```bash
git clone https://github.com/mhxie/reflectl.git
cd reflectl
```

Create `.mcp.json` in the project root:

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

### First Run

```bash
claude                # open Claude Code in the project
/introspect           # build your self-model from your notes
/reflect              # start your first session
```

## Sessions

Type `/reflect` to get a menu of everything you can do:

| Mode | What happens |
|------|-------------|
| **Daily Reflection** | Reflects on today's notes, asks questions at increasing depth, surfaces a forgotten connection |
| **Weekly Review** | Energy + attention audit across the week |
| **Explore** | Finds hidden connections and open threads across your notes |
| **Goal Review** | Checks progress on goals — progressing, neglected, or shifted |
| **Decision Journal** | Structured decision-making with framework cross-validation |
| **Energy Audit** | Four-dimension assessment (physical, mental, emotional, social) |
| **Read & Discuss** | Multi-lens reading of an article or note, then interactive discussion |
| **Deep Dive** | Full briefing on a topic — your notes + web research + resources + framework |
| **Compact Notes** | Find and merge redundant notes |
| **Process Meeting** | Turn a work meeting transcript into structured notes with action items |

You can also go direct: `/review`, `/weekly`, `/decision`, `/explore`, `/energy-audit`, `/curate`, `/introspect`, `/sync`, `/lint`.

**Knowledge layer commands:**

| Command | What it does |
|---|---|
| `/sync` | Push `zk/wiki/` entries to Reflect for mobile display. One-way, manifest-tracked, never pulls back. |
| `/lint` | Corpus-level structural check over `zk/wiki/` and the sync manifest — parse errors, duplicate titles, slug drift, manifest dead rows. Run before `/sync` or whenever trust scores shift unexpectedly. |

## The Team

Eleven agents work together during sessions. You don't need to manage them — the orchestrator dispatches automatically. But you can talk to any of them directly:

- *"find notes about X"* — sends Researcher to search your notes
- *"read [[Article]] with critical lens"* — sends Reader to analyze
- *"challenge my assumption about X"* — sends Challenger to probe
- *"compact my notes on Y"* — sends Curator to merge
- *"recommend reading on Z"* — sends Librarian to curate
- *"what's happening in the world on X"* — sends Scout to search the web

## How It Works

```
Capture sources                 Local data layer (zk/)              Display
(Reflect, Readwise,  ─sync──>   L4  zk/wiki/         ──/sync──>  Reflect
 voice, mobile)                 (trust-scored)                   (mobile read)
                                L3  zk/papers/
                                L2  zk/daily-notes/, reflections/,
                                    preprints/, agent-findings/, ...
                                L1  zk/cache/, zk/readwise/

                                        ^
                                        |
                                        v
                                Claude Code (Orchestrator)
                                        |
                    +-----------+-------+-------+-----------+
                    v           v               v           v
              Agent Team    Sessions      Frameworks   Trust engine
              (11 agents)  (10 types)   (22 frameworks) (trust.py,
                    |           |               |         lint.py)
                    v           v               v
              Protocols    zk/reflections/    Cross-validation
              (20 rules)   (session outputs)  & Pattern Library
```

**Five-tier knowledge model.** Everything under `zk/` is classified by depth of crystallization — raw capture (L1), working notes (L2), externally-certified papers (L3), locally-certified wiki entries (L4). Directory = tier; no tags required. Agents read from disk via semantic search and grep, not via MCP. Reflect is demoted to a capture + display surface.

**TrustRank over the wiki.** Wiki entries under `zk/wiki/` follow a structured schema: `## Claims` with `[C1]`, `[C2]`... headings, each backed by fenced `anchors` blocks containing `@anchor` (external evidence), `@cite` (internal edge to another wiki entry), and `@pass` (reviewer verification) markers with bi-temporal `valid_at`/`invalid_at` fields. `scripts/trust.py` runs Personalized PageRank with external anchors as seeds — trust mass enters the graph only at external sources and propagates through internal cites. No external anchor, no trust. `scripts/lint.py` enforces structural integrity across the corpus.

**Session reflection.** The orchestrator dispatches agents, gathers findings, runs a quality gate, and writes approved insights back to your Reflect daily notes. Session outputs are stored in `zk/reflections/`. All personal data under `zk/` is gitignored — only the system configuration (protocols, agents, commands, scripts) is committed.

Key design choices:
- **Local-first** — the knowledge layer lives on disk, not in a remote app. MCP is used only as a narrow escape hatch for today's unsynced capture and for pushing finished wiki entries to Reflect.
- **Reflect as append-only archival** — Reflect's MCP has `create_note` and `append_to_daily_note` but no update or delete. That's a drawback for editing, but a feature for recovery: any wiki entry pushed via `/sync` and any insight written back to a daily note leaves a tamper-evident trail in Reflect's cloud. If an AI-driven operation corrupts or deletes something locally under `zk/`, the Reflect copy of whatever was synced at the time is still there to review. Local is authoritative; Reflect is the forensic mirror for the slice of state that crossed the sync boundary. The rarely-triggered `/restore` command operationalizes this property: it stages the Reflect copy into `zk/cache/restore-<slug>.md` as degraded-prose reference for hand-reconstruction (the `/sync` pipeline is lossy by design, so the recovered body is not a drop-in replacement).
- **Deterministic trust scoring** — TrustRank is a stdlib-only Python pass, not an LLM heuristic. The same input always produces the same score.
- **Era-aware** — tracks life chapters with themes and directions (Mastery, Impact, Freedom, Connection, Creation)
- **Bilingual** — handles English and Chinese notes, matches your language
- **Self-improving** — the Evolver agent evolves the system, reviewed by external AI models (Codex, Gemini) via `scripts/review.sh`
- **Privacy by default** — personal data never leaves your machine

## License

MIT
