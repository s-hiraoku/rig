---
title: Core Concepts
description: The vocabulary Rig uses — roles (human / parent agent / child agent), runs, runners, prompt styles, worktree runs, artifacts, environment checks.
---

# Core Concepts

Rig has a small vocabulary. Start here so the rest of the guide reads cleanly.

## Roles

Rig is a three-tier system. Knowing who plays which role removes most of the
confusion later.

| Role | What they do |
| --- | --- |
| **Human** | Asks the parent agent in natural language. Reviews `result.md` and `diff.patch` through that agent. Approves patch application. |
| **Parent agent** (Cursor, Claude Code, Codex CLI, anything reading AGENTS.md) | Decides whether to use native subagents or Rig. Calls `rig run` (CLI) or `rig_run` (MCP) when Rig-backed artifacts are useful. Reads back artifacts and reports to the human. |
| **Child agent** (the CLI Rig launches — `codex exec` by default) | Executes the actual task. Writes its answer to stdout. |

The CLI is for **setup, debugging, and audit**. Day-to-day work usually goes
human → parent agent → native subagents when available, or Rig → child agent
→ artifacts → parent agent → human when Rig-backed records are needed.

## Run

A **run** is the unit Rig records every time the parent agent delegates work.
Each run captures the task, command metadata, stdout, stderr, final result,
and status.

Runs live under:

```txt
.rig/runs/<run-id>/
```

Typical files:

- `task.md` — the task the parent agent passed in (often a slightly cleaned-up
  version of what the human asked for).
- `command.json` — the child-agent command Rig executed or previewed.
- `stdout.log` / `stderr.log` — raw child-agent output.
- `result.md` — the trimmed final answer the parent agent reads back.
- `status.json` — id, status, timestamps, exit code, paths.
- `diff.patch` — captured patch for worktree runs only.

Run IDs follow `YYYYMMDD-HHMMSS-<agent>` so listings sort chronologically.

Parallel runs are multiple normal runs created from the same request. Each
attempt still has its own run ID, directory, status, logs, and result; Rig only
starts them concurrently and groups their CLI or MCP response.

Native parent-agent subagents are different: they are managed by the parent
agent itself, can receive role-specific instructions, and may already have
isolated workspaces. Rig instructions tell capable parent agents to prefer
native subagents for parallel or isolated work, then use Rig as a portable
fallback or audit layer.

## Child Agent

A named command in `.rig/config.yaml`. Rig ships with a working default for
Codex (`codex exec`), but any CLI with a stable non-interactive prompt mode
can be wired in. See [Agents](agents.md) for working configurations.

The parent agent never picks the binary; the parent picks an *agent name*, and
Rig looks up the binary in config.

## Runner

A runner controls how Rig actually starts the child agent.

- `exec` — non-interactive command execution. Rig appends the rendered prompt
  as the final argument. Right answer for nearly every modern coding CLI.
- `manual` — no command is launched. Rig creates a `waiting` run that the
  human or external workflow completes explicitly. Used for GUI / chat /
  out-of-band work.
- `pty` — experimental TTY-backed execution for CLIs that demand a real
  terminal.

## Prompt Style

`prompt_style` decides what string Rig appends to the child-agent command.
Three values: `rig`, `task`, `template`. Default is `rig`, which sends a
generic instruction asking the child agent to read `task.md`. Full reference
in [Prompt Styles](prompts.md).

## Worktree Run

A worktree run executes the child agent inside an isolated Git worktree under
`.rig/worktrees/<run-id>/` and captures the resulting diff as
`.rig/runs/<run-id>/diff.patch`. The main working tree stays untouched until
the human approves and the parent agent calls `rig worktree apply`.

This is the answer when the parent agent is about to do something risky or
large. See [Worktree Runs](worktrees.md) and
[Recipes → Refactor in an Isolated Worktree](recipes.md#refactor-in-an-isolated-worktree).

## Artifact

An artifact is a file written under `.rig/runs/<run-id>/`. Artifacts make runs
inspectable after the command exits and give the parent agent stable files to
read instead of CLI text. See [Run Artifacts](artifacts.md) for the
file-by-file reference.

## Status

Every run has a status. Lifecycle:

```txt
created → succeeded
created → failed
waiting → succeeded   (manual complete)
waiting → failed      (manual fail)
```

`created` is also the terminal status for `--dry-run` runs that never launched
a command.

## Environment Checks

`.rig/env.yaml` declares project-specific harness expectations: required
instruction files, optional agent asset managers. `rig env doctor` and
`rig env plan` report missing pieces without silently installing anything.
`rig env bootstrap` creates only the Rig-owned files.

See [Configuration → Environment Configuration](configuration.md#environment-configuration)
and [Workflows → Environment Setup](workflows.md#environment-setup).

## MCP Server

Rig is CLI-first, but it also exposes its run store and orchestrator as an
optional MCP server over stdio. MCP-native or shell-restricted parent agents
can call structured tools — `rig_run`, `rig_list_runs`, `rig_get_diff`, etc. —
against the same core operations. See [MCP Server](mcp.md).
