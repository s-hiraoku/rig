---
title: Workflows
---

# Workflows

Rig supports several ways to run or track agent work. Choose the workflow based
on how much isolation and review you need.

## Decision Guide

| Situation | Use | Why |
| --- | --- | --- |
| Small read-only or low-risk task | `rig run` | Fastest path with full logs and result history. |
| Existing working tree is dirty | `rig worktree run` | Keeps generated changes separate from current edits. |
| Large refactor or risky edit | `rig worktree run` | Captures a reviewable patch before applying it. |
| GUI, web, or external agent work | `manual` runner | Tracks the task and final result without launching a command. |
| Unsure which path fits | `rig suggest` | Inspects repo state and recommends a mode. |

## Normal Run

Use a normal run when the agent can operate directly in the current working
tree.

```bash
rig run codex --task "Review the current diff."
rig show latest
```

Rig writes the task, command metadata, stdout, stderr, result, and status under
`.rig/runs/<run-id>/`.

## Suggested Run

Use `rig suggest` before starting work when you want Rig to inspect the current
repository state.

```bash
rig suggest "Refactor the CLI command structure."
```

The suggestion is advisory. It never starts an agent and never applies a patch.

## Isolated Worktree Run

Use a worktree run when generated edits should be reviewed before they touch the
main working tree.

```bash
rig worktree run codex --task "Make the requested change."
rig worktree show latest
rig worktree apply latest
```

Worktree patches include untracked files that are not ignored by Git. Add large
generated directories to `.gitignore` before applying patches.

## Manual Run

Use the `manual` runner when work happens outside a command Rig can execute.

```yaml
agents:
  external:
    runner: manual
```

```bash
rig run external --task "Complete this in the external tool."
rig manual complete latest --result "Finished externally."
```

Manual runs start with status `waiting`. They must be completed or failed
explicitly.

## Environment Setup

Use environment commands to check the local harness before running agents.

```bash
rig env doctor
rig env plan
rig env bootstrap
rig guide agents
```

`env bootstrap` creates missing Rig-owned files only. Rig does not install
global tools or third-party agent assets.
