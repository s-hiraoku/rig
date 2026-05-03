from __future__ import annotations

import subprocess
from pathlib import Path


class WorktreeError(RuntimeError):
    pass


def create_worktree(repo_root: Path, worktree_path: Path) -> None:
    worktree_path.parent.mkdir(parents=True, exist_ok=True)
    run_git(repo_root, ["worktree", "add", "--detach", str(worktree_path), "HEAD"])


def capture_diff(worktree_path: Path) -> str:
    run_git(worktree_path, ["add", "-A"])
    completed = run_git(worktree_path, ["diff", "--cached", "--binary"], check=False)
    if completed.returncode not in {0, 1}:
        raise WorktreeError(completed.stderr.strip() or "Could not capture git diff.")
    return completed.stdout


def apply_patch(repo_root: Path, patch_path: Path) -> bool:
    if not patch_path.is_file():
        raise WorktreeError(f"Patch file does not exist: {patch_path}")
    completed = run_git(
        repo_root,
        ["apply", "--index", str(patch_path)],
        check=False,
    )
    applied_to_index = completed.returncode == 0
    if completed.returncode != 0:
        completed = run_git(repo_root, ["apply", str(patch_path)], check=False)
    if completed.returncode != 0:
        raise WorktreeError(completed.stderr.strip() or "Could not apply patch.")
    return applied_to_index


def prune_worktrees(repo_root: Path, worktrees_dir: Path) -> list[Path]:
    if not worktrees_dir.is_dir():
        return []

    removed: list[Path] = []
    for worktree_path in sorted(path for path in worktrees_dir.iterdir() if path.is_dir()):
        run_git(
            repo_root,
            ["worktree", "remove", "--force", str(worktree_path)],
        )
        removed.append(worktree_path)
    return removed


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
