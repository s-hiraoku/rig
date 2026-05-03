from __future__ import annotations

from pathlib import Path

import pytest

from rig.config import ConfigError, load_config


def test_load_config_reads_agent_command_and_args(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """version: 1
default_agent: codex
agents:
  codex:
    runner: exec
    command: custom-codex
    args:
      - exec
      - --sandbox
    prompt_style: task
""",
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.default_agent == "codex"
    assert config.agent("codex").runner == "exec"
    assert config.agent("codex").command == "custom-codex"
    assert config.agent("codex").args == ["exec", "--sandbox"]
    assert config.agent("codex").prompt_style == "task"


def test_load_config_rejects_invalid_agent_args(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """version: 1
agents:
  codex:
    command: codex
    args: exec
""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="agents.codex.args"):
        load_config(config_path)


def test_load_config_rejects_unsupported_runner(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """version: 1
agents:
  copilot:
    runner: pty
    command: copilot
""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="agents.copilot.runner"):
        load_config(config_path)
