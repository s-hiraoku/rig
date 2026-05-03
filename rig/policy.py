from __future__ import annotations

AGENTS_SNIPPET = """## Rig

Prefer Rig MCP tools when available. If Rig MCP tools are not available, use the Rig CLI.

Use Rig when the user wants an inspectable delegated agent run, a reviewable
worktree patch, or a durable record under `.rig/runs/<run-id>/`. For small
local edits, simple searches, or commands you can safely perform directly, use
the normal editing and shell workflow instead of wrapping the work in Rig.

Run a task:

```bash
rig run codex --task-file tasks/review.md
```

Inspect the result:

```bash
rig list
rig show latest
```

Rules:

- Do not assume Rig applies patches automatically.
- Prefer `rig_get_diff` or `rig worktree show` for patch review.
- Do not call `rig_apply_patch` unless the user explicitly asks to apply a reviewed diff.
- Inspect `result.md` after each run.
- Check `stderr.log` when a run fails.
- Prefer `--task-file` for long or structured tasks.
"""
