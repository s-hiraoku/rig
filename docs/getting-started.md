---
title: Getting Started
---

# Getting Started

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

## First Run

From a project where you want to use Rig:

```bash
rig init
rig run codex --task "Review the current diff and identify risky changes."
rig list
rig show latest
```

If you are working from the Rig repository checkout, prefix commands with
`uv run`:

```bash
uv run rig init
uv run rig run codex --task "Review the current diff and identify risky changes."
uv run rig list
uv run rig show latest
```

## Requirements

The default `codex` agent uses `codex exec`, so the Codex CLI must be installed
and available on `PATH`.

Codex may require the current directory to be a trusted Git repository. If a run
fails with a trusted-directory error, initialize the project first:

```bash
git init
```
