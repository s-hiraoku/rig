from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, cast

import yaml

from rig.config import RigConfig, load_config
from rig.run_context import RunContext

DEFAULT_CONFIG = """version: 1

default_agent: codex

agents:
  codex:
    command: codex
    runner: exec
    args:
      - exec

policy:
  default_mode: review
  allow_write: false
  allow_network: false

runs:
  directory: .rig/runs
"""

DEFAULT_ENV_CONFIG = """version: 1

agent_asset_managers:
  - id: apm
    label: APM
    command: apm
    hint: "Choose or install APM if this project uses APM-managed skills, hooks, prompts, or MCP config."
  - id: gh-skills
    label: GitHub skills manager
    command: gh
    args:
      - skills
      - --help
    hint: "Install or update GitHub CLI if this project uses `gh skills` workflows."
  - id: vercel-skills
    label: Vercel skills manager
    command: npx
    hint: "Install Node.js/npm if this project uses Vercel `skills` workflows."

required_files:
  - path: AGENTS.md
    label: Agent instructions
    hint: "Run: rig agents snippet"
"""


def merge_env_defaults(current: dict[str, Any], default: dict[str, Any]) -> bool:
    changed = False

    for key, value in default.items():
        if key in {"agent_asset_managers", "required_files"}:
            continue
        if key not in current:
            current[key] = value
            changed = True

    if merge_asset_managers(current, default):
        changed = True
    if merge_required_files(current, default):
        changed = True

    return changed


def merge_asset_managers(current: dict[str, Any], default: dict[str, Any]) -> bool:
    current_managers = current.get("agent_asset_managers")
    default_managers = default.get("agent_asset_managers")
    if not isinstance(default_managers, list):
        return False
    if current_managers is None:
        current["agent_asset_managers"] = default_managers
        return True
    if not isinstance(current_managers, list):
        return False

    changed = False
    current_by_id = {
        item.get("id"): item
        for item in current_managers
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    for default_item in default_managers:
        if not isinstance(default_item, dict):
            continue
        manager_id = default_item.get("id")
        if not isinstance(manager_id, str):
            continue

        current_item = current_by_id.get(manager_id)
        if current_item is None:
            current_managers.append(default_item)
            changed = True
            continue

        for key, value in default_item.items():
            if key == "required_files":
                if merge_required_files(current_item, default_item):
                    changed = True
            elif key not in current_item:
                current_item[key] = value
                changed = True

    return changed


def merge_required_files(current: dict[str, Any], default: dict[str, Any]) -> bool:
    current_files = current.get("required_files")
    default_files = default.get("required_files")
    if not isinstance(default_files, list):
        return False
    if current_files is None:
        current["required_files"] = default_files
        return True
    if not isinstance(current_files, list):
        return False

    changed = False
    current_paths = {
        required_file_path(item)
        for item in current_files
        if required_file_path(item) is not None
    }
    for default_item in default_files:
        path = required_file_path(default_item)
        if path is not None and path not in current_paths:
            current_files.append(default_item)
            current_paths.add(path)
            changed = True
    return changed


def required_file_path(item: object) -> str | None:
    if isinstance(item, str) and item:
        return item
    if isinstance(item, dict):
        path = item.get("path")
        if isinstance(path, str) and path:
            return path
    return None


class RigNotInitializedError(RuntimeError):
    pass


@dataclass(frozen=True)
class InitResult:
    created: list[str]
    updated: list[str]
    unchanged: list[str]

    @property
    def changed(self) -> bool:
        return bool(self.created or self.updated)


class RunStore:
    def __init__(self, cwd: Path) -> None:
        self.cwd = cwd.resolve()
        self.rig_dir = self.cwd / ".rig"
        self.runs_dir = self.rig_dir / "runs"
        self.config_path = self.rig_dir / "config.yaml"
        self.env_config_path = self.rig_dir / "env.yaml"

    def init(self) -> InitResult:
        created: list[str] = []
        updated: list[str] = []
        unchanged: list[str] = []

        rig_dir_exists = self.rig_dir.exists()
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        if not rig_dir_exists:
            created.append(".rig/")
        if self.runs_dir.exists():
            unchanged.append(".rig/runs/")

        if not self.config_path.exists():
            self.config_path.write_text(DEFAULT_CONFIG, encoding="utf-8")
            created.append(".rig/config.yaml")
        else:
            unchanged.append(".rig/config.yaml")

        if not self.env_config_path.exists():
            self.env_config_path.write_text(DEFAULT_ENV_CONFIG, encoding="utf-8")
            created.append(".rig/env.yaml")
        elif self.update_env_config_defaults():
            updated.append(".rig/env.yaml")
        else:
            unchanged.append(".rig/env.yaml")

        return InitResult(created=created, updated=updated, unchanged=unchanged)

    def update_env_config_defaults(self) -> bool:
        try:
            current = yaml.safe_load(self.env_config_path.read_text(encoding="utf-8"))
            default = yaml.safe_load(DEFAULT_ENV_CONFIG)
        except (OSError, yaml.YAMLError):
            return False

        if not isinstance(current, dict) or not isinstance(default, dict):
            return False

        current_config = cast(dict[str, Any], current)
        default_config = cast(dict[str, Any], default)
        changed = merge_env_defaults(current_config, default_config)
        if not changed:
            return False

        self.env_config_path.write_text(
            yaml.safe_dump(current_config, sort_keys=False),
            encoding="utf-8",
        )
        return True

    def ensure_initialized(self) -> None:
        if not self.rig_dir.is_dir():
            raise RigNotInitializedError(
                "Rig is not initialized in this repository.\nRun `rig init` first."
            )
        self.runs_dir.mkdir(parents=True, exist_ok=True)

    def load_config(self) -> RigConfig:
        self.ensure_initialized()
        return load_config(self.config_path)

    def create_run(self, agent: str, now: datetime | None = None) -> RunContext:
        self.ensure_initialized()
        timestamp = (now or datetime.now().astimezone()).strftime("%Y%m%d-%H%M%S")
        base_id = f"{timestamp}-{agent}"
        run_id = base_id
        suffix = 2
        while (self.runs_dir / run_id).exists():
            run_id = f"{base_id}-{suffix}"
            suffix += 1

        run_dir = self.runs_dir / run_id
        run_dir.mkdir(parents=True)
        return RunContext(
            id=run_id,
            agent=agent,
            run_dir=run_dir,
            task_path=run_dir / "task.md",
            command_path=run_dir / "command.json",
            stdout_path=run_dir / "stdout.log",
            stderr_path=run_dir / "stderr.log",
            result_path=run_dir / "result.md",
            status_path=run_dir / "status.json",
            cwd=self.cwd,
        )

    def write_task(self, context: RunContext, task: str) -> None:
        context.task_path.write_text(f"# Task\n\n{task.rstrip()}\n", encoding="utf-8")

    def write_command(self, context: RunContext, command: dict[str, Any]) -> None:
        context.command_path.write_text(
            json.dumps(command, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def write_status(
        self,
        context: RunContext,
        *,
        status: str,
        started_at: str,
        finished_at: str | None = None,
        exit_code: int | None = None,
    ) -> None:
        data: dict[str, Any] = {
            "id": context.id,
            "agent": context.agent,
            "status": status,
            "started_at": started_at,
            "finished_at": finished_at,
            "exit_code": exit_code,
            "run_dir": self._display_path(context.run_dir),
        }
        context.status_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def list_runs(self) -> list[dict[str, Any]]:
        self.ensure_initialized()
        runs: list[dict[str, Any]] = []
        for status_path in self.runs_dir.glob("*/status.json"):
            try:
                data = json.loads(status_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            runs.append(data)
        return sorted(runs, key=lambda item: str(item.get("started_at", "")), reverse=True)

    def latest_run(self) -> dict[str, Any] | None:
        runs = self.list_runs()
        return runs[0] if runs else None

    def find_run(self, run_id: str) -> dict[str, Any] | None:
        self.ensure_initialized()
        status_path = self.runs_dir / run_id / "status.json"
        if not status_path.is_file():
            return None
        try:
            return cast(
                dict[str, Any], json.loads(status_path.read_text(encoding="utf-8"))
            )
        except (OSError, json.JSONDecodeError):
            return None

    def read_result(self, run: dict[str, Any]) -> str:
        run_dir_value = run.get("run_dir")
        if not isinstance(run_dir_value, str) or not run_dir_value:
            return ""
        run_dir = self.cwd / run_dir_value
        result_path = run_dir / "result.md"
        if not result_path.is_file():
            return ""
        return result_path.read_text(encoding="utf-8")

    def _display_path(self, path: Path) -> str:
        try:
            return str(path.relative_to(self.cwd))
        except ValueError:
            return str(path)
