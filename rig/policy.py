from __future__ import annotations

AGENTS_SNIPPET = """## Rig

Prefer Rig MCP tools when available. If Rig MCP tools are not available, use the Rig CLI.

Use Rig when the user wants an inspectable delegated agent run, a reviewable
worktree patch, or a durable record under `.rig/runs/<run-id>/`. For small
local edits, simple searches, or commands you can safely perform directly, use
the normal editing and shell workflow instead of wrapping the work in Rig.

If the task may edit files, is risky, or the working tree is dirty, prefer
Rig's patch flow so the generated diff stays reviewable before it is applied.

Run a task:

```bash
rig delegate codex --task-file tasks/review.md
```

Inspect the result:

```bash
rig history
rig history show latest
```

Create a reviewable patch:

```bash
rig patch create codex --task-file tasks/change.md
rig patch show latest
```

Rules:

- Do not assume Rig applies patches automatically.
- Prefer `rig_patch_show` or `rig patch show` for patch review.
- Do not call `rig_patch_apply` or `rig patch apply` unless the user explicitly asks to apply a reviewed diff.
- Inspect `result.md` after each run.
- Check `stderr.log` when a run fails.
- Prefer `--task-file` for long or structured tasks.
- For long delegated runs, choose an explicit `--timeout-seconds` or
  `timeout_seconds` value that matches the task size, and set any parent shell
  tool timeout high enough for the Rig command to finish.
- For broader Codex project harness templates, skills, hooks, policies, and
  ledgers, use `rig harness` to inspect the companion `codex-harnesses` source.
"""


RIG_INSTRUCTION_PATH = ".rig/instructions/rig.md"
AGENTS_INSTRUCTION_PATH = "AGENTS.md"
AGENTS_SNIPPET_START = "<!-- BEGIN RIG INSTRUCTIONS -->"
AGENTS_SNIPPET_END = "<!-- END RIG INSTRUCTIONS -->"
CLAUDE_INSTRUCTION_PATH = "CLAUDE.md"
CLAUDE_SNIPPET_START = "<!-- BEGIN RIG INSTRUCTIONS -->"
CLAUDE_SNIPPET_END = "<!-- END RIG INSTRUCTIONS -->"


def agents_snippet(*, target: str = "all") -> str:
    if target == "all":
        return "\n\n".join(
            [
                agents_snippet(target="codex").rstrip(),
                agents_snippet(target="antigravity").rstrip(),
                skill_reference_snippet().rstrip(),
            ]
        ) + "\n"
    if target == "antigravity":
        return (
            "<!-- Suggested for AGENTS.md in Antigravity projects. -->\n\n"
            f"## Rig\n\nSee `{RIG_INSTRUCTION_PATH}` for Rig usage policy, "
            "artifact inspection rules, and patch-apply safety rules.\n"
        )
    if target == "claude":
        return (
            "<!-- Suggested for CLAUDE.md or Claude project instructions. -->\n\n"
            f"## Rig\n\nRead `{RIG_INSTRUCTION_PATH}` for Rig usage policy, "
            "artifact inspection rules, and patch-apply safety rules.\n"
        )
    if target == "codex":
        return (
            "<!-- Suggested for AGENTS.md. -->\n\n"
            f"## Rig\n\nSee `{RIG_INSTRUCTION_PATH}` for Rig usage policy, "
            "artifact inspection rules, and patch-apply safety rules.\n"
        )
    return AGENTS_SNIPPET


def skill_reference_snippet() -> str:
    return (
        "<!-- Suggested for Rig-related skill files. -->\n\n"
        f"# Rig\n\nRead `{RIG_INSTRUCTION_PATH}` before using Rig.\n"
    )


def agents_instruction_block() -> str:
    return (
        f"{AGENTS_SNIPPET_START}\n"
        f"{agents_snippet(target='codex').rstrip()}\n"
        f"{AGENTS_SNIPPET_END}\n"
    )


def claude_instruction_block() -> str:
    return (
        f"{CLAUDE_SNIPPET_START}\n"
        f"{agents_snippet(target='claude').rstrip()}\n"
        f"{CLAUDE_SNIPPET_END}\n"
    )


def rig_instruction_file_content() -> str:
    return (
        "# Rig Instructions\n\n"
        "This file is generated for agent instruction files to reference. "
        "Keep `AGENTS.md` and other top-level instruction files "
        "small by linking to this Rig-owned file.\n\n"
        f"{AGENTS_SNIPPET}"
    )
