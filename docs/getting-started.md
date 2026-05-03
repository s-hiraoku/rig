---
title: Getting Started
description: Install Rig and wire your parent AI agent to use it. Three steps; the CLI is mostly something you read about, not something you type.
---

# Getting Started

The goal of this page is one-time setup so that **the next time you ask your
AI to make a code change, it routes the work through Rig automatically**.

Three steps:

1. Install Rig.
2. Run `rig init` in the project.
3. Tell the parent AI to use Rig (paste a snippet into `AGENTS.md` /
   `CLAUDE.md`).

After that, you talk to your AI; the AI talks to Rig.

## 1. Install

Rig ships as a `uv tool`:

```bash
uv tool install "rig @ git+https://github.com/s-hiraoku/rig.git"
```

Verify:

```bash
rig --help
```

To pull the latest version later:

```bash
uv tool install --force --refresh "rig @ git+https://github.com/s-hiraoku/rig.git"
```

<div class="callout" markdown="1">
<span class="callout-title">Requires uv</span>
If you don't have uv yet, install it from
<a href="https://docs.astral.sh/uv/">docs.astral.sh/uv</a> first.
</div>

## 2. Initialize The Project

In the repo where you want Rig:

```bash
rig init
```

That creates:

```txt
.rig/
  config.yaml   # the child agent Rig will launch (Codex by default)
  env.yaml      # required files and optional asset managers
  runs/         # run history, per-machine
```

`rig init` is safe to run repeatedly. For reset flags see
[Configuration → Initialize Or Reset](configuration.md#initialize-or-reset).

## 3. Tell Your AI To Use Rig

This is the step that actually matters. The parent agent only knows to call
Rig if your project's instruction file says so.

Generate the snippet:

```bash
rig guide agents --target codex --write   # for AGENTS.md
rig guide agents --target claude --write  # for CLAUDE.md
```

`--write` writes the long-form policy to `.rig/instructions/rig.md` and prints
a 3–4 line snippet. Paste the snippet into `AGENTS.md` or `CLAUDE.md`.

Example `AGENTS.md`:

```markdown
## Rig

See `.rig/instructions/rig.md` for Rig usage policy, artifact inspection
rules, and patch-apply safety rules.
```

That's it. Any agent that reads AGENTS.md (Codex CLI, Cursor with custom
instructions, Claude Code with project rules) will now prefer Rig for
delegated work.

### MCP-aware parents (Cursor, Claude Code, …)

If your parent agent speaks MCP, also expose Rig as an MCP server so it can
call structured tools instead of parsing CLI text:

```bash
rig mcp serve
```

Add an entry to your client's MCP config that runs `rig mcp serve` over
stdio. Details: [MCP Server](mcp.md).

## 4. Try It

Now stop typing Rig commands. Talk to your AI:

> **You:** "Review the current diff in `rig/cli.py` and flag anything risky."

The parent agent calls `rig_run` (MCP) or `rig run` (CLI) under the hood.
Rig writes to `.rig/runs/<run-id>/`:

- `task.md` — the request
- `command.json` — the child agent invocation
- `stdout.log` / `stderr.log` — the child agent's output
- `result.md` — the trimmed final answer
- `status.json` — outcome, exit code, timestamps

The parent agent reads `result.md` and reports the summary to you.

For risky edits, ask for isolation:

> **You:** "Refactor the worktree helper. Use a worktree, the change is
> non-trivial."
>
> **Parent agent:** *(calls `rig_run` with `worktree=True`)* "Done. The patch
> is in `.rig/runs/…/diff.patch`. Highlights: … Want me to apply it?"

You decide. If you say "apply," the agent calls `rig worktree apply` (assuming
patch application is enabled in your client — see
[MCP → Safety Defaults](mcp.md#safety-defaults)).

## Appendix A: Local Development Of Rig Itself

For contributors hacking on Rig:

```bash
git clone https://github.com/s-hiraoku/rig.git
cd rig
uv sync --group dev
uv run rig --help
```

zsh completion: `contrib/completions/rig.zsh`.

## Appendix B: When You Do Type CLI Commands

You'll occasionally use the CLI directly — for setup, debugging, audit, and
operational tasks. The parent agent does not need to be involved for these:

```bash
rig list                    # recent runs
rig show latest             # last run's metadata + result
rig env doctor              # local setup diagnostics
rig env doctor --json       # CI-friendly diagnostics
rig worktree show latest    # the captured patch
rig worktree apply latest   # apply the captured patch
```

Full surface: [Command Reference](commands.md). Day-to-day delegation does not
require any of this.

## Requirements

The default child agent `codex` runs `codex exec`, so the Codex CLI must be
installed and on `PATH`. To use a different child agent, see [Agents](agents.md).

Codex requires the working directory to be a trusted Git repository. If a run
fails with a trusted-directory error, run `git init` first.

## Next Steps

- Learn the role model: [Core Concepts](concepts.md)
- Pick a delegation flow: [Workflows](workflows.md)
- Read prompts you can give your AI: [Recipes](recipes.md)
- Add another child agent: [Agents](agents.md)
