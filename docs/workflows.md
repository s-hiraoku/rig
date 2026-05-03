---
title: Workflows
description: Decision guide for choosing between rig run, rig worktree run, manual runs, and environment setup.
---

# Workflows

Rig supports several ways to run or track agent work. Choose the workflow
based on how much isolation and review you need. For full end-to-end
examples, see [Recipes](recipes.md).

## Decision Guide

| Situation | Use | Why |
| --- | --- | --- |
| Small read-only or low-risk task | `rig run` | Fastest path with full logs and result history. |
| Working tree is dirty | `rig worktree run` | Keeps generated changes separate from current edits. |
| Large refactor or risky edit | `rig worktree run` | Captures a reviewable patch before applying it. |
| GUI, web, or external agent work | `manual` runner | Tracks the task and final result without launching a command. |
| Unsure which path fits | `rig suggest` | Inspects repo state and recommends a mode. |

<div class="callout callout-tip" markdown="1">
<span class="callout-title">Tip</span>
When in doubt, start with <code>rig suggest "..."</code>. It is read-only — it
inspects the repo and prints a recommendation without ever launching the
agent.
</div>

## Normal Run

Use a normal run when the agent can operate directly in the current working
tree.

```bash
rig run codex --task "Review the current diff."
rig show latest
```

Rig writes the task, command metadata, stdout, stderr, result, and status
under `.rig/runs/<run-id>/`. Add `--json` to receive structured output for
scripts:

```bash
rig run codex --task "Review the current diff." --json | jq '.status'
```

`--dry-run` writes the run artifacts and command preview without executing
the agent — useful for confirming the exact argv Rig would launch.

## Suggested Run

Use `rig suggest` before starting work when you want Rig to inspect the
current repository state.

```bash
rig suggest "Refactor the CLI command structure."
```

The suggestion is advisory. It never starts an agent and never applies a
patch. Use `--json` for scripted use:

```bash
rig suggest "..." --json | jq -r '.recommendation'
```

The output includes the recommended command parts, the reasons Rig produced
that recommendation, and observations about the current repo state.

## Isolated Worktree Run

Use a worktree run when generated edits should be reviewed before they touch
the main working tree.

```bash
rig worktree run codex --task "Make the requested change."
rig worktree show latest
rig worktree apply latest
```

If the patch is wrong, iterate without losing earlier attempts; each attempt
is its own run with its own diff.

```bash
rig worktree run codex --task "Try again. The previous patch missed the worktree path."
```

Clean up Rig-owned worktrees when you are done:

```bash
rig worktree prune
```

<div class="callout callout-warn" markdown="1">
<span class="callout-title">Warning</span>
Worktree patches include untracked files that are not ignored by Git. Add
generated build artifacts to <code>.gitignore</code> before applying patches.
</div>

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
explicitly:

```bash
rig manual fail latest --error "Blocked in external review."
```

The legacy `rig history complete` / `rig history fail` forms still work but
are normalized to `rig manual …` internally.

## Environment Setup

Use environment commands to check the local harness before running agents.

```bash
rig env doctor          # human-readable diagnostics
rig env doctor --json   # structured output for CI
rig env plan            # read-only setup plan
rig env bootstrap       # create missing Rig-owned files
rig env manager status  # check declared asset managers
rig guide agents        # generate AGENTS.md / CLAUDE.md snippet
```

`env bootstrap` creates only Rig-owned files. Rig does not install global
tools or third-party agent assets. `rig env doctor` statuses are `ok`,
`missing`, `optional`, and `warn`.

See [Configuration → Environment Configuration](configuration.md#environment-configuration)
for the schema of `.rig/env.yaml`.
