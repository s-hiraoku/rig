from __future__ import annotations

from pathlib import Path

from conftest import init_git_repo

from rig import env_doctor
from rig.policy import RIG_INSTRUCTION_PATH


def test_build_doctor_report_reports_missing_basics(tmp_path: Path) -> None:
    report = env_doctor.build_doctor_report(tmp_path)

    labels = {check.label: check for check in report.checks}
    assert labels["Git repository"].status == "missing"
    assert labels["Rig config"].status == "missing"
    assert labels["Rig history directory"].status == "missing"
    assert labels["Rig instructions"].status == "missing"
    assert labels["AGENTS.md"].status == "missing"
    assert "Run: rig init" in report.suggestions


def test_build_doctor_report_detects_minimal_setup(tmp_path: Path) -> None:
    init_git_repo(tmp_path)
    (tmp_path / ".rig" / "runs").mkdir(parents=True)
    (tmp_path / ".rig" / "config.yaml").write_text(
        """version: 1
agents:
  codex:
    command: definitely-missing-codex
""",
        encoding="utf-8",
    )
    instruction_path = tmp_path / RIG_INSTRUCTION_PATH
    instruction_path.parent.mkdir(parents=True)
    instruction_path.write_text("# Rig Instructions\n", encoding="utf-8")
    (tmp_path / "AGENTS.md").write_text(
        f"## Rig\n\nSee `{RIG_INSTRUCTION_PATH}`.\n", encoding="utf-8"
    )

    report = env_doctor.build_doctor_report(tmp_path)

    labels = {check.label: check for check in report.checks}
    assert labels["Git repository"].status == "ok"
    assert labels["Rig config"].status == "ok"
    assert labels["Rig history directory"].status == "ok"
    assert labels["Rig instructions"].status == "ok"
    assert labels["AGENTS.md Rig reference"].status == "ok"
    assert labels["Agent command: codex"].status == "missing"


def test_build_doctor_report_warns_for_missing_agents_reference(
    tmp_path: Path,
) -> None:
    (tmp_path / "AGENTS.md").write_text("No Rig reference.\n", encoding="utf-8")

    report = env_doctor.build_doctor_report(tmp_path)

    labels = {check.label: check for check in report.checks}
    assert labels["AGENTS.md"].status == "ok"
    assert labels["AGENTS.md Rig reference"].status == "warn"


def test_build_doctor_report_warns_for_legacy_gemini_agent(
    tmp_path: Path,
) -> None:
    (tmp_path / ".rig").mkdir()
    (tmp_path / ".rig" / "config.yaml").write_text(
        """version: 1
agents:
  gemini:
    command: gemini
    args:
      - -p
    prompt_style: task
""",
        encoding="utf-8",
    )

    report = env_doctor.build_doctor_report(tmp_path)

    labels = {check.label: check for check in report.checks}
    assert labels["Agent command: gemini"].status == "warn"
    assert "legacy Gemini CLI config" in labels["Agent command: gemini"].detail
    assert (
        "Update agents.gemini in .rig/config.yaml to use `command: agy`, "
        "`args: [-p]`, and `prompt_style: task`."
    ) in report.suggestions


def test_build_doctor_report_only_requires_agents_reference(
    tmp_path: Path,
) -> None:
    (tmp_path / "AGENTS.md").write_text("No Rig reference.\n", encoding="utf-8")

    report = env_doctor.build_doctor_report(tmp_path)

    labels = {check.label: check for check in report.checks}
    assert labels["AGENTS.md Rig reference"].status == "warn"
    assert "Run: rig init" in report.suggestions


def test_format_doctor_report_includes_suggestions() -> None:
    report = env_doctor.DoctorReport(
        checks=[
            env_doctor.DoctorCheck(
                "Agent command: codex", "missing", "`codex` not found"
            )
        ],
        suggestions=["Install `codex` or update agents.codex.command."],
    )

    output = env_doctor.format_doctor_report(report)

    assert "Rig doctor" in output
    assert "[missing] Agent command: codex" in output
    assert "- Install `codex` or update agents.codex.command." in output
