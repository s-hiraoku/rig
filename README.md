# Rig

Rig is a local AI coding harness for running coding agents with file-backed
tasks, inspectable artifacts, and a simple run history.

Rig's main unit is a run. A run records the task, the command Rig executed,
stdout, stderr, the final result, and status metadata under `.rig/runs/`.

## Installation

Install directly from GitHub:

```bash
uv tool install git+https://github.com/s-hiraoku/rig.git
```

Then check that the command is available:

```bash
rig --help
```

For local development, clone the repository and install the development
environment:

```bash
git clone https://github.com/s-hiraoku/rig.git
cd rig
uv sync --group dev
```

Run the CLI from the project checkout:

```bash
uv run rig --help
```

If you are working from a checkout, use `uv run rig ...`. If you installed Rig
with `uv tool install`, use `rig ...`.

## Requirements

`rig run codex` calls `codex exec`, so the Codex CLI must be installed and
available on `PATH` before running Codex through Rig.

Codex may also require the current directory to be a trusted Git repository.
If a run fails with this error:

```txt
Not inside a trusted directory and --skip-git-repo-check was not specified.
```

initialize the project as a Git repository before trying again:

```bash
git init
```

## Quick Start

From a project where you want to use Rig:

```bash
rig init
rig run codex --task "Review the current diff and identify risky changes."
rig runs list
rig runs show latest
```

From this repository checkout, prefix commands with `uv run`:

```bash
uv run rig init
uv run rig run codex --task "Review the current diff and identify risky changes."
uv run rig runs list
uv run rig runs show latest
```

## Commands

### `rig init`

Initializes Rig in the current repository.

It creates:

```txt
.rig/
  config.yaml
  runs/
```

The command is safe to run more than once. If `.rig/` already exists, it prints
`Rig already initialized.` and leaves existing files in place.

Example:

```bash
uv run rig init
```

The generated `.rig/config.yaml` controls the command Rig uses for each agent.
For Codex, Rig reads `agents.codex.command` and `agents.codex.args`:

```yaml
agents:
  codex:
    command: codex
    args:
      - exec
```

### `rig run codex --task "..."`

Starts a new Codex run using task text passed directly on the command line.

Rig creates a unique run directory, writes the task to `task.md`, executes
the configured Codex command, captures stdout and stderr, writes `result.md`,
and records the final status in `status.json`.

Example:

```bash
uv run rig run codex --task "Review the current diff and identify risky changes."
```

Example output:

```txt
Run: 20260502-203012-codex
Status: succeeded
Result: .rig/runs/20260502-203012-codex/result.md
```

### `rig run codex --task-file task.md`

Starts a new Codex run using task text read from a file.

Use this when the task is too long or structured to pass comfortably as a shell
argument.

Example:

```bash
uv run rig run codex --task-file task.md
```

Provide exactly one of `--task` or `--task-file`. Passing both, or passing
neither, is an error.

### `rig runs list`

Lists recent runs by reading `.rig/runs/*/status.json`.

Example:

```bash
uv run rig runs list
```

Example output:

```txt
ID                         AGENT   STATUS     STARTED
20260502-203012-codex      codex   succeeded  2026-05-02 20:30:12
20260502-201500-codex      codex   failed     2026-05-02 20:15:00
```

### `rig runs show latest`

Shows metadata and the result for the most recent run.

Example:

```bash
uv run rig runs show latest
```

### `rig runs show <run-id>`

Shows metadata and the result for a specific run.

Example:

```bash
uv run rig runs show 20260502-203012-codex
```

### `rig agents snippet`

Prints a Markdown snippet that users can paste into `AGENTS.md` or similar
agent instruction files.

Rig does not edit `AGENTS.md` automatically. The snippet tells AI coding agents
to prefer future Rig MCP tools when available, fall back to the Rig CLI, and
inspect run artifacts after each run.

Example:

```bash
uv run rig agents snippet
```

## Run Artifacts

Each run creates these files:

```txt
.rig/runs/<run-id>/
  task.md
  command.json
  stdout.log
  stderr.log
  result.md
  status.json
```

- `task.md`: the task Rig gave to the agent
- `command.json`: the command Rig executed and when it started
- `stdout.log`: raw stdout from the agent command
- `stderr.log`: raw stderr from the agent command
- `result.md`: human-readable result; currently copied from stdout
- `status.json`: run ID, agent, status, timestamps, exit code, and run path

## Development

Run checks:

```bash
uv run pytest
uv run ruff check .
uv run mypy rig tests
```
