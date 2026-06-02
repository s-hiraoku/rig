from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import yaml

from rig.config import ConfigError, load_config
from rig.policy import CLAUDE_INSTRUCTION_PATH, RIG_INSTRUCTION_PATH

LEGACY_GEMINI_COMMANDS = {"gemini"}


@dataclass(frozen=True)
class DoctorCheck:
    label: str
    status: str
    detail: str


@dataclass(frozen=True)
class DoctorReport:
    checks: list[DoctorCheck]
    suggestions: list[str]


@dataclass(frozen=True)
class RequiredFile:
    path: str
    label: str
    hint: str | None = None


@dataclass(frozen=True)
class AssetManager:
    id: str
    label: str
    command: str
    args: list[str]
    required_files: list[RequiredFile]
    hint: str | None = None


@dataclass(frozen=True)
class EnvConfig:
    required_files: list[RequiredFile]
    asset_managers: list[AssetManager]


@dataclass(frozen=True)
class ManagerFileStatus:
    path: str
    label: str
    status: str
    hint: str | None = None


@dataclass(frozen=True)
class ManagerStatus:
    id: str
    label: str
    command: str
    args: list[str]
    status: str
    detail: str
    required_files: list[ManagerFileStatus]
    hint: str | None = None


@dataclass(frozen=True)
class ManagerStatusReport:
    managers: list[ManagerStatus]
    warnings: list[str]


def build_doctor_report(cwd: Path) -> DoctorReport:
    root = cwd.resolve()
    checks: list[DoctorCheck] = []
    suggestions: list[str] = []

    if is_git_repo(root):
        checks.append(DoctorCheck("Git repository", "ok", "found"))
    else:
        checks.append(DoctorCheck("Git repository", "missing", "not found"))
        suggestions.append("Run: git init")

    rig_dir = root / ".rig"
    config_path = rig_dir / "config.yaml"
    runs_dir = rig_dir / "runs"
    instruction_path = root / RIG_INSTRUCTION_PATH

    if config_path.is_file():
        checks.append(DoctorCheck("Rig config", "ok", ".rig/config.yaml"))
        add_agent_command_checks(config_path, checks, suggestions)
    else:
        checks.append(DoctorCheck("Rig config", "missing", "missing .rig/config.yaml"))
        suggestions.append("Run: rig init")

    if runs_dir.is_dir():
        checks.append(DoctorCheck("Rig history directory", "ok", ".rig/runs/"))
    else:
        checks.append(
            DoctorCheck("Rig history directory", "missing", "missing .rig/runs/")
        )
        suggestions.append("Run: rig init")

    if instruction_path.is_file():
        checks.append(DoctorCheck("Rig instructions", "ok", RIG_INSTRUCTION_PATH))
    else:
        checks.append(
            DoctorCheck(
                "Rig instructions",
                "missing",
                f"missing {RIG_INSTRUCTION_PATH}",
            )
        )
        suggestions.append("Run: rig init")

    claude_path = root / CLAUDE_INSTRUCTION_PATH
    claude_has_rig_reference = False
    if claude_path.is_file():
        checks.append(DoctorCheck("CLAUDE.md", "ok", "found"))
        content = claude_path.read_text(encoding="utf-8", errors="replace")
        claude_has_rig_reference = RIG_INSTRUCTION_PATH in content
        if claude_has_rig_reference:
            checks.append(DoctorCheck("CLAUDE.md Rig reference", "ok", "found"))
        else:
            checks.append(
                DoctorCheck("CLAUDE.md Rig reference", "warn", "not found")
            )
            suggestions.append("Run: rig init")
    else:
        checks.append(DoctorCheck("CLAUDE.md", "missing", "not found"))
        suggestions.append("Run: rig init")

    agents_path = root / "AGENTS.md"
    if agents_path.is_file():
        checks.append(DoctorCheck("AGENTS.md", "ok", "found"))
        content = agents_path.read_text(encoding="utf-8", errors="replace")
        if RIG_INSTRUCTION_PATH in content:
            checks.append(DoctorCheck("AGENTS.md Rig reference", "ok", "found"))
        elif claude_has_rig_reference:
            checks.append(
                DoctorCheck(
                    "AGENTS.md Rig reference",
                    "optional",
                    "not found; CLAUDE.md references Rig",
                )
            )
        else:
            checks.append(
                DoctorCheck("AGENTS.md Rig reference", "warn", "not found")
            )
            suggestions.append(f"Reference `{RIG_INSTRUCTION_PATH}` from AGENTS.md.")
    else:
        checks.append(DoctorCheck("AGENTS.md", "optional", "not found"))
        if not claude_has_rig_reference:
            suggestions.append("Add the Rig snippet from `rig init` to AGENTS.md.")

    return DoctorReport(checks=checks, suggestions=dedupe(suggestions))


def add_agent_command_checks(
    config_path: Path, checks: list[DoctorCheck], suggestions: list[str]
) -> None:
    try:
        config = load_config(config_path)
    except ConfigError as exc:
        checks.append(DoctorCheck("Configured agents", "warn", str(exc)))
        return

    for name, agent in sorted(config.agents.items()):
        if agent.command in LEGACY_GEMINI_COMMANDS:
            checks.append(
                DoctorCheck(
                    f"Agent command: {name}",
                    "warn",
                    "legacy Gemini CLI config; migrate this agent to Antigravity",
                )
            )
            suggestions.append(
                f"Update agents.{name} in .rig/config.yaml to use "
                "`command: agy`, `args: [-p]`, and `prompt_style: task`."
            )
            continue

        path = shutil.which(agent.command)
        if path is not None:
            checks.append(DoctorCheck(f"Agent command: {name}", "ok", path))
        else:
            checks.append(
                DoctorCheck(
                    f"Agent command: {name}",
                    "missing",
                    f"`{agent.command}` not found on PATH",
                )
            )
            suggestions.append(
                f"Install `{agent.command}` or update agents.{name}.command in "
                ".rig/config.yaml."
            )


def is_git_repo(cwd: Path) -> bool:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return False
    return completed.returncode == 0 and completed.stdout.strip() == "true"


def format_doctor_report(report: DoctorReport) -> str:
    lines = ["Rig doctor", ""]
    for check in report.checks:
        lines.append(f"[{check.status}] {check.label}: {check.detail}")
    lines.append("")
    lines.append("Suggestions")
    if report.suggestions:
        lines.extend(f"- {suggestion}" for suggestion in report.suggestions)
    else:
        lines.append("- No action needed.")
    return "\n".join(lines) + "\n"


def dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            result.append(value)
            seen.add(value)
    return result


def build_manager_status_report(cwd: Path) -> ManagerStatusReport:
    root = cwd.resolve()
    env_path = root / ".rig" / "env.yaml"
    if not env_path.is_file():
        return ManagerStatusReport(
            managers=[],
            warnings=[".rig/env.yaml not found. Run: rig init"],
        )

    checks: list[DoctorCheck] = []
    env_config = load_env_config(env_path, checks)
    warnings = [f"{check.label}: {check.detail}" for check in checks]
    return ManagerStatusReport(
        managers=[
            manager_status(root, manager) for manager in env_config.asset_managers
        ],
        warnings=warnings,
    )


def manager_status(root: Path, manager: AssetManager) -> ManagerStatus:
    path = shutil.which(manager.command)
    if path is None:
        status = "optional"
        detail = f"`{manager.command}` not found on PATH"
    elif manager.args:
        status, detail = check_manager_command(manager)
    else:
        status = "ok"
        detail = path

    return ManagerStatus(
        id=manager.id,
        label=manager.label,
        command=manager.command,
        args=manager.args,
        status=status,
        detail=detail,
        required_files=[
            manager_file_status(root, required_file)
            for required_file in manager.required_files
        ],
        hint=manager.hint,
    )


def check_manager_command(manager: AssetManager) -> tuple[str, str]:
    command = [manager.command, *manager.args]
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return "warn", "could not check"
    if completed.returncode == 0:
        return "ok", "available"
    return "warn", "check command failed"


def manager_file_status(root: Path, required_file: RequiredFile) -> ManagerFileStatus:
    status = "ok" if (root / required_file.path).is_file() else "missing"
    return ManagerFileStatus(
        path=required_file.path,
        label=required_file.label,
        status=status,
        hint=required_file.hint,
    )


def load_env_config(env_path: Path, checks: list[DoctorCheck]) -> EnvConfig:
    try:
        raw = yaml.safe_load(env_path.read_text(encoding="utf-8"))
    except OSError:
        checks.append(
            DoctorCheck("Rig env config", "warn", "could not read .rig/env.yaml")
        )
        return EnvConfig(required_files=[], asset_managers=[])
    except yaml.YAMLError:
        checks.append(
            DoctorCheck("Rig env config", "warn", "could not parse .rig/env.yaml")
        )
        return EnvConfig(required_files=[], asset_managers=[])

    if raw is None:
        return EnvConfig(required_files=[], asset_managers=[])
    if not isinstance(raw, dict):
        checks.append(DoctorCheck("Rig env config", "warn", "must contain a mapping"))
        return EnvConfig(required_files=[], asset_managers=[])

    value = cast(dict[str, Any], raw)
    return EnvConfig(
        required_files=parse_required_files(value, checks),
        asset_managers=parse_asset_managers(value, checks),
    )


def parse_required_files(
    value: dict[str, Any],
    checks: list[DoctorCheck],
    *,
    field_path: str = "required_files",
    check_label: str = "Rig env required files",
) -> list[RequiredFile]:
    raw_required_files = value.get("required_files", [])
    if raw_required_files is None:
        return []
    if not isinstance(raw_required_files, list):
        checks.append(
            DoctorCheck(check_label, "warn", f"`{field_path}` must be a list")
        )
        return []

    required_files: list[RequiredFile] = []
    for index, item in enumerate(raw_required_files):
        parsed = parse_required_file(
            item,
            index,
            checks,
            field_path=field_path,
            check_label=check_label,
        )
        if parsed is not None:
            required_files.append(parsed)
    return required_files


def parse_asset_managers(
    value: dict[str, Any], checks: list[DoctorCheck]
) -> list[AssetManager]:
    raw_managers = value.get("agent_asset_managers", [])
    if raw_managers is None:
        return []
    if not isinstance(raw_managers, list):
        checks.append(
            DoctorCheck(
                "Rig env asset managers",
                "warn",
                "`agent_asset_managers` must be a list",
            )
        )
        return []

    managers: list[AssetManager] = []
    for index, item in enumerate(raw_managers):
        parsed = parse_asset_manager(item, index, checks)
        if parsed is not None:
            managers.append(parsed)
    return managers


def parse_asset_manager(
    item: object, index: int, checks: list[DoctorCheck]
) -> AssetManager | None:
    if not isinstance(item, dict):
        checks.append(
            DoctorCheck(
                "Rig env asset managers",
                "warn",
                f"agent_asset_managers[{index}] must be a mapping",
            )
        )
        return None

    value = cast(dict[str, Any], item)
    manager_id = value.get("id")
    if not isinstance(manager_id, str) or not manager_id:
        checks.append(
            DoctorCheck(
                "Rig env asset managers",
                "warn",
                f"agent_asset_managers[{index}].id must be a non-empty string",
            )
        )
        return None

    command = value.get("command")
    if not isinstance(command, str) or not command:
        checks.append(
            DoctorCheck(
                "Rig env asset managers",
                "warn",
                f"agent_asset_managers[{index}].command must be a non-empty string",
            )
        )
        return None

    label = value.get("label", manager_id)
    if not isinstance(label, str) or not label:
        checks.append(
            DoctorCheck(
                "Rig env asset managers",
                "warn",
                f"agent_asset_managers[{index}].label must be a non-empty string",
            )
        )
        return None

    args = value.get("args", [])
    if args is None:
        args = []
    if not isinstance(args, list) or not all(isinstance(arg, str) for arg in args):
        checks.append(
            DoctorCheck(
                "Rig env asset managers",
                "warn",
                f"agent_asset_managers[{index}].args must be a list of strings",
            )
        )
        return None

    hint = value.get("hint")
    if hint is not None and not isinstance(hint, str):
        checks.append(
            DoctorCheck(
                "Rig env asset managers",
                "warn",
                f"agent_asset_managers[{index}].hint must be a string",
            )
        )
        return None

    return AssetManager(
        id=manager_id,
        label=label,
        command=command,
        args=cast(list[str], args),
        required_files=parse_required_files(
            value,
            checks,
            field_path=f"agent_asset_managers[{index}].required_files",
            check_label="Rig env asset manager files",
        ),
        hint=hint,
    )


def parse_required_file(
    item: object,
    index: int,
    checks: list[DoctorCheck],
    *,
    field_path: str,
    check_label: str,
) -> RequiredFile | None:
    item_path = f"{field_path}[{index}]"
    if isinstance(item, str):
        if not item:
            checks.append(
                DoctorCheck(check_label, "warn", f"{item_path} must not be empty")
            )
            return None
        return RequiredFile(path=item, label=item)

    if not isinstance(item, dict):
        checks.append(
            DoctorCheck(
                check_label, "warn", f"{item_path} must be a string or mapping"
            )
        )
        return None

    value = cast(dict[str, Any], item)
    path = value.get("path")
    if not isinstance(path, str) or not path:
        checks.append(
            DoctorCheck(
                check_label, "warn", f"{item_path}.path must be a non-empty string"
            )
        )
        return None

    label = value.get("label", path)
    if not isinstance(label, str) or not label:
        checks.append(
            DoctorCheck(
                check_label, "warn", f"{item_path}.label must be a non-empty string"
            )
        )
        return None

    hint = value.get("hint")
    if hint is not None and not isinstance(hint, str):
        checks.append(
            DoctorCheck(
                check_label, "warn", f"{item_path}.hint must be a string"
            )
        )
        return None

    return RequiredFile(path=path, label=label, hint=hint)


def format_manager_status_report(report: ManagerStatusReport) -> str:
    lines = ["Rig agent asset managers", ""]
    if report.warnings:
        lines.append("Warnings")
        lines.extend(f"- {warning}" for warning in report.warnings)
        lines.append("")

    if not report.managers:
        lines.append("No agent asset managers declared in .rig/env.yaml.")
        return "\n".join(lines) + "\n"

    for manager in report.managers:
        command = " ".join([manager.command, *manager.args])
        lines.append(f"[{manager.status}] {manager.label}: {command}")
        lines.append(f"  {manager.detail}")
        if manager.hint:
            lines.append(f"  Hint: {manager.hint}")
        if manager.required_files:
            lines.append("  Required files:")
            for required_file in manager.required_files:
                lines.append(
                    f"  - [{required_file.status}] "
                    f"{required_file.label}: {required_file.path}"
                )
                if required_file.status != "ok" and required_file.hint:
                    lines.append(f"    Hint: {required_file.hint}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
