from __future__ import annotations

PROMPT_TEMPLATE_PLACEHOLDERS = ("agent", "task_path", "task", "task_md")


def prompt_template_values(
    *, agent: str, task_path: str, task: str, task_md: str
) -> dict[str, str]:
    return {
        "agent": agent,
        "task_path": task_path,
        "task": task,
        "task_md": task_md,
    }


def empty_prompt_template_values() -> dict[str, str]:
    return {key: "" for key in PROMPT_TEMPLATE_PLACEHOLDERS}
