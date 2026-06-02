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
  claude:
    command: claude
    args:
      - -p
    prompt_style: task
  antigravity:
    command: agy
    args:
      - -p
    prompt_style: task
  copilot:
    command: copilot
    args:
      - -p
    prompt_style: task
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

Antigravity CLI:

```yaml
agents:
  antigravity:
    command: agy
    args:
      - -p
    prompt_style: task
```

Rig launches `agy` from the run's execution directory, so Antigravity scopes the
workspace to that directory while `-p` receives Rig's prompt as the final
argument.

Antigravity image generation:

```yaml
agents:
  antigravity-image:
    command: agy
    args:
      - -p
    prompt_style: template
    timeout_seconds: 1200
    prompt_template: |
      You are running through Rig as {agent}.

      Use Antigravity's image-generation capability with Nano Banana 2 or
      Nano Banana Pro 2 when available. Treat the user task below as an asset
      generation request.

      Save generated image files inside the current workspace. If the task does
      not name an output path, use assets/generated/.

      Do not print base64 or inline image bytes to stdout. After generation,
      print this marker and a concise summary with output file paths, the model
      or tool used if known, and any policy or quota failures:

      --- RIG RESULT ---

      Task:
      {task}
```

This keeps Rig vendor-neutral: Rig only launches `agy` and records the normal
run artifacts, while Antigravity decides whether and how to invoke its
generative image tool.

GitHub Copilot CLI:

```yaml
agents:
  copilot:
    command: copilot
    args:
      - -p
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
