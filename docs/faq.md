---
title: FAQ
description: Frequently asked questions about Rig — its scope, safety model, runner choices, and how it compares to package managers and IDE integrations.
---

# FAQ

## What is Rig in one sentence?

A local CLI that runs coding agents and writes a complete, plain-file run
history under `.rig/runs/` so the work stays inspectable.

## Why not just call `codex exec` directly?

Calling the CLI directly works fine for one-off use, but you lose:

- A consistent task file you can re-run later.
- Captured stdout, stderr, exit code, and timing.
- An optional captured patch for isolated runs.
- A standard place for other tools (MCP clients, scripts) to read results.

Rig is the thinnest layer that gives you that history without changing how the
underlying CLI behaves.

## How is Rig different from a package manager for agent assets?

Rig deliberately does not own skills, hooks, prompt libraries, or MCP server
configuration. Tools like APM, GitHub CLI `gh skill`, and Vercel `skills` exist
to fetch, lock, audit, and deploy those. Rig:

- Runs the agent command and stores results.
- Diagnoses whether expected files and external tools exist
  (`rig env doctor`).
- Generates Rig-owned policy at `.rig/instructions/rig.md`.

It does not silently install or rewrite any third-party agent asset.

## Is Rig a sandbox?

No. Rig executes the configured agent command in your shell with your
credentials. Worktree runs add isolation at the *file system* level — edits
land in `.rig/worktrees/<run-id>/` instead of the main working tree — but the
agent process still runs locally.

If you need stronger isolation, run Rig itself inside a container or VM.

## Will Rig commit or push for me?

No. Rig writes files under `.rig/` and, when you explicitly invoke
`rig worktree apply`, runs `git apply` on a captured patch. It never commits,
never pushes, and never opens PRs.

## Do I have to use Codex?

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

It is a stdout marker. When Rig sees the literal line `--- RIG RESULT ---` in
the agent's stdout, it stores only the text *after* the marker in `result.md`.
The full stdout is preserved in `stdout.log`. This lets agents print verbose
logs and still surface a clean final answer through `rig show latest`.

See [Run Artifacts → Result Extraction](artifacts.md#result-extraction).

## How do I delete a run?

Delete the directory under `.rig/runs/<run-id>/`. Rig has no "delete" command;
runs are plain files. Read `.rig/runs/` with whatever shell tools you prefer.

## Can I run multiple agents on the same task?

Yes — run the same `--task-file` through each agent. Every run is its own
directory, so outputs do not collide. See
[Recipes → Compare Two Agents on the Same Task](recipes.md#compare-two-agents-on-the-same-task).

## Why are some MCP tools disabled by default?

`rig_apply_patch` modifies the working tree. It is disabled unless the server
starts with `RIG_MCP_ALLOW_APPLY=1`. The default is to never let a remote
MCP client apply patches without an explicit human opt-in.

MCP `cwd` values are also confined to the server's launch directory by
default; set `RIG_MCP_ROOT=/path` to widen the allowed scope. Relative
`task_file` paths must stay inside the chosen `cwd`.

See [MCP Server → Safety Defaults](mcp.md#safety-defaults).

## My CLI works only with a TTY. What do I do?

Try the experimental `pty` runner. It allocates a PTY, writes the rendered
prompt as input, and captures the merged transcript. See
[Agents → Experimental: PTY runner](agents.md#experimental-pty-runner).

## How do I version `.rig/`?

Most teams check `.rig/config.yaml` and `.rig/env.yaml` into Git, and add
`.rig/runs/` and `.rig/worktrees/` to `.gitignore`. Run history is per-machine;
config is shared.

## Does Rig work without Git?

`rig init` does not require a Git repository, but Codex's default mode does.
For non-Codex agents the requirement is whatever that CLI imposes. Worktree
runs do require Git because they use `git worktree`.

## How do I update Rig?

```bash
uv tool install --force --refresh "rig @ git+https://github.com/s-hiraoku/rig.git"
```

Rig is published as a `uv tool`. There is no separate update command.

## Where do I file bugs or feature requests?

Open an issue on the
[GitHub repository](https://github.com/s-hiraoku/rig/issues). Run
`rig env doctor --json` first and attach the output — it captures the bits
about your setup that usually matter.
