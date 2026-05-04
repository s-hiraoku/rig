---
title: MCP Server
description: Run Rig as an MCP server so MCP-aware parent agents (Cursor, Claude Code, …) can call structured tools instead of parsing CLI text.
---

# MCP Server

Rig can run an MCP server over stdio:

```bash
rig mcp serve
```

This is how MCP-aware parent agents — Cursor, Claude Code, anything else
with an MCP client — reach Rig. They call structured tools (`rig_run`,
`rig_list_runs`, `rig_get_diff`, …) instead of parsing CLI text.

## Tools

| Tool | Purpose |
| --- | --- |
| `rig_run` | Start a new run. Mirrors `rig run`. |
| `rig_list_runs` | List recent runs. Mirrors `rig list`. |
| `rig_list_agents` | List configured child agents from `.rig/config.yaml`. |
| `rig_suggest` | Recommend `rig_run` vs `rig_run` with `worktree=true` for a task. |
| `rig_get_run` | Read run metadata. |
| `rig_get_result` | Read `result.md`. |
| `rig_get_diff` | Read `diff.patch` for a worktree run. |
| `rig_apply_patch` | Apply a captured worktree patch. **Disabled by default.** |

The orchestrator and run store backing these tools are exactly the same as
the ones the CLI uses. `rig_run` also accepts `parallel`; values greater than
1 return a top-level `runs` list with one structured outcome per run.
Parallel worktree runs are rejected.

## Resources And Prompts

The MCP server also exposes:

- `rig_policy` — a prompt the parent agent can fetch to learn Rig's usage
  policy.
- `rig://policy` — the same policy as a resource URI.
- `rig://agents-md` — the project's `AGENTS.md` content (when present), so
  the parent can pull project-specific agent guidance over the same channel.

## Safety Defaults
{: #safety-defaults }

MCP calls are confined to the server's launch directory by default. To
operate on repositories under a broader root:

```bash
RIG_MCP_ROOT=/Users/me/code rig mcp serve
```

`cwd` values supplied by the parent agent must resolve inside `RIG_MCP_ROOT`.
Relative `task_file` paths are resolved from the selected `cwd` and must
also stay inside that project.

`rig_apply_patch` is disabled unless the server starts with:

```bash
RIG_MCP_ALLOW_APPLY=1 rig mcp serve
```

Enable patch application only when the parent agent should be allowed to
apply reviewed worktree patches after explicit human approval. The default —
disabled — is intentional: a remote MCP client should not modify your
working tree without an out-of-band opt-in.

## Environment Variables

| Variable | Effect |
| --- | --- |
| `RIG_MCP_ROOT` | Allow MCP `cwd` and `task_file` paths to resolve under this root. Defaults to the server launch directory. |
| `RIG_MCP_ALLOW_APPLY` | Set to `1` to enable `rig_apply_patch`. Defaults to disabled. |

## Connecting From An MCP Client

The exact wiring depends on the client. The pattern is:

1. Add a server entry that runs `rig mcp serve` over stdio.
2. (Optional) set `RIG_MCP_ROOT` if the client needs to operate on multiple
   repositories.
3. (Optional, opt-in) set `RIG_MCP_ALLOW_APPLY=1` when patch application is
   intentional.

See [Recipes → Run Rig Through MCP](recipes.md#run-rig-through-mcp) for a
short end-to-end example.

## Inspecting MCP Calls

MCP-driven runs land in the same `.rig/runs/<run-id>/` layout as CLI runs,
including `command.json` showing the resolved argv. There is no separate
"MCP run" surface — every MCP `rig_run` call produces a normal run that
`rig list` and `rig show` can read.

This is also why audit and debugging stay simple: whether the parent agent
spoke to Rig over MCP or via the CLI, the artifacts on disk look the same.
