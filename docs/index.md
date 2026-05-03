---
title: Rig User Guide
---

# Rig User Guide

Rig is a local harness for running AI coding agents while keeping their work
inspectable. It records every task, command, result, log, and optional patch in
plain files under the repository.

This site is the structured user guide. The README stays short; these pages are
organized by what you are trying to do.

<div class="callout">
Use Rig when you want agent work to leave an audit trail: what was asked, what
command ran, what changed, and where to inspect the result.
</div>

## Choose A Path

<div class="card-grid">
  <a href="getting-started.html"><strong>Install and run once</strong><span>Set up Rig, run Codex through it, and inspect the first result.</span></a>
  <a href="workflows.html"><strong>Pick the right workflow</strong><span>Normal runs, isolated worktree edits, manual runs, and environment setup.</span></a>
  <a href="configuration.html"><strong>Configure agents</strong><span>Agent commands, runners, prompt styles, timeouts, and environment checks.</span></a>
  <a href="mcp.html"><strong>Connect MCP clients</strong><span>Expose Rig as structured MCP tools with cwd and patch-apply safety gates.</span></a>
</div>

## Mental Model

Rig has four layers:

| Layer | What it answers | Start with |
| --- | --- | --- |
| Runs | What did the agent do? | [Core Concepts](concepts.md) |
| Workflows | How should I run this task? | [Workflows](workflows.md) |
| Configuration | Which command and policy should Rig use? | [Configuration](configuration.md) |
| Integrations | How do other tools call Rig? | [MCP Server](mcp.md) |

## Common Jobs

- First-time setup: [Getting Started](getting-started.md)
- Choose normal run versus worktree run: [Workflows](workflows.md)
- Inspect files written by a run: [Run Artifacts](artifacts.md)
- Look up exact flags: [Command Reference](commands.md)
- Fix local setup issues: [Troubleshooting](troubleshooting.md)
- Maintain this documentation site: [GitHub Pages](github-pages.md)

## Repository

- [GitHub repository](https://github.com/s-hiraoku/rig)
- [Changelog](https://github.com/s-hiraoku/rig/blob/main/CHANGELOG.md)
- [Roadmap](https://github.com/s-hiraoku/rig/blob/main/ROADMAP.md)
