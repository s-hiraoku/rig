---
title: Worktree Runs
---

# Worktree Runs

Worktree runs execute an agent in an isolated Git worktree under
`.rig/worktrees/<run-id>/`.

This is useful when you want an agent to edit files without touching the main
working tree immediately.

## Run in a Worktree

```bash
rig worktree run codex --task "Make the requested change."
```

Rig captures the resulting patch as:

```txt
.rig/runs/<run-id>/diff.patch
```

## Inspect the Patch

```bash
rig worktree show latest
```

## Apply the Patch

```bash
rig worktree apply latest
```

Review the patch before applying it. Worktree patches include untracked files
that are not ignored by Git, so large generated directories should be listed in
`.gitignore`.

## Clean Up Worktrees

```bash
rig worktree prune
```
