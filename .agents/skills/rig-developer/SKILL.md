---
name: rig-developer
description: Use when implementing or reviewing Rig itself, including changes to the CLI, runners, run artifacts, worktree isolation, MCP adapter, environment diagnostics, or agent harness documentation.
---

# Rig Developer

Use this skill for changes inside the Rig repository.

## Boundaries

- Rig is a local AI coding harness, not an agent-to-agent protocol, workflow
  engine, PTY automation framework, or package manager for agent assets.
- Keep the core model stable: `Task -> Run -> AgentAdapter -> Artifacts`.
- Prefer declarative `.rig/config.yaml` agent definitions over vendor-specific
  Python branches.
- Keep skills, hooks, prompts, and MCP client config as external assets that Rig
  can detect or document but should not silently install.

## Implementation Rules

- Preserve run artifacts: `task.md`, `command.json`, `stdout.log`,
  `stderr.log`, `result.md`, and `status.json`; worktree runs also write
  `diff.patch`.
- Keep CLI and MCP behavior aligned. MCP tools should call the same run store,
  orchestrator, worktree, and artifact paths as the CLI.
- Keep safety defaults explicit. `RIG_MCP_ROOT` constrains accepted `cwd`
  values, and `RIG_MCP_ALLOW_APPLY=1` gates MCP patch application.
- Use fake commands for tests. Real agent CLIs, credentials, or network access
  belong only in explicit opt-in smoke checks.
- For new runners or prompt modes, add focused config parsing tests, CLI tests,
  artifact assertions, and docs examples.

## Verification

Run from the repository checkout:

```bash
uv run pytest -q
uv run ruff check .
uv run mypy rig tests
```

Use `uv run rig ...` when manually exercising the CLI from this checkout.
