"""Agent adapter registry."""

from __future__ import annotations

from typing import TypeAlias

from rig.adapters.exec import ExecAdapter
from rig.adapters.manual import ManualAdapter
from rig.adapters.pty import PtyAdapter
from rig.config import AgentConfig
from rig.runners import SUPPORTED_RUNNERS

AgentAdapter: TypeAlias = ExecAdapter | ManualAdapter | PtyAdapter

RUNNERS: dict[str, type[AgentAdapter]] = {
    "exec": ExecAdapter,
    "manual": ManualAdapter,
    "pty": PtyAdapter,
}

assert set(RUNNERS) == set(SUPPORTED_RUNNERS)


def create_adapter(
    name: str, config: AgentConfig, *, task: str | None = None
) -> AgentAdapter:
    adapter = RUNNERS[config.runner](name, config)
    if isinstance(adapter, ExecAdapter):
        adapter.task = task
    return adapter
