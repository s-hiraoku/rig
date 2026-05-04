"""Agent adapter registry."""

from __future__ import annotations

from rig.adapters.exec import ExecAdapter
from rig.config import AgentConfig


def create_adapter(name: str, config: AgentConfig) -> ExecAdapter:
    return ExecAdapter(name, config)
