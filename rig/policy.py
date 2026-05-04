from __future__ import annotations

AGENTS_SNIPPET = """## Rig

Prefer Rig MCP tools when available. If Rig MCP tools are not available, use the Rig CLI.

Use Rig when the user wants an inspectable delegated agent run, a reviewable
worktree patch, or a durable record under `.rig/runs/<run-id>/`. For small
local edits, simple searches, or commands you can safely perform directly, use
the normal editing and shell workflow instead of wrapping the work in Rig.

If the parent agent has native subagents, parallel agents, or isolated
workspaces, prefer those native capabilities for parallel attempts,
role-split work, cross-review, and isolated implementation. Pass the task,
constraints, and expected output directly to each subagent, then synthesize
their results for the human. Use Rig parallel/worktree features when native
subagents are unavailable, when the user asks for Rig-managed artifacts, or
when a durable `.rig/runs/<run-id>/` audit trail is the main goal.

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
- Prefer native parent-agent subagents over `rig run --parallel` when available.
- Prefer native isolated subagent workspaces over `rig worktree run` when available.
- For long delegated runs, choose an explicit `--timeout-seconds` or
  `timeout_seconds` value that matches the task size, and set any parent shell
  tool timeout high enough for the Rig command to finish.
"""


RIG_INSTRUCTION_PATH = ".rig/instructions/rig.md"


def agents_snippet(*, target: str = "generic") -> str:
    if target == "claude":
        return (
            "<!-- Suggested for CLAUDE.md or Claude project instructions. -->\n\n"
            f"## Rig\n\nRead `{RIG_INSTRUCTION_PATH}` for Rig usage policy, "
            "artifact inspection rules, and patch-apply safety rules.\n"
        )
    if target == "codex":
        return (
            "<!-- Suggested for AGENTS.md in Codex projects. -->\n\n"
            f"## Rig\n\nSee `{RIG_INSTRUCTION_PATH}` for Rig usage policy, "
            "artifact inspection rules, and patch-apply safety rules.\n"
        )
    return AGENTS_SNIPPET


def rig_instruction_file_content() -> str:
    return (
        "# Rig Instructions\n\n"
        "This file is generated for agent instruction files to reference. "
        "Keep `AGENTS.md`, `CLAUDE.md`, and other top-level instruction files "
        "small by linking to this Rig-owned file.\n\n"
        f"{AGENTS_SNIPPET}"
    )
