from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime

from rig.run_context import RunContext


class CodexNotFoundError(RuntimeError):
    pass


@dataclass(frozen=True)
class AgentResult:
    exit_code: int
    stdout: str
    stderr: str


class CodexAdapter:
    name = "codex"

    def __init__(self, command: str = "codex") -> None:
        self.command = command

    def build_prompt(self, context: RunContext) -> str:
        task_path = context.task_path.relative_to(context.cwd)
        return "\n".join(
            [
                "You are running as a delegated Codex agent through Rig.",
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
        return [self.command, "exec", self.build_prompt(context)]

    def command_metadata(self, context: RunContext, started_at: str) -> dict[str, object]:
        command = self.build_command(context)
        return {
            "agent": self.name,
            "command": command[0],
            "args": command[1:],
            "cwd": str(context.cwd),
            "started_at": started_at,
        }

    def run(self, context: RunContext) -> AgentResult:
        command = self.build_command(context)
        if shutil.which(command[0]) is None:
            raise CodexNotFoundError(
                "Codex CLI was not found on PATH.\nInstall Codex or update .rig/config.yaml."
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


def iso_now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")

