from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from rig import env_doctor


def test_build_doctor_report_reports_missing_basics(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(env_doctor.shutil, "which", lambda command: None)

    report = env_doctor.build_doctor_report(tmp_path)

    labels = {check.label: check for check in report.checks}
    assert labels["Git repository"].status == "missing"
    assert labels["Rig config"].status == "missing"
    assert labels["Codex CLI"].status == "missing"
    assert labels["Rig env config"].status == "optional"
    assert "Run: git init" in report.suggestions
    assert "Run: rig init" in report.suggestions
    assert "Run: rig guide agents" in report.suggestions
    assert (
        "Create .rig/env.yaml to declare project-specific harness requirements."
        in report.suggestions
    )


def test_build_doctor_report_detects_agent_environment_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / ".git").mkdir()
    (tmp_path / ".rig" / "runs").mkdir(parents=True)
    (tmp_path / ".rig" / "config.yaml").write_text("version: 1\n", encoding="utf-8")
    (tmp_path / ".rig" / "env.yaml").write_text(
        """version: 1
agent_asset_managers:
  - id: apm
    label: APM
    command: apm
    hint: "Choose or install APM if needed."
    required_files:
      - path: apm.yml
        label: APM manifest
        hint: "Create apm.yml"
  - id: gh-skills
    label: GitHub skills manager
    command: gh
    args:
      - skills
      - --help
    hint: "Install or update GitHub CLI if needed."
  - id: vercel-skills
    label: Vercel skills manager
    command: npx
    hint: "Install Node.js/npm if needed."
required_files:
  - path: AGENTS.md
    label: Agent instructions
    hint: "Run: rig guide agents"
  - path: docs/harness.md
    label: Harness docs
    hint: "Create docs/harness.md"
""",
        encoding="utf-8",
    )
    (tmp_path / "AGENTS.md").write_text(
        "## Rig\n\nRun `rig show latest`.\n", encoding="utf-8"
    )

    def fake_which(command: str) -> str | None:
        return f"/usr/bin/{command}"

    def fake_run(
        args: list[str],
        *,
        capture_output: bool,
        text: bool,
        timeout: int,
        check: bool,
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")

    monkeypatch.setattr(env_doctor.shutil, "which", fake_which)
    monkeypatch.setattr(env_doctor.subprocess, "run", fake_run)

    report = env_doctor.build_doctor_report(tmp_path)

    labels = {check.label: check for check in report.checks}
    assert labels["Git repository"].status == "ok"
    assert labels["Rig config"].status == "ok"
    assert labels["Rig runs directory"].status == "ok"
    assert labels["Codex CLI"].status == "ok"
    assert labels["Agent asset manager: APM"].status == "ok"
    assert labels["Agent asset manager: GitHub skills manager"].status == "ok"
    assert labels["Agent asset manager: Vercel skills manager"].status == "ok"
    assert labels["Rig AGENTS.md snippet"].status == "ok"
    assert labels["Rig env config"].status == "ok"
    assert labels["Agent asset manager file: APM / APM manifest"].status == "missing"
    assert labels["Required file: Agent instructions"].status == "ok"
    assert labels["Required file: Harness docs"].status == "missing"
    assert "Create apm.yml" in report.suggestions
    assert "Create docs/harness.md" in report.suggestions


def test_format_doctor_report_includes_suggestions() -> None:
    report = env_doctor.DoctorReport(
        checks=[env_doctor.DoctorCheck("Codex CLI", "missing", "`codex` not found")],
        suggestions=["Install Codex CLI."],
    )

    output = env_doctor.format_doctor_report(report)

    assert "Rig environment" in output
    assert "[missing] Codex CLI: `codex` not found" in output
    assert "Suggested next steps" in output
    assert "- Install Codex CLI." in output


def test_build_doctor_report_warns_for_missing_rig_snippet(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "AGENTS.md").write_text("No Rig snippet.\n", encoding="utf-8")
    monkeypatch.setattr(env_doctor.shutil, "which", lambda command: None)

    report = env_doctor.build_doctor_report(tmp_path)

    labels = {check.label: check for check in report.checks}
    assert labels["AGENTS.md"].status == "ok"
    assert labels["Rig AGENTS.md snippet"].status == "warn"


def test_build_doctor_report_warns_for_invalid_env_yaml(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / ".rig").mkdir()
    (tmp_path / ".rig" / "env.yaml").write_text("required_files: nope\n", encoding="utf-8")
    monkeypatch.setattr(env_doctor.shutil, "which", lambda command: None)

    report = env_doctor.build_doctor_report(tmp_path)

    labels = {check.label: check for check in report.checks}
    assert labels["Rig env config"].status == "ok"
    assert labels["Rig env required files"].status == "warn"


def test_build_doctor_report_warns_for_invalid_manager_required_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / ".rig").mkdir()
    (tmp_path / ".rig" / "env.yaml").write_text(
        """version: 1
agent_asset_managers:
  - id: apm
    label: APM
    command: apm
    required_files: nope
""",
        encoding="utf-8",
    )
    monkeypatch.setattr(env_doctor.shutil, "which", lambda command: None)

    report = env_doctor.build_doctor_report(tmp_path)

    labels = {check.label: check for check in report.checks}
    assert labels["Rig env asset manager files"].status == "warn"


def test_format_env_plan_lists_gaps_and_actions() -> None:
    report = env_doctor.DoctorReport(
        checks=[
            env_doctor.DoctorCheck("Rig config", "missing", "missing .rig/config.yaml"),
            env_doctor.DoctorCheck(
                "Agent asset manager: APM", "optional", "`apm` not found on PATH"
            ),
        ],
        suggestions=[
            "Run: rig init",
            "Choose an agent asset manager if this project needs shared skills, hooks, prompts, or MCP config.",
        ],
    )

    output = env_doctor.format_env_plan(report)

    assert "Rig environment plan" in output
    assert "Desired harness" in output
    assert "[missing] Rig config: missing .rig/config.yaml" in output
    assert "[optional] Agent asset manager: APM: `apm` not found on PATH" in output
    assert "Planned actions" in output
    assert "- Run: rig init" in output
    assert "Agent asset managers are optional" in output
    assert "No files will be changed." in output


def test_format_env_plan_handles_no_gaps() -> None:
    report = env_doctor.DoctorReport(
        checks=[env_doctor.DoctorCheck("Rig config", "ok", ".rig/config.yaml")],
        suggestions=[],
    )

    output = env_doctor.format_env_plan(report)

    assert "- [ok] No gaps detected." in output
    assert "- No action needed." in output
