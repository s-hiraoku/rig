---
title: Prompt Styles
description: How Rig builds the prompt it appends to the agent command — rig, task, and template styles with placeholder reference.
---

# Prompt Styles

`prompt_style` decides what Rig actually sends to the agent. The chosen style
controls a single string that becomes the final positional argument of the
configured command. Everything else — `command`, `args`, `timeout_seconds` — is
unchanged.

`.rig/runs/<run-id>/command.json` records the resolved argv, so you can always
inspect the exact prompt Rig used.

## At a Glance

| Style | What Rig sends | Use when |
| --- | --- | --- |
| `rig` (default) | A short instruction asking the agent to read `task.md` | The agent has direct file access and benefits from generic guardrails. |
| `task` | The raw task file content, verbatim | The agent expects only the user prompt (Claude `-p`, Gemini `--prompt`). |
| `template` | A custom string rendered from `prompt_template` | You need a precise instruction envelope or a structured marker. |

## `rig` Style

The default style produces a Rig-flavored instruction. Rig writes the user
task to `task.md` and asks the agent to open that file:

```text
You are running as a delegated codex agent through Rig.

Read the task file:

.rig/runs/20260504-141500-codex/task.md

Complete the task and write your final answer to stdout.

Do not assume Rig will automatically apply changes.
If you modify files, explain what you changed.
```

This is appropriate for Codex, where `codex exec` opens the file path it
receives and treats it as the active task.

## `task` Style

`task` skips the wrapper. Rig passes the raw text from `task.md` as the final
argument, with nothing prepended.

```yaml
agents:
  claude:
    runner: exec
    command: claude
    args: [-p]
    prompt_style: task
```

If the task is `Refactor the worktree helper.`, the executed command is
effectively:

```bash
claude -p "Refactor the worktree helper."
```

Use `task` for CLIs whose `-p` / `--prompt` flag expects a single user message
rather than a wrapped instruction.

## `template` Style

`template` renders `prompt_template` as a Python `str.format` template. It is
the only style that lets you control the full prompt envelope.

```yaml
agents:
  reviewer:
    runner: exec
    command: codex
    args: [exec]
    prompt_style: template
    prompt_template: |
      You are {agent}, reviewing one task end-to-end.

      Task ({task_path}):

      {task_md}

      Reply with a Markdown report. Begin the final answer with the literal
      marker `--- RIG RESULT ---` so Rig can extract it.
```

The placeholders are validated at config load time, so an unknown placeholder
fails loudly with `Config value … uses unknown placeholder` instead of breaking
mid-run.

### Placeholder reference

| Placeholder | Value |
| --- | --- |
| `{agent}` | The configured agent name (the YAML key under `agents`). |
| `{task}` | The raw task text passed to `--task` or read from `--task-file`. |
| `{task_md}` | The full content of the saved `task.md`, including any header Rig writes. |
| `{task_path}` | Path to `task.md` relative to the run's execution cwd. |

`{task}` and `{task_md}` differ only in trailing newlines and any header lines
Rig may attach. Use `{task_md}` when you want the version on disk.

### Worked Examples

Strict structured response:

```yaml
prompt_template: |
  Reply only with JSON of shape {{"status": string, "summary": string}}.
  Task: {task}
```

Notice the doubled braces (`{{` and `}}`) — `str.format` treats single braces
as placeholders.

Minimal envelope that still references the saved file:

```yaml
prompt_template: "Read {task_path} and complete the task."
```

Append context the team always wants:

```yaml
prompt_template: |
  Coding standards: see AGENTS.md and `.rig/instructions/rig.md`.
  Task ({agent}, {task_path}):

  {task_md}
```

## Result Marker

Independently of `prompt_style`, agents can emit a sentinel line so Rig keeps
only the final answer in `result.md`:

```text
--- RIG RESULT ---
```

When Rig finds the marker in stdout, `result.md` contains only the text after
it, while `stdout.log` keeps the full output. This lets a verbose agent run
print logs and still surface a clean final answer through `rig show latest`.

See [Run Artifacts → Result Extraction](artifacts.md#result-extraction).

## Per-CLI Recommendations

| CLI | Recommended `prompt_style` |
| --- | --- |
| Codex (`codex exec`) | `rig` (default) |
| Claude Code (`claude -p`) | `task` |
| Gemini (`gemini --prompt`) | `task` |
| GitHub Copilot CLI (`copilot -p`) | `task` |
| Custom review or report jobs | `template` |

Combine `template` with a result marker to keep run output predictable across
CLIs that otherwise print very different log shapes.

## Inspect the Resolved Prompt

To see the exact argv Rig used for a past run, read `command.json`:

```bash
cat .rig/runs/<run-id>/command.json
```

The last entry of `args` is the prompt Rig produced. For dry runs, the same
file is written without executing the agent (`rig run … --dry-run`).
