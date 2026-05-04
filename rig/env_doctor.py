from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from rig.config import ConfigError, load_config
from rig.policy import CLAUDE_INSTRUCTION_PATH, RIG_INSTRUCTION_PATH


@dataclass(frozen=True)
class DoctorCheck:
    label: str
    status: str
    detail: str


@dataclass(frozen=True)
class DoctorReport:
    checks: list[DoctorCheck]
    suggestions: list[str]


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

    agents_path = root / "AGENTS.md"
    if agents_path.is_file():
        checks.append(DoctorCheck("AGENTS.md", "ok", "found"))
        content = agents_path.read_text(encoding="utf-8", errors="replace")
        if RIG_INSTRUCTION_PATH in content:
            checks.append(DoctorCheck("AGENTS.md Rig reference", "ok", "found"))
        else:
            checks.append(
                DoctorCheck("AGENTS.md Rig reference", "warn", "not found")
            )
            suggestions.append("Run: rig init")
    else:
        checks.append(DoctorCheck("AGENTS.md", "missing", "not found"))
        suggestions.append("Run: rig init")

    claude_path = root / CLAUDE_INSTRUCTION_PATH
    if claude_path.is_file():
        checks.append(DoctorCheck("CLAUDE.md", "ok", "found"))
        content = claude_path.read_text(encoding="utf-8", errors="replace")
        if RIG_INSTRUCTION_PATH in content:
            checks.append(DoctorCheck("CLAUDE.md Rig reference", "ok", "found"))
        else:
            checks.append(
                DoctorCheck("CLAUDE.md Rig reference", "warn", "not found")
            )
            suggestions.append("Run: rig init")
    else:
        checks.append(DoctorCheck("CLAUDE.md", "missing", "not found"))
        suggestions.append("Run: rig init")

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
