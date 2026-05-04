---
title: MCP Server
description: Expose Rig as MCP tools for parent agents that cannot call the CLI directly.
---

# MCP Server

Rig is CLI-first. For MCP-native or shell-restricted parent agents, run:

```bash
rig mcp serve
```

## Tools

| Tool | Purpose |
| --- | --- |
| `rig_delegate` | Delegate a task to a configured child agent. |
| `rig_patch_create` | Run a task in an isolated worktree and capture a patch. |
| `rig_history` | List recent runs. |
| `rig_history_show` | Read one run's metadata and result. |
| `rig_patch_show` | Read a captured `diff.patch`. |
| `rig_patch_apply` | Apply a reviewed patch. Disabled by default. |
| `rig_list_agents` | List configured child agents. |

The MCP tools use the same run store and artifacts as the CLI.

## Safety Defaults

`rig_patch_apply` is disabled unless the server starts with:

```bash
RIG_MCP_ALLOW_APPLY=1 rig mcp serve
```

Enable patch application only when the parent agent should be allowed to apply
reviewed patches after explicit human approval.

MCP `cwd` values are confined to the server launch directory by default. Set
`RIG_MCP_ROOT=/path/to/root` to allow repositories under a broader root.

## Connecting From An MCP Client

Most MCP clients accept a JSON shape like this:

```json
{
  "mcpServers": {
    "rig": {
      "type": "stdio",
      "command": "rig",
      "args": ["mcp", "serve"],
      "env": {}
    }
  }
}
```

For local development from a Rig checkout:

```json
{
  "mcpServers": {
    "rig": {
      "type": "stdio",
      "command": "uv",
      "args": ["--directory", "/path/to/rig", "run", "rig", "mcp", "serve"],
      "env": {}
    }
  }
}
```

To allow several repositories under one parent directory:

```json
{
  "mcpServers": {
    "rig": {
      "type": "stdio",
      "command": "rig",
      "args": ["mcp", "serve"],
      "env": {
        "RIG_MCP_ROOT": "/Users/me/code"
      }
    }
  }
}
```

To allow patch application:

```json
{
  "mcpServers": {
    "rig": {
      "type": "stdio",
      "command": "rig",
      "args": ["mcp", "serve"],
      "env": {
        "RIG_MCP_ALLOW_APPLY": "1"
      }
    }
  }
}
```

## Client Examples

Cursor project config can live in `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "rig": {
      "type": "stdio",
      "command": "rig",
      "args": ["mcp", "serve"],
      "env": {
        "RIG_MCP_ROOT": "${workspaceFolder}"
      }
    }
  }
}
```

Claude Code can add a local stdio server from the command line:

```bash
claude mcp add --transport stdio rig -- rig mcp serve
```

## Inspecting MCP Calls

MCP-driven runs land in the same `.rig/runs/<run-id>/` layout as CLI runs,
including `command.json` showing the resolved argv.
