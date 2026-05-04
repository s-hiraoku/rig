---
title: Getting Started
description: Install Rig, initialize a project, and let a parent AI agent delegate work through Rig.
---

# Getting Started

Rig is usually called by a parent AI agent. You install it once, initialize the
project, let `rig init` update `AGENTS.md` and `CLAUDE.md`, then keep working
in natural language.

## 1. Install

```bash
uv tool install "rig @ git+https://github.com/s-hiraoku/rig.git"
rig --help
```

For local development from this repository:

```bash
uv sync --group dev
uv run rig --help
```

## 2. Initialize

```bash
rig init
```

This creates `.rig/config.yaml`, `.rig/instructions/rig.md`, `.rig/runs/`, and
managed Rig blocks in `AGENTS.md` and `CLAUDE.md`.

## 3. Use Rig Through Your Agent

Ask your parent AI agent:

> Review the current diff through Rig and summarize risky changes.

The parent agent calls:

```bash
rig delegate codex --task "Review the current diff and summarize risky changes."
```

For edits:

> Make the requested change through Rig as a patch. Show me the patch before applying.

The parent agent calls:

```bash
rig patch create codex --task "Make the requested change."
rig patch show latest
```

Only after approval should it call:

```bash
rig patch apply latest
```

## MCP Clients

If your parent agent is MCP-native or shell-restricted, add an MCP server entry
that runs:

```bash
rig mcp serve
```

See [MCP Server](mcp.md) for client configuration examples.

## Direct Human CLI Use

Humans still use the CLI for setup, debugging, audit, and review:

```bash
rig history
rig history show latest
rig patch show latest
rig doctor
```

## Requirements

The default child agent is `codex`, configured as `codex exec`. Install Codex
or edit `.rig/config.yaml` to point at another non-interactive coding CLI.
Patch runs require Git because Rig uses an isolated worktree internally.
