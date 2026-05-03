from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from rig.config import RigConfig

RISKY_TASK_WORDS = {
    "architecture",
    "delete",
    "migration",
    "rename",
    "reorganize",
    "restructure",
    "rewrite",
    "refactor",
}


@dataclass(frozen=True)
class Suggestion:
    mode: str
    agent: str
    command: list[str]
    confidence: str
    reasons: list[str]
    observations: dict[str, Any]


@dataclass(frozen=True)
class GitContext:
    is_git_repo: bool
    changed_files: list[str]
    staged_files: list[str]
    untracked_files: list[str]


def build_suggestion(
    cwd: Path,
    *,
    task: str,
    config: RigConfig | None,
    task_file: str | None = None,
) -> Suggestion:
    git_context = inspect_git_context(cwd)
    task_text = task.strip()
    task_lower = task_text.lower()
    ignored_task_file = normalize_task_file_path(cwd, task_file)
    changed_files = sorted(
        path
        for path in set(
            git_context.changed_files
            + git_context.staged_files
            + git_context.untracked_files
        )
        if not should_ignore_changed_file(path, ignored_task_file)
    )
    changed_dirs = sorted(
        {Path(path).parts[0] for path in changed_files if Path(path).parts}
    )
    tests_present = has_tests(cwd)
    risky_words = sorted(word for word in RISKY_TASK_WORDS if word in task_lower)

    score = 0
    reasons: list[str] = []
    if not git_context.is_git_repo:
        reasons.append("No git repository detected, so worktree isolation is unavailable.")
    if changed_files:
        score += 2
        reasons.append(
            f"Current working tree already has {len(changed_files)} changed file(s)."
        )
    if len(changed_files) >= 5:
        score += 1
        reasons.append("The existing change set spans several files.")
    if len(changed_dirs) >= 3:
        score += 1
        reasons.append("Changes are spread across multiple top-level directories.")
    if len(task_text) >= 240 or "\n" in task:
        score += 1
        reasons.append("The task is long enough that a task file may be easier to review.")
    if risky_words:
        score += 2
        reasons.append(f"Task wording suggests riskier change type(s): {', '.join(risky_words)}.")
    if tests_present:
        reasons.append("Tests were detected, so verification should be part of the run.")
    else:
        reasons.append("No obvious test directory or pytest configuration was detected.")

    use_worktree = git_context.is_git_repo and score >= 2
    mode = "worktree" if use_worktree else "run"
    if use_worktree:
        reasons.insert(0, "Use an isolated worktree so the generated patch stays reviewable.")
    else:
        reasons.insert(0, "Use a normal Rig run for a small or low-risk task.")

    agent = config.default_agent if config is not None else "codex"
    command = ["rig"]
    if use_worktree:
        command.extend(["worktree", "run"])
    else:
        command.append("run")
    command.append(agent)
    if task_file is not None:
        command.extend(["--task-file", task_file])
    elif should_prefer_task_file(task):
        command.extend(["--task-file", "task.md"])
    else:
        command.extend(["--task", task_text or "<task>"])

    observations: dict[str, Any] = {
        "git_repo": git_context.is_git_repo,
        "changed_file_count": len(changed_files),
        "changed_files": changed_files,
        "top_level_directory_count": len(changed_dirs),
        "tests_present": tests_present,
        "task_length": len(task),
        "risky_words": risky_words,
        "initialized": config is not None,
    }
    confidence = "medium" if git_context.is_git_repo else "low"
    if changed_files or risky_words:
        confidence = "high"

    return Suggestion(
        mode=mode,
        agent=agent,
        command=command,
        confidence=confidence,
        reasons=reasons,
        observations=observations,
    )


def inspect_git_context(cwd: Path) -> GitContext:
    if not is_git_repo(cwd):
        return GitContext(
            is_git_repo=False,
            changed_files=[],
            staged_files=[],
            untracked_files=[],
        )
    return GitContext(
        is_git_repo=True,
        changed_files=git_lines(cwd, ["diff", "--name-only"]),
        staged_files=git_lines(cwd, ["diff", "--cached", "--name-only"]),
        untracked_files=git_lines(cwd, ["ls-files", "--others", "--exclude-standard"]),
    )


def is_git_repo(cwd: Path) -> bool:
    completed = run_git(cwd, ["rev-parse", "--is-inside-work-tree"])
    return completed.returncode == 0 and completed.stdout.strip() == "true"


def git_lines(cwd: Path, args: list[str]) -> list[str]:
    completed = run_git(cwd, args)
    if completed.returncode != 0:
        return []
    return [line for line in completed.stdout.splitlines() if line]


def run_git(cwd: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["git", *args],
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return subprocess.CompletedProcess(args=["git", *args], returncode=1)


def has_tests(cwd: Path) -> bool:
    if (cwd / "tests").is_dir() or (cwd / "test").is_dir():
        return True
    pyproject = cwd / "pyproject.toml"
    if pyproject.is_file():
        text = pyproject.read_text(encoding="utf-8", errors="replace").lower()
        return "pytest" in text or "[tool.pytest" in text
    return False


def should_prefer_task_file(task: str) -> bool:
    return "\n" in task or len(task.strip()) >= 240


def should_ignore_changed_file(path: str, task_file: str | None) -> bool:
    return path == task_file or path.startswith(".rig/")


def normalize_task_file_path(cwd: Path, task_file: str | None) -> str | None:
    if task_file is None:
        return None
    path = Path(task_file).expanduser()
    if not path.is_absolute():
        return path.as_posix()
    try:
        return path.resolve().relative_to(cwd.resolve()).as_posix()
    except ValueError:
        return path.as_posix()
