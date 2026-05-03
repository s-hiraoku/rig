from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


class WorktreeError(RuntimeError):
    pass


@dataclass(frozen=True)
class ApplyResult:
    applied_to_index: bool
    index_error: str | None = None


@dataclass(frozen=True)
class PruneResult:
    removed: list[Path]
    failed: list[tuple[Path, str]]


def create_worktree(repo_root: Path, worktree_path: Path) -> None:
    worktree_path.parent.mkdir(parents=True, exist_ok=True)
    run_git(repo_root, ["worktree", "add", "--detach", str(worktree_path), "HEAD"])


def capture_diff(worktree_path: Path) -> str:
    run_git(worktree_path, ["add", "-A"])
    completed = run_git(worktree_path, ["diff", "--cached", "--binary"], check=False)
    if completed.returncode not in {0, 1}:
        raise WorktreeError(completed.stderr.strip() or "Could not capture git diff.")
    return completed.stdout


def apply_patch(repo_root: Path, patch_path: Path) -> ApplyResult:
    if not patch_path.is_file():
        raise WorktreeError(f"Patch file does not exist: {patch_path}")
    completed = run_git(
        repo_root,
        ["apply", "--index", str(patch_path)],
        check=False,
    )
    applied_to_index = completed.returncode == 0
    index_error = None if applied_to_index else completed.stderr.strip()
    if completed.returncode != 0:
        completed = run_git(repo_root, ["apply", str(patch_path)], check=False)
    if completed.returncode != 0:
        raise WorktreeError(completed.stderr.strip() or "Could not apply patch.")
    return ApplyResult(applied_to_index=applied_to_index, index_error=index_error)


def prune_worktrees(repo_root: Path, worktrees_dir: Path) -> PruneResult:
    if not worktrees_dir.is_dir():
        return PruneResult(removed=[], failed=[])

    removed: list[Path] = []
    failed: list[tuple[Path, str]] = []
    for worktree_path in sorted(path for path in worktrees_dir.iterdir() if path.is_dir()):
        completed = run_git(
            repo_root,
            ["worktree", "remove", "--force", str(worktree_path)],
            check=False,
        )
        if completed.returncode == 0:
            removed.append(worktree_path)
        else:
            failed.append(
                (
                    worktree_path,
                    completed.stderr.strip() or "Could not remove worktree.",
                )
            )
    return PruneResult(removed=removed, failed=failed)


def run_git(
    cwd: Path, args: list[str], *, check: bool = True
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    if check and completed.returncode != 0:
        raise WorktreeError(completed.stderr.strip() or "Git command failed.")
    return completed
