from __future__ import annotations

import json
from pathlib import Path

import pytest
from conftest import init_git_repo, install_fake_command, install_fake_script

from rig import cli
from rig.policy import RIG_INSTRUCTION_PATH, rig_instruction_file_content


def test_top_level_help_shows_new_command_shape(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        cli.main(["--help"])

    assert exc_info.value.code == 0
    output = capsys.readouterr().out
    assert "{init,delegate,patch,history,doctor,mcp}" in output
    assert "worktree" not in output
    assert "suggest" not in output
    assert "manual" not in output


def test_init_creates_config_history_and_instructions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)

    assert cli.main(["init"]) == 0

    assert (tmp_path / ".rig" / "config.yaml").is_file()
    assert (tmp_path / ".rig" / "runs").is_dir()
    assert (tmp_path / RIG_INSTRUCTION_PATH).is_file()
    assert (tmp_path / "CLAUDE.md").is_file()
    assert not (tmp_path / ".rig" / "env.yaml").exists()
    output = capsys.readouterr().out
    assert "CLAUDE.md now references .rig/instructions/rig.md" in output
    assert "Add this snippet to AGENTS.md" in output
    assert RIG_INSTRUCTION_PATH in output


def test_init_force_resets_config_and_instructions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    cli.main(["init"])
    (tmp_path / ".rig" / "config.yaml").write_text("custom: config\n", encoding="utf-8")
    (tmp_path / RIG_INSTRUCTION_PATH).write_text("custom\n", encoding="utf-8")

    assert cli.main(["init", "--force"]) == 0

    output = capsys.readouterr().out
    assert "Updated: .rig/config.yaml" in output
    assert f"Updated: {RIG_INSTRUCTION_PATH}" in output
    assert "Backup: .rig/config.yaml.bak-" in output
    assert f"Backup: {RIG_INSTRUCTION_PATH}.bak-" in output
    assert "default_agent: codex" in (tmp_path / ".rig" / "config.yaml").read_text(
        encoding="utf-8"
    )
    assert (tmp_path / RIG_INSTRUCTION_PATH).read_text(
        encoding="utf-8"
    ) == rig_instruction_file_content()


def test_delegate_writes_run_artifacts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    cli.main(["init"])
    install_fake_command(tmp_path, monkeypatch, stdout="done\n")

    assert cli.main(["delegate", "codex", "--task", "hello"]) == 0

    captured = capsys.readouterr()
    assert "Status: succeeded" in captured.out
    run_dir = next((tmp_path / ".rig" / "runs").iterdir())
    assert (run_dir / "task.md").read_text(encoding="utf-8") == "# Task\n\nhello\n"
    assert (run_dir / "stdout.log").read_text(encoding="utf-8") == "done\n"
    assert (run_dir / "stderr.log").read_text(encoding="utf-8") == ""
    assert (run_dir / "result.md").read_text(encoding="utf-8") == "done\n"
    command = json.loads((run_dir / "command.json").read_text(encoding="utf-8"))
    assert command["agent"] == "codex"
    assert command["command"] == "codex"
    assert "runner" not in command


def test_delegate_supports_json_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    cli.main(["init"])
    install_fake_command(tmp_path, monkeypatch, stdout="done\n")
    capsys.readouterr()

    assert cli.main(["delegate", "codex", "--task", "hello", "--json"]) == 0

    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is True
    assert data["status"] == "succeeded"
    assert data["run_id"].endswith("-codex")


def test_delegate_uses_default_agent_when_agent_is_omitted(
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
    command: custom-agent
    prompt_style: task
""",
        encoding="utf-8",
    )

    assert cli.main(["delegate", "--task", "hello"]) == 0

    capsys.readouterr()
    run_dir = next((tmp_path / ".rig" / "runs").iterdir())
    assert run_dir.name.endswith("-helper")


def test_delegate_rejects_missing_or_duplicate_task(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    cli.main(["init"])
    task_file = tmp_path / "task.md"
    task_file.write_text("hello", encoding="utf-8")

    assert cli.main(["delegate", "codex"]) == 2
    assert (
        cli.main(
            ["delegate", "codex", "--task", "hello", "--task-file", str(task_file)]
        )
        == 2
    )

    assert "Provide exactly one of --task or --task-file." in capsys.readouterr().err


def test_delegate_dry_run_writes_command_without_executing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    cli.main(["init"])

    assert cli.main(["delegate", "codex", "--task", "hello", "--dry-run"]) == 0

    output = capsys.readouterr().out
    assert "Status: created" in output
    run_dir = next((tmp_path / ".rig" / "runs").iterdir())
    assert (run_dir / "result.md").read_text(encoding="utf-8") == (
        "Dry run: command was not executed.\n"
    )
    assert not (tmp_path / "fake-command-argv.json").exists()


def test_history_lists_and_shows_runs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    cli.main(["init"])
    install_fake_command(tmp_path, monkeypatch, stdout="done\n")
    cli.main(["delegate", "codex", "--task", "hello"])
    capsys.readouterr()

    assert cli.main(["history"]) == 0
    history_output = capsys.readouterr().out
    assert "codex" in history_output
    assert "succeeded" in history_output

    assert cli.main(["history", "show", "latest"]) == 0
    show_output = capsys.readouterr().out
    assert "--- Result ---" in show_output
    assert "done" in show_output


def test_patch_create_show_apply_and_prune(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    init_git_repo(tmp_path)
    cli.main(["init"])
    install_fake_script(
        tmp_path,
        monkeypatch,
        name="edit-file",
        body="from pathlib import Path\nPath('tracked.txt').write_text('after\\n', encoding='utf-8')\nprint('edited')\n",
    )
    (tmp_path / ".rig" / "config.yaml").write_text(
        """version: 1
agents:
  edit:
    command: edit-file
    prompt_style: task
""",
        encoding="utf-8",
    )

    assert cli.main(["patch", "create", "edit", "--task", "edit tracked"]) == 0
    create_output = capsys.readouterr().out
    assert "Diff: .rig/runs/" in create_output
    assert (tmp_path / "tracked.txt").read_text(encoding="utf-8") == "before\n"

    assert cli.main(["patch", "show", "latest"]) == 0
    diff_output = capsys.readouterr().out
    assert "--- Diff ---" in diff_output
    assert "+after" in diff_output

    assert cli.main(["patch", "apply", "latest"]) == 0
    assert (tmp_path / "tracked.txt").read_text(encoding="utf-8") == "after\n"

    assert cli.main(["patch", "prune"]) == 0


def test_doctor_prints_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    cli.main(["init"])
    capsys.readouterr()

    assert cli.main(["doctor"]) == 0

    output = capsys.readouterr().out
    assert "Rig doctor" in output
    assert "Rig config" in output


def test_deleted_commands_are_not_registered() -> None:
    parser = cli.build_parser()
    valid_invocations = (
        ["init"],
        ["delegate", "codex", "--task", "check"],
        ["patch", "prune"],
        ["history"],
        ["history", "show", "latest"],
        ["doctor"],
        ["mcp", "serve"],
    )
    for argv in valid_invocations:
        parser.parse_args(argv)

    for command in (
        "run",
        "list",
        "show",
        "worktree",
        "suggest",
        "manual",
        "guide",
        "env",
    ):
        with pytest.raises(SystemExit) as exc_info:
            parser.parse_args([command])
        assert exc_info.value.code == 2
