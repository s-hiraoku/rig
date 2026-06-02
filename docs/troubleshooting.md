---
title: Troubleshooting
description: Fix common Rig setup and run issues.
---

# Troubleshooting

## Rig Is Not Initialized

Run:

```bash
rig init
```

## The Parent Agent Is Not Using Rig

Make sure `AGENTS.md` or your parent agent's project instructions reference:

```txt
.rig/instructions/rig.md
```

`rig init` prints a ready-to-paste snippet.

## No Runs Found

Start a delegated run first:

```bash
rig delegate codex --task "Review the current diff."
```

Then inspect it:

```bash
rig history
rig history show latest
```

## Patch Apply Is Disabled Over MCP

Start the server with:

```bash
RIG_MCP_ALLOW_APPLY=1 rig mcp serve
```

Only enable this for clients that should be allowed to apply reviewed patches.

## Command Not Found

`rig doctor` checks configured child-agent commands. Install the missing CLI or
edit `.rig/config.yaml`.

For Antigravity CLI, use:

```yaml
agents:
  antigravity:
    command: agy
    args: [-p]
    prompt_style: task
```

If an older Rig config still has a `gemini` agent, update that agent to the
Antigravity command above or rename it to `antigravity`.

For image generation through Antigravity, add a separate `antigravity-image`
agent with `prompt_style: template`; see [Agents](agents.md#examples). The
template should tell Antigravity to save image files in the workspace and print
only file paths and errors in the Rig result.
