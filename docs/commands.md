---
title: Command Reference
description: Compact reference of every Rig CLI command. The parent agent invokes most of these on your behalf; this page is for setup, debugging, and audit.
---

# Command Reference

This page is a compact reference. For scenario-based guidance, start with
[Workflows](workflows.md) or [Recipes](recipes.md).

<div class="callout" markdown="1">
<span class="callout-title">Who runs these?</span>
In day-to-day use, the parent AI agent calls these commands (or the
equivalent MCP tools). You'll mostly type them yourself for first-time setup,
debugging, and audit — see <a href="getting-started.html">Getting Started →
Appendix B</a>.
</div>

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

### Setup

| Command | Purpose |
| --- | --- |
| `rig init` | Initialize `.rig/`. |
| `rig init --reset config` | Back up and recreate `.rig/config.yaml`. |
| `rig init --reset env` | Back up and recreate `.rig/env.yaml`. |
| `rig init --reset all` / `--force` | Reset both. |
| `rig guide agents [--target all,codex,claude] [--write] [--force]` | Generate AGENTS.md / CLAUDE.md / skill references and (with `--write`) `.rig/instructions/rig.md`. |

### Run

| Command | Purpose |
| --- | --- |
| `rig run [agent] --task "..."` | Run a child agent in the current working tree. Falls back to `default_agent`. |
| `rig run [agent] --task-file task.md` | Run with a task read from a file. |
| `rig run [agent] --task "..." --dry-run` | Write run artifacts and command preview without executing the child agent. |
| `rig run [agent] --task "..." --json` | Print the run outcome as JSON. |
| `rig suggest "..." [--json]` | Recommend `rig run` vs `rig worktree run` without executing. |

### Inspect

| Command | Purpose |
| --- | --- |
| `rig list [--json]` | List recent runs. |
| `rig show <run-id|latest> [--json]` | Show run metadata and result. |
| `rig worktree show <run-id|latest>` | Show metadata and the captured patch. |

### Worktree

| Command | Purpose |
| --- | --- |
| `rig worktree run [agent] --task "..."` | Run in an isolated worktree. |
| `rig worktree apply <run-id|latest>` | Apply the captured patch with `git apply`. |
| `rig worktree prune` | Remove Rig-created worktrees. |

### Manual

| Command | Purpose |
| --- | --- |
| `rig manual complete <run-id|latest> --result "..."` | Complete a `waiting` manual run. |
| `rig manual complete <run-id|latest> --result-file result.md` | Same, from a file. |
| `rig manual fail <run-id|latest> --error "..."` | Fail a `waiting` manual run. |
| `rig manual fail <run-id|latest> --error-file error.txt` | Same, from a file. |
| `rig history complete <...>` / `rig history fail <...>` | Legacy aliases. |

### Environment

| Command | Purpose |
| --- | --- |
| `rig env doctor [--json]` | Diagnose the local harness environment. |
| `rig env plan` | Read-only environment plan. |
| `rig env bootstrap` | Create missing Rig-owned environment files. |
| `rig env manager status [--json]` | Show configured agent asset manager status. |

### MCP

| Command | Purpose |
| --- | --- |
| `rig mcp serve` | Run the MCP server over stdio. See [MCP Server](mcp.md). |

## Run Options

Provide exactly one of `--task` or `--task-file`. Passing both, or passing
neither, is an error.

`--dry-run` writes the task, command preview, and status metadata without
starting the child agent. Dry runs use status `created`.

`--json` is available on `run`, `list`, `show`, `suggest`, and `env doctor`
for scripts and MCP-style integrations that should not parse human text.

## Run IDs

Run IDs follow `YYYYMMDD-HHMMSS-<agent>` and are stable for the lifetime of
the run directory. Pass `latest` to commands that accept a run ID to refer
to the most recent run.

## Notes

- Worktree patches include untracked files that are not ignored by Git. Keep
  large generated directories in `.gitignore` before applying a patch.
- Child agents can print `--- RIG RESULT ---`; Rig will keep only the text
  after that marker in `result.md` while preserving full stdout in
  `stdout.log`.
- `prompt_style: template` enables `prompt_template` with `{agent}`,
  `{task_path}`, `{task}`, and `{task_md}` placeholders. See
  [Prompt Styles](prompts.md).
- MCP tools expose the same run store and orchestrator as the CLI. The
  initial tool set is `rig_run`, `rig_list_runs`, `rig_list_agents`,
  `rig_suggest`, `rig_get_run`, `rig_get_result`, `rig_get_diff`, and
  `rig_apply_patch`. See [MCP Server](mcp.md).
- MCP also exposes the `rig_policy` prompt and `rig://policy` /
  `rig://agents-md` resources for agent policy and project instructions.
- MCP `cwd` values must stay under the server launch directory, or under
  `RIG_MCP_ROOT` when it is set. MCP `task_file` paths are resolved from
  `cwd` and must stay inside that project.
- MCP `rig_apply_patch` is disabled unless the server is started with
  `RIG_MCP_ALLOW_APPLY=1`.
- The legacy `rig history list`, `rig history show`, `rig history complete`,
  and `rig history fail` forms are normalized to the current `list`, `show`,
  and `manual` commands for compatibility.

## See Also

- [Configuration](configuration.md) — `.rig/config.yaml` and `.rig/env.yaml`.
- [Agents](agents.md) — per-CLI child agent configurations.
- [Prompt Styles](prompts.md) — what Rig sends to the child agent.
- [Run Artifacts](artifacts.md) — what Rig writes to disk.
