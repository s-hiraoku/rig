from __future__ import annotations

from pathlib import Path

import pytest
from conftest import init_git_repo, install_fake_command, install_fake_script

from rig import cli
from rig.mcp_server import (
    apply_patch_tool,
    get_artifact_tool,
    get_diff_tool,
    get_run_tool,
    list_runs_tool,
    run_tool,
)


def test_mcp_run_and_read_result(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    cli.main(["init"])
    install_fake_command(tmp_path, monkeypatch, stdout="done\n")

    result = run_tool(task="hello", cwd=str(tmp_path))

    assert result["ok"] is True
    assert result["status"] == "succeeded"
    assert result["run_id"]
    assert list_runs_tool(cwd=str(tmp_path))["runs"][0]["id"] == result["run_id"]
    assert get_run_tool(run_id="latest", cwd=str(tmp_path))["run"]["id"] == result["run_id"]
    assert get_artifact_tool(
        run_id=result["run_id"], filename="result.md", cwd=str(tmp_path)
    )["content"] == "done\n"


def test_mcp_run_returns_structured_error_for_bad_input(tmp_path: Path) -> None:
    store = cli.RunStore(tmp_path)
    store.init()

    result = run_tool(task=None, task_file=None, cwd=str(tmp_path))

    assert result == {
        "ok": False,
        "error": "Provide exactly one of --task or --task-file.",
    }


def test_mcp_run_resolves_relative_task_file_from_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    other_dir = tmp_path / "server-cwd"
    repo_dir = tmp_path / "repo"
    other_dir.mkdir()
    repo_dir.mkdir()
    monkeypatch.chdir(other_dir)
    cli.RunStore(repo_dir).init()
    install_fake_command(tmp_path, monkeypatch, stdout="done\n")
    (repo_dir / "task.md").write_text("hello from file\n", encoding="utf-8")

    result = run_tool(task_file="task.md", cwd=str(repo_dir))

    assert result["ok"] is True
    run_dir = next((repo_dir / ".rig" / "runs").iterdir())
    assert (run_dir / "task.md").read_text(encoding="utf-8") == "hello from file\n"


def test_mcp_get_run_handles_missing_history(tmp_path: Path) -> None:
    cli.RunStore(tmp_path).init()

    result = get_run_tool(run_id="latest", cwd=str(tmp_path))

    assert result == {"ok": False, "error": "No runs found."}


def test_mcp_worktree_diff_and_apply(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
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
    run = run_tool(task="edit tracked", agent="edit", worktree=True, cwd=str(tmp_path))

    diff = get_diff_tool(run_id=run["run_id"], cwd=str(tmp_path))
    assert diff["ok"] is True
    assert "+after" in diff["diff"]

    applied = apply_patch_tool(run_id=run["run_id"], cwd=str(tmp_path))
    assert applied["ok"] is True
    assert applied["applied"] is True
    assert (tmp_path / "tracked.txt").read_text(encoding="utf-8") == "after\n"
