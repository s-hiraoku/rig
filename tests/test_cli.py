from __future__ import annotations

import json
from pathlib import Path

import pytest

from rig import cli
from rig.adapters.codex import AgentResult
from rig.run_context import RunContext


def test_init_command_creates_rig(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)

    assert cli.main(["init"]) == 0

    assert (tmp_path / ".rig" / "config.yaml").is_file()
    assert (tmp_path / ".rig" / "runs").is_dir()


def test_run_requires_initialized_repo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)

    assert cli.main(["run", "codex", "--task", "hello"]) == 1

    captured = capsys.readouterr()
    assert "Rig is not initialized" in captured.err


def test_run_rejects_missing_or_duplicate_task(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    cli.main(["init"])

    assert cli.main(["run", "codex"]) == 2
    task_file = tmp_path / "task.md"
    task_file.write_text("hello", encoding="utf-8")
    assert cli.main(["run", "codex", "--task", "hello", "--task-file", str(task_file)]) == 2

    captured = capsys.readouterr()
    assert "Provide exactly one of --task or --task-file." in captured.err


def test_run_codex_writes_artifacts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    cli.main(["init"])

    def fake_run(self: object, context: RunContext) -> AgentResult:
        assert context.task_path.read_text(encoding="utf-8") == "# Task\n\nhello\n"
        return AgentResult(exit_code=0, stdout="done\n", stderr="")

    monkeypatch.setattr(cli.CodexAdapter, "run", fake_run)

    assert cli.main(["run", "codex", "--task", "hello"]) == 0

    captured = capsys.readouterr()
    assert "Status: succeeded" in captured.out

    run_dirs = list((tmp_path / ".rig" / "runs").iterdir())
    assert len(run_dirs) == 1
    run_dir = run_dirs[0]
    assert (run_dir / "task.md").read_text(encoding="utf-8") == "# Task\n\nhello\n"
    assert (run_dir / "stdout.log").read_text(encoding="utf-8") == "done\n"
    assert (run_dir / "stderr.log").read_text(encoding="utf-8") == ""
    assert (run_dir / "result.md").read_text(encoding="utf-8") == "done\n"

    command = json.loads((run_dir / "command.json").read_text(encoding="utf-8"))
    assert command["agent"] == "codex"
    assert command["command"] == "codex"
    assert command["args"][0] == "exec"

    status = json.loads((run_dir / "status.json").read_text(encoding="utf-8"))
    assert status["status"] == "succeeded"
    assert status["exit_code"] == 0


def test_run_codex_uses_configured_command(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    cli.main(["init"])
    (tmp_path / ".rig" / "config.yaml").write_text(
        """version: 1
default_agent: codex
agents:
  codex:
    command: custom-codex
    args:
      - exec
      - --profile
      - review
""",
        encoding="utf-8",
    )

    def fake_run(self: object, context: RunContext) -> AgentResult:
        return AgentResult(exit_code=0, stdout="done\n", stderr="")

    monkeypatch.setattr(cli.CodexAdapter, "run", fake_run)

    assert cli.main(["run", "codex", "--task", "hello"]) == 0

    capsys.readouterr()
    run_dir = next((tmp_path / ".rig" / "runs").iterdir())
    command = json.loads((run_dir / "command.json").read_text(encoding="utf-8"))
    assert command["command"] == "custom-codex"
    assert command["args"][:3] == ["exec", "--profile", "review"]


def test_run_codex_reports_invalid_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    cli.main(["init"])
    (tmp_path / ".rig" / "config.yaml").write_text(
        """version: 1
agents:
  codex:
    command: codex
    args: exec
""",
        encoding="utf-8",
    )

    assert cli.main(["run", "codex", "--task", "hello"]) == 1

    captured = capsys.readouterr()
    assert "agents.codex.args" in captured.err
    assert list((tmp_path / ".rig" / "runs").iterdir()) == []


def test_failed_run_prints_stderr_summary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    cli.main(["init"])

    def fake_run(self: object, context: RunContext) -> AgentResult:
        return AgentResult(exit_code=1, stdout="", stderr="first error\nsecond error\n")

    monkeypatch.setattr(cli.CodexAdapter, "run", fake_run)

    assert cli.main(["run", "codex", "--task", "hello"]) == 1

    output = capsys.readouterr().out
    assert "Status: failed" in output
    assert "Error: first error" in output


def test_runs_list_and_show_latest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    cli.main(["init"])

    def fake_run(self: object, context: RunContext) -> AgentResult:
        return AgentResult(exit_code=0, stdout="latest result\n", stderr="")

    monkeypatch.setattr(cli.CodexAdapter, "run", fake_run)
    cli.main(["run", "codex", "--task", "hello"])

    assert cli.main(["runs", "list"]) == 0
    list_output = capsys.readouterr().out
    assert "ID" in list_output
    assert "codex" in list_output
    assert "succeeded" in list_output

    assert cli.main(["runs", "show", "latest"]) == 0
    show_output = capsys.readouterr().out
    assert "--- Result ---" in show_output
    assert "latest result" in show_output


def test_agents_snippet_prints_agents_md_section(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)

    assert cli.main(["agents", "snippet"]) == 0

    output = capsys.readouterr().out
    assert "## Rig" in output
    assert "Prefer Rig MCP tools when available" in output
    assert "rig run codex --task-file" in output
    assert "rig runs show latest" in output
