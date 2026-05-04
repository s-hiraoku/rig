# Rig

Rig is a local AI coding harness for delegated agent work. A parent AI agent
uses Rig to hand a task to a configured child coding agent, preserve the run as
plain files, and optionally hold edits as a reviewable patch before applying
them.

Rig is built primarily for AI agents to use, but the CLI is also useful for
humans during setup, debugging, audit, and patch review. The normal workflow is:
a human asks a parent AI agent for help; the parent calls `rig delegate` for
read-only or low-risk work, or `rig patch create` when file edits should stay
isolated; Rig writes artifacts under `.rig/runs/`; the parent reads those
artifacts back to the human.

Rig's main unit is a run. A run records the task, command metadata, stdout,
stderr, the final result, and status metadata under `.rig/runs/<run-id>/`.
Patch runs also record `diff.patch`.

## Installation

Install directly from GitHub:

```bash
uv tool install "rig @ git+https://github.com/s-hiraoku/rig.git"
```

For local development:

```bash
git clone https://github.com/s-hiraoku/rig.git
cd rig
uv sync --group dev
uv run rig --help
```

If you are working from a checkout, use `uv run rig ...`. If you installed Rig
with `uv tool install`, use `rig ...`.

## Quick Start

Initialize Rig in the project:

```bash
rig init
```

This creates:

```txt
.rig/
  config.yaml
  instructions/rig.md
  runs/
CLAUDE.md
```

`rig init` updates `CLAUDE.md` with a small Rig block and also prints a snippet
to add to `AGENTS.md` or other parent-agent instructions. Both point the parent
agent at `.rig/instructions/rig.md`, which contains the Rig usage policy.

After setup, talk to your parent AI agent in natural language:

> Review the current diff through Rig and summarize risky changes.

Behind the scenes, the parent agent runs:

```bash
rig delegate codex --task "Review the current diff and summarize risky changes."
```

For edits that should be reviewed before touching the main working tree:

```bash
rig patch create codex --task "Make the requested change."
rig patch show latest
rig patch apply latest
```

Humans can inspect the history directly:

```bash
rig history
rig history show latest
```

## Commands

Core commands:

| Command | Purpose |
| --- | --- |
| `rig delegate [agent] --task "..."` | Run a configured child coding agent and record artifacts. |
| `rig delegate [agent] --task-file task.md` | Same, with task text read from a file. |
| `rig patch create [agent] --task "..."` | Run a child agent in an isolated worktree and capture `diff.patch`. |
| `rig patch show <run-id\|latest>` | Show a captured patch. |
| `rig patch apply <run-id\|latest>` | Apply a reviewed patch with `git apply`. |
| `rig patch prune` | Remove Rig-created worktrees. |
| `rig history` | List recent runs. |
| `rig history show <run-id\|latest>` | Show one run's metadata and result. |
| `rig doctor` | Check the local Rig setup. |
| `rig mcp serve` | Expose Rig as MCP tools for MCP-native parent agents. |

`rig delegate` and `rig patch create` support `--task`, `--task-file`,
`--dry-run`, `--timeout-seconds`, and `--json`.

## Configuration

`.rig/config.yaml` defines the child-agent commands Rig can launch:

```yaml
default_agent: codex

agents:
  codex:
    command: codex
    args:
      - exec
```

Each agent uses non-interactive command execution. Rig appends the rendered
prompt as the final argument. Additional options:

- `prompt_style: rig` passes Rig's standard instruction prompt with a task file path.
- `prompt_style: task` passes the raw task content.
- `prompt_style: template` uses `prompt_template` with `{agent}`, `{task_path}`,
  `{task}`, and `{task_md}`.
- `timeout_seconds` sets the child process timeout.

## Run Artifacts

Each run creates:

```txt
.rig/runs/<run-id>/
  task.md
  command.json
  stdout.log
  stderr.log
  result.md
  status.json
```

Patch runs also write `diff.patch`. If the child agent prints
`--- RIG RESULT ---`, Rig stores only the text after that marker in
`result.md` while preserving full stdout in `stdout.log`.

## Requirements

The default `codex` agent calls `codex exec`, so the Codex CLI must be
installed and available on `PATH`. Worktree-backed patch runs require Git.

## Development

Run checks:

```bash
uv run pytest
uv run ruff check .
uv run mypy rig tests
```
