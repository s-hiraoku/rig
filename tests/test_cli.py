from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from rig import cli


def install_fake_command(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    name: str = "codex",
    stdout: str = "done\n",
    stderr: str = "",
    exit_code: int = 0,
) -> Path:
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir(exist_ok=True)
    command_path = bin_dir / name
    command_path.write_text(
        "\n".join(
            [
                f"#!{sys.executable}",
                "import json",
                "import pathlib",
                "import sys",
                "pathlib.Path('fake-command-argv.json').write_text(json.dumps(sys.argv), encoding='utf-8')",
                f"sys.stdout.write({stdout!r})",
                f"sys.stderr.write({stderr!r})",
                f"raise SystemExit({exit_code})",
                "",
            ]
        ),
        encoding="utf-8",
    )
    command_path.chmod(0o755)
    monkeypatch.setenv("PATH", str(bin_dir))
    return command_path


def test_init_command_creates_rig(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)

    assert cli.main(["init"]) == 0

    assert (tmp_path / ".rig" / "config.yaml").is_file()
    assert (tmp_path / ".rig" / "env.yaml").is_file()
    assert (tmp_path / ".rig" / "runs").is_dir()


def test_init_command_does_not_update_existing_rig(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    cli.main(["init"])
    (tmp_path / ".rig" / "env.yaml").write_text(
        "version: 1\nagent_asset_managers: []\nrequired_files: []\n",
        encoding="utf-8",
    )

    assert cli.main(["init"]) == 0

    captured = capsys.readouterr()
    assert "Rig already up to date." in captured.out
    assert "id: gh-skills" not in (tmp_path / ".rig" / "env.yaml").read_text(
        encoding="utf-8"
    )


def test_init_command_force_resets_config_and_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    cli.main(["init"])
    (tmp_path / ".rig" / "config.yaml").write_text("custom: config\n", encoding="utf-8")
    (tmp_path / ".rig" / "env.yaml").write_text("custom: env\n", encoding="utf-8")

    assert cli.main(["init", "--force"]) == 0

    captured = capsys.readouterr()
    assert "Updated: .rig/config.yaml" in captured.out
    assert "Updated: .rig/env.yaml" in captured.out
    assert "Backup: .rig/config.yaml.bak-" in captured.out
    assert "Backup: .rig/env.yaml.bak-" in captured.out
    assert "default_agent: codex" in (tmp_path / ".rig" / "config.yaml").read_text(
        encoding="utf-8"
    )
    assert "agent_asset_managers:" in (tmp_path / ".rig" / "env.yaml").read_text(
        encoding="utf-8"
    )


def test_init_command_reset_env_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    cli.main(["init"])
    (tmp_path / ".rig" / "config.yaml").write_text("custom: config\n", encoding="utf-8")
    (tmp_path / ".rig" / "env.yaml").write_text("custom: env\n", encoding="utf-8")

    assert cli.main(["init", "--reset", "env"]) == 0

    captured = capsys.readouterr()
    assert "Updated: .rig/config.yaml" not in captured.out
    assert "Updated: .rig/env.yaml" in captured.out
    assert "custom: config" in (tmp_path / ".rig" / "config.yaml").read_text(
        encoding="utf-8"
    )
    assert "agent_asset_managers:" in (tmp_path / ".rig" / "env.yaml").read_text(
        encoding="utf-8"
    )


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
    install_fake_command(tmp_path, monkeypatch, stdout="done\n")

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
    fake_argv = json.loads((tmp_path / "fake-command-argv.json").read_text())
    assert fake_argv[1] == "exec"
    assert "Read the task file" in fake_argv[2]

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
    install_fake_command(tmp_path, monkeypatch, name="custom-codex", stdout="done\n")
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

    assert cli.main(["run", "codex", "--task", "hello"]) == 0

    capsys.readouterr()
    run_dir = next((tmp_path / ".rig" / "runs").iterdir())
    command = json.loads((run_dir / "command.json").read_text(encoding="utf-8"))
    assert command["command"] == "custom-codex"
    assert command["args"][:3] == ["exec", "--profile", "review"]
    assert command["runner"] == "exec"


def test_run_configured_exec_agent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    cli.main(["init"])
    install_fake_command(tmp_path, monkeypatch, name="copilot", stdout="copilot done\n")
    (tmp_path / ".rig" / "config.yaml").write_text(
        """version: 1
default_agent: codex
agents:
  codex:
    runner: exec
    command: codex
    args:
      - exec
  copilot:
    runner: exec
    command: copilot
    args:
      - -p
    prompt_style: task
""",
        encoding="utf-8",
    )

    assert cli.main(["run", "copilot", "--task", "hello"]) == 0

    output = capsys.readouterr().out
    assert "Status: succeeded" in output
    run_dir = next((tmp_path / ".rig" / "runs").iterdir())
    assert run_dir.name.endswith("-copilot")
    assert (run_dir / "result.md").read_text(encoding="utf-8") == "copilot done\n"

    fake_argv = json.loads((tmp_path / "fake-command-argv.json").read_text())
    assert fake_argv[0].endswith("/copilot")
    assert fake_argv[1] == "-p"
    assert fake_argv[2] == "# Task\n\nhello\n"

    command = json.loads((run_dir / "command.json").read_text(encoding="utf-8"))
    assert command["agent"] == "copilot"
    assert command["runner"] == "exec"
    assert command["command"] == "copilot"
    assert command["args"][0] == "-p"


def test_run_manual_agent_creates_waiting_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    cli.main(["init"])
    (tmp_path / ".rig" / "config.yaml").write_text(
        """version: 1
agents:
  external:
    runner: manual
""",
        encoding="utf-8",
    )

    assert cli.main(["run", "external", "--task", "finish this elsewhere"]) == 0

    output = capsys.readouterr().out
    assert "Status: waiting" in output
    run_dir = next((tmp_path / ".rig" / "runs").iterdir())
    assert run_dir.name.endswith("-external")
    assert (run_dir / "stdout.log").read_text(encoding="utf-8") == ""
    assert (run_dir / "stderr.log").read_text(encoding="utf-8") == ""
    assert "Manual run is waiting" in (run_dir / "result.md").read_text(
        encoding="utf-8"
    )

    command = json.loads((run_dir / "command.json").read_text(encoding="utf-8"))
    assert command["agent"] == "external"
    assert command["runner"] == "manual"
    assert command["command"] == "manual"

    status = json.loads((run_dir / "status.json").read_text(encoding="utf-8"))
    assert status["status"] == "waiting"
    assert status["exit_code"] is None


def test_runs_complete_manual_run_with_result_text(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    cli.main(["init"])
    (tmp_path / ".rig" / "config.yaml").write_text(
        """version: 1
agents:
  external:
    runner: manual
""",
        encoding="utf-8",
    )
    cli.main(["run", "external", "--task", "finish this elsewhere"])
    run_dir = next((tmp_path / ".rig" / "runs").iterdir())

    assert cli.main(["runs", "complete", "latest", "--result", "done elsewhere"]) == 0

    output = capsys.readouterr().out
    assert "Status: succeeded" in output
    assert (run_dir / "result.md").read_text(encoding="utf-8") == "done elsewhere\n"
    status = json.loads((run_dir / "status.json").read_text(encoding="utf-8"))
    assert status["status"] == "succeeded"
    assert status["exit_code"] == 0
    assert status["finished_at"] is not None


def test_runs_complete_requires_one_result_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    cli.main(["init"])

    assert cli.main(["runs", "complete", "latest"]) == 2

    assert "Provide exactly one of --result or --result-file." in capsys.readouterr().err


def test_run_codex_dry_run_writes_artifacts_without_executing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    cli.main(["init"])

    assert cli.main(["run", "codex", "--task", "hello", "--dry-run"]) == 0

    output = capsys.readouterr().out
    assert "Status: created" in output
    assert "Command: .rig/runs/" in output

    run_dir = next((tmp_path / ".rig" / "runs").iterdir())
    assert (run_dir / "task.md").read_text(encoding="utf-8") == "# Task\n\nhello\n"
    assert (run_dir / "stdout.log").read_text(encoding="utf-8") == ""
    assert (run_dir / "stderr.log").read_text(encoding="utf-8") == ""
    assert (run_dir / "result.md").read_text(encoding="utf-8") == (
        "Dry run: command was not executed.\n"
    )

    command = json.loads((run_dir / "command.json").read_text(encoding="utf-8"))
    assert command["command"] == "codex"
    assert command["args"][0] == "exec"
    assert not (tmp_path / "fake-command-argv.json").exists()

    status = json.loads((run_dir / "status.json").read_text(encoding="utf-8"))
    assert status["status"] == "created"
    assert status["exit_code"] is None


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
    install_fake_command(
        tmp_path,
        monkeypatch,
        stdout="",
        stderr="first error\nsecond error\n",
        exit_code=1,
    )

    assert cli.main(["run", "codex", "--task", "hello"]) == 1

    output = capsys.readouterr().out
    assert "Status: failed" in output
    assert "Error: first error" in output


def test_runs_list_and_show_latest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    cli.main(["init"])
    install_fake_command(tmp_path, monkeypatch, stdout="latest result\n")
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


def test_runs_list_handles_empty_history(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    cli.main(["init"])

    assert cli.main(["runs", "list"]) == 0

    output = capsys.readouterr().out
    assert "ID" in output
    assert "No runs found." in output


def test_runs_show_latest_handles_empty_history(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    cli.main(["init"])

    assert cli.main(["runs", "show", "latest"]) == 1

    assert "No runs found." in capsys.readouterr().err


def test_runs_show_handles_unreadable_status(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    cli.main(["init"])
    run_dir = tmp_path / ".rig" / "runs" / "bad-run"
    run_dir.mkdir()
    (run_dir / "status.json").write_text("{not json", encoding="utf-8")

    assert cli.main(["runs", "show", "bad-run"]) == 1

    assert "Run not found or unreadable: bad-run" in capsys.readouterr().err


def test_runs_show_handles_missing_result(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    cli.main(["init"])
    run_dir = tmp_path / ".rig" / "runs" / "missing-result"
    run_dir.mkdir()
    (run_dir / "status.json").write_text(
        json.dumps(
            {
                "id": "missing-result",
                "agent": "codex",
                "status": "succeeded",
                "started_at": "2026-05-02T20:30:12+09:00",
                "finished_at": "2026-05-02T20:31:04+09:00",
                "exit_code": 0,
                "run_dir": ".rig/runs/missing-result",
            }
        ),
        encoding="utf-8",
    )

    assert cli.main(["runs", "show", "missing-result"]) == 0

    output = capsys.readouterr().out
    assert "ID:        missing-result" in output
    assert "Exit code: 0" in output
    assert "(result.md is missing or empty)" in output


def test_runs_show_failed_run_includes_stderr(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    cli.main(["init"])
    run_dir = tmp_path / ".rig" / "runs" / "failed-run"
    run_dir.mkdir()
    (run_dir / "status.json").write_text(
        json.dumps(
            {
                "id": "failed-run",
                "agent": "codex",
                "status": "failed",
                "started_at": "2026-05-02T20:30:12+09:00",
                "finished_at": "2026-05-02T20:31:04+09:00",
                "exit_code": 2,
                "run_dir": ".rig/runs/failed-run",
            }
        ),
        encoding="utf-8",
    )
    (run_dir / "result.md").write_text("", encoding="utf-8")
    (run_dir / "stderr.log").write_text("first error\nsecond error\n", encoding="utf-8")

    assert cli.main(["runs", "show", "failed-run"]) == 0

    output = capsys.readouterr().out
    assert "Status:    failed" in output
    assert "Exit code: 2" in output
    assert "Stderr:    .rig/runs/failed-run/stderr.log" in output
    assert "--- Error ---" in output
    assert "first error" in output
    assert "second error" in output


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


def test_env_doctor_prints_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)

    assert cli.main(["env", "doctor"]) == 0

    output = capsys.readouterr().out
    assert "Rig environment" in output
    assert "Rig config" in output
    assert "Suggested next steps" in output


def test_env_plan_prints_read_only_plan(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)

    assert cli.main(["env", "plan"]) == 0

    output = capsys.readouterr().out
    assert "Rig environment plan" in output
    assert "Desired harness" in output
    assert "Planned actions" in output
    assert "No files will be changed." in output


def test_env_bootstrap_creates_missing_rig_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)

    assert cli.main(["env", "bootstrap"]) == 0

    output = capsys.readouterr().out
    assert "Rig environment bootstrap" in output
    assert "Created: .rig/config.yaml" in output
    assert "Created: .rig/env.yaml" in output
    assert "Next steps" in output
    assert "Run: rig agents snippet" in output
    assert "Rig did not install external tools or third-party agent assets." in output
    assert (tmp_path / ".rig" / "config.yaml").is_file()
    assert (tmp_path / ".rig" / "env.yaml").is_file()


def test_env_bootstrap_does_not_overwrite_existing_env_yaml(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    cli.main(["init"])
    (tmp_path / ".rig" / "env.yaml").write_text("custom: true\n", encoding="utf-8")

    assert cli.main(["env", "bootstrap"]) == 0

    output = capsys.readouterr().out
    assert "Rig already up to date." in output
    assert (tmp_path / ".rig" / "env.yaml").read_text(encoding="utf-8") == (
        "custom: true\n"
    )
