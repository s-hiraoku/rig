from __future__ import annotations

from datetime import datetime

from rig.adapters.exec import AgentCommandNotFoundError, AgentResult, ExecAdapter
from rig.config import AgentConfig
from rig.run_context import RunContext


class CodexNotFoundError(AgentCommandNotFoundError):
    pass


class CodexAdapter(ExecAdapter):
    def __init__(self, command: str = "codex", args: list[str] | None = None) -> None:
        config = AgentConfig(
            command=command,
            args=args or ["exec"],
            prompt_style="rig",
            prompt_template=None,
            timeout_seconds=300,
        )
        super().__init__("codex", config)

    def run(self, context: RunContext) -> AgentResult:
        try:
            return super().run(context)
        except AgentCommandNotFoundError as exc:
            raise CodexNotFoundError(
                "Codex CLI was not found on PATH.\n"
                "Install Codex or update .rig/config.yaml."
            ) from exc


def iso_now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")
