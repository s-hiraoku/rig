from __future__ import annotations

import json
from pathlib import Path

import pytest
from conftest import init_git_repo, install_fake_command, install_fake_script

from rig import cli


def test_top_level_help_shows_command_shape(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        cli.main(["--help"])

    assert exc_info.value.code == 0
    output = capsys.readouterr().out
    assert "{init,run,list,show,worktree,manual,guide,env,mcp,suggest}" in output
    assert "worktree" in output
    assert "history" not in output
    assert "diff" not in output
    assert "apply" not in output


def test_mcp_serve_handles_keyboard_interrupt(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def fake_serve_mcp() -> None:
        raise KeyboardInterrupt

    import rig.mcp_server

    monkeypatch.setattr(rig.mcp_server, "serve_mcp", fake_serve_mcp)

    assert cli.main(["mcp", "serve"]) == 130

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "Interrupted.\n"


def test_suggest_recommends_normal_run_for_clean_repo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    init_git_repo(tmp_path)
    cli.main(["init"])
    capsys.readouterr()

    assert cli.main(["suggest", "Explain the project"]) == 0

    output = capsys.readouterr().out
    assert "Recommendation: run" in output
    assert "Command:        rig run codex --task 'Explain the project'" in output
    assert "- Git repo: yes" in output
    assert "- Rig initialized: yes" in output


def test_suggest_recommends_worktree_for_dirty_repo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    init_git_repo(tmp_path)
    cli.main(["init"])
    (tmp_path / "tracked.txt").write_text("after\n", encoding="utf-8")
    capsys.readouterr()

    assert cli.main(["suggest", "Refactor the CLI command structure"]) == 0

    output = capsys.readouterr().out
    assert "Recommendation: worktree" in output
    assert "Command:        rig worktree run codex --task" in output
    assert "Use an isolated worktree" in output
    assert "- Changed files: 1" in output


def test_suggest_supports_json_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    init_git_repo(tmp_path)
    cli.main(["init"])
    capsys.readouterr()

    assert cli.main(["suggest", "hello", "--json"]) == 0

    data = json.loads(capsys.readouterr().out)
    assert data["mode"] == "run"
    assert data["agent"] == "codex"
    assert data["command"] == ["rig", "run", "codex", "--task", "hello"]
    assert data["observations"]["git_repo"] is True


def test_suggest_allows_uninitialized_repo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    init_git_repo(tmp_path)

    assert cli.main(["suggest", "hello", "--json"]) == 0

    data = json.loads(capsys.readouterr().out)
    assert data["mode"] == "run"
    assert data["observations"]["initialized"] is False


def test_suggest_rejects_invalid_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    init_git_repo(tmp_path)
    cli.main(["init"])
    capsys.readouterr()
    (tmp_path / ".rig" / "config.yaml").write_text("[broken\n", encoding="utf-8")

    assert cli.main(["suggest", "hello"]) == 1

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "Could not parse config file" in captured.err


def test_suggest_prefers_task_file_for_long_task_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    init_git_repo(tmp_path)
    cli.main(["init"])
    task_file = tmp_path / "task.md"
    task_file.write_text("Line one\nLine two\n", encoding="utf-8")
    capsys.readouterr()

    assert cli.main(["suggest", "--task-file", str(task_file)]) == 0

    output = capsys.readouterr().out
    assert f"Command:        rig run codex --task-file {task_file}" in output


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


def test_run_rejects_empty_task_file_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    cli.main(["init"])

    assert cli.main(["run", "codex", "--task-file", ""]) == 2

    captured = capsys.readouterr()
    assert "--task-file requires a non-empty path." in captured.err


def test_run_accepts_empty_inline_task(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    cli.main(["init"])
    install_fake_command(tmp_path, monkeypatch, stdout="done\n")

    assert cli.main(["run", "codex", "--task", ""]) == 0

    capsys.readouterr()
    run_dir = next((tmp_path / ".rig" / "runs").iterdir())
    assert (run_dir / "task.md").read_text(encoding="utf-8") == "# Task\n\n\n"


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


def test_run_supports_json_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    cli.main(["init"])
    install_fake_command(tmp_path, monkeypatch, stdout="done\n")
    capsys.readouterr()

    assert cli.main(["run", "codex", "--task", "hello", "--json"]) == 0

    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is True
    assert data["exit_code"] == 0
    assert data["status"] == "succeeded"
    assert data["run_id"].endswith("-codex")
    assert data["result_path"].startswith(".rig/runs/")
    assert data["diff_path"] is None
    assert data["lines"] == [
        f"Run: {data['run_id']}",
        "Status: succeeded",
        f"Result: {data['result_path']}",
    ]


def test_run_uses_default_agent_when_agent_is_omitted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    cli.main(["init"])
    install_fake_command(tmp_path, monkeypatch, name="custom-agent", stdout="done\n")
    (tmp_path / ".rig" / "config.yaml").write_text(
        """version: 1
default_agent: helper
agents:
  helper:
    runner: exec
    command: custom-agent
    prompt_style: task
""",
        encoding="utf-8",
    )

    assert cli.main(["run", "--task", "hello"]) == 0

    capsys.readouterr()
    run_dir = next((tmp_path / ".rig" / "runs").iterdir())
    assert run_dir.name.endswith("-helper")
    status = json.loads((run_dir / "status.json").read_text(encoding="utf-8"))
    assert status["agent"] == "helper"


def test_task_file_is_preserved_without_added_heading(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    cli.main(["init"])
    install_fake_command(tmp_path, monkeypatch, stdout="done\n")
    task_file = tmp_path / "task.md"
    task_file.write_text("# Existing Task\n\nDo it.\n", encoding="utf-8")

    assert cli.main(["run", "codex", "--task-file", str(task_file)]) == 0

    capsys.readouterr()
    run_dir = next((tmp_path / ".rig" / "runs").iterdir())
    assert (run_dir / "task.md").read_text(encoding="utf-8") == (
        "# Existing Task\n\nDo it.\n"
    )


def test_prompt_template_can_override_rig_prompt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    cli.main(["init"])
    install_fake_command(tmp_path, monkeypatch, stdout="done\n")
    (tmp_path / ".rig" / "config.yaml").write_text(
        """version: 1
agents:
  templated:
    runner: exec
    command: codex
    prompt_style: template
    prompt_template: "Agent={agent}; Path={task_path}; Body={task}"
""",
        encoding="utf-8",
    )

    assert cli.main(["run", "templated", "--task", "hello"]) == 0

    capsys.readouterr()
    run_dir = next((tmp_path / ".rig" / "runs").iterdir())
    command = json.loads((run_dir / "command.json").read_text(encoding="utf-8"))
    prompt = command["args"][-1]
    assert "Agent=templated" in prompt
    assert "Path=.rig/runs/" in prompt
    assert "Body=hello" in prompt
    assert "Body=# Task" not in prompt


def test_exec_runner_times_out(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    cli.main(["init"])
    install_fake_script(
        tmp_path,
        monkeypatch,
        name="slow-exec",
        body="import time\nprint('started')\ntime.sleep(5)\n",
    )
    (tmp_path / ".rig" / "config.yaml").write_text(
        """version: 1
agents:
  slow:
    runner: exec
    command: slow-exec
    timeout_seconds: 1
""",
        encoding="utf-8",
    )

    assert cli.main(["run", "slow", "--task", "hello"]) == 1

    output = capsys.readouterr().out
    assert "Status: failed" in output
    run_dir = next((tmp_path / ".rig" / "runs").iterdir())
    status = json.loads((run_dir / "status.json").read_text(encoding="utf-8"))
    assert status["exit_code"] == 124
    assert "timed out" in (run_dir / "stderr.log").read_text(encoding="utf-8")


def test_large_stdout_result_is_truncated_but_log_is_preserved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    cli.main(["init"])
    install_fake_script(
        tmp_path,
        monkeypatch,
        name="loud",
        body="print('x' * 50000)\n",
    )
    (tmp_path / ".rig" / "config.yaml").write_text(
        """version: 1
agents:
  loud:
    runner: exec
    command: loud
    prompt_style: task
""",
        encoding="utf-8",
    )

    assert cli.main(["run", "loud", "--task", "hello"]) == 0

    capsys.readouterr()
    run_dir = next((tmp_path / ".rig" / "runs").iterdir())
    assert len((run_dir / "stdout.log").read_text(encoding="utf-8")) > 50000
    result = (run_dir / "result.md").read_text(encoding="utf-8")
    assert result.startswith("Result truncated from stdout.log.")
    assert len(result) < 41000


def test_result_marker_keeps_only_final_result_in_result_md(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    cli.main(["init"])
    install_fake_script(
        tmp_path,
        monkeypatch,
        name="marked-result",
        body="print('logs')\nprint('--- RIG RESULT ---')\nprint('final answer')\n",
    )
    (tmp_path / ".rig" / "config.yaml").write_text(
        """version: 1
agents:
  marked:
    runner: exec
    command: marked-result
    prompt_style: task
""",
        encoding="utf-8",
    )

    assert cli.main(["run", "marked", "--task", "hello"]) == 0

    capsys.readouterr()
    run_dir = next((tmp_path / ".rig" / "runs").iterdir())
    assert (run_dir / "stdout.log").read_text(encoding="utf-8").startswith("logs")
    assert (run_dir / "result.md").read_text(encoding="utf-8") == "final answer\n"


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


def test_run_pty_agent_creates_transcript(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    cli.main(["init"])
    install_fake_script(
        tmp_path,
        monkeypatch,
        name="interactive",
        body=(
            "import os\n"
            "import sys\n"
            "print(f'tty={os.isatty(0)}')\n"
            "print(sys.argv[1])\n"
        ),
    )
    (tmp_path / ".rig" / "config.yaml").write_text(
        """version: 1
agents:
  interactive:
    runner: pty
    command: interactive
    timeout_seconds: 5
    prompt_style: task
""",
        encoding="utf-8",
    )

    assert cli.main(["run", "interactive", "--task", "hello pty"]) == 0

    output = capsys.readouterr().out
    assert "Status: succeeded" in output
    run_dir = next((tmp_path / ".rig" / "runs").iterdir())
    result = (run_dir / "result.md").read_text(encoding="utf-8")
    assert "tty=True" in result
    assert "# Task" in result
    assert "hello pty" in result

    command = json.loads((run_dir / "command.json").read_text(encoding="utf-8"))
    assert command["agent"] == "interactive"
    assert command["runner"] == "pty"


def test_run_pty_agent_times_out(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    cli.main(["init"])
    install_fake_script(
        tmp_path,
        monkeypatch,
        name="slow-interactive",
        body="import time\nprint('started')\ntime.sleep(5)\n",
    )
    (tmp_path / ".rig" / "config.yaml").write_text(
        """version: 1
agents:
  slow:
    runner: pty
    command: slow-interactive
    timeout_seconds: 1
""",
        encoding="utf-8",
    )

    assert cli.main(["run", "slow", "--task", "hello"]) == 1

    output = capsys.readouterr().out
    assert "Status: failed" in output
    run_dir = next((tmp_path / ".rig" / "runs").iterdir())
    result = (run_dir / "result.md").read_text(encoding="utf-8")
    stderr = (run_dir / "stderr.log").read_text(encoding="utf-8")
    assert "Rig PTY runner timed out after 1 seconds." not in result
    assert "Rig PTY runner timed out after 1 seconds." in stderr
    status = json.loads((run_dir / "status.json").read_text(encoding="utf-8"))
    assert status["exit_code"] == 124


def test_run_pty_agent_reports_missing_command(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    cli.main(["init"])
    (tmp_path / ".rig" / "config.yaml").write_text(
        """version: 1
agents:
  missing:
    runner: pty
    command: missing-pty-command
""",
        encoding="utf-8",
    )

    assert cli.main(["run", "missing", "--task", "hello"]) == 1

    captured = capsys.readouterr()
    assert "missing-pty-command" in captured.err
    run_dir = next((tmp_path / ".rig" / "runs").iterdir())
    status = json.loads((run_dir / "status.json").read_text(encoding="utf-8"))
    assert status["exit_code"] == 127


def test_complete_manual_run_with_result_text(
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

    assert cli.main(["history", "complete", "latest", "--result", "done elsewhere"]) == 0

    output = capsys.readouterr().out
    assert "Status: succeeded" in output
    assert (run_dir / "result.md").read_text(encoding="utf-8") == "done elsewhere\n"
    status = json.loads((run_dir / "status.json").read_text(encoding="utf-8"))
    assert status["status"] == "succeeded"
    assert status["exit_code"] == 0
    assert status["finished_at"] is not None


def test_manual_group_completes_waiting_run(
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

    assert cli.main(["manual", "complete", "latest", "--result", "done elsewhere"]) == 0

    output = capsys.readouterr().out
    assert "Status: succeeded" in output
    assert (run_dir / "result.md").read_text(encoding="utf-8") == "done elsewhere\n"


def test_complete_requires_one_result_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    cli.main(["init"])

    assert cli.main(["history", "complete", "latest"]) == 2

    assert "Provide exactly one of --result or --result-file." in capsys.readouterr().err


def test_complete_refuses_non_waiting_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    cli.main(["init"])
    install_fake_command(tmp_path, monkeypatch, stdout="already done\n")
    cli.main(["run", "codex", "--task", "hello"])
    run_dir = next((tmp_path / ".rig" / "runs").iterdir())

    assert cli.main(["history", "complete", "latest", "--result", "overwrite"]) == 1

    captured = capsys.readouterr()
    assert "Run is not waiting and cannot be completed" in captured.err
    assert (run_dir / "result.md").read_text(encoding="utf-8") == "already done\n"


def test_fail_manual_run_with_error_text(
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

    assert cli.main(["history", "fail", "latest", "--error", "blocked elsewhere"]) == 1

    output = capsys.readouterr().out
    assert "Status: failed" in output
    assert "Error: blocked elsewhere" in output
    assert (run_dir / "stderr.log").read_text(encoding="utf-8") == "blocked elsewhere\n"
    status = json.loads((run_dir / "status.json").read_text(encoding="utf-8"))
    assert status["status"] == "failed"
    assert status["exit_code"] == 1
    assert status["finished_at"] is not None

    assert cli.main(["show", "latest"]) == 0
    show_output = capsys.readouterr().out
    assert "--- Error ---" in show_output
    assert "blocked elsewhere" in show_output


def test_fail_requires_one_error_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    cli.main(["init"])

    assert cli.main(["history", "fail", "latest"]) == 2

    assert "Provide exactly one of --error or --error-file." in capsys.readouterr().err


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


def test_list_and_show_latest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    cli.main(["init"])
    install_fake_command(tmp_path, monkeypatch, stdout="latest result\n")
    cli.main(["run", "codex", "--task", "hello"])

    assert cli.main(["list"]) == 0
    list_output = capsys.readouterr().out
    assert "ID" in list_output
    assert "codex" in list_output
    assert "succeeded" in list_output

    assert cli.main(["show", "latest"]) == 0
    show_output = capsys.readouterr().out
    assert "--- Result ---" in show_output
    assert "latest result" in show_output


def test_list_and_show_support_json_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    cli.main(["init"])
    install_fake_command(tmp_path, monkeypatch, stdout="latest result\n")
    cli.main(["run", "codex", "--task", "hello"])
    capsys.readouterr()

    assert cli.main(["list", "--json"]) == 0
    list_data = json.loads(capsys.readouterr().out)
    assert list_data[0]["agent"] == "codex"

    assert cli.main(["show", "latest", "--json"]) == 0
    show_data = json.loads(capsys.readouterr().out)
    assert show_data["agent"] == "codex"


def test_history_group_remains_available(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    cli.main(["init"])
    install_fake_command(tmp_path, monkeypatch, stdout="latest result\n")
    cli.main(["run", "codex", "--task", "hello"])

    assert cli.main(["history", "list"]) == 0
    assert "codex" in capsys.readouterr().out

    assert cli.main(["history", "show", "latest"]) == 0
    assert "latest result" in capsys.readouterr().out


def test_list_handles_empty_history(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    cli.main(["init"])

    assert cli.main(["list"]) == 0

    output = capsys.readouterr().out
    assert "ID" in output
    assert "No runs found." in output


def test_show_latest_handles_empty_history(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    cli.main(["init"])

    assert cli.main(["show", "latest"]) == 1

    assert "No runs found." in capsys.readouterr().err


def test_show_handles_unreadable_status(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    cli.main(["init"])
    run_dir = tmp_path / ".rig" / "runs" / "bad-run"
    run_dir.mkdir()
    (run_dir / "status.json").write_text("{not json", encoding="utf-8")

    assert cli.main(["show", "bad-run"]) == 1

    assert "Run not found or unreadable: bad-run" in capsys.readouterr().err


def test_show_handles_missing_result(
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

    assert cli.main(["show", "missing-result"]) == 0

    output = capsys.readouterr().out
    assert "ID:        missing-result" in output
    assert "Exit code: 0" in output
    assert "(result.md is missing or empty)" in output


def test_show_failed_run_includes_stderr(
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

    assert cli.main(["show", "failed-run"]) == 0

    output = capsys.readouterr().out
    assert "Status:    failed" in output
    assert "Exit code: 2" in output
    assert "Stderr:    .rig/runs/failed-run/stderr.log" in output
    assert "--- Error ---" in output
    assert "first error" in output
    assert "second error" in output


def test_guide_agents_prints_agents_md_section(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)

    assert cli.main(["guide", "agents"]) == 0

    output = capsys.readouterr().out
    assert "## Rig" in output
    assert "Suggested for AGENTS.md" in output
    assert "Suggested for CLAUDE.md" in output
    assert "Suggested for Rig-related skill files" in output
    assert ".rig/instructions/rig.md" in output


def test_guide_agents_supports_targets_and_markdown_format(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)

    assert cli.main(["guide", "agents", "--target", "claude", "--format", "markdown"]) == 0

    output = capsys.readouterr().out
    assert "Suggested for CLAUDE.md" in output
    assert "## Rig" in output
    assert ".rig/instructions/rig.md" in output
    assert "rig guide agents --write" in output


def test_guide_agents_help_notes_target_independent_write(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        cli.main(["guide", "agents", "--help"])

    assert exc_info.value.code == 0
    assert "target-independent" in capsys.readouterr().out


def test_guide_agents_target_omits_write_note_when_instruction_file_exists(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    instruction_path = tmp_path / ".rig" / "instructions" / "rig.md"
    instruction_path.parent.mkdir(parents=True)
    instruction_path.write_text("# Existing\n", encoding="utf-8")

    assert cli.main(["guide", "agents", "--target", "codex"]) == 0

    output = capsys.readouterr().out
    assert "Suggested for AGENTS.md" in output
    assert "rig guide agents --write" not in output


def test_guide_agents_write_creates_rig_instruction_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)

    assert cli.main(["guide", "agents", "--write"]) == 0

    instruction_path = tmp_path / ".rig" / "instructions" / "rig.md"
    assert instruction_path.is_file()
    content = instruction_path.read_text(encoding="utf-8")
    assert "# Rig Instructions" in content
    assert "Prefer Rig MCP tools when available" in content
    output = capsys.readouterr().out
    assert "Wrote: .rig/instructions/rig.md" in output
    assert "Suggested for AGENTS.md" in output
    assert "Suggested for CLAUDE.md" in output
    assert "Suggested for Rig-related skill files" in output
    assert "See `.rig/instructions/rig.md`" in output


def test_guide_agents_write_refuses_to_overwrite_without_force(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    instruction_path = tmp_path / ".rig" / "instructions" / "rig.md"
    instruction_path.parent.mkdir(parents=True)
    instruction_path.write_text("custom\n", encoding="utf-8")

    assert cli.main(["guide", "agents", "--write"]) == 1

    assert instruction_path.read_text(encoding="utf-8") == "custom\n"
    assert "already exists" in capsys.readouterr().err


def test_guide_agents_write_force_overwrites_instruction_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    instruction_path = tmp_path / ".rig" / "instructions" / "rig.md"
    instruction_path.parent.mkdir(parents=True)
    instruction_path.write_text("custom\n", encoding="utf-8")

    assert cli.main(["guide", "agents", "--write", "--force"]) == 0

    assert "# Rig Instructions" in instruction_path.read_text(encoding="utf-8")
    assert "Wrote: .rig/instructions/rig.md" in capsys.readouterr().out


def test_guide_agents_force_requires_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)

    assert cli.main(["guide", "agents", "--force"]) == 2

    assert "--force requires --write." in capsys.readouterr().err


def test_env_doctor_prints_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)

    assert cli.main(["env", "doctor"]) == 0

    output = capsys.readouterr().out
    assert "Rig environment" in output
    assert "Rig config" in output
    assert "Suggested next steps" in output


def test_env_doctor_supports_json_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)

    assert cli.main(["env", "doctor", "--json"]) == 0

    data = json.loads(capsys.readouterr().out)
    assert data["checks"][0]["label"] == "Git repository"
    assert "suggestions" in data


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


def test_env_manager_status_reports_configured_managers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    cli.main(["init"])

    assert cli.main(["env", "manager", "status"]) == 0

    output = capsys.readouterr().out
    assert "Rig agent asset managers" in output
    assert "APM" in output
    assert "GitHub skills manager" in output
    assert "Vercel skills manager" in output


def test_env_manager_status_supports_json_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    cli.main(["init"])
    capsys.readouterr()

    assert cli.main(["env", "manager", "status", "--json"]) == 0

    data = json.loads(capsys.readouterr().out)
    assert [manager["id"] for manager in data["managers"]] == [
        "apm",
        "gh-skills",
        "vercel-skills",
    ]
    assert data["warnings"] == []


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
    assert "Run: rig guide agents" in output
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
