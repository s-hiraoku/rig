# Rig

Rig is a local AI coding harness for running coding agents with file-backed
tasks, inspectable artifacts, and a simple run history.

Rig's main unit is a run. A run records the task, the command Rig executed,
stdout, stderr, the final result, and status metadata under `.rig/runs/`.

See [ROADMAP.md](ROADMAP.md) for planned phases, including worktree support,
generic execution runners, and MCP tools.
See [docs/commands.md](docs/commands.md) for the compact command reference.

Rig does not try to replace package managers for agent assets. Tools such as
APM, GitHub CLI `gh skill`, Vercel `skills`, or manual team conventions can own
fetching, locking, auditing, and deploying skills, hooks, prompts, and MCP
server configuration. Rig focuses on running agents and preserving inspectable
run artifacts.

Rig can still help with the surrounding harness environment. Users can declare
project-specific required files in `.rig/env.yaml`; Rig diagnoses whether those
files exist and points to the right external installer, package manager, or team
process. Rig should not silently install or rewrite third-party agent assets.

## Installation

Install directly from GitHub:

```bash
uv tool install "rig @ git+https://github.com/s-hiraoku/rig.git"
```

Then check that the command is available:

```bash
rig --help
```

To reinstall the latest version from GitHub:

```bash
uv tool install --force --refresh "rig @ git+https://github.com/s-hiraoku/rig.git"
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

Optional zsh completion is available at `contrib/completions/rig.zsh`.

## Requirements

`rig run <agent>` executes the configured agent command from `.rig/config.yaml`.
The default `codex` agent calls `codex exec`, so the Codex CLI must be installed
and available on `PATH` before running Codex through Rig.

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
rig list
rig show latest
```

From this repository checkout, prefix commands with `uv run`:

```bash
uv run rig init
uv run rig run codex --task "Review the current diff and identify risky changes."
uv run rig list
uv run rig show latest
```

For an isolated agent edit:

```bash
rig worktree run codex --task "Make the requested change."
rig worktree show latest
rig worktree apply latest
```

## Commands

### `rig init`

Initializes Rig in the current repository.

It creates:

```txt
.rig/
  config.yaml
  env.yaml
  runs/
```

The command is safe to run more than once. If `.rig/` already exists, Rig keeps
existing files in place and recreates missing Rig-owned files. It does not edit
existing `.rig/config.yaml` or `.rig/env.yaml`. If nothing changes, it prints
`Rig already up to date.`

Use an explicit reset when you want to return generated config to the current
Rig defaults. Existing files are backed up before they are replaced:

```bash
uv run rig init --reset config
uv run rig init --reset env
uv run rig init --reset all
uv run rig init --force
```

`--force` is equivalent to `--reset all`.

Example:

```bash
uv run rig init
```

The generated `.rig/config.yaml` controls the command Rig uses for each agent.
If `rig run` omits the agent name, Rig uses `default_agent`. For Codex, Rig
reads `agents.codex.command` and `agents.codex.args`:

```yaml
agents:
  codex:
    runner: exec
    command: codex
    args:
      - exec
```

Rig currently supports the `exec` runner: non-interactive command execution with
the task prompt appended as the final argument. Other CLIs can be configured the
same way when they expose a stable non-interactive prompt mode:

```yaml
agents:
  copilot:
    runner: exec
    command: copilot
    args:
      - -p
    prompt_style: task
  gemini:
    runner: exec
    command: gemini
    args:
      - --prompt
    prompt_style: task
```

`prompt_style: rig` passes Rig's standard instruction prompt with a task file
path. `prompt_style: task` passes the raw task file content. `timeout_seconds`
applies to both `exec` and `pty` runners. `prompt_style: template` plus
`prompt_template` can replace Rig's generated prompt and may use `{agent}`,
`{task_path}`, `{task}` for the raw user task, and `{task_md}` for the saved
task file content.

If an agent prints `--- RIG RESULT ---`, Rig stores only the text after that
marker in `result.md` while preserving full stdout in `stdout.log`.

Rig also supports the `manual` runner for human-driven, GUI-driven, or external
agent work. It creates a run with status `waiting` and writes the task/artifact
files without executing a command:

```yaml
agents:
  external:
    runner: manual
```

The `pty` runner is experimental. Use it only for CLIs that require a TTY. Rig
captures the terminal transcript into `stdout.log` and `result.md`; stderr is
merged into that transcript by the terminal:

```yaml
agents:
  interactive:
    runner: pty
    command: interactive-agent
    args:
      - --prompt
    timeout_seconds: 300
    prompt_style: task
```

The generated `.rig/env.yaml` declares the default harness environment checks.
By default it lists APM, GitHub CLI `gh skills`, and Vercel `skills` via `npx`
as optional agent asset managers, and declares `AGENTS.md` as a required file
for the project harness:

```yaml
agent_asset_managers:
  - id: apm
    label: APM
    command: apm
  - id: gh-skills
    label: GitHub skills manager
    command: gh
    args:
      - skills
      - --help
  - id: vercel-skills
    label: Vercel skills manager
    command: npx

required_files:
  - path: AGENTS.md
    label: Agent instructions
```

### `rig run <agent> --task "..."`

Starts a new agent run using task text passed directly on the command line.

Rig creates a unique run directory, writes the task to `task.md`, executes
the configured agent command, captures stdout and stderr, writes `result.md`,
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

Use `--dry-run` to create the run directory, task file, command metadata, and
status file without executing the agent:

```bash
uv run rig run codex --task "Review the current diff." --dry-run
```

Dry-run runs use status `created` and write the command preview to
`command.json`.

### `rig run <agent> --task-file task.md`

Starts a new agent run using task text read from a file.

Use this when the task is too long or structured to pass comfortably as a shell
argument.

Example:

```bash
uv run rig run codex --task-file task.md
```

Provide exactly one of `--task` or `--task-file`. Passing both, or passing
neither, is an error.

### `rig worktree run <agent> --task "..."`

Runs an agent in an isolated Git worktree under `.rig/worktrees/<run-id>/`.
Rig captures the resulting patch as `.rig/runs/<run-id>/diff.patch` and leaves
the main working tree unchanged.

Example:

```bash
uv run rig worktree run codex --task "Make the requested change."
```

### `rig list`

Lists recent runs by reading `.rig/runs/*/status.json`.

Unreadable run metadata is skipped. If there are no readable runs, Rig prints
`No runs found.`. Add `--json` for machine-readable output. The grouped form is
also available as `rig history list`.

Example:

```bash
uv run rig list
```

Example output:

```txt
ID                         AGENT   STATUS     STARTED
20260502-203012-codex      codex   succeeded  2026-05-02 20:30:12
20260502-201500-codex      codex   failed     2026-05-02 20:15:00
```

### `rig show latest`

Shows metadata and the result for the most recent run.

If no readable runs exist, Rig prints `No runs found.`. Add `--json` to print
metadata only as JSON. The grouped form is also available as
`rig history show latest`.

Example:

```bash
uv run rig show latest
```

### `rig show <run-id>`

Shows metadata and the result for a specific run.

If the run metadata is missing or unreadable, Rig reports that the run was not
found or unreadable. If `result.md` is missing, Rig still shows the run metadata.
Failed runs also show the exit code and an `--- Error ---` section sourced from
`stderr.log`, so a failed run remains inspectable even when `result.md` is empty.

Example:

```bash
uv run rig show 20260502-203012-codex
```

### `rig worktree show <run-id>`

Prints the captured patch for a worktree run. Use `latest` for the most recent
run.

Example:

```bash
uv run rig worktree show latest
```

### `rig worktree apply <run-id>`

Applies a captured worktree patch to the current repository using `git apply`.
Use this only after inspecting the patch. Worktree patches include untracked
files that are not ignored by Git; keep large generated directories in
`.gitignore` before applying.

Example:

```bash
uv run rig worktree apply latest
```

### `rig worktree prune`

Removes Rig-created worktrees under `.rig/worktrees/`.

Example:

```bash
uv run rig worktree prune
```

### `rig history complete <run-id>`

Completes a waiting manual run by writing `result.md` and marking the run as
`succeeded`. Use `latest` to complete the most recent run. Rig refuses to
complete runs that are not currently `waiting`, so this command does not
overwrite finished exec runs by accident.

Example:

```bash
uv run rig history complete latest --result "Finished in Copilot Chat."
uv run rig history complete 20260502-203012-external --result-file result.md
```

### `rig history fail <run-id>`

Fails a waiting manual run by writing `stderr.log` and marking the run as
`failed`. Like `complete`, this command only operates on runs that are currently
`waiting`.

Example:

```bash
uv run rig history fail latest --error "Blocked in external review."
uv run rig history fail 20260502-203012-external --error-file error.txt
```

### `rig guide agents`

Prints a Markdown snippet that users can paste into `AGENTS.md` or similar
agent instruction files.

Rig does not edit `AGENTS.md` automatically. The snippet tells AI coding agents
to prefer future Rig MCP tools when available, fall back to the Rig CLI, and
inspect run artifacts after each run.

Example:

```bash
uv run rig guide agents
```

### `rig env doctor`

Runs read-only diagnostics for the local Rig and agent harness environment.

It checks for the Git repository, `.rig/config.yaml`, `.rig/runs/`, Codex CLI,
known optional agent asset managers, `AGENTS.md`, and required files declared in
`.rig/env.yaml`. Rig does not install tools or edit third-party agent asset
files.

Statuses are `ok`, `missing`, `optional`, and `warn`. Required Rig/Codex basics
use `missing` when absent; external asset managers are usually `optional`;
partial or inconsistent setup uses `warn`.

Declare project-specific required files in `.rig/env.yaml`:

```yaml
version: 1

required_files:
  - AGENTS.md
  - path: docs/agent-harness.md
    label: Agent harness docs
    hint: "Create docs/agent-harness.md with team setup notes."
  - path: docs/harness.md
    label: Harness docs
    hint: "Create docs/harness.md with team setup notes."
```

You can also attach required config files to a specific asset manager. When the
file is missing, `rig env doctor` and `rig env plan` show the manager name and
the missing file. The `path` is intentionally free-form, so each project can use
the filename its chosen manager expects, such as `apm.yml`, `apm.yaml`, or a
vendor-specific config file:

```yaml
version: 1

agent_asset_managers:
  - id: apm
    label: APM
    command: apm
    required_files:
      - path: apm.yml
        label: APM manifest
        hint: "Create apm.yml or remove this manager from .rig/env.yaml."
```

Example:

```bash
uv run rig env doctor
```

### `rig env plan`

Shows a read-only plan for the desired Rig harness environment.

It reuses the same checks as `rig env doctor`, then summarizes the desired setup,
current gaps, and suggested external commands. It does not change files, install
tools, or deploy third-party agent assets.

Example:

```bash
uv run rig env plan
```

### `rig env bootstrap`

Creates missing Rig-owned environment files, then prints the remaining next
steps from `rig env doctor`. It follows the same safety rule as `rig init`:
existing `.rig/config.yaml` and `.rig/env.yaml` are not overwritten. Rig does
not install external tools or deploy third-party agent assets.

Example:

```bash
uv run rig env bootstrap
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
