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

## Environment Check Failures

Use:

```bash
rig env doctor
rig env plan
```

These commands report missing Rig files, required project files, configured
agent commands, and optional agent asset managers.
