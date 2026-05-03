---
title: Rig User Guide
description: Rig is a local AI coding harness — file-backed tasks, inspectable run artifacts, isolated worktree edits, and an MCP server.
---

<section class="hero" markdown="0">
  <span class="hero-eyebrow">Local AI coding harness</span>
  <h1>Run agents. Keep the receipts.</h1>
  <p>
    Rig wraps coding CLIs like Codex, Claude Code, Gemini, and Copilot in a thin,
    file-backed harness. Every task, command, log, result, and patch lands in
    plain files under <code>.rig/</code> so agent work stays inspectable, replayable,
    and reviewable.
  </p>
  <div class="hero-actions">
    <a class="btn btn-primary" href="getting-started.html">Get started →</a>
    <a class="btn btn-secondary" href="https://github.com/s-hiraoku/rig" rel="noopener">View on GitHub</a>
  </div>
</section>

```bash
uv tool install "rig @ git+https://github.com/s-hiraoku/rig.git"
rig init
rig run codex --task "Review the current diff and identify risky changes."
rig show latest
```

<div class="callout" markdown="1">
<span class="callout-title">Why Rig</span>
Use Rig when you want agent work to leave an audit trail: what was asked, which
command ran, what changed, and where to inspect the result — all without a
database or a cloud service.
</div>

## Choose A Path

<div class="card-grid" markdown="0">
  <a href="getting-started.html"><strong>Install and run once</strong><span>Set up Rig, run Codex through it, and inspect the first result.</span></a>
  <a href="workflows.html"><strong>Pick the right workflow</strong><span>Normal, isolated worktree, manual, and environment-setup flows.</span></a>
  <a href="recipes.html"><strong>Real-world recipes</strong><span>End-to-end examples for PR review, refactors, test coverage, and multi-agent runs.</span></a>
  <a href="agents.html"><strong>Configure agents</strong><span>Codex, Claude, Gemini, Copilot, and external GUI agents.</span></a>
  <a href="mcp.html"><strong>Connect MCP clients</strong><span>Expose Rig as MCP tools with cwd and patch-apply safety gates.</span></a>
  <a href="faq.html"><strong>FAQ</strong><span>Why Rig, how it differs from package managers, and the safety model.</span></a>
</div>

## Mental Model

Rig has four layers. Pick the first row that matches your current question.

| Layer | What it answers | Start with |
| --- | --- | --- |
| Runs | What did the agent do? | [Core Concepts](concepts.md) · [Run Artifacts](artifacts.md) |
| Workflows | How should I run this task? | [Workflows](workflows.md) · [Recipes](recipes.md) |
| Configuration | Which command and policy should Rig use? | [Configuration](configuration.md) · [Agents](agents.md) · [Prompt Styles](prompts.md) |
| Integrations | How do other tools call Rig? | [MCP Server](mcp.md) |

## Common Jobs

- First-time setup: [Getting Started](getting-started.md)
- Choose between normal and worktree runs: [Workflows](workflows.md)
- Inspect files written by a run: [Run Artifacts](artifacts.md)
- Look up exact flags: [Command Reference](commands.md)
- Configure a non-Codex CLI: [Agents](agents.md)
- Customize the prompt Rig sends: [Prompt Styles](prompts.md)
- Fix local setup issues: [Troubleshooting](troubleshooting.md)
- Maintain this documentation site: [GitHub Pages](github-pages.md)

## What Rig Is Not

- **Not a package manager for agent assets.** Tools like APM, GitHub CLI
  `gh skill`, or Vercel `skills` own fetching, locking, and deploying skills,
  hooks, prompts, and MCP server configuration.
- **Not a sandbox.** Rig runs the configured agent command in your shell. Use
  worktree runs when you want generated edits to land somewhere safer than the
  main working tree.
- **Not a cloud service.** Rig is a local CLI. All state lives under `.rig/`.

## Repository

- [GitHub repository](https://github.com/s-hiraoku/rig)
- [Changelog](https://github.com/s-hiraoku/rig/blob/main/CHANGELOG.md)
- [Roadmap](https://github.com/s-hiraoku/rig/blob/main/ROADMAP.md)
