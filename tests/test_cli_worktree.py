from __future__ import annotations

import json
from pathlib import Path

import pytest
from conftest import init_git_repo, install_fake_script

from rig import cli


def test_run_worktree_captures_diff(
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
    runner: exec
    command: edit-file
    prompt_style: task
""",
        encoding="utf-8",
    )

    assert cli.main(["worktree", "run", "edit", "--task", "edit tracked"]) == 0

    output = capsys.readouterr().out
    assert "Diff: .rig/runs/" in output
    run_dir = next((tmp_path / ".rig" / "runs").iterdir())
    diff = (run_dir / "diff.patch").read_text(encoding="utf-8")
    assert "-before" in diff
    assert "+after" in diff
    status = json.loads((run_dir / "status.json").read_text(encoding="utf-8"))
    assert status["worktree_dir"].startswith(".rig/worktrees/")
    assert status["diff_path"].endswith("/diff.patch")
    assert (tmp_path / "tracked.txt").read_text(encoding="utf-8") == "before\n"


def test_run_worktree_captures_untracked_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    init_git_repo(tmp_path)
    cli.main(["init"])
    install_fake_script(
        tmp_path,
        monkeypatch,
        name="create-file",
        body="from pathlib import Path\nPath('new_file.txt').write_text('new\\n', encoding='utf-8')\nprint('created')\n",
    )
    (tmp_path / ".rig" / "config.yaml").write_text(
        """version: 1
agents:
  creator:
    runner: exec
    command: create-file
    prompt_style: task
""",
        encoding="utf-8",
    )

    assert cli.main(["worktree", "run", "creator", "--task", "create file"]) == 0

    capsys.readouterr()
    run_dir = next((tmp_path / ".rig" / "runs").iterdir())
    diff = (run_dir / "diff.patch").read_text(encoding="utf-8")
    assert "new_file.txt" in diff
    assert "+new" in diff
    assert not (tmp_path / "new_file.txt").exists()


def test_worktree_pty_run_uses_worktree_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    init_git_repo(tmp_path)
    cli.main(["init"])
    install_fake_script(
        tmp_path,
        monkeypatch,
        name="pty-edit",
        body="from pathlib import Path\nPath('tracked.txt').write_text('after\\n', encoding='utf-8')\nprint('edited')\n",
    )
    (tmp_path / ".rig" / "config.yaml").write_text(
        """version: 1
agents:
  pty_edit:
    runner: pty
    command: pty-edit
    timeout_seconds: 5
    prompt_style: task
""",
        encoding="utf-8",
    )

    assert cli.main(["worktree", "run", "pty_edit", "--task", "edit tracked"]) == 0

    capsys.readouterr()
    run_dir = next((tmp_path / ".rig" / "runs").iterdir())
    diff = (run_dir / "diff.patch").read_text(encoding="utf-8")
    assert "-before" in diff
    assert "+after" in diff
    assert (tmp_path / "tracked.txt").read_text(encoding="utf-8") == "before\n"


def test_worktree_show_and_apply_worktree_run(
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
    runner: exec
    command: edit-file
    prompt_style: task
""",
        encoding="utf-8",
    )
    cli.main(["worktree", "run", "edit", "--task", "edit tracked"])

    assert cli.main(["worktree", "show", "latest"]) == 0
    diff_output = capsys.readouterr().out
    assert "+after" in diff_output

    assert cli.main(["worktree", "apply", "latest"]) == 0

    output = capsys.readouterr().out
    assert "Applied: .rig/runs/" in output
    assert (tmp_path / "tracked.txt").read_text(encoding="utf-8") == "after\n"


def test_worktree_apply_empty_worktree_diff_is_noop(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    init_git_repo(tmp_path)
    cli.main(["init"])
    install_fake_script(
        tmp_path,
        monkeypatch,
        name="noop",
        body="print('noop')\n",
    )
    (tmp_path / ".rig" / "config.yaml").write_text(
        """version: 1
agents:
  noop:
    runner: exec
    command: noop
    prompt_style: task
""",
        encoding="utf-8",
    )
    cli.main(["worktree", "run", "noop", "--task", "do nothing"])

    assert cli.main(["worktree", "apply", "latest"]) == 0

    output = capsys.readouterr().out
    assert "No changes to apply: .rig/runs/" in output
    assert (tmp_path / "tracked.txt").read_text(encoding="utf-8") == "before\n"


def test_worktree_apply_missing_diff_reports_specific_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    cli.main(["init"])
    run_dir = tmp_path / ".rig" / "runs" / "missing-diff"
    run_dir.mkdir()
    (run_dir / "status.json").write_text(
        json.dumps(
            {
                "id": "missing-diff",
                "agent": "codex",
                "status": "succeeded",
                "started_at": "2026-05-02T20:30:12+09:00",
                "finished_at": "2026-05-02T20:31:04+09:00",
                "run_dir": ".rig/runs/missing-diff",
                "diff_path": ".rig/runs/missing-diff/diff.patch",
            }
        ),
        encoding="utf-8",
    )

    assert cli.main(["worktree", "apply", "missing-diff"]) == 1

    assert (
        "Diff file is missing: .rig/runs/missing-diff/diff.patch"
        in capsys.readouterr().err
    )


def test_worktree_prune_removes_rig_worktrees(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    init_git_repo(tmp_path)
    cli.main(["init"])
    install_fake_script(
        tmp_path,
        monkeypatch,
        name="noop",
        body="print('noop')\n",
    )
    (tmp_path / ".rig" / "config.yaml").write_text(
        """version: 1
agents:
  noop:
    runner: exec
    command: noop
    prompt_style: task
""",
        encoding="utf-8",
    )
    cli.main(["worktree", "run", "noop", "--task", "do nothing"])
    capsys.readouterr()

    assert any((tmp_path / ".rig" / "worktrees").iterdir())
    assert cli.main(["worktree", "prune"]) == 0

    output = capsys.readouterr().out
    assert "Removed: .rig/worktrees/" in output
    assert list((tmp_path / ".rig" / "worktrees").iterdir()) == []


def test_worktree_prune_reports_partial_failures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.chdir(tmp_path)
    init_git_repo(tmp_path)
    cli.main(["init"])
    worktrees_dir = tmp_path / ".rig" / "worktrees"
    (worktrees_dir / "bad-worktree").mkdir(parents=True)

    assert cli.main(["worktree", "prune"]) == 1

    assert "Failed: .rig/worktrees/bad-worktree:" in capsys.readouterr().err
