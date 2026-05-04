---
title: Run Artifacts
description: File-by-file reference for what Rig writes under .rig/runs/<run-id>/ — task, command, logs, result, status, and worktree patch.
---

# Run Artifacts

Rig stores run history as plain files. The parent agent reads them after a
run; you can also read them directly when you want to audit or debug.
This page is the file-by-file reference. For the higher-level picture, see
[Core Concepts](concepts.md).

## Directory Layout

```txt
.rig/runs/<run-id>/
  task.md
  command.json
  stdout.log
  stderr.log
  result.md
  status.json
  diff.patch       # worktree runs only
```

`<run-id>` follows `YYYYMMDD-HHMMSS-<agent>` so listings sort
chronologically.

## Files

| File | Purpose |
| --- | --- |
| `task.md` | The task the parent agent passed to Rig. |
| `command.json` | Child-agent name, command, args, execution directory, timing. |
| `stdout.log` | Raw standard output from the child-agent command. |
| `stderr.log` | Raw standard error from the child-agent command. |
| `result.md` | Human-readable result; what `rig history show` prints and what the parent agent reads back. |
| `status.json` | Run ID, status, timestamps, exit code, run directory, optional diff path. |
| `diff.patch` | Captured patch from an isolated worktree run. |

### `task.md`

The task as the parent agent passed it in. For `--task`, this is the literal
string. For `--task-file`, it is a copy of the source file. Either way, this
is the canonical "what was asked" record for the run.

### `command.json`

```json
{
  "agent": "codex",
  "runner": "exec",
  "command": "codex",
  "args": ["exec", "<rendered prompt>"],
  "cwd": "/path/to/project",
  "started_at": "2026-05-04T14:15:00+00:00"
}
```

The last entry of `args` is the resolved prompt — useful when debugging a
templated `prompt_style`. Dry runs write the same file without launching
the command.

### `stdout.log` / `stderr.log`

Raw byte-for-byte output, decoded as UTF-8 with replacement on errors. If
the child agent crashes mid-run, `stderr.log` typically contains the
traceback and `stdout.log` contains whatever made it to stdout before the
crash.

### `result.md`

The human-readable result. By default, `result.md` mirrors stdout. If the
child agent emits the marker described in
[Result Extraction](#result-extraction), `result.md` contains only the text
after it. The parent agent normally reads `result.md` (not `stdout.log`)
when reporting back to you.

For `failed` runs, `rig history show` also surfaces the exit code and a short
`--- Error ---` section sourced from `stderr.log`, even when `result.md`
is empty.

### `status.json`

```json
{
  "id": "20260504-141500-codex",
  "agent": "codex",
  "status": "succeeded",
  "started_at": "2026-05-04T14:15:00+00:00",
  "finished_at": "2026-05-04T14:15:09+00:00",
  "exit_code": 0,
  "run_dir": ".rig/runs/20260504-141500-codex"
}
```

Patch runs add a `diff_path` field pointing at `diff.patch`.

### `diff.patch`

A unified diff captured from the isolated worktree, suitable for `git apply`.
`rig patch show <run-id>` prints this file alongside metadata; `rig
patch apply <run-id>` runs `git apply` against it. See
[Patch Runs](worktrees.md).

## Result Extraction
{: #result-extraction }

By default, `result.md` mirrors stdout. If a child agent prints this marker:

```txt
--- RIG RESULT ---
```

Rig stores only the text after the marker in `result.md`, while preserving
the full stdout in `stdout.log`. This lets verbose child agents print logs
and still surface a clean final answer to the parent agent.

You can encourage the marker via your prompt template:

```yaml
prompt_template: |
  ...
  Begin the final answer with the literal marker `--- RIG RESULT ---`.
```

## Status Values

| Status | Meaning |
| --- | --- |
| `created` | Dry run artifacts were written, but no child-agent command ran. |
| `succeeded` | Child-agent command succeeded. |
| `failed` | Child-agent command failed or timed out. |

## Inspect Artifacts

Most of the time, the parent agent reads these for you. To inspect manually:

```bash
rig history
rig history show latest
rig patch show latest
```

Or use the files directly when debugging command execution or integrating
with other local tools:

```bash
ls .rig/runs/$(ls -1t .rig/runs | head -n1)
jq . .rig/runs/<run-id>/status.json
jq . .rig/runs/<run-id>/command.json
```

## Versioning Run History

`.rig/runs/` is per-machine. Most teams add it to `.gitignore` and only
commit `.rig/config.yaml` and `.rig/instructions/rig.md`. Run records are useful as a
local audit log; sharing them across machines is rarely worth the merge
noise.
