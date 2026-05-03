---
title: Configuration
---

# Configuration

Rig creates its local files with:

```bash
rig init
```

The generated structure is:

```txt
.rig/
  config.yaml
  env.yaml
  runs/
```

## Agent Configuration

`.rig/config.yaml` controls the command Rig uses for each agent. If `rig run`
omits the agent name, Rig uses `default_agent`.

Example:

```yaml
default_agent: codex

agents:
  codex:
    runner: exec
    command: codex
    args:
      - exec
```

For another CLI, configure the command and prompt style:

```yaml
agents:
  gemini:
    runner: exec
    command: gemini
    args:
      - --prompt
    prompt_style: task
```

## Prompt Styles

- `rig`: passes Rig's standard instruction prompt with a task file path.
- `task`: passes the raw task file content.
- `template`: renders `prompt_template`.

Template variables:

- `{agent}`: configured agent name.
- `{task_path}`: path to the saved task file.
- `{task}`: raw user task text.
- `{task_md}`: saved task file content.

## Environment Configuration

`.rig/env.yaml` declares harness checks for `rig env doctor` and
`rig env plan`.

Example:

```yaml
version: 1

required_files:
  - path: AGENTS.md
    label: Agent instructions
    hint: "Create AGENTS.md with project-specific agent guidance."
```

Rig reports missing files and tools, but it does not silently install global
tools or rewrite third-party agent assets.
