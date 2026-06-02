---
title: Recipes
description: Short examples for parent agents and humans using Rig.
---

# Recipes

## Review The Current Diff

Ask your parent agent:

> Review the current diff through Rig and flag risky behavior changes.

Behind the scenes:

```bash
rig delegate codex --task "Review the current diff and flag risky behavior changes."
rig history show latest
```

## Make A Reviewable Edit

Ask:

> Make the requested change through Rig as a patch. Show me the patch before applying.

Behind the scenes:

```bash
rig patch create codex --task "Make the requested change."
rig patch show latest
```

After approval:

```bash
rig patch apply latest
```

## Use A Task File

For long tasks:

```bash
rig delegate codex --task-file tasks/review.md
rig patch create codex --task-file tasks/change.md
```

## Generate An Image With Antigravity

Add an `antigravity-image` agent like the example in
[Agents](agents.md#examples), then delegate the asset request:

```bash
rig delegate antigravity-image --task "Use Nano Banana 2 to generate a 1024x1024 PNG app icon for Rig. Save it to assets/generated/rig-icon.png."
rig history show latest
```

Rig records the prompt, stdout, stderr, result, and status in the run directory.
The generated image itself is saved in the workspace path requested in the task.

## Check Setup

```bash
rig doctor
rig doctor --json
```

## Use MCP

```bash
rig mcp serve
```

With patch application enabled, only when you trust the parent agent and client:

```bash
RIG_MCP_ALLOW_APPLY=1 rig mcp serve
```

MCP-native agents should call `rig_delegate` for normal work and
`rig_patch_create` for reviewable edits. See [MCP Server](mcp.md) for client
configuration examples.
