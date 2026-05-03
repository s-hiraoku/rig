---
title: Getting Started
description: The shortest path from no Rig setup to one inspectable run, plus local development from a checkout.
---

# Getting Started

This page is the shortest path from no Rig setup to one inspectable run. For
choosing between normal, worktree, and manual flows, see
[Workflows](workflows.md). For end-to-end recipes, see [Recipes](recipes.md).

## Installation

Install Rig directly from GitHub:

```bash
uv tool install "rig @ git+https://github.com/s-hiraoku/rig.git"
```

Check that the command is available:

```bash
rig --help
```

To reinstall the latest version:

```bash
uv tool install --force --refresh "rig @ git+https://github.com/s-hiraoku/rig.git"
```

<div class="callout" markdown="1">
<span class="callout-title">Requires uv</span>
Rig is published as a <code>uv tool</code>. Install
<a href="https://docs.astral.sh/uv/">uv</a> first if you do not have it.
</div>

## Local Development

Clone the repository and install the development environment:

```bash
git clone https://github.com/s-hiraoku/rig.git
cd rig
uv sync --group dev
```

Run Rig from the checkout:

```bash
uv run rig --help
```

Optional zsh completion is available at `contrib/completions/rig.zsh`.

## First Run

From a project where you want to use Rig:

```bash
rig init
rig suggest "Review the current diff and identify risky changes."
rig run codex --task "Review the current diff and identify risky changes."
rig list
rig show latest
```

If you are working from the Rig repository checkout, prefix commands with
`uv run`:

```bash
uv run rig init
uv run rig suggest "Review the current diff and identify risky changes."
uv run rig run codex --task "Review the current diff and identify risky changes."
uv run rig list
uv run rig show latest
```

Inspect the generated files with [Run Artifacts](artifacts.md) when you need
more detail than `rig show` prints.

## What `rig init` Creates

```txt
.rig/
  config.yaml   # agents, runners, prompt styles
  env.yaml      # required files and optional asset managers
  runs/         # run history (per-machine)
```

`rig init` is safe to run repeatedly. See
[Configuration → Initialize Or Reset](configuration.md#initialize-or-reset)
for the reset flags.

## Environment Check

After initialization, inspect the local harness setup:

```bash
rig env doctor
rig env doctor --json   # machine-readable form for CI
rig env plan
```

Use `rig env bootstrap` to create missing Rig-owned files. Rig will not
install external tools or third-party agent assets.

## Requirements

The default `codex` agent uses `codex exec`, so the Codex CLI must be
installed and available on `PATH`. To use a different CLI, see
[Agents](agents.md).

Codex may require the current directory to be a trusted Git repository. If a
run fails with a trusted-directory error, initialize the project first:

```bash
git init
```

## Next Steps

- Pick a workflow: [Workflows](workflows.md)
- Try a real recipe: [Recipes](recipes.md)
- Configure another agent: [Agents](agents.md)
- Customize prompts: [Prompt Styles](prompts.md)
