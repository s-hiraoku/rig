from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass

from rig.config import AgentConfig
from rig.run_context import RunContext


class AgentCommandNotFoundError(RuntimeError):
    pass


@dataclass(frozen=True)
class AgentResult:
    exit_code: int
    stdout: str
    stderr: str


class ExecAdapter:
    def __init__(self, name: str, config: AgentConfig) -> None:
        self.name = name
        self.config = config

    @property
    def command(self) -> str:
        return self.config.command

    @property
    def args(self) -> list[str]:
        return self.config.args

    def build_prompt(self, context: RunContext) -> str:
        task_path = context.task_path.relative_to(context.cwd)
        if self.config.prompt_style == "task":
            return context.task_path.read_text(encoding="utf-8")
        return "\n".join(
            [
                f"You are running as a delegated {self.name} agent through Rig.",
                "",
                "Read the task file:",
                "",
                str(task_path),
                "",
                "Complete the task and write your final answer to stdout.",
                "",
                "Do not assume Rig will automatically apply changes.",
                "If you modify files, explain what you changed.",
            ]
        )

    def build_command(self, context: RunContext) -> list[str]:
        return [self.command, *self.args, self.build_prompt(context)]

    def command_metadata(self, context: RunContext, started_at: str) -> dict[str, object]:
        command = self.build_command(context)
        return {
            "agent": self.name,
            "runner": self.config.runner,
            "command": command[0],
            "args": command[1:],
            "cwd": str(context.cwd),
            "started_at": started_at,
        }

    def run(self, context: RunContext) -> AgentResult:
        command = self.build_command(context)
        if shutil.which(command[0]) is None:
            raise AgentCommandNotFoundError(
                f"Agent command was not found on PATH: {command[0]}\n"
                "Install the command or update .rig/config.yaml."
            )

        completed = subprocess.run(
            command,
            cwd=context.cwd,
            capture_output=True,
            text=True,
            check=False,
        )
        return AgentResult(
            exit_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )
