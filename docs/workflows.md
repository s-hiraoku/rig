---
title: Workflows
description: How the parent agent should delegate work — normal runs, isolated worktree edits, manual runs, and environment checks. With decision rules.
---

# Workflows

Rig supports several delegation patterns. The parent agent picks one per task;
the human only needs to know the rules so they can override when the agent
chooses wrong. Concrete end-to-end examples live in [Recipes](recipes.md).

## Decision Guide

The parent agent should pick the first row that matches the task.

| Situation | Use | Why |
| --- | --- | --- |
| Read-only or low-risk task | `rig run` | Fastest Rig-backed path; full logs and history. |
| Need multiple independent answers to the same prompt | Native parent-agent subagents, then `rig run --parallel N` | Subagents can run in parallel with richer role/context control; Rig parallel is the fallback artifact-backed path. |
| Working tree is dirty | Native isolated subagent workspace, then `rig worktree run` | Prefer the parent agent's own isolation when it exists; Rig worktrees provide a portable fallback. |
| Large refactor or risky edit | Native isolated subagent workspace, then `rig worktree run` | Use Rig worktrees when the parent agent cannot isolate work itself or when a Rig patch artifact is useful. |
| GUI / web / external agent work | `manual` runner | Tracks task and result without launching a command. |
| Unsure | `rig suggest` | Read-only check that returns a recommendation. |

<div class="callout callout-tip" markdown="1">
<span class="callout-title">Tip</span>
When in doubt, the parent agent should call <code>rig_suggest</code> first.
It inspects the repo and returns a recommended mode without running anything.
</div>

## Normal Run

Use a normal run when the child agent can operate directly in the current
working tree.

The parent agent calls (CLI form shown for clarity):

```bash
rig run codex --task "Review the current diff."
rig show latest
```

Or over MCP:

```jsonc
// rig_run tool call
{ "agent": "codex", "task": "Review the current diff." }
```

Rig writes task, command metadata, stdout, stderr, result, and status under
`.rig/runs/<run-id>/`. The parent agent reads `result.md` and reports the
summary to the human.

`--dry-run` writes the run artifacts and command preview without executing
the child agent — useful when the parent agent wants to confirm the exact
argv it would launch.

For long delegated runs, the parent agent should choose a timeout explicitly:

```bash
rig run codex --task-file tasks/large-review.md --timeout-seconds 3600
```

This controls Rig's child-agent timeout. If the parent invokes Rig through a
shell tool with its own timeout, that outer timeout must also be long enough.

If the parent agent has native subagents, use those first for several
independent attempts. Give each subagent the same task, constraints, and
expected output, then synthesize the results for the human. Use
`--parallel N` when native subagents are unavailable or when the user wants
Rig-managed run artifacts:

```bash
rig run codex --task "Review this API design and list risks." --parallel 3
```

Each Rig-managed attempt gets its own run ID and result. Parallel runs are
best for review, analysis, ranking ideas, or comparing answers in parent
agents that do not have native subagents. Use explicit run IDs when reading
back results; `latest` only names one of the completed attempts.

## Suggested Run

When the parent agent is unsure whether the working tree is safe to touch:

```bash
rig suggest "Refactor the CLI command structure."
```

Or:

```jsonc
// rig_suggest tool call
{ "task": "Refactor the CLI command structure." }
```

The suggestion is advisory. Nothing is launched and nothing is applied. The
parent agent uses the recommendation to decide between `rig_run` and
`rig_run` with `worktree=true`.

## Isolated Worktree Run

For non-trivial edits the parent agent should isolate by default. If the
parent agent can launch native subagents in isolated workspaces, prefer that
path and ask each subagent to report its changes and verification. Use Rig
worktrees when native isolation is unavailable or when the user wants a
captured `.rig/runs/<run-id>/diff.patch` artifact:

```bash
rig worktree run codex --task "Make the requested change."
rig worktree show latest
# After human approval:
rig worktree apply latest
```

Or over MCP: `rig_run` with `worktree=true`, then `rig_get_diff`, then —
only after explicit human approval and only if the server allows it —
`rig_apply_patch`.

If the patch is wrong, the parent agent re-runs without losing earlier
attempts; each attempt is its own run with its own diff.

```bash
rig worktree run codex --task "Try again. The previous attempt missed the worktree path."
```

When done:

```bash
rig worktree prune
```

<div class="callout callout-warn" markdown="1">
<span class="callout-title">Warning</span>
Worktree patches include untracked files that are not ignored by Git. Add
generated build artifacts to <code>.gitignore</code> before applying.
</div>

## Manual Run

Use the `manual` runner when the work happens somewhere Rig should not launch
a command — a design tool, a chat client, an external system.

```yaml
agents:
  external:
    runner: manual
```

The parent agent (or the human directly) opens the run:

```bash
rig run external --task "Complete this in the external tool."
```

The run starts in `waiting`. When the work is done, complete it explicitly:

```bash
rig manual complete latest --result "Finished externally."
```

If the work is blocked or abandoned:

```bash
rig manual fail latest --error "Blocked in external review."
```

`complete` and `fail` only operate on runs currently in `waiting`, so a real
`exec` run is never overwritten by accident. The legacy `rig history complete`
/ `rig history fail` forms are normalized to `rig manual …` internally.

## Environment Setup
{: #environment-setup }

The CLI commands the human runs to keep the harness healthy. The parent agent
does not normally call these.

```bash
rig env doctor          # human-readable diagnostics
rig env doctor --json   # CI-friendly
rig env plan            # read-only setup plan
rig env bootstrap       # create missing Rig-owned files
rig env manager status  # check declared asset managers
rig guide agents        # generate AGENTS.md / CLAUDE.md snippet
```

`env bootstrap` creates only Rig-owned files. Rig does not install global
tools or third-party agent assets. `rig env doctor` statuses are `ok`,
`missing`, `optional`, and `warn`.

The `.rig/env.yaml` schema is documented in
[Configuration → Environment Configuration](configuration.md#environment-configuration).
