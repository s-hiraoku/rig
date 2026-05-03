---
title: Core Concepts
description: The vocabulary Rig uses — runs, agents, runners, worktree runs, artifacts, and environment checks.
---

# Core Concepts

Rig has a small vocabulary. This page defines each term and links to the page
that goes deeper.

## Run

A run is Rig's main unit of work. Each run records the task, command metadata,
stdout, stderr, final result, and status metadata.

Runs are stored under:

```txt
.rig/runs/<run-id>/
```

Typical files include:

- `task.md` — the user task saved for the agent.
- `command.json` — the command Rig executed or previewed.
- `stdout.log` — captured standard output.
- `stderr.log` — captured standard error.
- `result.md` — the final result shown by `rig show`.
- `status.json` — run status and metadata.
- `diff.patch` — captured patch for worktree runs.

Run IDs follow `YYYYMMDD-HHMMSS-<agent>` so listings sort chronologically.

## Agent

An agent is a configured command in `.rig/config.yaml`. Rig ships with a
useful default for Codex, but other CLIs can be configured when they expose a
stable non-interactive prompt mode. See [Agents](agents.md) for working
configurations.

## Runner

A runner controls how Rig starts work.

- `exec` — non-interactive command execution. Rig appends the rendered prompt
  as the final argument.
- `manual` — creates a `waiting` run for human-driven or external agent work.
  No command is launched; you complete the run with `rig manual complete` or
  `rig manual fail`.
- `pty` — experimental TTY-backed execution for CLIs that require a terminal.

## Prompt Style

`prompt_style` decides what string Rig appends to the agent command. Three
styles are supported: `rig`, `task`, and `template`. The default is `rig`,
which sends a generic instruction asking the agent to read `task.md`. See
[Prompt Styles](prompts.md) for the full reference.

## Worktree Run

A worktree run executes an agent in an isolated Git worktree under
`.rig/worktrees/<run-id>/` and captures the resulting patch. This keeps the
main working tree unchanged until the patch is reviewed and applied. See
[Worktree Runs](worktrees.md) and the
[Recipes → Refactor in an Isolated Worktree](recipes.md#refactor-in-an-isolated-worktree)
flow.

## Artifact

An artifact is a file written under `.rig/runs/<run-id>/`. Artifacts make
runs inspectable after the command exits and give integrations stable files
to read. See [Run Artifacts](artifacts.md) for the file-by-file reference.

## Status

Every run has a status. The lifecycle is:

```txt
created → succeeded
created → failed
waiting → succeeded   (manual complete)
waiting → failed      (manual fail)
```

`created` is also the terminal status for `--dry-run` runs that never
launched a command.

## Environment Checks

`.rig/env.yaml` describes project-specific harness expectations such as
required instruction files or optional agent asset managers. `rig env doctor`
and `rig env plan` report missing pieces without silently installing
third-party tools. `rig env bootstrap` creates only the Rig-owned files.

See [Configuration → Environment Configuration](configuration.md#environment-configuration)
and [Workflows → Environment Setup](workflows.md#environment-setup).

## MCP Server

Rig exposes its run store and orchestrator as an MCP server over stdio.
MCP-capable agents can list runs, start runs, read results, and read captured
patches without parsing CLI text. See [MCP Server](mcp.md).
