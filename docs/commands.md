# Command Reference

## Common Flow

```bash
rig init
rig run --task "Review the current diff."
rig list
rig show latest
```

## Worktree Flow

```bash
rig worktree run codex --task "Make the requested change."
rig worktree show latest
rig worktree apply latest
```

## Commands

- `rig init`: initialize `.rig/`.
- `rig run [agent] --task "..."`: run an agent in the current working tree. If
  `[agent]` is omitted, Rig uses `default_agent`.
- `rig run [agent] --task-file task.md`: run an agent with a task file.
- `rig list [--json]`: list recent runs.
- `rig show <run-id|latest> [--json]`: show run metadata and result.
- `rig worktree run [agent] --task "..."`: run an agent in an isolated worktree.
- `rig worktree show <run-id|latest>`: show the captured worktree patch.
- `rig worktree apply <run-id|latest>`: apply the captured worktree patch.
- `rig worktree prune`: remove Rig-created worktrees.
- `rig history complete <run-id|latest>`: complete a waiting manual run.
- `rig history fail <run-id|latest>`: fail a waiting manual run.
- `rig env doctor`: diagnose the local harness environment.
- `rig env plan`: show a read-only environment plan.
- `rig env bootstrap`: create missing Rig-owned environment files.
- `rig guide agents`: generate an `AGENTS.md` snippet.
