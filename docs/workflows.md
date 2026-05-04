---
title: Workflows
description: When to use delegate runs, patch runs, history inspection, and doctor.
---

# Workflows

Rig has two execution workflows.

## Delegate

Use `rig delegate` for read-only tasks, reviews, explanations, and low-risk
work where the child agent can run in the current working tree.

```bash
rig delegate codex --task "Review the current diff."
rig history show latest
```

Rig records the task, command, stdout, stderr, result, and status under
`.rig/runs/<run-id>/`.

## Patch

Use `rig patch create` when the child agent may edit files, the change is
non-trivial, or the current working tree should stay untouched until review.

```bash
rig patch create codex --task "Make the requested change."
rig patch show latest
rig patch apply latest
```

The child agent runs in an isolated Git worktree under `.rig/worktrees/`.
Rig captures the resulting diff as `.rig/runs/<run-id>/diff.patch`.

## History

Use history commands when a human or parent agent needs to inspect what
happened:

```bash
rig history
rig history show latest
```

`history show` prints metadata, artifact paths, and `result.md`. Failed runs
also show `stderr.log`.

## Setup Check

Use `rig doctor` when setup looks wrong:

```bash
rig doctor
rig doctor --json
```

It checks Git, `.rig/config.yaml`, `.rig/runs/`, `.rig/instructions/rig.md`,
`AGENTS.md`, and configured child-agent commands.
