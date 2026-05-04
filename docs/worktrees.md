---
title: Worktree Runs
description: Have the parent agent run a child agent in an isolated Git worktree, capture the patch, and apply it only after human review.
---

# Worktree Runs

A worktree run executes the child agent inside an isolated Git worktree
under `.rig/worktrees/<run-id>/`. Rig captures the resulting patch as
`.rig/runs/<run-id>/diff.patch`, leaving the main working tree untouched
until you approve.

This is the right choice when:

- The current working tree is dirty and you don't want the child agent to
  touch it.
- The change is large enough that a review step before applying makes sense.
- You want to compare patches from different child agents on the same task.

For end-to-end recipes, see
[Recipes → Refactor in an Isolated Worktree](recipes.md#refactor-in-an-isolated-worktree).

## Run In A Worktree

The parent agent calls `rig_run` with `worktree=true`, or:

```bash
rig worktree run codex --task "Make the requested change."
```

Rig creates `.rig/worktrees/<run-id>/`, runs the child agent there, and
writes the captured patch to `.rig/runs/<run-id>/diff.patch`.

## Inspect The Patch

```bash
rig worktree show latest
rig worktree show 20260504-141500-codex
```

Output includes the run metadata and the captured patch. The parent agent
typically reads this and summarizes for you; you can also read it directly.

## Apply The Patch

After human approval:

```bash
rig worktree apply latest
```

`apply` runs `git apply` on the captured patch against the main working
tree. Conflicts are reported as `git apply` errors; resolve them with the
usual Git tooling.

Over MCP, this maps to `rig_apply_patch`, which is **disabled by default**.
The parent agent can call it only when you started the server with
`RIG_MCP_ALLOW_APPLY=1`. See
[MCP Server → Safety Defaults](mcp.md#safety-defaults).

<div class="callout callout-warn" markdown="1">
<span class="callout-title">Warning</span>
Worktree patches include untracked files that are not ignored by Git. Add
generated build artifacts (e.g. <code>node_modules</code>, <code>dist</code>,
caches) to <code>.gitignore</code> before applying patches, or you will
commit the child agent's scratch directories.
</div>

## Iterate

If the patch is wrong, ask the parent agent to try again with a corrected
task. Each attempt is its own run with its own diff — earlier attempts
remain inspectable.

> "That diff was too aggressive. Try again. Keep behavior identical for the
> dry-run path."

You can compare attempts by run ID:

```bash
rig worktree show 20260504-141500-codex > /tmp/a.patch
rig worktree show 20260504-142000-codex > /tmp/b.patch
diff /tmp/a.patch /tmp/b.patch
```

## Clean Up

```bash
rig worktree prune
```

`prune` removes Rig-created directories under `.rig/worktrees/`. It does not
touch the run records under `.rig/runs/`, so the captured patches remain
inspectable.

## How It Differs From `rig run`

| | `rig run` | `rig worktree run` |
| --- | --- | --- |
| Where edits land | Current working tree | `.rig/worktrees/<run-id>/` |
| Captures `diff.patch` | No | Yes |
| Requires Git | Whatever the child agent requires | Yes (uses `git worktree`) |
| Apply step | N/A | Explicit `rig worktree apply` |

Both flows write the same artifact set under `.rig/runs/<run-id>/`. The only
extra file for worktree runs is `diff.patch`.

`rig run --parallel N` is available for normal runs when you want multiple
independent answers to the same task. Parallel worktree runs are not supported
because `git worktree` operations share repository locks; start separate
worktree runs and compare explicit run IDs instead.

If the parent agent already supports native subagents with isolated
workspaces, prefer that native isolation for parallel edit attempts. Use Rig
worktrees as the portable fallback, or when the captured `diff.patch` artifact
is the reason for using Rig.

## When Not To Use Worktrees

- Read-only tasks (review, explain, suggest). A normal `rig run` is faster.
- CLIs that resolve paths relative to the calling shell rather than the
  process cwd. Worktree runs change cwd into `.rig/worktrees/<run-id>/`; if
  the CLI walks up to find the repo root, it should work fine — but verify
  with a small task first.
