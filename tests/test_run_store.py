from __future__ import annotations

from datetime import datetime
from pathlib import Path

from rig.run_store import RunStore


def test_init_creates_config_and_runs_dir(tmp_path: Path) -> None:
    store = RunStore(tmp_path)

    assert store.init() is True

    assert (tmp_path / ".rig" / "config.yaml").is_file()
    assert (tmp_path / ".rig" / "runs").is_dir()
    assert "default_agent: codex" in (tmp_path / ".rig" / "config.yaml").read_text(
        encoding="utf-8"
    )


def test_init_is_idempotent(tmp_path: Path) -> None:
    store = RunStore(tmp_path)

    assert store.init() is True
    assert store.init() is False


def test_create_run_uses_suffix_for_same_second(tmp_path: Path) -> None:
    store = RunStore(tmp_path)
    store.init()
    now = datetime(2026, 5, 2, 20, 30, 12)

    first = store.create_run("codex", now=now)
    second = store.create_run("codex", now=now)

    assert first.id == "20260502-203012-codex"
    assert second.id == "20260502-203012-codex-2"
    assert first.run_dir.is_dir()
    assert second.run_dir.is_dir()


def test_write_task_uses_markdown_heading(tmp_path: Path) -> None:
    store = RunStore(tmp_path)
    store.init()
    context = store.create_run("codex")

    store.write_task(context, "Review the current diff.")

    assert context.task_path.read_text(encoding="utf-8") == (
        "# Task\n\nReview the current diff.\n"
    )

