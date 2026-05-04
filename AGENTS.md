## Rig

This repository builds Rig, a local AI coding harness. Keep Rig focused on
running child agents, recording inspectable artifacts, isolating risky edits,
and exposing the same run model through CLI and MCP.

Use `.rig/instructions/rig.md` when present for the generic Rig usage policy.
For this repository specifically:

- Prefer `uv run ...` for local commands from the checkout.
- Run `uv run pytest -q`, `uv run ruff check .`, and `uv run mypy rig tests`
  before handing off substantial changes.
- Use deterministic fake commands in tests. Do not require real Codex, Claude,
  Gemini, Copilot, credentials, or networked agent calls for normal tests.
- Keep vendor-specific agent behavior in `.rig/config.yaml` examples and docs;
  do not add first-class vendor branches unless a stable CLI contract requires it.
- Preserve the run artifact contract: `task.md`, `command.json`, `stdout.log`,
  `stderr.log`, `result.md`, and `status.json`. Worktree runs also produce
  `diff.patch`.
- Use `rig suggest` before uncertain or risky delegated work. Use isolated
  worktree runs for non-trivial edits when native parent-agent isolation is not
  available.
- Inspect results with `rig show latest` or the matching MCP tools before
  summarizing them.
- Keep MCP safety defaults intact: `RIG_MCP_ROOT` bounds accepted paths, and
  `RIG_MCP_ALLOW_APPLY=1` is required before MCP patch application is enabled.
- Do not make Rig a package manager for skills, hooks, prompts, MCP configs, or
  third-party agent assets. Detect and document those tools; leave installation
  and deployment to external managers or project conventions.
