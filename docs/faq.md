---
title: FAQ
description: Frequently asked questions about Rig — its scope, the three-role model, the safety boundary, and how it compares to other tools.
---

# FAQ

## What is Rig in one sentence?

A local harness that AI coding agents call to delegate work, while writing
a complete, plain-file run history under `.rig/runs/` so the work stays
inspectable, reviewable, and replayable.

## Who actually types `rig run`?

In normal use, your parent AI agent does — Cursor, Claude Code, Codex CLI,
or any other tool reading your `AGENTS.md` / `CLAUDE.md`. You ask in plain
language; the parent agent calls `rig run` (CLI) or `rig_run` (MCP) on your
behalf.

You only type Rig commands directly for setup, debugging, and audit. See
[Getting Started → Appendix B](getting-started.md).

## Why not just call `codex exec` directly?

Calling the CLI directly works fine for one-off use, but you lose:

- A consistent task file you can re-run later.
- Captured stdout, stderr, exit code, and timing.
- An optional captured patch for isolated runs.
- A standard place for the parent agent (and other tools) to read results.

Rig is the thinnest layer that gives you that history without changing how
the underlying CLI behaves.

## How is Rig different from a package manager for agent assets?

Rig deliberately does not own skills, hooks, prompt libraries, or MCP
server configuration. Tools like APM, GitHub CLI `gh skill`, and Vercel
`skills` exist to fetch, lock, audit, and deploy those. Rig:

- Runs the child-agent command and stores results.
- Diagnoses whether expected files and external tools exist
  (`rig env doctor`).
- Generates Rig-owned policy at `.rig/instructions/rig.md`.

It does not silently install or rewrite any third-party agent asset.

## Is Rig a sandbox?

No. Rig executes the configured child-agent command in your shell with your
credentials. Worktree runs add isolation at the *file system* level —
edits land in `.rig/worktrees/<run-id>/` instead of the main working tree —
but the process itself still runs locally.

If you need stronger isolation, run the parent agent (or Rig itself) inside
a container or VM.

## Will Rig commit or push for me?

No. Rig writes files under `.rig/` and, when you (or the parent agent on
your behalf) explicitly invoke `rig worktree apply`, runs `git apply` on a
captured patch. It never commits, never pushes, and never opens PRs.

## Do I have to use Codex as the child agent?

No. Codex is the default because `codex exec` exposes a stable
non-interactive prompt mode, but any CLI with a similar shape can be
configured. See [Agents](agents.md) for working configurations of Claude,
Gemini, Copilot, and external GUI agents (`manual` runner).

## What runner should I use?

| Runner | Use when |
| --- | --- |
| `exec` | The CLI accepts a single non-interactive prompt argument. (Most modern coding CLIs.) |
| `manual` | Work happens in a GUI, chat client, or any tool Rig should not launch. |
| `pty` | The CLI requires a real TTY and refuses to run otherwise. Experimental. |

`exec` is almost always the right answer.

## What does `--- RIG RESULT ---` actually do?

It is a stdout marker. When Rig sees the literal line `--- RIG RESULT ---`
in the child agent's stdout, it stores only the text *after* the marker in
`result.md`. The full stdout is preserved in `stdout.log`. This lets child
agents print verbose logs and still surface a clean final answer to the
parent agent.

See [Run Artifacts → Result Extraction](artifacts.md#result-extraction).

## How do I delete a run?

Delete the directory under `.rig/runs/<run-id>/`. Rig has no "delete"
command; runs are plain files. Read `.rig/runs/` with whatever shell tools
you prefer.

## Can the parent agent run multiple child agents on the same task?

Yes — pass the same `--task-file` through each child agent. Every run is
its own directory, so outputs do not collide. See
[Recipes → Compare Two Child Agents On The Same Task](recipes.md#compare-two-child-agents-on-the-same-task).

If you want multiple attempts from the same configured agent, use
`rig run <agent> --task-file task.md --parallel N`. Parallel mode creates
separate run directories for each attempt. It is limited to normal runs;
parallel worktree runs are rejected.

When the parent agent has native subagents, prefer those for parallel attempts
and role-split work. Rig parallel mode is for clients without native
subagents, or for cases where the durable `.rig/runs/` artifact trail matters.

## Why are some MCP tools disabled by default?

`rig_apply_patch` modifies the working tree. It is disabled unless the
server starts with `RIG_MCP_ALLOW_APPLY=1`. The default is to never let a
remote MCP client apply patches without an explicit human opt-in.

MCP `cwd` values are also confined to the server's launch directory by
default; set `RIG_MCP_ROOT=/path` to widen the allowed scope. Relative
`task_file` paths must stay inside the chosen `cwd`.

See [MCP Server → Safety Defaults](mcp.md#safety-defaults).

## My CLI works only with a TTY. What do I do?

Try the experimental `pty` runner. It allocates a PTY, writes the rendered
prompt as input, and captures the merged transcript. See
[Agents → Experimental: PTY runner](agents.md#experimental-pty-runner).

## How do I version `.rig/`?

Most teams check `.rig/config.yaml`, `.rig/env.yaml`, and
`.rig/instructions/rig.md` into Git, and add `.rig/runs/` and
`.rig/worktrees/` to `.gitignore`. Run history is per-machine; config and
instructions are shared.

## Does Rig work without Git?

`rig init` does not require a Git repository, but Codex's default mode
does. For non-Codex child agents the requirement is whatever that CLI
imposes. Worktree runs do require Git because they use `git worktree`.

## How do I update Rig?

```bash
uv tool install --force --refresh "rig @ git+https://github.com/s-hiraoku/rig.git"
```

Rig is published as a `uv tool`. There is no separate update command.

## When should I bypass Rig and edit directly?

For trivial changes, simple searches, and shell commands you can safely
perform yourself, asking the parent agent to wrap the work in Rig is
overhead without benefit. The Rig usage policy generated by
`rig guide agents` says exactly this. Use Rig when you want a delegated
agent run with an audit trail; use direct edits otherwise.

## Where do I file bugs or feature requests?

Open an issue on the
[GitHub repository](https://github.com/s-hiraoku/rig/issues). Run
`rig env doctor --json` first and attach the output — it captures the
bits about your setup that usually matter.
