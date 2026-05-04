---
title: Configuration
description: Rig's two configuration files — .rig/config.yaml for child agents and .rig/env.yaml for environment checks.
---

# Configuration

Rig keeps configuration in two files under `.rig/`. `rig init` creates them
with sensible defaults. Both are plain YAML and can be hand-edited.

```txt
.rig/
  config.yaml   # child agents, runners, prompt styles
  env.yaml      # required files and optional asset managers
  runs/         # run history (per-machine)
```

For per-CLI working examples (Codex, Claude, Gemini, Copilot, manual), see
[Agents](agents.md). For prompt-string behavior, see
[Prompt Styles](prompts.md).

## Initialize Or Reset
{: #initialize-or-reset }

```bash
rig init                # create missing files; never overwrite
rig init --reset config # back up and recreate config.yaml
rig init --reset env    # back up and recreate env.yaml
rig init --reset all    # both
rig init --force        # equivalent to --reset all
```

`rig init` is safe to run repeatedly. If nothing changes, it prints
`Rig already up to date.`

## Agent Configuration

`.rig/config.yaml` defines the child-agent commands Rig launches when the
parent agent calls `rig_run`. If the parent omits the agent name, Rig uses
`default_agent`.

```yaml
default_agent: codex

agents:
  codex:
    runner: exec
    command: codex
    args:
      - exec
```

### Schema

| Field | Type | Notes |
| --- | --- | --- |
| `default_agent` | string | Agent name used when `rig_run` / `rig run` is called without one. |
| `agents.<name>.runner` | `exec` / `manual` / `pty` | See [Runner](#runner). |
| `agents.<name>.command` | string | The executable Rig launches. Required for `exec` and `pty`. |
| `agents.<name>.args` | list of string | Extra args inserted before the rendered prompt. |
| `agents.<name>.prompt_style` | `rig` (default) / `task` / `template` | See [Prompt Styles](prompts.md). |
| `agents.<name>.prompt_template` | string | Required when `prompt_style: template`. |
| `agents.<name>.timeout_seconds` | integer | Applies to `exec` and `pty`. |

Use `rig run --timeout-seconds N` or MCP `timeout_seconds` for a one-off
override when a parent agent knows a delegated run needs more time than the
shared config default.

### Runner

- `exec` — non-interactive command execution. Rig appends the rendered
  prompt as the final argument.
- `manual` — create a `waiting` run without executing a command. Used for
  GUI / chat / out-of-band work.
- `pty` — experimental TTY-backed execution for CLIs that require a
  terminal.

### Examples

A second `exec` agent for a different CLI:

```yaml
agents:
  gemini:
    runner: exec
    command: gemini
    args:
      - --prompt
    prompt_style: task
    timeout_seconds: 600
```

A manual runner for GUI work:

```yaml
agents:
  external:
    runner: manual
```

A templated prompt:

```yaml
agents:
  reviewer:
    runner: exec
    command: codex
    args: [exec]
    prompt_style: template
    prompt_template: |
      You are {agent}. Read {task_path} and reply with a Markdown report.
```

## Prompt Styles

`prompt_style` decides what string Rig appends to the child-agent command.

- `rig` (default) — Rig's standard instruction with a task file path.
- `task` — the raw task file content, verbatim.
- `template` — renders `prompt_template`.

Template variables:

- `{agent}` — child-agent name.
- `{task}` — raw task text passed to `--task` or read from `--task-file`.
- `{task_md}` — saved task file content.
- `{task_path}` — path to the saved task file relative to the run cwd.

See [Prompt Styles](prompts.md) for worked examples and per-CLI guidance.

## Environment Configuration
{: #environment-configuration }

`.rig/env.yaml` declares harness checks for `rig env doctor` and
`rig env plan`. The schema is intentionally small and forward-compatible
through the `version` field.

```yaml
version: 1

required_files:
  - path: AGENTS.md
    label: Agent instructions
    hint: "Create AGENTS.md with project-specific agent guidance."
```

Required files can be written as strings or mappings:

```yaml
required_files:
  - AGENTS.md
  - path: docs/agent-harness.md
    label: Agent harness docs
    hint: "Create docs/agent-harness.md with MCP, skills, and hooks guidance."
```

Optional asset managers live under `agent_asset_managers`. The generated
default declares APM, GitHub CLI `gh skills`, and Vercel `skills` via `npx`.
Rig checks whether the configured commands exist; it does not install them.

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
```

Asset managers can also declare their own required files. When a file is
missing, `rig env doctor` reports both the manager name and the missing
file:

```yaml
agent_asset_managers:
  - id: apm
    label: APM
    command: apm
    required_files:
      - path: apm.yml
        label: APM manifest
        hint: "Create apm.yml or remove this manager from .rig/env.yaml."
```

Rig reports missing files and tools, but it does not silently install global
tools or rewrite third-party agent assets.

## What `rig init` Does Not Do

- It does not edit existing `.rig/config.yaml` or `.rig/env.yaml`.
- It does not install Codex, Claude, Gemini, Copilot, or any asset manager.
- It does not create or edit `AGENTS.md`, `CLAUDE.md`, or skill files.
- It does not commit or push.

If you want generated config to match the current Rig defaults, use
`rig init --reset config` (the previous file is backed up first).
