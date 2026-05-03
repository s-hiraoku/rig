from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


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

    add_git_checks(root, checks, suggestions)
    add_rig_checks(root, checks, suggestions)
    add_tool_checks(checks, suggestions)
    add_agent_asset_checks(root, checks, suggestions)

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


def add_tool_checks(checks: list[DoctorCheck], suggestions: list[str]) -> None:
    add_tool_check(
        checks,
        suggestions,
        label="Codex CLI",
        command="codex",
        install_hint="Install Codex CLI and ensure `codex` is on PATH.",
        missing_status="missing",
    )
    add_tool_check(
        checks,
        suggestions,
        label="APM",
        command="apm",
        install_hint="Install APM if this project uses APM-managed agent assets.",
        missing_status="optional",
    )
    gh_found = add_tool_check(
        checks,
        suggestions,
        label="GitHub CLI",
        command="gh",
        install_hint="Install GitHub CLI if you use `gh skill` workflows.",
        missing_status="optional",
    )
    if gh_found:
        add_gh_skill_check(checks, suggestions)

    add_tool_check(
        checks,
        suggestions,
        label="npx",
        command="npx",
        install_hint="Install Node.js/npm if you use Vercel `skills` workflows.",
        missing_status="optional",
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


def add_gh_skill_check(checks: list[DoctorCheck], suggestions: list[str]) -> None:
    try:
        completed = subprocess.run(
            ["gh", "skill", "--help"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        checks.append(DoctorCheck("gh skill", "warn", "could not check"))
        suggestions.append("Run: gh skill --help")
        return

    if completed.returncode == 0:
        checks.append(DoctorCheck("gh skill", "ok", "available"))
    else:
        checks.append(DoctorCheck("gh skill", "optional", "not available"))
        suggestions.append("Update GitHub CLI or enable `gh skill` if needed.")


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

    apm_path = root / "apm.yml"
    apm_lock_path = root / "apm.lock.yaml"
    if apm_path.is_file():
        checks.append(DoctorCheck("APM manifest", "ok", "apm.yml"))
        if apm_lock_path.is_file():
            checks.append(DoctorCheck("APM lockfile", "ok", "apm.lock.yaml"))
        else:
            checks.append(DoctorCheck("APM lockfile", "warn", "not found"))
            suggestions.append("Run: apm install")
    else:
        checks.append(DoctorCheck("APM manifest", "optional", "not found"))
        suggestions.append("Create apm.yml if this project uses APM.")


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
        "- Optional agent asset managers available as needed: APM, `gh skill`, Vercel `skills` via `npx`",
        "- Optional agent instructions such as `AGENTS.md` include the Rig snippet",
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
