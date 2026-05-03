---
title: Command Reference
---

# Command Reference

## Common Flow

```bash
rig init
rig suggest "Review the current diff."
rig run codex --task "Review the current diff."
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
- `rig run [agent] --task "..." --dry-run`: create run artifacts and command
  metadata without executing the agent.
- `rig run [agent] --task "..." --json`: print the run outcome as structured JSON.
- `rig suggest "..." [--json]`: suggest whether to use `rig run` or
  `rig worktree run` without executing an agent.
- `rig list [--json]`: list recent runs.
- `rig show <run-id|latest> [--json]`: show run metadata and result.
- `rig worktree run [agent] --task "..."`: run an agent in an isolated worktree.
- `rig worktree show <run-id|latest>`: show run metadata and the captured patch.
- `rig worktree apply <run-id|latest>`: apply the captured worktree patch.
- `rig worktree prune`: remove Rig-created worktrees.
- `rig manual complete <run-id|latest>`: complete a waiting manual run.
- `rig manual fail <run-id|latest>`: fail a waiting manual run.
- `rig history complete <run-id|latest>`: complete a waiting manual run.
- `rig history fail <run-id|latest>`: fail a waiting manual run.
- `rig env doctor [--json]`: diagnose the local harness environment.
- `rig env plan`: show a read-only environment plan.
- `rig env bootstrap`: create missing Rig-owned environment files.
- `rig guide agents`: generate an `AGENTS.md` snippet.
- `rig mcp serve`: run Rig's MCP server over stdio.

## Run Options

Provide exactly one of `--task` or `--task-file`.

`--dry-run` writes the task, command preview, and status metadata without
starting the configured agent. Dry runs are useful for checking the command Rig
would execute.

`--json` is available on `run`, `list`, `show`, `suggest`, and `env doctor` for
scripts and MCP-style integrations that should not parse human text.

## Notes

- Worktree patches include untracked files that are not ignored by Git. Keep
  large generated directories in `.gitignore` before applying a patch.
- Agents can print `--- RIG RESULT ---`; Rig will keep only the text after that
  marker in `result.md` while preserving full stdout in `stdout.log`.
- `prompt_style: template` enables `prompt_template` with `{agent}`,
  `{task_path}`, `{task}`, and `{task_md}` placeholders.
- MCP tools expose the same run store and orchestrator as the CLI. The initial
  tool set is `rig_run`, `rig_list_runs`, `rig_list_agents`, `rig_suggest`,
  `rig_get_run`, `rig_get_result`, `rig_get_diff`, and `rig_apply_patch`.
- MCP also exposes the `rig_policy` prompt and `rig://policy` /
  `rig://agents-md` resources for agent policy and project instructions.
- MCP `cwd` values must stay under the server launch directory, or under
  `RIG_MCP_ROOT` when it is set. MCP `task_file` paths are resolved from `cwd`
  and must stay inside that project.
- MCP `rig_apply_patch` is disabled unless the server is started with
  `RIG_MCP_ALLOW_APPLY=1`.
- The legacy `rig history list`, `rig history show`, `rig history complete`,
  and `rig history fail` forms are normalized to the current `list`, `show`,
  and `manual` commands for compatibility.
