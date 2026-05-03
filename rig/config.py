from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import yaml

from rig.prompt import empty_prompt_template_values
from rig.runners import SUPPORTED_RUNNERS


@dataclass(frozen=True)
class AgentConfig:
    runner: str
    command: str
    args: list[str]
    prompt_style: str
    prompt_template: str | None
    timeout_seconds: int


@dataclass(frozen=True)
class RigConfig:
    default_agent: str
    agents: dict[str, AgentConfig]

    def agent(self, name: str) -> AgentConfig:
        try:
            return self.agents[name]
        except KeyError as exc:
            raise ConfigError(f"Agent is not configured: {name}") from exc


class ConfigError(RuntimeError):
    pass


def load_config(path: Path) -> RigConfig:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ConfigError(f"Could not read config file: {path}") from exc
    except yaml.YAMLError as exc:
        raise ConfigError(f"Could not parse config file: {path}") from exc

    if not isinstance(raw, dict):
        raise ConfigError("Config file must contain a YAML mapping.")

    default_agent = raw.get("default_agent", "codex")
    if not isinstance(default_agent, str):
        raise ConfigError("Config value `default_agent` must be a string.")

    raw_agents = raw.get("agents", {})
    if not isinstance(raw_agents, dict):
        raise ConfigError("Config value `agents` must be a mapping.")

    agents: dict[str, AgentConfig] = {}
    for name, value in raw_agents.items():
        if not isinstance(name, str):
            raise ConfigError("Agent names must be strings.")
        if not isinstance(value, dict):
            raise ConfigError(f"Agent config for `{name}` must be a mapping.")
        agents[name] = parse_agent_config(name, cast(dict[str, Any], value))

    return RigConfig(default_agent=default_agent, agents=agents)


def parse_agent_config(name: str, value: dict[str, Any]) -> AgentConfig:
    runner = value.get("runner", "exec")
    if not isinstance(runner, str) or not runner:
        raise ConfigError(f"Config value `agents.{name}.runner` must be a string.")
    if runner not in SUPPORTED_RUNNERS:
        raise ConfigError(
            f"Config value `agents.{name}.runner` must be `exec`, `manual`, or `pty`."
        )

    command = value.get("command", name)
    if not isinstance(command, str) or not command:
        raise ConfigError(f"Config value `agents.{name}.command` must be a string.")

    args = value.get("args", [])
    if args is None:
        args = []
    if not isinstance(args, list) or not all(isinstance(item, str) for item in args):
        raise ConfigError(f"Config value `agents.{name}.args` must be a list of strings.")

    prompt_style = value.get("prompt_style", "rig")
    if not isinstance(prompt_style, str) or not prompt_style:
        raise ConfigError(
            f"Config value `agents.{name}.prompt_style` must be a string."
        )
    if prompt_style not in {"rig", "task", "template"}:
        raise ConfigError(
            f"Config value `agents.{name}.prompt_style` must be `rig`, `task`, or `template`."
        )

    prompt_template = value.get("prompt_template")
    if prompt_template is not None and not isinstance(prompt_template, str):
        raise ConfigError(
            f"Config value `agents.{name}.prompt_template` must be a string."
        )
    if prompt_template is not None and prompt_style != "template":
        raise ConfigError(
            f"Config value `agents.{name}.prompt_style` must be `template` when prompt_template is set."
        )
    if prompt_template is None and prompt_style == "template":
        raise ConfigError(
            f"Config value `agents.{name}.prompt_template` is required when prompt_style is `template`."
        )
    if prompt_template is not None:
        validate_prompt_template(name, prompt_template)

    timeout_seconds = value.get("timeout_seconds", 300)
    if (
        not isinstance(timeout_seconds, int)
        or isinstance(timeout_seconds, bool)
        or timeout_seconds <= 0
    ):
        raise ConfigError(
            f"Config value `agents.{name}.timeout_seconds` must be a positive integer."
        )

    return AgentConfig(
        runner=runner,
        command=command,
        args=cast(list[str], args),
        prompt_style=prompt_style,
        prompt_template=prompt_template,
        timeout_seconds=timeout_seconds,
    )


def validate_prompt_template(name: str, prompt_template: str) -> None:
    try:
        prompt_template.format(**empty_prompt_template_values())
    except KeyError as exc:
        raise ConfigError(
            f"Config value `agents.{name}.prompt_template` uses unknown placeholder: {exc.args[0]}"
        ) from exc
    except (IndexError, ValueError) as exc:
        raise ConfigError(
            f"Config value `agents.{name}.prompt_template` has invalid format: {exc}"
        ) from exc
