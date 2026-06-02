from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from rig.run_store import RunStore


def test_init_creates_config_and_runs_dir(tmp_path: Path) -> None:
    store = RunStore(tmp_path)
    result = store.init()

    assert result.changed is True
    assert ".rig/" in result.created
    assert ".rig/runs/" in result.created
    assert ".rig/config.yaml" in result.created
    assert ".rig/instructions/rig.md" in result.created
    assert "AGENTS.md" in result.created

    assert (tmp_path / ".rig" / "config.yaml").is_file()
    assert (tmp_path / ".rig" / "instructions" / "rig.md").is_file()
    assert (tmp_path / "AGENTS.md").is_file()
    assert (tmp_path / ".rig" / "runs").is_dir()
    assert "default_agent: codex" in (tmp_path / ".rig" / "config.yaml").read_text(
        encoding="utf-8"
    )
    assert "Rig Instructions" in (
        tmp_path / ".rig" / "instructions" / "rig.md"
    ).read_text(
        encoding="utf-8"
    )
    assert not (tmp_path / ".rig" / "env.yaml").exists()
    assert ".rig/instructions/rig.md" in (tmp_path / "AGENTS.md").read_text(
        encoding="utf-8"
    )
    config = store.load_config()
    assert config.agent("antigravity").command == "agy"
    assert config.agent("antigravity").args == ["-p"]
    assert config.agent("antigravity").prompt_style == "task"


def test_init_is_idempotent(tmp_path: Path) -> None:
    store = RunStore(tmp_path)

    assert store.init().changed is True
    assert store.init().changed is False


def test_init_appends_references_to_existing_instruction_files(tmp_path: Path) -> None:
    (tmp_path / "AGENTS.md").write_text("# Agents\n\nKeep this.\n", encoding="utf-8")
    store = RunStore(tmp_path)

    result = store.init()

    assert "AGENTS.md" in result.updated
    agents_content = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert "# Agents\n\nKeep this." in agents_content
    assert ".rig/instructions/rig.md" in agents_content
    assert store.init().changed is False


def test_init_does_not_update_existing_instruction_file(tmp_path: Path) -> None:
    store = RunStore(tmp_path)
    store.init()
    instruction_path = tmp_path / ".rig" / "instructions" / "rig.md"
    instruction_path.write_text("custom instructions\n", encoding="utf-8")

    result = store.init()

    assert result.changed is False
    assert instruction_path.read_text(encoding="utf-8") == "custom instructions\n"


def test_init_reset_config_backs_up_and_recreates_config(tmp_path: Path) -> None:
    store = RunStore(tmp_path)
    store.init()
    (tmp_path / ".rig" / "config.yaml").write_text("custom: true\n", encoding="utf-8")
    now = datetime(2026, 5, 3, 12, 34, 56)

    result = store.init(reset="config", now=now)

    assert result.updated == [".rig/config.yaml"]
    assert result.backups == [".rig/config.yaml.bak-20260503-123456"]
    assert "default_agent: codex" in (tmp_path / ".rig" / "config.yaml").read_text(
        encoding="utf-8"
    )
    assert (tmp_path / ".rig" / "config.yaml.bak-20260503-123456").read_text(
        encoding="utf-8"
    ) == "custom: true\n"


def test_init_reset_all_backs_up_config_and_instructions(tmp_path: Path) -> None:
    store = RunStore(tmp_path)
    store.init()
    (tmp_path / ".rig" / "config.yaml").write_text("custom: config\n", encoding="utf-8")
    instruction_path = tmp_path / ".rig" / "instructions" / "rig.md"
    instruction_path.write_text("custom instructions\n", encoding="utf-8")
    now = datetime(2026, 5, 3, 12, 34, 56)

    result = store.init(reset="all", now=now)

    assert result.updated == [".rig/config.yaml", ".rig/instructions/rig.md"]
    assert result.backups == [
        ".rig/config.yaml.bak-20260503-123456",
        ".rig/instructions/rig.md.bak-20260503-123456",
    ]
    assert "default_agent: codex" in (tmp_path / ".rig" / "config.yaml").read_text(
        encoding="utf-8"
    )
    assert "Rig Instructions" in instruction_path.read_text(
        encoding="utf-8"
    )
    assert not (tmp_path / ".rig" / "env.yaml").exists()


def test_create_run_uses_suffix_for_same_second(tmp_path: Path) -> None:
    store = RunStore(tmp_path)
    store.init()
    now = datetime(2026, 5, 2, 20, 30, 12)

    first = store.create_run("codex", raw_task="first", now=now)
    second = store.create_run("codex", raw_task="second", now=now)

    assert first.id == "20260502-203012-codex"
    assert second.id == "20260502-203012-codex-2"
    assert first.run_dir.is_dir()
    assert second.run_dir.is_dir()


def test_list_runs_breaks_started_at_ties_by_id(tmp_path: Path) -> None:
    store = RunStore(tmp_path)
    store.init()
    now = datetime(2026, 5, 2, 20, 30, 12)
    first = store.create_run("codex", raw_task="first", now=now)
    second = store.create_run("codex", raw_task="second", now=now)
    started_at = "2026-05-02T20:30:12+09:00"
    store.write_status(first, status="succeeded", started_at=started_at, exit_code=0)
    store.write_status(second, status="succeeded", started_at=started_at, exit_code=0)

    latest = store.latest_run()
    assert [run["id"] for run in store.list_runs()] == [second.id, first.id]
    assert latest is not None
    assert latest["id"] == second.id


def test_latest_run_uses_numeric_suffix_for_started_at_ties(tmp_path: Path) -> None:
    store = RunStore(tmp_path)
    store.init()
    now = datetime(2026, 5, 2, 20, 30, 12)
    contexts = [
        store.create_run("codex", raw_task=f"run {index}", now=now)
        for index in range(10)
    ]
    started_at = "2026-05-02T20:30:12+09:00"
    for context in contexts:
        store.write_status(
            context,
            status="succeeded",
            started_at=started_at,
            exit_code=0,
        )

    latest = store.latest_run()
    assert contexts[-1].id == "20260502-203012-codex-10"
    assert latest is not None
    assert latest["id"] == contexts[-1].id


def test_find_run_rejects_paths_outside_runs_dir(tmp_path: Path) -> None:
    store = RunStore(tmp_path)
    store.init()
    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()
    (outside_dir / "status.json").write_text(
        json.dumps({"id": "outside", "status": "succeeded"}),
        encoding="utf-8",
    )

    assert store.find_run("../../outside") is None
    assert store.find_run(str(outside_dir)) is None
    assert store.find_run("nested/run") is None
    assert store.find_run("nested\\run") is None
    assert store.find_run("..") is None


def test_write_task_uses_markdown_heading(tmp_path: Path) -> None:
    store = RunStore(tmp_path)
    store.init()
    context = store.create_run("codex", raw_task="Review the current diff.")

    store.write_task(context, "Review the current diff.")

    assert context.task_path.read_text(encoding="utf-8") == (
        "# Task\n\nReview the current diff.\n"
    )


def test_write_task_can_preserve_task_file_content(tmp_path: Path) -> None:
    store = RunStore(tmp_path)
    store.init()
    context = store.create_run("codex", raw_task="# Existing\n\nDo it.\n")

    store.write_task(context, "# Existing\n\nDo it.\n", wrap=False)

    assert context.task_path.read_text(encoding="utf-8") == "# Existing\n\nDo it.\n"
