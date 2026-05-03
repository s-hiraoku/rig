from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, cast

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
    args:
      - --no-install
      - skills
      - --help
    hint: "Install Node.js/npm if this project uses Vercel `skills` workflows."

required_files:
  - path: AGENTS.md
    label: Agent instructions
    hint: "Run: rig guide agents"
"""


class RigNotInitializedError(RuntimeError):
    pass


@dataclass(frozen=True)
class InitResult:
    created: list[str]
    updated: list[str]
    backups: list[str]
    unchanged: list[str]

    @property
    def changed(self) -> bool:
        return bool(self.created or self.updated)


@dataclass(frozen=True)
class RunArtifacts:
    cwd: Path
    runs_dir: Path
    run: dict[str, Any]

    @property
    def run_dir(self) -> Path | None:
        run_dir_value = self.run.get("run_dir")
        if not isinstance(run_dir_value, str) or not run_dir_value:
            return None
        run_dir = resolve_metadata_path(
            run_dir_value,
            base=self.cwd,
            root=self.runs_dir,
            field="run_dir",
        )
        return run_dir

    def path(self, filename: str) -> Path | None:
        """Return an artifact path, raising ValueError if filename escapes run_dir."""
        run_dir = self.run_dir
        if run_dir is None:
            return None
        artifact_path = (run_dir / filename).resolve()
        if not artifact_path.is_relative_to(run_dir):
            raise ValueError(f"artifact path is outside the run directory: {filename}")
        return artifact_path

    def read(self, filename: str) -> str:
        artifact_path = self.path(filename)
        if artifact_path is None or not artifact_path.is_file():
            return ""
        return artifact_path.read_text(encoding="utf-8", errors="replace")

    def write(self, filename: str, content: str) -> None:
        artifact_path = self.path(filename)
        if artifact_path is None:
            raise RigNotInitializedError("Run metadata does not contain a run directory.")
        artifact_path.write_text(content, encoding="utf-8")


class RunStore:
    def __init__(self, cwd: Path) -> None:
        self.cwd = cwd.resolve()
        self.rig_dir = self.cwd / ".rig"
        self.runs_dir = self.rig_dir / "runs"
        self.worktrees_dir = self.rig_dir / "worktrees"
        self.config_path = self.rig_dir / "config.yaml"
        self.env_config_path = self.rig_dir / "env.yaml"

    def init(
        self, *, reset: str | None = None, now: datetime | None = None
    ) -> InitResult:
        created: list[str] = []
        updated: list[str] = []
        backups: list[str] = []
        unchanged: list[str] = []

        rig_dir_exists = self.rig_dir.exists()
        runs_dir_exists = self.runs_dir.exists()
        if not rig_dir_exists:
            created.append(".rig/")
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        if runs_dir_exists:
            unchanged.append(".rig/runs/")
        else:
            created.append(".rig/runs/")

        reset_config = reset in {"config", "all"}
        reset_env = reset in {"env", "all"}

        if reset_config:
            self.reset_file(
                self.config_path,
                DEFAULT_CONFIG,
                ".rig/config.yaml",
                created=created,
                updated=updated,
                backups=backups,
                now=now,
            )
        elif not self.config_path.exists():
            self.config_path.write_text(DEFAULT_CONFIG, encoding="utf-8")
            created.append(".rig/config.yaml")
        else:
            unchanged.append(".rig/config.yaml")

        if reset_env:
            self.reset_file(
                self.env_config_path,
                DEFAULT_ENV_CONFIG,
                ".rig/env.yaml",
                created=created,
                updated=updated,
                backups=backups,
                now=now,
            )
        elif not self.env_config_path.exists():
            self.env_config_path.write_text(DEFAULT_ENV_CONFIG, encoding="utf-8")
            created.append(".rig/env.yaml")
        else:
            unchanged.append(".rig/env.yaml")

        return InitResult(
            created=created,
            updated=updated,
            backups=backups,
            unchanged=unchanged,
        )

    def reset_file(
        self,
        path: Path,
        content: str,
        display_path: str,
        *,
        created: list[str],
        updated: list[str],
        backups: list[str],
        now: datetime | None,
    ) -> None:
        if path.exists():
            backup_path = self.backup_path(path, now=now)
            path.replace(backup_path)
            backups.append(self.display_path(backup_path))
            updated.append(display_path)
        else:
            created.append(display_path)
        path.write_text(content, encoding="utf-8")

    def backup_path(self, path: Path, *, now: datetime | None = None) -> Path:
        timestamp = (now or datetime.now().astimezone()).strftime("%Y%m%d-%H%M%S")
        backup_path = path.with_name(f"{path.name}.bak-{timestamp}")
        suffix = 2
        while backup_path.exists():
            backup_path = path.with_name(f"{path.name}.bak-{timestamp}-{suffix}")
            suffix += 1
        return backup_path

    def ensure_initialized(self) -> None:
        if not self.rig_dir.is_dir():
            raise RigNotInitializedError(
                "Rig is not initialized in this repository.\nRun `rig init` first."
            )
        self.runs_dir.mkdir(parents=True, exist_ok=True)

    def load_config(self) -> RigConfig:
        self.ensure_initialized()
        return load_config(self.config_path)

    def create_run(
        self, agent: str, raw_task: str, now: datetime | None = None
    ) -> RunContext:
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
            raw_task=raw_task,
            run_dir=run_dir,
            task_path=run_dir / "task.md",
            command_path=run_dir / "command.json",
            stdout_path=run_dir / "stdout.log",
            stderr_path=run_dir / "stderr.log",
            result_path=run_dir / "result.md",
            status_path=run_dir / "status.json",
            diff_path=run_dir / "diff.patch",
            worktree_path=None,
            cwd=self.cwd,
            execution_cwd=self.cwd,
        )

    def write_task(self, context: RunContext, task: str, *, wrap: bool = True) -> None:
        content = f"# Task\n\n{task.rstrip()}\n" if wrap else ensure_trailing_newline(task)
        context.task_path.write_text(content, encoding="utf-8")

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
            "run_dir": self.display_path(context.run_dir),
            "execution_cwd": self.display_path(context.execution_cwd),
        }
        if context.worktree_path is not None:
            data["worktree_dir"] = self.display_path(context.worktree_path)
            data["diff_path"] = self.display_path(context.diff_path)
        context.status_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def write_run_status(
        self,
        run: dict[str, Any],
        *,
        status: str,
        finished_at: str | None = None,
        exit_code: int | None = None,
    ) -> None:
        run_dir = self.artifacts(run).run_dir
        if run_dir is None:
            raise RigNotInitializedError("Run metadata does not contain a run directory.")
        status_path = run_dir / "status.json"
        data = dict(run)
        data["status"] = status
        data["finished_at"] = finished_at
        data["exit_code"] = exit_code
        status_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def write_run_artifact(
        self, run: dict[str, Any], filename: str, content: str
    ) -> None:
        self.artifacts(run).write(filename, content)

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

    def resolve_run(self, run_id: str) -> dict[str, Any] | None:
        return self.latest_run() if run_id == "latest" else self.find_run(run_id)

    def find_run(self, run_id: str) -> dict[str, Any] | None:
        self.ensure_initialized()
        run_dir = resolve_run_lookup_path(run_id, runs_dir=self.runs_dir)
        if run_dir is None:
            return None
        status_path = run_dir / "status.json"
        if not status_path.is_file():
            return None
        try:
            return cast(
                dict[str, Any], json.loads(status_path.read_text(encoding="utf-8"))
            )
        except (OSError, json.JSONDecodeError):
            return None

    def read_result(self, run: dict[str, Any]) -> str:
        return self.read_artifact(run, "result.md")

    def read_artifact(self, run: dict[str, Any], filename: str) -> str:
        return self.artifacts(run).read(filename)

    def artifacts(self, run: dict[str, Any]) -> RunArtifacts:
        return RunArtifacts(self.cwd, self.runs_dir, run)

    def resolve_diff_path(self, run: dict[str, Any]) -> Path | None:
        diff_path_value = run.get("diff_path")
        if not isinstance(diff_path_value, str) or not diff_path_value:
            return None
        run_dir = self.artifacts(run).run_dir
        if run_dir is None:
            raise RigNotInitializedError("Run metadata does not contain a run directory.")
        return resolve_metadata_path(
            diff_path_value,
            base=self.cwd,
            root=run_dir,
            field="diff_path",
        )

    def display_path(self, path: Path) -> str:
        try:
            return str(path.relative_to(self.cwd))
        except ValueError:
            return str(path)


def resolve_metadata_path(value: str, *, base: Path, root: Path, field: str) -> Path:
    path = Path(value).expanduser()
    resolved = path.resolve() if path.is_absolute() else (base / path).resolve()
    if not resolved.is_relative_to(root):
        raise ValueError(f"{field} is outside the expected Rig directory: {value}")
    return resolved


def resolve_run_lookup_path(run_id: str, *, runs_dir: Path) -> Path | None:
    if not run_id:
        return None
    path = Path(run_id)
    if path.is_absolute() or path.name != run_id or run_id in {".", ".."}:
        return None
    resolved = (runs_dir / run_id).resolve()
    runs_root = runs_dir.resolve()
    if resolved.parent != runs_root or not resolved.is_relative_to(runs_root):
        return None
    return resolved


def ensure_trailing_newline(value: str) -> str:
    return value if value.endswith("\n") else f"{value}\n"
