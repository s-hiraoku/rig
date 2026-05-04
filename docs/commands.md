---
title: Command Reference
description: Compact reference of Rig's current CLI.
---

# Command Reference

Rig's CLI is intentionally small. Parent AI agents normally call these commands
for you, and humans use them for setup, debugging, audit, and patch review.

## Core Flow

```bash
rig init
rig delegate codex --task "Review the current diff."
rig history
rig history show latest
```

## Patch Flow

```bash
rig patch create codex --task "Make the requested change."
rig patch show latest
rig patch apply latest
rig patch prune
```

## Commands

| Command | Purpose |
| --- | --- |
| `rig init` | Create `.rig/config.yaml`, `.rig/instructions/rig.md`, and `.rig/runs/`. |
| `rig init --reset config` | Back up and recreate `.rig/config.yaml`. |
| `rig init --reset instructions` | Back up and recreate `.rig/instructions/rig.md`. |
| `rig init --reset all` / `--force` | Reset both Rig-owned generated files. |
| `rig delegate [agent] --task "..."` | Delegate a task to a configured child agent. |
| `rig delegate [agent] --task-file task.md` | Delegate a task read from a file. |
| `rig delegate [agent] --task "..." --dry-run` | Write artifacts and command metadata without executing. |
| `rig delegate [agent] --task "..." --json` | Print structured run outcome. |
| `rig delegate [agent] --task "..." --timeout-seconds N` | Override the configured timeout for one run. |
| `rig patch create [agent] --task "..."` | Run in an isolated worktree and capture `diff.patch`. |
| `rig patch show <run-id\|latest>` | Show metadata and captured patch. |
| `rig patch apply <run-id\|latest>` | Apply a reviewed patch using `git apply`. |
| `rig patch prune` | Remove Rig-created worktrees. |
| `rig history [--json]` | List recent runs. |
| `rig history show <run-id\|latest> [--json]` | Show run metadata and result. |
| `rig doctor [--json]` | Diagnose the local Rig setup. |
| `rig mcp serve` | Run the optional MCP server over stdio. |

## Notes

- Provide exactly one of `--task` or `--task-file`.
- `latest` means the most recent readable run under `.rig/runs/`.
- Patch runs keep generated edits out of the main working tree until
  `rig patch apply`.
- `rig patch apply` should only be called after reviewing `rig patch show`.
- Child agents can print `--- RIG RESULT ---`; Rig keeps only the text after
  that marker in `result.md`.

## See Also

- [Getting Started](getting-started.md)
- [Workflows](workflows.md)
- [Run Artifacts](artifacts.md)
- [MCP Server](mcp.md)
