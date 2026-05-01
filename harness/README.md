# Harness

Provider-neutral registry files for the Reflectl runtime layer.

| File | Purpose |
|---|---|
| `commands.toml` | Portable workflow names mapped to `.claude/commands/*.md` sources and Codex prompts. |
| `agents.toml` | Portable role names mapped to `.claude/agents/*.md` sources and model profiles. |
| `models.toml` | Role-level model profiles for Claude Code and Codex. |
| `capabilities.toml` | Runtime-neutral capability names and the Codex-side tool that implements each. The Claude Code mapping lives in `.claude/agents/*.md` `tools:` frontmatter (single source of truth). |

Use the helper CLI instead of scraping TOML directly:

```bash
python3 scripts/reflectl.py status
python3 scripts/reflectl.py commands
python3 scripts/reflectl.py agents
python3 scripts/reflectl.py prompt reflect
python3 scripts/reflectl.py agent-prompt researcher
```

Before finishing harness changes:

```bash
python3 scripts/harness_lint.py
python3 scripts/harness_smoke.py
```

The lint checks that Claude command/agent files, portable registries, model
profiles, capabilities, `AGENTS.md`, `CLAUDE.md`, and the repo-scoped Codex
skill stay aligned.

The smoke test exercises the helper CLI and JSON surfaces without reading the
private vault.
