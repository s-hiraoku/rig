from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

import yaml


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


def build_doctor_report(cwd: Path) -> DoctorReport:
    root = cwd.resolve()
    checks: list[DoctorCheck] = []
    suggestions: list[str] = []

    add_git_checks(root, checks, suggestions)
    add_rig_checks(root, checks, suggestions)
    add_codex_check(checks, suggestions)
    add_agent_asset_checks(root, checks, suggestions)
    add_env_config_checks(root, checks, suggestions)

    return DoctorReport(checks=checks, suggestions=dedupe(suggestions))


def add_git_checks(
    root: Path, checks: list[DoctorCheck], suggestions: list[str]
) -> None:
    if find_git_dir(root) is not None:
        checks.append(DoctorCheck("Git repository", "ok", "found"))
    else:
        checks.append(DoctorCheck("Git repository", "missing", "not found"))
        suggestions.append("Run: git init")


def add_rig_checks(
    root: Path, checks: list[DoctorCheck], suggestions: list[str]
) -> None:
    rig_dir = root / ".rig"
    config_path = rig_dir / "config.yaml"
    runs_dir = rig_dir / "runs"

    if config_path.is_file():
        checks.append(DoctorCheck("Rig config", "ok", ".rig/config.yaml"))
    else:
        checks.append(DoctorCheck("Rig config", "missing", "missing .rig/config.yaml"))
        suggestions.append("Run: rig init")

    if runs_dir.is_dir():
        checks.append(DoctorCheck("Rig runs directory", "ok", ".rig/runs/"))
    else:
        checks.append(DoctorCheck("Rig runs directory", "missing", "missing .rig/runs/"))
        suggestions.append("Run: rig init")


def add_codex_check(checks: list[DoctorCheck], suggestions: list[str]) -> None:
    add_tool_check(
        checks,
        suggestions,
        label="Codex CLI",
        command="codex",
        install_hint="Install Codex CLI and ensure `codex` is on PATH.",
        missing_status="missing",
    )


def add_tool_check(
    checks: list[DoctorCheck],
    suggestions: list[str],
    *,
    label: str,
    command: str,
    install_hint: str,
    missing_status: str,
) -> bool:
    path = shutil.which(command)
    if path:
        checks.append(DoctorCheck(label, "ok", path))
        return True

    checks.append(DoctorCheck(label, missing_status, f"`{command}` not found on PATH"))
    suggestions.append(install_hint)
    return False


def add_agent_asset_checks(
    root: Path, checks: list[DoctorCheck], suggestions: list[str]
) -> None:
    agents_path = root / "AGENTS.md"
    if agents_path.is_file():
        checks.append(DoctorCheck("AGENTS.md", "ok", "found"))
        content = agents_path.read_text(encoding="utf-8", errors="replace")
        if "## Rig" in content and "rig runs show latest" in content:
            checks.append(DoctorCheck("Rig AGENTS.md snippet", "ok", "found"))
        else:
            checks.append(DoctorCheck("Rig AGENTS.md snippet", "warn", "not found"))
            suggestions.append("Run: rig agents snippet")
    else:
        checks.append(DoctorCheck("AGENTS.md", "optional", "not found"))
        suggestions.append("Run: rig agents snippet")


def add_env_config_checks(
    root: Path, checks: list[DoctorCheck], suggestions: list[str]
) -> None:
    env_path = root / ".rig" / "env.yaml"
    if not env_path.is_file():
        checks.append(DoctorCheck("Rig env config", "optional", "not found"))
        suggestions.append("Create .rig/env.yaml to declare project-specific harness requirements.")
        return

    checks.append(DoctorCheck("Rig env config", "ok", ".rig/env.yaml"))
    env_config = load_env_config(env_path, checks)
    for manager in env_config.asset_managers:
        add_asset_manager_check(manager, checks, suggestions)
        add_manager_required_file_checks(root, manager, checks, suggestions)

    for required_file in env_config.required_files:
        add_required_file_check(
            root,
            required_file,
            label=f"Required file: {required_file.label}",
            checks=checks,
            suggestions=suggestions,
        )


def add_manager_required_file_checks(
    root: Path,
    manager: AssetManager,
    checks: list[DoctorCheck],
    suggestions: list[str],
) -> None:
    for required_file in manager.required_files:
        add_required_file_check(
            root,
            required_file,
            label=f"Agent asset manager file: {manager.label} / {required_file.label}",
            checks=checks,
            suggestions=suggestions,
        )


def add_required_file_check(
    root: Path,
    required_file: RequiredFile,
    *,
    label: str,
    checks: list[DoctorCheck],
    suggestions: list[str],
) -> None:
    target = root / required_file.path
    if target.is_file():
        checks.append(DoctorCheck(label, "ok", required_file.path))
    else:
        checks.append(DoctorCheck(label, "missing", required_file.path))
        if required_file.hint:
            suggestions.append(required_file.hint)


def add_asset_manager_check(
    manager: AssetManager, checks: list[DoctorCheck], suggestions: list[str]
) -> None:
    path = shutil.which(manager.command)
    label = f"Agent asset manager: {manager.label}"
    if path is None:
        checks.append(
            DoctorCheck(label, "optional", f"`{manager.command}` not found on PATH")
        )
        if manager.hint:
            suggestions.append(manager.hint)
        return

    if not manager.args:
        checks.append(DoctorCheck(label, "ok", path))
        return

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
        checks.append(DoctorCheck(label, "warn", "could not check"))
        if manager.hint:
            suggestions.append(manager.hint)
        return

    if completed.returncode == 0:
        checks.append(DoctorCheck(label, "ok", "available"))
    else:
        checks.append(DoctorCheck(label, "warn", "check command failed"))
        if manager.hint:
            suggestions.append(manager.hint)


def load_env_config(env_path: Path, checks: list[DoctorCheck]) -> EnvConfig:
    try:
        raw = yaml.safe_load(env_path.read_text(encoding="utf-8"))
    except OSError:
        checks.append(DoctorCheck("Rig env config", "warn", "could not read .rig/env.yaml"))
        return EnvConfig(required_files=[], asset_managers=[])
    except yaml.YAMLError:
        checks.append(DoctorCheck("Rig env config", "warn", "could not parse .rig/env.yaml"))
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
                DoctorCheck(
                    check_label,
                    "warn",
                    f"{item_path} must not be empty",
                )
            )
            return None
        return RequiredFile(path=item, label=item)

    if not isinstance(item, dict):
        checks.append(
            DoctorCheck(
                check_label,
                "warn",
                f"{item_path} must be a string or mapping",
            )
        )
        return None

    value = cast(dict[str, Any], item)
    path = value.get("path")
    if not isinstance(path, str) or not path:
        checks.append(
            DoctorCheck(
                check_label,
                "warn",
                f"{item_path}.path must be a non-empty string",
            )
        )
        return None

    label = value.get("label", path)
    if not isinstance(label, str) or not label:
        checks.append(
            DoctorCheck(
                check_label,
                "warn",
                f"{item_path}.label must be a non-empty string",
            )
        )
        return None

    hint = value.get("hint")
    if hint is not None and not isinstance(hint, str):
        checks.append(
            DoctorCheck(
                check_label,
                "warn",
                f"{item_path}.hint must be a string",
            )
        )
        return None

    return RequiredFile(path=path, label=label, hint=hint)


def find_git_dir(start: Path) -> Path | None:
    current = start
    while True:
        git_dir = current / ".git"
        if git_dir.exists():
            return git_dir
        if current.parent == current:
            return None
        current = current.parent


def format_doctor_report(report: DoctorReport) -> str:
    lines = ["Rig environment", ""]
    for check in report.checks:
        lines.append(f"{format_status(check.status)} {check.label}: {check.detail}")

    if report.suggestions:
        lines.extend(["", "Suggested next steps"])
        lines.extend(f"- {suggestion}" for suggestion in report.suggestions)

    return "\n".join(lines)


def format_env_plan(report: DoctorReport) -> str:
    lines = [
        "Rig environment plan",
        "",
        "Desired harness",
        "- Git repository for trusted agent execution",
        "- Rig initialized with `.rig/config.yaml` and `.rig/runs/`",
        "- Codex CLI available for `rig run codex`",
        "- Optional agent asset managers available as needed: APM, `gh skills`, Vercel `skills` via `npx`, or manual instructions",
        "- Optional agent instructions such as `AGENTS.md` include the Rig snippet",
        "- Project-specific required files declared in `.rig/env.yaml` are present",
        "",
        "Current gaps",
    ]

    gaps = [
        check
        for check in report.checks
        if check.status in {"missing", "warn", "optional"}
    ]
    if gaps:
        lines.extend(
            f"- {format_status(check.status)} {check.label}: {check.detail}"
            for check in gaps
        )
    else:
        lines.append("- [ok] No gaps detected.")

    lines.extend(["", "Planned actions"])
    if report.suggestions:
        lines.extend(f"- {suggestion}" for suggestion in report.suggestions)
    else:
        lines.append("- No action needed.")

    if any("asset manager" in check.label for check in report.checks):
        lines.append(
            "- Agent asset managers are optional. Pick one only if this project needs shared skills, hooks, prompts, or MCP config."
        )

    lines.extend(
        [
            "",
            "No files will be changed.",
            "Rig will not install external tools or third-party agent assets from this plan.",
        ]
    )
    return "\n".join(lines)


def format_status(status: str) -> str:
    if status == "ok":
        return "[ok]"
    if status == "missing":
        return "[missing]"
    if status == "optional":
        return "[optional]"
    if status == "warn":
        return "[warn]"
    return f"[{status}]"


def dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result
