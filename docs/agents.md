---
title: Agents
description: Configure the child coding agents Rig launches.
---

# Agents

An agent is a named command in `.rig/config.yaml`. Rig always launches agents
through non-interactive command execution and appends the rendered prompt as the
final argument.

```yaml
default_agent: codex

agents:
  codex:
    command: codex
    args:
      - exec
```

## Examples

Claude Code:

```yaml
agents:
  claude:
    command: claude
    args:
      - -p
    prompt_style: task
```

Gemini:

```yaml
agents:
  gemini:
    command: gemini
    args:
      - --prompt
    prompt_style: task
```

## Prompt Styles

- `rig` sends Rig's standard delegated-agent prompt and a task file path.
- `task` sends the saved task content verbatim.
- `template` renders `prompt_template`.

Templates may use `{agent}`, `{task_path}`, `{task}`, and `{task_md}`.

## Timeout

Set a default timeout per agent:

```yaml
agents:
  codex:
    command: codex
    args: [exec]
    timeout_seconds: 600
```

For a single run:

```bash
rig delegate codex --task-file tasks/review.md --timeout-seconds 1200
```
