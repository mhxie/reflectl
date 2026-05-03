# Atelier

Your AI-native personal operating system — the workshop, tools, and circle of operators that surrounds your **œuvre** (the accumulating body of your notes, decisions, and reflections, kept locally under `$OV/`). The system reads and writes plain Markdown; nothing leaves your machine. A 12-specialist agent team (le cercle) and a deterministic trust engine score and structure what you keep. Self-improving on a weekly cadence.

Capture what you learn. Reflect on what you think. Research what you don't know. Read deeply. Make decisions. Track goals across life chapters. Crystallize knowledge you trust. All orchestrated over a local-first Zettelkasten — your data on your machine, scored by `scripts/trust.py`, refined every session.

Runs first-class on [Claude Code](https://docs.anthropic.com/en/docs/claude-code); ships with a Codex compatibility layer through `AGENTS.md` plus runtime adapter contracts.

## What It Does

**Reflect** — Daily check-ins grounded in what you actually wrote. Surfaces forgotten connections, challenges assumptions, tracks goals across life chapters.

**Read** — Deep-reads articles, saved notes, and transcripts through multiple lenses (critical, structural, practical, dialectical). Multiple readers analyze in parallel; you discuss what they found.

**Plan** — Goal reviews, decision journals, and energy audits. Tracks what's progressing, what's neglected, what's emerging. Uses 22+ thinking frameworks with cross-validation.

**Act** — Compact redundant notes, deep-dive into a topic with 4 agents in parallel, triage notes for cleanup, or curate your Readwise inbox.

**Learn** — Get reading recommendations, or introspect to rebuild your self-model.

**Wiki** — Crystallize validated thinking into `$OV/wiki/` entries with structured claims, external anchors, and bi-temporal markers. `scripts/trust.py` runs Personalized PageRank with external anchors as trust seeds. `/lint` enforces corpus-level structure and harness health.

Session reflections write to `$OV/reflections/`. Daily notes are user-authored — the system reads them but never writes.

## Getting Started

### Prerequisites

- One AI runtime CLI:
  - [Claude Code](https://docs.anthropic.com/en/docs/claude-code) for native slash commands and agent teams
  - [Codex CLI](https://github.com/openai/codex) for the portable `AGENTS.md` harness and external review
- [uv](https://docs.astral.sh/uv/) — Python package manager

**Optional — second-opinion external reviewer:**
- [Gemini CLI](https://github.com/google-gemini/gemini-cli) — `npm i -g @google/gemini-cli`

Core scripts (`trust.py`, `lint.py`, `staleness.py`, `session_log.py`, `privacy_check.py`, `zk_audit.py`) are stdlib-only. Semantic search and document conversion deps are managed via `pyproject.toml`.

### Install

```bash
git clone https://github.com/mhxie/reflectl.git ~/atelier  # repo URL pending rename
cd ~/atelier
uv sync                # install dependencies from pyproject.toml
```

Set `$OV` to point to your vault (the directory containing `daily-notes/`, `wiki/`, `reflections/`, etc.):

```bash
echo 'export OV="$HOME/path/to/your/vault"' >> ~/.zshrc
source ~/.zshrc
```

The system is fully local-first — no remote services, APIs, or accounts required. All personal content lives under `$OV/` and is gitignored. Only system configuration (protocols, agents, commands, scripts) is committed.

### First Run

Claude Code:

```bash
claude                # open Claude Code in the project
/introspect           # build your self-model from your notes (reads $OV/daily-notes/)
/reflect              # start your first session
```

Codex:

```bash
python3 scripts/atelier.py run reflect            # fresh Codex TUI on /reflect (default)
python3 scripts/atelier.py run lint --exec        # one-shot, no TUI
python3 scripts/atelier.py run reflect "context here"
python3 scripts/atelier.py run promote --resume   # continue most recent session (resume_friendly only)
python3 scripts/atelier.py run promote --fork     # branch from most recent without mutating it
```

The `run` subcommand spawns `codex` with the generated prompt pre-loaded and the repo as the working directory. Codex reads `AGENTS.md`, picks up the repo-scoped skill under `.agents/skills/`, then adapts `.claude/commands/*.md` through `protocols/runtime-adapters.md`.

Reflection-type commands (`/reflect`, `/weekly`, `/review`, `/decision`, etc.) default to fresh sessions because reusing a prior session pollutes the new reflection. Continuation-friendly commands (`/promote`) are marked `resume_friendly = true` in `harness/commands.toml`; pass `--resume` to chain off a recent session, or `--fork` to branch without mutating it.

## Sessions

Type `/reflect` to get a menu of everything you can do:

| Mode | What happens |
|------|-------------|
| Daily Reflection | Reflects on today's notes, asks questions at increasing depth, surfaces a forgotten connection |
| Weekly Review | Energy + attention audit across the week |
| Explore | Finds hidden connections and open threads across your notes |
| Goal Review | Checks progress on goals — progressing, neglected, or shifted |
| Decision Journal | Structured decision-making with framework cross-validation |
| Energy Audit | Four-dimension assessment (physical, mental, emotional, social) |
| Read & Discuss | Multi-lens reading of an article or note, then interactive discussion |
| Deep Dive | Full briefing on a topic — your notes + web research + resources + framework |
| Compact Notes | Find and merge redundant notes |
| Curate Inbox | Goal-aware triage of your Readwise inbox — score, route, and tag |
| Note Triage | Scan for compaction candidates across your notes |
| Process Meeting | Turn a work meeting transcript into structured notes with action items |

You can also go direct: `/review`, `/weekly`, `/decision`, `/explore`, `/energy-audit`, `/curate`, `/introspect`, `/lint`, `/promote`, `/paper-review`, `/dine`, `/prm`, `/civ`, `/system-review`.

**Knowledge layer commands:**

| Command | What it does |
|---|---|
| `/promote` | Create an L4 wiki entry from L2 source notes: Researcher finds claims + anchors, Curator drafts schema-compliant entry, orchestrator writes after approval. |
| `/lint` | Corpus-level structural check over `$OV/wiki/` (parse errors, duplicate titles, slug drift, orphan entries, graph topology). Also harness health: CLAUDE.md size and formatting, privacy gate, ingestion hygiene. |

## The Team

Twelve specialist agents (le cercle) work together during sessions. The orchestrator dispatches automatically; you can also talk to any of them directly:

- *"find notes about X"* — sends Researcher (the Observer)
- *"read [[Article]] with critical lens"* — sends Reader
- *"challenge my assumption about X"* — sends Challenger (the Critic)
- *"compact my notes on Y"* — sends Curator (the Collector)
- *"recommend reading on Z"* — sends Librarian (the Cataloguer)
- *"what's happening in the world on X"* — sends Scout (the Flâneur)

Full cercle archetype map (Observer / Colorist / Arbiter / Critic / Structuralist / Collector / Flâneur / Reader / Cataloguer / Scribe / Master / Steward) lives in `protocols/atelier.md`.

## How It Works

```
Capture sources                  Local data layer ($OV/)
(Readwise inbox,                 L4  $OV/wiki/        ─ locally certified
 voice notes,                        (trust-scored canon)
 markdown editor)                L3  $OV/papers/      ─ peer-reviewed
                                 L2  $OV/daily-notes/ + reflections/ +
                                     research/ + preprints/ +
                                     agent-findings/ + drafts/ + …
                                 L1  $OV/cache/, $OV/readwise/

                                         ^
                                         |
                                         v
                            AI runtime (Claude Code or Codex)
                                         |
                     +-----------+-------+-------+-----------+
                     v           v               v           v
                Le Cercle    Sessions     Frameworks    Trust engine
                (12 agents)  (12 types)   (22 + xval)   (trust.py,
                     |           |               |        lint.py)
                     v           v               v
                Protocols    $OV/reflections/   Cross-validation
                (~25 rules)  (session outputs)  & Pattern Library
```

**Five-tier knowledge model.** Everything under `$OV/` is classified by depth of crystallization — raw capture (L1), working notes (L2), externally-certified papers (L3), locally-certified wiki entries (L4). Directory = tier; no tags required. Agents read from disk via semantic search and grep.

**TrustRank over the wiki.** Wiki entries under `$OV/wiki/` follow a structured schema: `## Claims` with `[C1]`, `[C2]`... headings, each backed by fenced `anchors` blocks containing `@anchor` (external evidence), `@cite` (internal edge to another wiki entry), and `@pass` (reviewer verification) markers with bi-temporal `valid_at`/`invalid_at` fields. `scripts/trust.py` runs Personalized PageRank with external anchors as seeds; trust mass enters the graph only at external sources and propagates through internal cites. No external anchor, no trust. `scripts/lint.py` enforces structural integrity across the corpus.

**Session output.** The orchestrator dispatches agents, gathers findings, runs a quality gate, and writes session output to `$OV/reflections/`. Daily notes are user-authored — the system reads them but never writes. All personal data under `$OV/` is gitignored; only system configuration is committed.

**Harness engineering.** `CLAUDE.md` is kept under 8KB because it is inherited by every Claude subagent; each line costs N tokens times N agents per session. `AGENTS.md` and `.agents/skills/atelier/SKILL.md` give Codex the root contract and workflow trigger. `harness/models.toml`, `harness/capabilities.toml`, `harness/commands.toml`, `harness/agents.toml`, and `protocols/runtime-adapters.md` keep provider and runtime assumptions explicit. `scripts/atelier.py` gives Codex command and role discovery plus prompt generation. Critical rules live at the top (primacy effect); detailed specifications load on demand from protocols and agent definitions. The Master of the Atelier (Evolver) has a "subtract before adding" principle and a root-instruction budget gate. `/lint` Phase 0 checks harness health alongside the wiki structural pass.

Key design choices:

- **Local-first**: the knowledge layer lives on disk under `$OV/`, not in a remote app. No external services required.
- **Deterministic trust scoring**: TrustRank is a stdlib-only Python pass, not an LLM heuristic. The same input always produces the same score.
- **Era-aware**: tracks life chapters with themes and directions (Mastery, Impact, Freedom, Connection, Creation).
- **Bilingual**: handles English and Chinese notes; matches your language.
- **Self-improving**: the Master of the Atelier evolves the system, reviewed by external AI models (Codex, Gemini) via `scripts/review.sh`.
- **Privacy by default**: personal data never leaves your machine. `scripts/privacy_check.py` gates committed-file diffs against private filename stems; the Steward (privacy-reviewer agent) catches semantic leaks.

## Vocabulary

The system has a narrative register from the impressionist atelier — *le cercle* (the agents), *the Painter* (you), *the œuvre* (your accumulating body of work), *impression* / *étude* / *tableau* / *série* / *sitting* / *sketch* / *commission*. The register lives in conversation and identity. **Operational keys are unchanged**: slash commands stay `/reflect`, `/promote`, `/lint`, etc.; agent dispatch keys stay `researcher`, `synthesizer`, …; file paths under `$OV/` stay as documented above. Full glossary: `CLAUDE.md` § Vocabulary and `protocols/atelier.md`.

## License

MIT
