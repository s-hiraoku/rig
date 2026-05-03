"""Agent adapter registry."""

from __future__ import annotations

from typing import TypeAlias

from rig.adapters.exec import ExecAdapter
from rig.adapters.manual import ManualAdapter
from rig.adapters.pty import PtyAdapter
from rig.config import AgentConfig

AgentAdapter: TypeAlias = ExecAdapter | ManualAdapter | PtyAdapter

RUNNERS: dict[str, type[AgentAdapter]] = {
    "exec": ExecAdapter,
    "manual": ManualAdapter,
    "pty": PtyAdapter,
}


def create_adapter(name: str, config: AgentConfig) -> AgentAdapter:
    return RUNNERS[config.runner](name, config)
