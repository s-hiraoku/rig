"""Unit tests for the lower-level rig.worktree helpers."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from rig import worktree


def test_apply_patch_reports_index_and_worktree_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    patch_path = tmp_path / "diff.patch"
    patch_path.write_text("not a patch\n", encoding="utf-8")

    def fake_run_git(
        cwd: Path, args: list[str], *, check: bool = True
    ) -> subprocess.CompletedProcess[str]:
        if "--index" in args:
            return subprocess.CompletedProcess(args, 1, "", "index failed")
        return subprocess.CompletedProcess(args, 1, "", "apply failed")

    monkeypatch.setattr(worktree, "run_git", fake_run_git)

    with pytest.raises(worktree.WorktreeError) as exc_info:
        worktree.apply_patch(tmp_path, patch_path)

    message = str(exc_info.value)
    assert "git apply failed: apply failed" in message
    assert "initial --index attempt: index failed" in message
