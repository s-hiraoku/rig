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
  Antigravity, Copilot, credentials, or networked agent calls for normal tests.
- Keep vendor-specific agent behavior in `.rig/config.yaml` examples and docs;
  do not add first-class vendor branches unless a stable CLI contract requires it.
- Preserve the run artifact contract: `task.md`, `command.json`, `stdout.log`,
  `stderr.log`, `result.md`, and `status.json`. Worktree runs also produce
  `diff.patch`. Run discovery and listing are keyed off `status.json`; the
  other artifacts are still expected to be produced and preserved for
  inspection and consumers.
- Use `rig delegate` for inspectable read-only or low-risk delegated work.
  Use `rig patch create` for uncertain or risky delegated edits when native
  parent-agent isolation is not available, and review `rig patch show latest`
  before applying.
- Inspect results with `rig history show latest` or the matching MCP tools before
  summarizing them.
- Use `rig harness` when you need the companion `codex-harnesses` source for
  project AGENTS templates, skills, hooks, policies, ledgers, or verification
  scripts.
- Keep MCP safety defaults intact: `RIG_MCP_ROOT` bounds accepted paths, and
  `RIG_MCP_ALLOW_APPLY=1` is required before MCP patch application is enabled.
- Do not make Rig a package manager for skills, hooks, prompts, MCP configs, or
  third-party agent assets. Detect and document those tools; leave installation
  and deployment to external managers or project conventions.
