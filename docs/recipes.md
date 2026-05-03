---
title: Recipes
description: End-to-end Rig recipes — PR review, isolated refactors, test coverage, multi-agent comparisons, and manual GUI flows.
---

# Recipes

Each recipe is a complete end-to-end flow. They assume Rig is installed and
`rig init` has been run in the project. For setup, see
[Getting Started](getting-started.md).

## Review the Current Diff

Use Rig as a reproducible PR review front-end. Every review is a run; the
result lands in `.rig/runs/<run-id>/result.md`.

```bash
rig run codex --task "Review the staged and unstaged diff. Identify bugs, regressions, and risky behavior changes. End the response with a `--- RIG RESULT ---` marker followed by a one-paragraph summary."
rig show latest
```

Inspect a previous review:

```bash
rig list
rig show 20260504-141500-codex
```

For team-wide consistency, check `result.md` into a non-tracked review folder
or attach it to the PR description.

## Refactor in an Isolated Worktree

Worktree runs let an agent edit files in `.rig/worktrees/<run-id>/` without
touching the working tree. Rig captures the resulting patch, which you review
before applying.

```bash
rig worktree run codex --task "Extract the worktree helper out of cli.py into rig/worktree_cli.py. Keep behavior identical."
rig worktree show latest
```

If the patch looks good:

```bash
rig worktree apply latest
```

If not, iterate without losing the previous attempt — each attempt is a new
run with its own diff.

```bash
rig worktree run codex --task "Try again. The previous attempt did not preserve the dry-run path."
```

When done:

```bash
rig worktree prune
```

<div class="callout callout-warn" markdown="1">
<span class="callout-title">Warning</span>
Worktree patches include untracked files that are not ignored by Git. Add
generated build artifacts to <code>.gitignore</code> before applying patches,
or you will commit the agent's scratch directories.
</div>

## Decide Before Running

`rig suggest` inspects the working tree and recommends a flow without starting
an agent:

```bash
rig suggest "Refactor the CLI command structure." --json
```

The JSON form is convenient inside scripts:

```bash
rig suggest "..." --json | jq -r '.recommendation'
# -> rig run | rig worktree run
```

Wire that into a pre-commit or chat slash command to nudge contributors toward
the safer flow when the working tree is dirty.

## Add Test Coverage Before Touching Code

A two-step recipe: first generate tests, then implement the change against
them. Each step is an independent run, so you can keep the green commit and
discard the implementation attempt if it goes wrong.

```bash
rig worktree run codex --task "Add failing pytest cases for tests/test_run_store.py covering the dry-run path. Do not modify rig/run_store.py."
rig worktree show latest
rig worktree apply latest
```

Then implement against the new tests:

```bash
rig worktree run codex --task "Make the new tests pass. Keep changes minimal."
rig worktree show latest
rig worktree apply latest
```

## Compare Two Agents on the Same Task

Configure multiple agents in `.rig/config.yaml` (see [Agents](agents.md)),
then run the same task through each. Each run is its own directory so the
outputs do not collide.

```bash
rig worktree run codex --task-file task.md
rig worktree run claude --task-file task.md
rig list
diff <(rig worktree show 20260504-1500-codex)  <(rig worktree show 20260504-1505-claude)
```

`task-file` keeps the prompt identical between runs.

## Manual / GUI Flow

Track work that happens outside any CLI Rig can launch. The `manual` runner
records the task and waits.

```yaml
# .rig/config.yaml
agents:
  design:
    runner: manual
```

```bash
rig run design --task "Update the toolbar in Figma. Export the SVG into ui/icons/."
# ... do the work in Figma ...
rig manual complete latest --result "Toolbar updated and SVG exported."
rig show latest
```

If the work is blocked or abandoned:

```bash
rig manual fail latest --error "Blocked on design review."
```

`complete` and `fail` only operate on runs currently in `waiting`, so a real
exec run is never overwritten by accident.

## Dry-Run Before Risk

`--dry-run` writes `task.md`, `command.json`, and `status.json` (status:
`created`) without launching the agent. Useful when you want to confirm the
exact argv Rig will execute.

```bash
rig run codex --task "Replace os.system with subprocess everywhere." --dry-run
cat .rig/runs/$(ls -1t .rig/runs | head -n1)/command.json
```

Then commit to the run:

```bash
rig run codex --task "Replace os.system with subprocess everywhere."
```

## Run Rig Through MCP

If your editor or chat tool speaks MCP, expose Rig as a server so the agent
can list runs, start new runs, and read captured patches without parsing CLI
text.

```bash
rig mcp serve
```

Or, with patch application enabled, only when you trust the connected agent:

```bash
RIG_MCP_ALLOW_APPLY=1 rig mcp serve
```

See [MCP Server](mcp.md) for the tool surface, resource URIs, and the
`RIG_MCP_ROOT` scope flag.

## Generate AGENTS.md / CLAUDE.md Snippets

`rig guide agents` prints a Markdown snippet you can paste into project
instruction files. With `--write`, Rig also stores the long-form policy at
`.rig/instructions/rig.md`, so your `AGENTS.md` stays small.

```bash
rig guide agents --target codex --write
rig guide agents --target claude --write --force
```

Rig never edits `AGENTS.md` or `CLAUDE.md` directly. You paste the snippet
once; the long-form policy lives under `.rig/`.

## Diagnose The Local Setup

Run before opening an issue or sharing a debug log:

```bash
rig env doctor --json | jq
rig env plan
rig env manager status
```

These commands are read-only. They report missing Rig files, required project
files declared in `.rig/env.yaml`, configured agent commands, and optional
asset managers — without installing anything.
