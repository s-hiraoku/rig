---
title: Agents
description: Configure Codex, Claude Code, Gemini, Copilot, and external GUI agents in Rig's config.yaml.
---

# Agents

An agent in Rig is a named command in `.rig/config.yaml`. Rig appends a rendered
prompt as the final argument and captures stdout, stderr, and exit status into
run artifacts. This page collects working configurations for common CLIs.

For runner semantics and prompt placeholder reference, see
[Configuration](configuration.md) and [Prompt Styles](prompts.md).

<div class="callout callout-tip" markdown="1">
<span class="callout-title">Tip</span>
Rig does not ship vendor-specific magic. If a CLI exposes a stable
non-interactive prompt mode, it can be configured as an `exec` runner.
</div>

## Codex (default)

The default agent. `codex exec` reads the appended prompt and writes the agent
turn to stdout.

```yaml
default_agent: codex

agents:
  codex:
    runner: exec
    command: codex
    args:
      - exec
```

Codex requires the working directory to be a trusted Git repository. If a run
fails with `Not inside a trusted directory`, run `git init` first. See
[Troubleshooting](troubleshooting.md#trusted-directory-error).

## Claude Code

Claude Code's `claude` CLI accepts a single non-interactive prompt with `-p`
(`--print`).

```yaml
agents:
  claude:
    runner: exec
    command: claude
    args:
      - -p
    prompt_style: task
```

Use `prompt_style: task` so the saved task file content is passed verbatim
instead of Rig's wrapper instructions. Add `--output-format stream-json` or
`--output-format json` if you want to feed Rig's stdout to other tools.

To generate Claude project instructions referencing Rig:

```bash
rig guide agents --target claude --write
```

This creates `.rig/instructions/rig.md` and prints a snippet you can paste into
`CLAUDE.md`.

## Gemini

```yaml
agents:
  gemini:
    runner: exec
    command: gemini
    args:
      - --prompt
    prompt_style: task
```

`prompt_style: task` keeps the prompt minimal so Gemini sees only the task
text. Configure model selection through Gemini's own flags, e.g. add
`--model` and the model name to `args`.

## GitHub Copilot CLI

```yaml
agents:
  copilot:
    runner: exec
    command: copilot
    args:
      - -p
    prompt_style: task
```

Copilot CLI emits human-readable output by default. Pair it with the
`--- RIG RESULT ---` marker if your prompt asks Copilot to print a structured
final answer; Rig will keep only the text after the marker in `result.md`.
See [Run Artifacts → Result Extraction](artifacts.md#result-extraction).

## Templated prompts

Use `prompt_style: template` when an agent needs a precise instruction
envelope. The template can reference `{agent}`, `{task}`, `{task_md}`,
and `{task_path}`.

```yaml
agents:
  reviewer:
    runner: exec
    command: codex
    args:
      - exec
    prompt_style: template
    prompt_template: |
      You are {agent}. Review the following task and reply with a
      single Markdown section that begins with the literal marker
      `--- RIG RESULT ---`.

      Task ({task_path}):

      {task_md}
```

See [Prompt Styles](prompts.md) for the full placeholder reference and more
worked examples.

## Manual / GUI agents

Use the `manual` runner when work happens in a GUI, a chat interface, or any
tool Rig should not launch directly. Rig writes the task and waits for an
explicit `complete` or `fail`.

```yaml
agents:
  external:
    runner: manual
```

```bash
rig run external --task "Implement the new toolbar in the design app."
# ... do the work elsewhere ...
rig manual complete latest --result-file result.md
```

`rig manual fail latest --error "Blocked in design review."` records a failure
with the same artifact layout as a real run. Status transitions are restricted
to runs currently in `waiting`, so this never overwrites a finished run.

## Experimental: PTY runner

Some interactive CLIs require a real terminal. The `pty` runner allocates a
PTY, writes the rendered prompt as input, and captures the merged transcript
to `stdout.log` and `result.md`.

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

Use the PTY runner only when the CLI cannot be driven through a single argv.
For most modern coding CLIs, `exec` is simpler and more reproducible.

## Switching the default agent

`default_agent` selects which agent runs when `rig run` is called without an
explicit name. Set it once in `.rig/config.yaml`:

```yaml
default_agent: claude

agents:
  codex:
    runner: exec
    command: codex
    args: [exec]
  claude:
    runner: exec
    command: claude
    args: [-p]
    prompt_style: task
```

```bash
rig run --task "Refactor the worktree helper."   # uses claude
rig run codex --task "Refactor the worktree helper."   # uses codex explicitly
```

## Per-agent timeouts

`timeout_seconds` applies to both `exec` and `pty` runners. When the configured
agent runs longer than the limit, Rig terminates the process and records a
`failed` status with the captured output.

```yaml
agents:
  codex:
    runner: exec
    command: codex
    args: [exec]
    timeout_seconds: 600
```

## Asset managers vs. Rig agents

A Rig agent is the command Rig executes. The agent's *assets* — prompts, hooks,
skills, MCP server lists — are managed by external tools (APM, GitHub CLI
`gh skill`, Vercel `skills`, or your team's own scripts). Declare those as
optional asset managers in `.rig/env.yaml` so `rig env doctor` can report
their availability without installing anything. See
[Configuration → Environment Configuration](configuration.md#environment-configuration).
