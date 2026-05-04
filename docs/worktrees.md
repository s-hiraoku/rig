---
title: Patch Runs
description: How Rig uses Git worktrees to create reviewable patches.
---

# Patch Runs

The user-facing command is `rig patch`. Internally, Rig uses Git worktrees to
keep generated edits out of the main working tree.

```bash
rig patch create codex --task "Make the requested change."
rig patch show latest
rig patch apply latest
rig patch prune
```

Use patch runs for file edits, risky changes, dirty working trees, and any task
where the human should review the diff before applying it.

Patch runs write `diff.patch` under the run directory:

```txt
.rig/runs/<run-id>/diff.patch
```

`rig patch apply` uses `git apply`. Review `rig patch show` first.
