---
title: Run Artifacts
---

# Run Artifacts

Rig stores run history as plain files so a completed or failed agent run remains
inspectable without special tooling.

## Directory Layout

```txt
.rig/runs/<run-id>/
  task.md
  command.json
  stdout.log
  stderr.log
  result.md
  status.json
  diff.patch
```

`diff.patch` is present for worktree runs.

## Files

| File | Purpose |
| --- | --- |
| `task.md` | Saved task text passed to the agent. |
| `command.json` | Agent name, command, args, execution directory, and timing metadata. |
| `stdout.log` | Raw standard output from the agent command. |
| `stderr.log` | Raw standard error from the agent command. |
| `result.md` | Human-readable result shown by `rig show`. |
| `status.json` | Run ID, status, timestamps, exit code, run directory, and optional diff path. |
| `diff.patch` | Captured patch from an isolated worktree run. |

## Result Extraction

By default, `result.md` mirrors stdout. If an agent prints this marker:

```txt
--- RIG RESULT ---
```

Rig stores only the text after the marker in `result.md` while preserving the
full stdout in `stdout.log`.

## Status Values

| Status | Meaning |
| --- | --- |
| `created` | Dry run artifacts were written, but no agent command ran. |
| `waiting` | Manual runner created a run that needs explicit completion or failure. |
| `succeeded` | Agent command or manual completion succeeded. |
| `failed` | Agent command failed or the manual run was marked failed. |

## Inspect Artifacts

Use the CLI for common inspection:

```bash
rig list
rig show latest
rig worktree show latest
```

Use the files directly when debugging command execution or integrating with
other local tools.
