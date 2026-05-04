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


RIG_INSTRUCTION_PATH = ".rig/instructions/rig.md"


def agents_snippet(*, target: str = "all") -> str:
    if target == "all":
        return "\n\n".join(
            [
                agents_snippet(target="codex").rstrip(),
                agents_snippet(target="claude").rstrip(),
                skill_reference_snippet().rstrip(),
            ]
        ) + "\n"
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


def skill_reference_snippet() -> str:
    return (
        "<!-- Suggested for Rig-related skill files. -->\n\n"
        f"# Rig\n\nRead `{RIG_INSTRUCTION_PATH}` before using Rig.\n"
    )


def rig_instruction_file_content() -> str:
    return (
        "# Rig Instructions\n\n"
        "This file is generated for agent instruction files to reference. "
        "Keep `AGENTS.md`, `CLAUDE.md`, and other top-level instruction files "
        "small by linking to this Rig-owned file.\n\n"
        f"{AGENTS_SNIPPET}"
    )
