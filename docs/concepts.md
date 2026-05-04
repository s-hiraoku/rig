---
title: Core Concepts
description: Roles, runs, artifacts, and patch runs.
---

# Core Concepts

## Roles

| Role | What they do |
| --- | --- |
| Human | Asks a parent AI agent for help and reviews results or patches. |
| Parent agent | Calls Rig through CLI or MCP and reports artifacts back to the human. |
| Child agent | The configured coding CLI Rig launches, such as `codex exec`. |

## Run

A run is one delegated child-agent execution. Runs live under:

```txt
.rig/runs/<run-id>/
```

Typical artifacts:

- `task.md`
- `command.json`
- `stdout.log`
- `stderr.log`
- `result.md`
- `status.json`
- `diff.patch` for patch runs

## Delegate Run

`rig delegate` executes a child agent in the current working tree and records
artifacts.

## Patch Run

`rig patch create` executes a child agent in an isolated Git worktree and
captures its changes as `diff.patch`. The main working tree stays unchanged
until `rig patch apply`.

## MCP

`rig mcp serve` exposes the same core operations as MCP tools:
`rig_delegate`, `rig_patch_create`, `rig_history`, `rig_history_show`,
`rig_patch_show`, `rig_patch_apply`, and `rig_list_agents`.
