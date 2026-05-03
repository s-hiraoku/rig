---
title: Rig User Guide
---

# Rig User Guide

Rig is a local AI coding harness for running coding agents with file-backed
tasks, inspectable artifacts, and simple run history.

This guide is a starter structure for the GitHub Pages site. It is intentionally
small so the detailed content can grow alongside the CLI.

## Start Here

- [Getting Started](getting-started.md)
- [Core Concepts](concepts.md)
- [Configuration](configuration.md)
- [Command Reference](commands.md)
- [Worktree Runs](worktrees.md)
- [MCP Server](mcp.md)
- [Troubleshooting](troubleshooting.md)

## Common Flow

```bash
rig init
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

## Repository

- [GitHub repository](https://github.com/s-hiraoku/rig)
- [Changelog](https://github.com/s-hiraoku/rig/blob/main/CHANGELOG.md)
- [Roadmap](https://github.com/s-hiraoku/rig/blob/main/ROADMAP.md)
