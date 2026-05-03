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
    assert config.agent("codex").prompt_template is None
    assert config.agent("codex").timeout_seconds == 300


def test_load_config_accepts_prompt_template(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """version: 1
agents:
  codex:
    command: codex
    prompt_style: template
    prompt_template: "Agent {agent} reads {task_path}: {task}"
""",
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.agent("codex").prompt_template == (
        "Agent {agent} reads {task_path}: {task}"
    )


def test_load_config_rejects_prompt_template_unknown_placeholder(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """version: 1
agents:
  codex:
    command: codex
    prompt_style: template
    prompt_template: "Agent {agent} reads {wrong_key}"
""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="unknown placeholder: wrong_key"):
        load_config(config_path)


def test_load_config_rejects_prompt_template_invalid_format(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """version: 1
agents:
  codex:
    command: codex
    prompt_style: template
    prompt_template: "Agent {agent"
""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="invalid format"):
        load_config(config_path)


def test_load_config_rejects_prompt_template_without_template_style(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """version: 1
agents:
  codex:
    command: codex
    prompt_template: "hello"
""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="prompt_style"):
        load_config(config_path)


def test_load_config_rejects_template_style_without_prompt_template(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """version: 1
agents:
  codex:
    command: codex
    prompt_style: template
""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="prompt_template"):
        load_config(config_path)


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


def test_load_config_accepts_manual_runner(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """version: 1
agents:
  external:
    runner: manual
""",
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.agent("external").runner == "manual"
    assert config.agent("external").command == "external"


def test_load_config_accepts_pty_runner_with_timeout(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """version: 1
agents:
  interactive:
    runner: pty
    command: interactive
    timeout_seconds: 5
""",
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.agent("interactive").runner == "pty"
    assert config.agent("interactive").timeout_seconds == 5


def test_load_config_rejects_invalid_timeout(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """version: 1
agents:
  interactive:
    runner: pty
    timeout_seconds: 0
""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="agents.interactive.timeout_seconds"):
        load_config(config_path)


def test_load_config_rejects_unsupported_runner(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        """version: 1
agents:
  copilot:
    runner: docker
    command: copilot
""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigError, match="agents.copilot.runner"):
        load_config(config_path)
