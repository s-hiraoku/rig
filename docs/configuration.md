---
title: Configuration
description: Rig's config file for child coding agents.
---

# Configuration

Rig keeps shared configuration in `.rig/config.yaml`. `rig init` creates it and
never overwrites an existing file unless you pass a reset flag.

```bash
rig init
rig init --reset config
rig init --reset instructions
rig init --reset all
```

## Agent Configuration

```yaml
default_agent: codex

agents:
  codex:
    command: codex
    args:
      - exec
```

| Field | Type | Notes |
| --- | --- | --- |
| `default_agent` | string | Agent used when `rig delegate` or `rig patch create` omits one. |
| `agents.<name>.command` | string | Executable Rig launches. |
| `agents.<name>.args` | list of string | Args inserted before the rendered prompt. |
| `agents.<name>.prompt_style` | `rig` / `task` / `template` | Prompt rendering mode. Default: `rig`. |
| `agents.<name>.prompt_template` | string | Required for `prompt_style: template`. |
| `agents.<name>.timeout_seconds` | integer | Child process timeout. Default: 300. |

Rig always uses non-interactive command execution. The old `runner` field is not
supported.

## Prompt Templates

Templates may use:

- `{agent}`
- `{task_path}`
- `{task}`
- `{task_md}`

```yaml
agents:
  reviewer:
    command: codex
    args: [exec]
    prompt_style: template
    prompt_template: |
      Review {task_path} as {agent}.

      {task_md}
```

## What `rig init` Does Not Do

- It does not install Codex or any other child-agent CLI.
- It does not edit `AGENTS.md`.
- It does not commit, push, or open PRs.
