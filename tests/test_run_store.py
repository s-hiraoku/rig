from __future__ import annotations

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
    assert ".rig/env.yaml" in result.created

    assert (tmp_path / ".rig" / "config.yaml").is_file()
    assert (tmp_path / ".rig" / "env.yaml").is_file()
    assert (tmp_path / ".rig" / "runs").is_dir()
    assert "default_agent: codex" in (tmp_path / ".rig" / "config.yaml").read_text(
        encoding="utf-8"
    )
    assert "agent_asset_managers:" in (tmp_path / ".rig" / "env.yaml").read_text(
        encoding="utf-8"
    )


def test_init_is_idempotent(tmp_path: Path) -> None:
    store = RunStore(tmp_path)

    assert store.init().changed is True
    assert store.init().changed is False


def test_init_does_not_update_existing_env_yaml(tmp_path: Path) -> None:
    store = RunStore(tmp_path)
    store.init()
    (tmp_path / ".rig" / "env.yaml").write_text(
        """version: 1
agent_asset_managers:
  - id: apm
    label: Custom APM
    command: custom-apm
required_files: []
""",
        encoding="utf-8",
    )

    result = store.init()

    assert result.changed is False
    content = (tmp_path / ".rig" / "env.yaml").read_text(encoding="utf-8")
    assert "label: Custom APM" in content
    assert "command: custom-apm" in content
    assert "id: gh-skills" not in content


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


def test_init_reset_all_backs_up_config_and_env(tmp_path: Path) -> None:
    store = RunStore(tmp_path)
    store.init()
    (tmp_path / ".rig" / "config.yaml").write_text("custom: config\n", encoding="utf-8")
    (tmp_path / ".rig" / "env.yaml").write_text("custom: env\n", encoding="utf-8")
    now = datetime(2026, 5, 3, 12, 34, 56)

    result = store.init(reset="all", now=now)

    assert result.updated == [".rig/config.yaml", ".rig/env.yaml"]
    assert result.backups == [
        ".rig/config.yaml.bak-20260503-123456",
        ".rig/env.yaml.bak-20260503-123456",
    ]
    assert "default_agent: codex" in (tmp_path / ".rig" / "config.yaml").read_text(
        encoding="utf-8"
    )
    assert "agent_asset_managers:" in (tmp_path / ".rig" / "env.yaml").read_text(
        encoding="utf-8"
    )


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
