---
title: Rig User Guide
description: Rig is a local harness that AI coding agents call to delegate work and leave behind inspectable, reviewable run artifacts.
---

<section class="hero" markdown="0">
  <span class="hero-eyebrow">Harness for AI coding agents</span>
  <h1>Let the AI work. Keep the receipts.</h1>
  <p>
    Rig is a local harness that <strong>parent AI agents</strong> like
    Claude Code, Cursor, and Codex CLI call to <strong>delegate coding work</strong>.
    You ask the AI in plain language; the AI invokes <code>rig delegate</code> (CLI)
    or <code>rig_delegate</code> (MCP) behind the scenes; Rig records the task, command,
    logs, result, and any patch as plain files under <code>.rig/</code>.
  </p>
  <div class="hero-actions">
    <a class="btn btn-primary" href="getting-started.html">Set up Rig →</a>
    <a class="btn btn-secondary" href="https://github.com/s-hiraoku/rig" rel="noopener">View on GitHub</a>
  </div>
</section>

<div class="callout" markdown="1">
<span class="callout-title">What Rig solves</span>
AI coding agents are powerful, but the trail of what was asked, what changed,
and why is easy to lose. Rig forces the parent agent to drop every delegated
task into <code>.rig/runs/&lt;run-id&gt;/task.md</code>, capture the result in
<code>result.md</code>, and (for risky edits) hold the changes in a worktree
as <code>diff.patch</code> so you can review before applying.
</div>

## How You Actually Use It

You don't type Rig commands. You talk to your AI in natural language.

> **You:** "Review the current diff and flag anything risky."
>
> **Parent AI** *(Cursor / Claude Code / Codex CLI)*: *(internally calls
> `rig delegate`)* — "I ran the review through Rig. Here's the summary
> from `result.md` …"

The parent agent knows to use Rig because your project's instructions reference
`.rig/instructions/rig.md`. `rig init` creates that file and updates both
`AGENTS.md` and `CLAUDE.md` with small reference blocks. See
[Getting Started](getting-started.md).

## Choose A Path

<div class="card-grid" markdown="0">
  <a href="getting-started.html"><strong>Set up once</strong><span>Install Rig, run <code>rig init</code>, and point your AI at <code>.rig/instructions/rig.md</code>.</span></a>
  <a href="workflows.html"><strong>Pick the right flow</strong><span>Delegate runs for reviews, patch runs for reviewable edits.</span></a>
  <a href="develop-with-rig.html"><strong>Install the skill</strong><span>Add <code>develop-with-rig</code> so parent agents use Rig for delegation and patch isolation.</span></a>
  <a href="recipes.html"><strong>Real recipes</strong><span>End-to-end examples with the natural-language prompts you'd actually give your AI.</span></a>
  <a href="agents.html"><strong>Configure child agents</strong><span>Codex, Claude, Gemini, Copilot — the CLIs Rig launches on the parent agent's behalf.</span></a>
  <a href="mcp.html"><strong>Optional MCP</strong><span>Expose Rig as MCP tools for MCP-native or shell-restricted parents.</span></a>
  <a href="faq.html"><strong>FAQ</strong><span>Why Rig, what Rig is not, and when to bypass it and use the CLI directly.</span></a>
</div>

## Mental Model

Three roles, in order:

| Role | What they do |
| --- | --- |
| **Human** (you) | Ask the parent agent in natural language. Review `result.md` and `diff.patch` through that agent. Approve patch application. |
| **Parent agent** (Cursor, Claude Code, Codex CLI, anything reading AGENTS.md) | Calls `rig delegate` (CLI) or `rig_delegate` (MCP) to delegate work. Reads back artifacts and reports to you. |
| **Child agent** (the CLI Rig launches — `codex exec` by default) | Performs the actual task, writes its answer to stdout. Rig captures everything to disk. |

You only touch the CLI directly for **setup, debugging, and audit**. Day-to-day
work flows through the parent agent.

## Where To Look

| Layer | Question | Start with |
| --- | --- | --- |
| Runs | What did the child agent do? | [Core Concepts](concepts.md) · [Run Artifacts](artifacts.md) |
| Workflows | How should this task be delegated? | [Workflows](workflows.md) · [Develop With Rig Skill](develop-with-rig.md) · [Recipes](recipes.md) |
| Configuration | Which child agent and policy should Rig use? | [Configuration](configuration.md) · [Agents](agents.md) · [Prompt Styles](prompts.md) |
| Integration | How does a shell-restricted parent reach Rig? | [MCP Server](mcp.md) |

## What Rig Is Not

- **Not an AI model.** Rig has no inference, no API keys, no opinions of its
  own. It's a harness around CLIs you already use.
- **Not a sandbox.** The child agent runs in your shell with your credentials.
  Worktree runs add file-system isolation; the process itself still runs locally.
- **Not a package manager for agent assets.** Rig runs configured local commands
  and records artifacts. It does not install skills, hooks, prompts, or MCP
  server lists.
- **Not a cloud service.** Everything lives under `.rig/` in your repo.

## Repository

- [GitHub repository](https://github.com/s-hiraoku/rig)
- [Changelog](https://github.com/s-hiraoku/rig/blob/main/CHANGELOG.md)
- [Roadmap](https://github.com/s-hiraoku/rig/blob/main/ROADMAP.md)
