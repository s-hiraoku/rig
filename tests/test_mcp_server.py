from __future__ import annotations

import json
from pathlib import Path

import pytest
from conftest import init_git_repo, install_fake_command, install_fake_script

from rig import cli
from rig.mcp_server import (
    apply_patch_tool,
    create_mcp_server,
    get_artifact_tool,
    get_diff_tool,
    get_run_tool,
    list_agents_tool,
    list_runs_tool,
    policy_prompt,
    project_agents_md,
    run_tool,
)


@pytest.mark.anyio
async def test_mcp_server_registers_tools_prompts_and_resources() -> None:
    server = create_mcp_server()

    tools = {tool.name for tool in await server.list_tools()}
    prompts = {prompt.name for prompt in await server.list_prompts()}
    resources = {str(resource.uri) for resource in await server.list_resources()}

    assert tools == {
        "rig_delegate",
        "rig_patch_create",
        "rig_history",
        "rig_history_show",
        "rig_list_agents",
        "rig_patch_show",
        "rig_patch_apply",
    }
    assert prompts == {"rig_policy"}
    assert resources == {"rig://policy", "rig://agents-md"}


def test_mcp_delegate_and_read_history(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    cli.main(["init"])
    install_fake_command(tmp_path, monkeypatch, stdout="done\n")

    result = run_tool(task="hello", cwd=str(tmp_path))

    assert result["ok"] is True
    assert result["status"] == "succeeded"
    assert list_runs_tool(cwd=str(tmp_path))["runs"][0]["id"] == result["run_id"]
    shown = get_run_tool(run_id="latest", cwd=str(tmp_path))
    assert shown["run"]["id"] == result["run_id"]
    assert shown["result"] == "done\n"
    assert get_artifact_tool(
        run_id=result["run_id"], filename="result.md", cwd=str(tmp_path)
    )["content"] == "done\n"


def test_mcp_delegate_rejects_invalid_timeout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    cli.main(["init"])

    result = run_tool(task="hello", timeout_seconds=0, cwd=str(tmp_path))

    assert result == {"ok": False, "error": "--timeout-seconds must be 1 or greater."}


def test_mcp_delegate_resolves_relative_task_file_from_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    server_cwd = tmp_path / "server-cwd"
    repo_dir = tmp_path / "repo"
    server_cwd.mkdir()
    repo_dir.mkdir()
    monkeypatch.chdir(server_cwd)
    monkeypatch.setenv("RIG_MCP_ROOT", str(tmp_path))
    cli.RunStore(repo_dir).init()
    install_fake_command(tmp_path, monkeypatch, stdout="done\n")
    (repo_dir / "task.md").write_text("hello from file\n", encoding="utf-8")

    result = run_tool(task_file="task.md", cwd=str(repo_dir))

    assert result["ok"] is True
    run_dir = next((repo_dir / ".rig" / "runs").iterdir())
    assert (run_dir / "task.md").read_text(encoding="utf-8") == "hello from file\n"


def test_mcp_rejects_cwd_outside_allowed_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    allowed_dir = tmp_path / "allowed"
    other_dir = tmp_path / "other"
    allowed_dir.mkdir()
    other_dir.mkdir()
    monkeypatch.chdir(allowed_dir)

    result = list_runs_tool(cwd=str(other_dir))

    assert result["ok"] is False
    assert result["error"].startswith("cwd outside allowed root:")


def test_mcp_list_agents_reports_configured_agents(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    cli.main(["init"])

    result = list_agents_tool(cwd=str(tmp_path))

    assert result["ok"] is True
    assert result["default_agent"] == "codex"
    assert result["agents"] == [
        {
            "name": "claude",
            "command": "claude",
            "args": ["-p"],
            "default": False,
        },
        {
            "name": "codex",
            "command": "codex",
            "args": ["exec"],
            "default": True,
        },
        {
            "name": "copilot",
            "command": "copilot",
            "args": ["-p"],
            "default": False,
        },
        {
            "name": "gemini",
            "command": "gemini",
            "args": ["--prompt"],
            "default": False,
        }
    ]


def test_mcp_policy_prompt_prefers_project_agents_md(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    cli.main(["init"])
    (tmp_path / "AGENTS.md").write_text("# Project Policy\n", encoding="utf-8")

    assert project_agents_md(cwd=str(tmp_path)) == "# Project Policy\n"
    assert policy_prompt(cwd=str(tmp_path)) == "# Project Policy\n"


def test_mcp_patch_show_and_apply(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("RIG_MCP_ALLOW_APPLY", "1")
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
    run = run_tool(task="edit tracked", agent="edit", worktree=True, cwd=str(tmp_path))

    diff = get_diff_tool(run_id=run["run_id"], cwd=str(tmp_path))
    assert diff["ok"] is True
    assert "+after" in diff["diff"]

    applied = apply_patch_tool(run_id=run["run_id"], cwd=str(tmp_path))
    assert applied["ok"] is True
    assert applied["applied"] is True
    assert (tmp_path / "tracked.txt").read_text(encoding="utf-8") == "after\n"


def test_mcp_patch_show_rejects_diff_path_outside_run_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    cli.RunStore(tmp_path).init()
    run_dir = tmp_path / ".rig" / "runs" / "bad-diff"
    run_dir.mkdir()
    (tmp_path / ".rig" / "runs" / "secret.patch").write_text(
        "not this patch\n", encoding="utf-8"
    )
    (run_dir / "status.json").write_text(
        json.dumps(
            {
                "id": "bad-diff",
                "agent": "codex",
                "status": "succeeded",
                "started_at": "2026-05-02T20:30:12+09:00",
                "run_dir": ".rig/runs/bad-diff",
                "diff_path": ".rig/runs/bad-diff/../secret.patch",
            }
        ),
        encoding="utf-8",
    )

    result = get_diff_tool(run_id="bad-diff", cwd=str(tmp_path))

    assert result == {
        "ok": False,
        "error": (
            "diff_path is outside the expected Rig directory: "
            ".rig/runs/bad-diff/../secret.patch"
        ),
    }


def test_mcp_get_result_rejects_run_dir_outside_runs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    cli.RunStore(tmp_path).init()
    outside_dir = tmp_path / "outside-run"
    outside_dir.mkdir()
    (outside_dir / "result.md").write_text("secret\n", encoding="utf-8")
    run_dir = tmp_path / ".rig" / "runs" / "bad-run-dir"
    run_dir.mkdir()
    (run_dir / "status.json").write_text(
        json.dumps(
            {
                "id": "bad-run-dir",
                "agent": "codex",
                "status": "succeeded",
                "started_at": "2026-05-02T20:30:12+09:00",
                "run_dir": "../outside-run",
            }
        ),
        encoding="utf-8",
    )

    result = get_artifact_tool(
        run_id="bad-run-dir", filename="result.md", cwd=str(tmp_path)
    )

    assert result == {
        "ok": False,
        "error": "run_dir is outside the expected Rig directory: ../outside-run",
    }


def test_mcp_patch_apply_requires_explicit_opt_in(tmp_path: Path) -> None:
    cli.RunStore(tmp_path).init()

    result = apply_patch_tool(cwd=str(tmp_path))

    assert result == {
        "ok": False,
        "error": "rig_patch_apply is disabled. Set RIG_MCP_ALLOW_APPLY=1 to enable it.",
    }
