---
title: Troubleshooting
description: Common Rig setup issues and their fixes — install, PATH, Codex trusted directory, waiting runs, env doctor, and Pages deploys.
---

# Troubleshooting

This page lists the most common setup problems. For lookup by topic, see the
[FAQ](faq.md).

## `rig` Command Is Not Found

Check that the install completed and that the tool directory is on `PATH`:

```bash
uv tool list
rig --help
```

If needed, reinstall:

```bash
uv tool install --force --refresh "rig @ git+https://github.com/s-hiraoku/rig.git"
```

If `uv tool list` shows Rig but the shell still cannot find it, ensure
`$(uv tool dir --bin)` is on your `PATH` (most shells do this automatically
after the first `uv tool install`).

## Codex Is Not Found

The default `codex` agent runs `codex exec`. Install the Codex CLI and
confirm that `codex` is available on `PATH`:

```bash
codex --help
```

If you use a different CLI, configure it in `.rig/config.yaml`. See
[Agents](agents.md).

## Trusted Directory Error

If Codex reports that the current directory is not trusted:

```txt
Not inside a trusted directory and --skip-git-repo-check was not specified.
```

Initialize the project as a Git repository, then retry the Rig command:

```bash
git init
```

This is a Codex requirement, not a Rig requirement. Other CLIs may not need
a Git repository.

## No Runs Found

`rig list` and `rig show latest` read `.rig/runs/`. Start a run first:

```bash
rig run codex --task "Review the current diff."
```

If `rig list` consistently prints `No runs found.` even after running, check
that you are in the same project directory. `.rig/runs/` is per-project.

## Run Is Waiting

A `manual` runner creates a run with status `waiting`. Complete or fail it
explicitly:

```bash
rig manual complete latest --result "Finished externally."
rig manual fail latest --error "Blocked externally."
```

These commands operate only on runs currently in `waiting`, so a real
`exec` run is never overwritten by accident.

## Run Failed With Exit Code 124

That is Rig's timeout signal. The configured agent ran longer than
`timeout_seconds`. Either raise the timeout in `.rig/config.yaml` or split
the task into smaller runs.

```yaml
agents:
  codex:
    timeout_seconds: 1200
```

## Worktree Patch Includes Unexpected Files

Worktree patches include untracked files that are not ignored by Git. If the
captured patch contains build artifacts, caches, or `node_modules`, add them
to `.gitignore` *before* re-running:

```text
node_modules/
dist/
.cache/
```

Then run again. The new patch will skip the ignored paths.

## Environment Check Failures

Use:

```bash
rig env doctor
rig env doctor --json   # structured form for CI or scripts
rig env plan
```

These commands report missing Rig files, required project files declared in
`.rig/env.yaml`, configured agent commands, and optional agent asset
managers. Statuses are `ok`, `missing`, `optional`, and `warn`.

`rig env bootstrap` creates Rig-owned files only. It does not install
external tools.

## MCP Client Cannot Read A File

MCP `cwd` values must resolve inside the server's launch directory, or
inside `RIG_MCP_ROOT` when set. MCP `task_file` values are resolved from the
selected `cwd` and must stay inside that project. If a client gets a
permission-style error, confirm the path is inside the allowed scope. See
[MCP Server → Safety Defaults](mcp.md#safety-defaults).

## MCP `rig_apply_patch` Returns Disabled

`rig_apply_patch` is disabled unless the server starts with
`RIG_MCP_ALLOW_APPLY=1`. Restart the server with that variable set, only
when patch application is intentional:

```bash
RIG_MCP_ALLOW_APPLY=1 rig mcp serve
```

## GitHub Pages Does Not Update

The Pages site is built from `docs/` by `.github/workflows/pages.yml`.
Confirm that GitHub Pages is configured to deploy from GitHub Actions, then
rerun the Pages workflow from the Actions tab. Changes outside `docs/**` do
not trigger that workflow unless `.github/workflows/pages.yml` also
changes.

See [GitHub Pages](github-pages.md) for the full pipeline.

## Reset Rig Configuration

To regenerate config back to current Rig defaults (with a backup of the
existing files):

```bash
rig init --reset config
rig init --reset env
rig init --reset all   # both
```

Run history under `.rig/runs/` is untouched by these commands.
