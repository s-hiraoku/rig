---
title: Troubleshooting
---

# Troubleshooting

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

## Codex Is Not Found

The default `codex` agent runs `codex exec`. Install the Codex CLI and confirm
that `codex` is available on `PATH`:

```bash
codex --help
```

## Trusted Directory Error

If Codex reports that the current directory is not trusted, initialize the
project as a Git repository:

```bash
git init
```

Then retry the Rig command.

## No Runs Found

`rig list` and `rig show latest` read `.rig/runs/`. Start a run first:

```bash
rig run codex --task "Review the current diff."
```

## Run Is Waiting

A `manual` runner creates a run with status `waiting`. Complete or fail it
explicitly:

```bash
rig manual complete latest --result "Finished externally."
rig manual fail latest --error "Blocked externally."
```

## Environment Check Failures

Use:

```bash
rig env doctor
rig env plan
```

These commands report missing Rig files, required project files, configured
agent commands, and optional agent asset managers.

## GitHub Pages Does Not Update

The Pages site is built from `docs/` by `.github/workflows/pages.yml`. Confirm
that GitHub Pages is configured to deploy from GitHub Actions, then rerun the
Pages workflow from the Actions tab. Changes outside `docs/**` do not trigger
that workflow unless `.github/workflows/pages.yml` also changes.
