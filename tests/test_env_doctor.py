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
    assert labels["APM"].status == "optional"
    assert labels["GitHub CLI"].status == "optional"
    assert labels["npx"].status == "optional"
    assert "Run: git init" in report.suggestions
    assert "Run: rig init" in report.suggestions
    assert "Run: rig agents snippet" in report.suggestions


def test_build_doctor_report_detects_agent_environment_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / ".git").mkdir()
    (tmp_path / ".rig" / "runs").mkdir(parents=True)
    (tmp_path / ".rig" / "config.yaml").write_text("version: 1\n", encoding="utf-8")
    (tmp_path / "AGENTS.md").write_text(
        "## Rig\n\nRun `rig runs show latest`.\n", encoding="utf-8"
    )
    (tmp_path / "apm.yml").write_text("version: 1\n", encoding="utf-8")
    (tmp_path / "apm.lock.yaml").write_text("lockfileVersion: 1\n", encoding="utf-8")

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
    assert labels["gh skill"].status == "ok"
    assert labels["Rig AGENTS.md snippet"].status == "ok"
    assert labels["APM manifest"].status == "ok"
    assert labels["APM lockfile"].status == "ok"


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


def test_build_doctor_report_warns_for_partial_agent_asset_setup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "AGENTS.md").write_text("No Rig snippet.\n", encoding="utf-8")
    (tmp_path / "apm.yml").write_text("version: 1\n", encoding="utf-8")
    monkeypatch.setattr(env_doctor.shutil, "which", lambda command: None)

    report = env_doctor.build_doctor_report(tmp_path)

    labels = {check.label: check for check in report.checks}
    assert labels["AGENTS.md"].status == "ok"
    assert labels["Rig AGENTS.md snippet"].status == "warn"
    assert labels["APM manifest"].status == "ok"
    assert labels["APM lockfile"].status == "warn"
