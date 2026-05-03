from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RunContext:
    id: str
    agent: str
    run_dir: Path
    task_path: Path
    command_path: Path
    stdout_path: Path
    stderr_path: Path
    result_path: Path
    status_path: Path
    diff_path: Path
    worktree_path: Path | None
    cwd: Path
    execution_cwd: Path
