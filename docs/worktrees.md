---
title: Worktree Runs
description: Run an agent in an isolated Git worktree, capture the patch, review it, and apply when ready.
---

# Worktree Runs

Worktree runs execute an agent in an isolated Git worktree under
`.rig/worktrees/<run-id>/`. Rig captures the resulting patch as
`.rig/runs/<run-id>/diff.patch`, leaving the main working tree untouched.

This is the right choice when:

- The current working tree is dirty and you do not want the agent to touch it.
- The change is large enough that a review step before applying makes sense.
- You want to run the same task through multiple agents and compare patches.

For end-to-end recipes, see
[Recipes → Refactor in an Isolated Worktree](recipes.md#refactor-in-an-isolated-worktree).

## Run In A Worktree

```bash
rig worktree run codex --task "Make the requested change."
```

Rig creates `.rig/worktrees/<run-id>/`, runs the agent there, and writes the
captured patch to `.rig/runs/<run-id>/diff.patch`.

## Inspect The Patch

```bash
rig worktree show latest
rig worktree show 20260504-141500-codex
```

Output includes the run metadata and the captured patch, ready for review.

## Apply The Patch

```bash
rig worktree apply latest
```

`apply` runs `git apply` on the captured patch against the main working tree.
Conflicts are reported as `git apply` errors; resolve them with the usual
Git tooling.

<div class="callout callout-warn" markdown="1">
<span class="callout-title">Warning</span>
Worktree patches include untracked files that are not ignored by Git. Add
generated build artifacts (e.g. <code>node_modules</code>, <code>dist</code>,
caches) to <code>.gitignore</code> before applying patches, or you will commit
the agent's scratch directories.
</div>

## Iterate

If the patch is wrong, do not edit it by hand. Run again with a corrected
task; each attempt is its own run with its own diff.

```bash
rig worktree run codex --task "Try again. Keep behavior identical for the dry-run path."
rig worktree show latest
```

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
remove the run records under `.rig/runs/`, so the captured patches remain
inspectable.

## How It Differs From `rig run`

| | `rig run` | `rig worktree run` |
| --- | --- | --- |
| Where edits land | Current working tree | `.rig/worktrees/<run-id>/` |
| Captures `diff.patch` | No | Yes |
| Requires Git | Whatever the CLI requires | Yes (uses `git worktree`) |
| Apply step | N/A | Explicit `rig worktree apply` |

Both flows write the same artifact set under `.rig/runs/<run-id>/`. The only
extra file for worktree runs is `diff.patch`.

## When Not To Use Worktrees

- Read-only tasks (review, explain, suggest). A normal `rig run` is faster.
- CLIs that resolve paths relative to the calling shell rather than the
  process cwd. Worktree runs change cwd into `.rig/worktrees/<run-id>/`; if
  the CLI walks up to find the repo root, it should work fine — but verify
  with a small task first.
