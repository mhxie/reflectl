# Runtime Adapters Protocol

Reflectl should run under Claude Code and Codex without forking the reflection
system. The core idea is to separate four concerns:

| Concern | Owned by | Example |
|---|---|---|
| Workflow | `protocols/`, command specs | `/reflect`, `/weekly`, `/review` |
| Role | `harness/agents.toml`, agent specs | Researcher, Synthesizer, Reviewer |
| Capability | `harness/capabilities.toml` | `semantic_query`, `write_local_file`, `web_search` |
| Runtime and model | adapters, local CLI config | Claude Code with Opus, Codex with GPT |

This follows the OpenClaw lesson: the system can use different models when the
provider and runtime are explicit metadata, not assumptions buried inside the
workflow.

## Runtime Surfaces

| Runtime | Reads | Native surface | Status |
|---|---|---|---|
| Claude Code | `CLAUDE.md` | `.claude/agents/`, `.claude/commands/` | Primary interactive harness |
| Codex | `AGENTS.md` | `.agents/skills/reflectl/`, Codex CLI, Codex review | Portable harness |

Claude Code remains the most complete native surface because the command files
currently use Claude constructs such as `AskUserQuestion` and `Agent(...)`.
Codex uses `AGENTS.md` plus this protocol to translate those constructs.

`harness/commands.toml` and `harness/agents.toml` are the registries shared by
both runtimes. They map portable names to the current Claude source files and
give Codex prompts that can be generated with `python3 scripts/reflectl.py
prompt <name>` and `python3 scripts/reflectl.py agent-prompt <name>`. The
repo-scoped `reflectl` skill points Codex to these registries without loading
every command or agent spec up front.

Codex does not yet ship a project-level custom slash-command surface, so the
parity invocation is `python3 scripts/reflectl.py run <command>`, which spawns
`codex` (or `codex exec` with `--exec`) with the generated workflow prompt
pre-loaded and the project root as the working directory. This is the
recommended Codex entry point until Codex documents a stable custom-prompt
format.

## Provider-Neutral Rules

- Do not add new provider-specific model names to shared protocols. Use a model
  profile from `harness/models.toml`.
- Do not add new provider-specific tool names to shared protocols. Use a
  capability from `harness/capabilities.toml`.
- Existing `.claude/` files may keep Claude frontmatter and tool names. They are
  adapter surfaces.
- New shared docs should say "run a semantic query" or "write a local file",
  not name provider-specific tools, unless they are documenting an adapter
  itself.
- If a runtime lacks a feature, degrade explicitly. Example: if Codex cannot
  spawn subagents in a given environment, read the target agent spec and run the
  step sequentially.

## Model Profiles

Agent roles ask for capability classes, not fixed provider models. Current
profile names:

| Profile | Used for |
|---|---|
| `deep_reflection` | broad vault reading and pattern discovery |
| `synthesis` | combining briefs into user-facing insight |
| `reflective_challenge` | probing questions and assumption tests |
| `framework_reasoning` | independent framework application |
| `system_evolution` | multi-file harness changes |
| `mechanical_review` | checklists, rubric scoring, diff review |
| `note_operations` | structured local note drafts |
| `web_research` | external context gathering |
| `deep_reading` | article and transcript analysis |
| `meeting_extraction` | action item and decision extraction |
| `recommendations` | reading and resource curation |

The concrete mapping is in `harness/models.toml`. Updating a provider or model
should usually touch that file only.

## Capability Profiles

Capabilities describe what an agent needs, independent of the runtime:

- `read_file`
- `search_text`
- `run_shell`
- `semantic_query`
- `web_search`
- `web_fetch`
- `write_local_file`
- `spawn_role`
- `ask_user`

The concrete tool mapping is in `harness/capabilities.toml`.

## Codex Command Execution

When a user asks Codex to run a Reflectl command:

1. Read `AGENTS.md`.
2. Read `CLAUDE.md` for domain rules and safety constraints.
3. Read `.claude/commands/<command>.md` for the workflow.
4. Translate Claude-specific constructs using the table in `AGENTS.md`.
5. Read any referenced agent specs from `.claude/agents/`.
6. Prefer local `$ZK/` files, `rg`, and `uv run scripts/semantic.py`.
7. Ask before any local file write under `$ZK/`.
8. Report any downgraded capability, such as missing web access or unavailable
   subagent dispatch.

If the command name is unknown, run `python3 scripts/reflectl.py commands` to
discover the registered command set. To produce a copyable invocation prompt,
run `python3 scripts/reflectl.py prompt <command>`.

If the role name is unknown, run `python3 scripts/reflectl.py agents` to
discover the registered agent set. To produce a focused role-emulation prompt,
run `python3 scripts/reflectl.py agent-prompt <agent>`.

## Migration Path

`.claude/` is the native command and agent surface today; Codex-readable root
instructions and neutral registries provide portability. Later phases can move
command and agent source into `harness/` and generate `.claude/` and `.codex/`
surfaces from it.

Useful next phases:

1. Generate `CLAUDE.md` from `AGENTS.md` or make it a symlink where supported.
2. Move agent roles into neutral specs and render Claude frontmatter from them.
3. Move command specs into neutral source and render Claude command files from them.
4. Extend `scripts/harness_lint.py` to reject provider-specific syntax in shared
   docs once the migration is complete.
