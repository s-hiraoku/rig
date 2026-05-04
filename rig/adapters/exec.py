from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from os.path import relpath

from rig.config import AgentConfig
from rig.prompt import prompt_template_values
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
        task_path = relpath(context.task_path, context.execution_cwd)
        if self.config.prompt_template is not None:
            return self.config.prompt_template.format(
                **prompt_template_values(
                    agent=self.name,
                    task_path=task_path,
                    task=context.raw_task,
                    task_md=context.task_path.read_text(encoding="utf-8"),
                )
            )
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
            "cwd": str(context.execution_cwd),
            "started_at": started_at,
            "timeout_seconds": self.config.timeout_seconds,
        }

    def run(self, context: RunContext) -> AgentResult:
        command = self.build_command(context)
        if shutil.which(command[0]) is None:
            raise AgentCommandNotFoundError(
                f"Agent command was not found on PATH: {command[0]}\n"
                "Install the command or update .rig/config.yaml."
            )

        try:
            completed = subprocess.run(
                command,
                cwd=context.execution_cwd,
                capture_output=True,
                text=True,
                check=False,
                timeout=self.config.timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            stdout = decode_timeout_output(exc.stdout)
            stderr = decode_timeout_output(exc.stderr)
            if stderr and not stderr.endswith("\n"):
                stderr += "\n"
            stderr += f"Rig exec runner timed out after {self.config.timeout_seconds} seconds.\n"
            return AgentResult(exit_code=124, stdout=stdout, stderr=stderr)

        return AgentResult(
            exit_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )


def decode_timeout_output(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value
