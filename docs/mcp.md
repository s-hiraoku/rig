---
title: MCP Server
---

# MCP Server

Rig can run an MCP server over stdio:

```bash
rig mcp serve
```

MCP-capable agents can use the server to start runs, list run history, inspect
results, and read captured worktree diffs without parsing CLI output.

## Initial Tools

- `rig_run`
- `rig_list_runs`
- `rig_list_agents`
- `rig_suggest`
- `rig_get_run`
- `rig_get_result`
- `rig_get_diff`
- `rig_apply_patch`

## Resources and Prompts

The MCP server also exposes:

- `rig_policy` prompt
- `rig://policy` resource
- `rig://agents-md` resource

## Safety Defaults

MCP calls are limited to the server's launch directory by default. Set
`RIG_MCP_ROOT=/path/to/root` when the server must operate on repositories under
a broader root.

Relative `task_file` values are resolved from the selected `cwd`, and must stay
inside that project.

`rig_apply_patch` is disabled unless the server starts with:

```bash
RIG_MCP_ALLOW_APPLY=1 rig mcp serve
```

Enable patch application only when the connected agent should be allowed to
apply reviewed worktree patches after explicit user instruction.
