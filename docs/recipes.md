---
title: Recipes
description: End-to-end examples — what to ask your AI, what Rig does behind the scenes, and how to review the result.
---

# Recipes

Each recipe is structured as:

- **Ask** — the natural-language prompt to give your parent AI.
- **Behind the scenes** — what the parent agent calls in Rig.
- **Review** — what to look at after.

Setup assumed: Rig installed, `rig init` run in the project, and the parent
agent has Rig usage policy via `AGENTS.md` / `CLAUDE.md`. See
[Getting Started](getting-started.md).

## Review The Current Diff

**Ask:**

> "Review the staged and unstaged diff. Flag bugs, regressions, and risky
> behavior changes. End the response with a `--- RIG RESULT ---` marker
> followed by a one-paragraph summary."

**Behind the scenes:** the parent agent calls `rig_run` (MCP) or
`rig run codex --task "…"`. Rig writes `task.md`, runs the child agent, and
captures `result.md`.

**Review:** ask the agent to read `result.md` to you, or check it directly:

```bash
rig list
rig show latest
```

The `--- RIG RESULT ---` marker keeps `result.md` clean even if the child
agent printed verbose logs (full stdout is preserved in `stdout.log`). See
[Run Artifacts → Result Extraction](artifacts.md#result-extraction).

## Refactor In An Isolated Worktree
{: #refactor-in-an-isolated-worktree }

**Ask:**

> "Extract the worktree helper out of `cli.py` into `rig/worktree_cli.py`.
> Keep behavior identical. Use a worktree — this is non-trivial."

**Behind the scenes:** the parent agent calls `rig_run` with `worktree=true`,
or `rig worktree run codex --task "…"`. The child agent edits files inside
`.rig/worktrees/<run-id>/`. Rig captures the resulting patch as
`.rig/runs/<run-id>/diff.patch`.

**Review:** ask the agent to walk you through the patch, or look at it
yourself:

```bash
rig worktree show latest
```

If the patch is right, approve it; the parent agent calls `rig worktree apply
latest`. If it's wrong, ask the agent to try again — each attempt is its own
run, so previous attempts stay inspectable.

> "That diff looked too aggressive. Try again, keep behavior identical for
> the dry-run path."

When you're done iterating:

```bash
rig worktree prune
```

<div class="callout callout-warn" markdown="1">
<span class="callout-title">Warning</span>
Worktree patches include untracked files that are not ignored by Git. Make
sure generated artifacts (<code>node_modules</code>, <code>dist</code>,
caches) are in <code>.gitignore</code> before approving the apply.
</div>

## Decide Before Running

When the working tree is messy or the change feels uncertain:

**Ask:**

> "Before you start, use `rig_suggest` and tell me whether you'd run this
> directly or in a worktree."

**Behind the scenes:** the parent agent calls `rig_suggest` (MCP) or
`rig suggest "…"`. The tool inspects repo state and returns a recommendation
without launching anything.

**Review:** the agent reports the recommendation; you confirm or override
before any actual run starts.

## Add Test Coverage Before Touching Code

Two-step delegation; each step is its own run.

**Ask 1:**

> "Add failing pytest cases for `tests/test_run_store.py` covering the
> dry-run path. Don't modify `rig/run_store.py`. Use a worktree."

After review and apply:

**Ask 2:**

> "Now make those new tests pass. Keep changes minimal. Worktree again."

Two distinct run IDs, two distinct diffs. If implementation step goes wrong,
the green-tests commit still stands.

## Compare Two Child Agents On The Same Task
{: #compare-two-child-agents-on-the-same-task }

When you want a second opinion from a different model:

**Ask:**

> "Run this same task through both `codex` and `claude`. Use a worktree for
> each so I can compare diffs."

**Behind the scenes:** the parent agent runs `rig worktree run codex
--task-file task.md` and `rig worktree run claude --task-file task.md`.
Identical task file, two separate run directories.

**Review:**

```bash
rig list
diff <(rig worktree show <codex-run-id>)  <(rig worktree show <claude-run-id>)
```

`task-file` keeps the prompts byte-identical between runs.

## Manual / GUI Flow

When the work happens somewhere Rig can't launch a command — Figma, a web
console, a notebook in another tab.

**Configure once:**

```yaml
agents:
  design:
    runner: manual
```

**Ask:**

> "Track that I'm updating the toolbar in Figma. Open a manual run."

**Behind the scenes:** the parent agent runs
`rig run design --task "Update the toolbar in Figma. Export the SVG."` and
the run starts in `waiting`.

**Then, after you finish in Figma:**

> "I'm done. Mark the run complete with this summary: 'Toolbar updated and
> SVG exported.'"

The agent runs `rig manual complete latest --result "…"`. Or
`rig manual fail latest --error "…"` if the work was blocked.

`complete` and `fail` only operate on `waiting` runs, so this never overwrites
an `exec` run by accident.

## Dry-Run Before Risk

Before an edit you're nervous about, ask the parent agent to dry-run first:

**Ask:**

> "Use `--dry-run` to show me exactly what command Rig would launch for this
> task before actually running it."

**Behind the scenes:** the parent agent calls `rig_run` with `dry_run=true`,
or `rig run codex --task "…" --dry-run`. Rig writes `task.md`,
`command.json`, and `status.json` (status: `created`) but does not start the
child agent.

**Review:**

```bash
cat .rig/runs/$(ls -1t .rig/runs | head -n1)/command.json
```

The last entry of `args` is the resolved prompt. If it looks right, ask the
agent to run for real.

## Run Rig Through MCP
{: #run-rig-through-mcp }

If your parent agent speaks MCP, expose Rig as a server so it can call
structured tools instead of parsing CLI text:

```bash
rig mcp serve
```

With patch application enabled, only when you trust the parent agent and
your client:

```bash
RIG_MCP_ALLOW_APPLY=1 rig mcp serve
```

See [MCP Server](mcp.md) for the tool surface, resource URIs, and the
`RIG_MCP_ROOT` scope flag.

## Generate AGENTS.md / CLAUDE.md Snippets

This is the one piece of CLI you do type yourself, once per project, so the
parent agent learns to use Rig:

```bash
rig guide agents --target codex --write
rig guide agents --target claude --write --force
```

`--write` produces `.rig/instructions/rig.md` (the long-form policy) and
prints the short snippet to paste into `AGENTS.md` / `CLAUDE.md`. Rig never
edits those files for you.

## Diagnose The Local Setup

Before opening an issue or sharing a debug log:

```bash
rig env doctor --json | jq
rig env plan
rig env manager status
```

These commands are read-only. They report missing Rig files, required project
files declared in `.rig/env.yaml`, configured agent commands, and optional
asset managers — without installing anything.
