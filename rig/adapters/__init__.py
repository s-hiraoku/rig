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

if set(RUNNERS) != set(SUPPORTED_RUNNERS):
    mismatch = ", ".join(sorted(set(RUNNERS) ^ set(SUPPORTED_RUNNERS)))
    raise RuntimeError(f"Runner registry mismatch: {mismatch}")


def create_adapter(name: str, config: AgentConfig) -> AgentAdapter:
    return RUNNERS[config.runner](name, config)
