# Codex

Codex runs against the Atelier system. It reads the root `AGENTS.md` and can
discover the repo-scoped skill in `.agents/skills/reflectl/SKILL.md` (skill
directory name remains `reflectl` until the optional repo-rename phase).
The current Claude Code command files remain the native command specs, and
Codex adapts them through `protocols/runtime-adapters.md`.

Start an interactive Codex session from the repo root:

```bash
codex -C . --sandbox workspace-write
```

Portable command invocation:

```bash
python3 scripts/reflectl.py status
python3 scripts/reflectl.py commands
python3 scripts/reflectl.py prompt reflect
python3 scripts/reflectl.py prompt lint
```

Paste the generated prompt into Codex. The helper reads `harness/commands.toml`
and points Codex at the matching `.claude/commands/*.md` spec.

Portable role discovery:

```bash
python3 scripts/reflectl.py agents
python3 scripts/reflectl.py agent-prompt researcher
```

Code review:

```bash
codex review --uncommitted
```

Before harness changes are finished:

```bash
python3 scripts/harness_lint.py
```
