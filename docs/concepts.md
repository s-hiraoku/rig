---
title: Core Concepts
---

# Core Concepts

## Run

A run is Rig's main unit of work. Each run records the task, command metadata,
stdout, stderr, final result, and status metadata.

Runs are stored under:

```txt
.rig/runs/<run-id>/
```

Typical files include:

- `task.md`: the user task saved for the agent.
- `command.json`: the command Rig executed or previewed.
- `stdout.log`: captured standard output.
- `stderr.log`: captured standard error.
- `result.md`: the final result shown by `rig show`.
- `status.json`: run status and metadata.
- `diff.patch`: captured patch for worktree runs.

## Agent

An agent is a configured command in `.rig/config.yaml`. Rig ships with a useful
default for Codex, but other CLIs can be configured when they expose a stable
non-interactive prompt mode.

## Runner

A runner controls how Rig starts work.

- `exec`: non-interactive command execution.
- `manual`: creates a waiting run for human-driven or external agent work.
- `pty`: experimental TTY-backed execution for CLIs that require a terminal.

## Worktree Run

A worktree run executes an agent in an isolated Git worktree and captures the
resulting patch. This keeps the main working tree unchanged until the patch is
reviewed and applied.

## Environment Checks

`.rig/env.yaml` describes project-specific harness expectations such as required
instruction files or optional agent asset managers. `rig env doctor` and
`rig env plan` report missing pieces without silently installing third-party
tools.
