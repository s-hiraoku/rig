---
title: Agents
description: Configure the child agents Rig launches — Codex, Claude Code, Gemini, Copilot, manual GUI agents — in .rig/config.yaml.
---

# Agents

In Rig, an *agent* is a named child-agent command in `.rig/config.yaml`. The
parent AI selects an agent by name (`codex`, `claude`, `gemini`, …) when it
calls `rig_run`; Rig launches that command, appends a rendered prompt as the
final argument, and captures stdout / stderr / exit status into run artifacts.

For runner semantics and prompt placeholders, see
[Configuration](configuration.md) and [Prompt Styles](prompts.md).

<div class="callout callout-tip" markdown="1">
<span class="callout-title">Tip</span>
Rig has no per-CLI magic. Any CLI with a stable non-interactive prompt mode
can be wired in as an <code>exec</code> runner.
</div>

## Codex (default child agent)

Default for new projects. `codex exec` reads the appended prompt and writes
the agent turn to stdout.

```yaml
default_agent: codex

agents:
  codex:
    runner: exec
    command: codex
    args:
      - exec
```

Codex requires the working directory to be a trusted Git repository. Run
`git init` first if you hit `Not inside a trusted directory`. See
[Troubleshooting → Trusted Directory Error](troubleshooting.md#trusted-directory-error).

## Claude Code

Claude Code's `claude` CLI takes a single non-interactive prompt with `-p`
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
`--output-format json` if you want Rig's stdout to feed other tools.

To add Claude project instructions that reference Rig:

```bash
rig guide agents --target claude --write
```

That writes `.rig/instructions/rig.md` and prints a snippet for `CLAUDE.md`.

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
text. Configure model selection through Gemini's own flags by adding them to
`args`.

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

Use `prompt_style: template` when a child agent needs a precise instruction
envelope. The template can reference `{agent}`, `{task}`, `{task_md}`, and
`{task_path}`.

```yaml
agents:
  reviewer:
    runner: exec
    command: codex
    args:
      - exec
    prompt_style: template
    prompt_template: |
      You are {agent}. Review the following task and reply with a single
      Markdown section that begins with the literal marker
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

The parent agent (or you) opens the run, then later closes it:

```bash
rig run external --task "Implement the new toolbar in the design app."
# … work happens elsewhere …
rig manual complete latest --result-file result.md
```

`rig manual fail latest --error "Blocked in design review."` records a
failure with the same artifact layout as a real run. Status transitions are
restricted to `waiting`, so this never overwrites a finished run.

## Experimental: PTY runner
{: #experimental-pty-runner }

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

## Switching the default child agent

`default_agent` selects which agent the parent uses when it calls `rig_run`
without an explicit name. Set it once in `.rig/config.yaml`:

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

Now `rig run --task "…"` (or a `rig_run` call with no `agent` field) uses
Claude.

## Per-agent timeouts

`timeout_seconds` applies to both `exec` and `pty` runners. When the child
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

A Rig agent is the command Rig executes. The agent's *assets* — prompts,
hooks, skills, MCP server lists — are managed by external tools (APM, GitHub
CLI `gh skill`, Vercel `skills`, or your team's own scripts). Declare those
as optional asset managers in `.rig/env.yaml` so `rig env doctor` can report
their availability without installing anything. See
[Configuration → Environment Configuration](configuration.md#environment-configuration).
