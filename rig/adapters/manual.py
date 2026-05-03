from __future__ import annotations

from os.path import relpath

from rig.config import AgentConfig
from rig.run_context import RunContext


class ManualAdapter:
    def __init__(self, name: str, config: AgentConfig) -> None:
        self.name = name
        self.config = config

    def command_metadata(self, context: RunContext, started_at: str) -> dict[str, object]:
        return {
            "agent": self.name,
            "runner": self.config.runner,
            "command": "manual",
            "args": [],
            "cwd": str(context.execution_cwd),
            "started_at": started_at,
        }

    def result_template(self, context: RunContext) -> str:
        task_path = relpath(context.task_path, context.execution_cwd)
        return "\n".join(
            [
                "Manual run is waiting for external work.",
                "",
                f"Task: {task_path}",
                "",
                "Write the final result here, or replace this file when the work is complete.",
                "",
            ]
        )
