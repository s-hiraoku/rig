---
title: Rig User Guide
---

# Rig User Guide

Rig is a local AI coding harness for running coding agents with file-backed
tasks, inspectable artifacts, and simple run history.

Rig's main unit is a run. Each run stores the task, command metadata, stdout,
stderr, result, status, and optional worktree patch under `.rig/runs/` so agent
work stays reviewable after the command exits.

## Start Here

- [Getting Started](getting-started.md)
- [Core Concepts](concepts.md)
- [Configuration](configuration.md)
- [Command Reference](commands.md)
- [Worktree Runs](worktrees.md)
- [MCP Server](mcp.md)
- [GitHub Pages](github-pages.md)
- [Troubleshooting](troubleshooting.md)

## Common Flow

```bash
rig init
rig suggest "Review the current diff."
rig run codex --task "Review the current diff."
rig list
rig show latest
```

## Isolated Edit Flow

```bash
rig worktree run codex --task "Make the requested change."
rig worktree show latest
rig worktree apply latest
```

## Harness Setup Flow

```bash
rig env doctor
rig env plan
rig env bootstrap
rig guide agents
```

## Repository

- [GitHub repository](https://github.com/s-hiraoku/rig)
- [Changelog](https://github.com/s-hiraoku/rig/blob/main/CHANGELOG.md)
- [Roadmap](https://github.com/s-hiraoku/rig/blob/main/ROADMAP.md)
