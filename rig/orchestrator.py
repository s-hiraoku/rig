from __future__ import annotations

import dataclasses
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from rig.adapters import create_adapter
from rig.adapters.codex import iso_now
from rig.adapters.exec import AgentCommandNotFoundError
from rig.adapters.manual import ManualAdapter
from rig.run_store import RunStore
from rig.worktree import WorktreeError, capture_diff, create_worktree


@dataclass(frozen=True)
class RunRequest:
    agent: str | None
    task: str | None
    task_file: str | None
    dry_run: bool
    worktree: bool


@dataclass(frozen=True)
class RunOutcome:
    exit_code: int
    lines: list[str]
    run_id: str
    status: str
    task_path: str | None = None
    command_path: str | None = None
    result_path: str | None = None
    diff_path: str | None = None
    error_summary: str | None = None

    @property
    def ok(self) -> bool:
        return self.exit_code == 0


def run_outcome_payload(outcome: RunOutcome) -> dict[str, Any]:
    return {"ok": outcome.ok, **dataclasses.asdict(outcome)}


@dataclass(frozen=True)
class TaskInput:
    text: str
    wrap: bool


class RunOrchestrator:
    def __init__(self, store: RunStore) -> None:
        self.store = store

    def run(self, request: RunRequest) -> RunOutcome:
        task_input = read_task(request)
        config = self.store.load_config()
        agent_name = request.agent or config.default_agent
        agent_config = config.agent(agent_name)

        context = self.store.create_run(agent_name, raw_task=task_input.text)
        if request.worktree:
            worktree_path = self.store.worktrees_dir / context.id
            create_worktree(self.store.cwd, worktree_path)
            context = replace(
                context,
                worktree_path=worktree_path,
                execution_cwd=worktree_path,
            )
        self.store.write_task(context, task_input.text, wrap=task_input.wrap)

        started_at = iso_now()
        command_adapter = create_adapter(agent_name, agent_config)
        if isinstance(command_adapter, ManualAdapter):
            self.store.write_command(
                context, command_adapter.command_metadata(context, started_at)
            )
            context.stdout_path.write_text("", encoding="utf-8")
            context.stderr_path.write_text("", encoding="utf-8")
            context.result_path.write_text(
                command_adapter.result_template(context), encoding="utf-8"
            )
            self.store.write_status(context, status="waiting", started_at=started_at)
            task_path = str(context.task_path.relative_to(context.cwd))
            result_path = str(context.result_path.relative_to(context.cwd))
            return RunOutcome(
                exit_code=0,
                run_id=context.id,
                status="waiting",
                task_path=task_path,
                result_path=result_path,
                lines=[
                    f"Run: {context.id}",
                    "Status: waiting",
                    f"Task: {task_path}",
                    f"Result: {result_path}",
                ],
            )

        self.store.write_command(
            context, command_adapter.command_metadata(context, started_at)
        )

        if request.dry_run:
            context.stdout_path.write_text("", encoding="utf-8")
            context.stderr_path.write_text("", encoding="utf-8")
            context.result_path.write_text(
                "Dry run: command was not executed.\n", encoding="utf-8"
            )
            self.store.write_status(context, status="created", started_at=started_at)
            command_path = str(context.command_path.relative_to(context.cwd))
            result_path = str(context.result_path.relative_to(context.cwd))
            return RunOutcome(
                exit_code=0,
                run_id=context.id,
                status="created",
                command_path=command_path,
                result_path=result_path,
                lines=[
                    f"Run: {context.id}",
                    "Status: created",
                    f"Command: {command_path}",
                    f"Result: {result_path}",
                ],
            )

        self.store.write_status(context, status="running", started_at=started_at)

        try:
            result = command_adapter.run(context)
        except AgentCommandNotFoundError:
            finished_at = iso_now()
            self.store.write_status(
                context,
                status="failed",
                started_at=started_at,
                finished_at=finished_at,
                exit_code=127,
            )
            raise
        except KeyboardInterrupt:
            finished_at = iso_now()
            context.stderr_path.write_text("Interrupted by user.\n", encoding="utf-8")
            self.store.write_status(
                context,
                status="aborted",
                started_at=started_at,
                finished_at=finished_at,
                exit_code=130,
            )
            error_path = str(context.stderr_path.relative_to(context.cwd))
            return RunOutcome(
                exit_code=130,
                run_id=context.id,
                status="aborted",
                error_summary=error_path,
                lines=[
                    f"Run: {context.id}",
                    "Status: aborted",
                    f"Error: {error_path}",
                ],
            )

        context.stdout_path.write_text(result.stdout, encoding="utf-8")
        context.stderr_path.write_text(result.stderr, encoding="utf-8")
        context.result_path.write_text(build_result_document(result.stdout), encoding="utf-8")
        if context.worktree_path is not None:
            try:
                context.diff_path.write_text(
                    capture_diff(context.worktree_path),
                    encoding="utf-8",
                )
            except WorktreeError as exc:
                finished_at = iso_now()
                diff_error = f"Rig worktree diff capture failed: {exc}\n"
                stderr = result.stderr
                if stderr and not stderr.endswith("\n"):
                    stderr += "\n"
                context.stderr_path.write_text(stderr + diff_error, encoding="utf-8")
                self.store.write_status(
                    context,
                    status="failed",
                    started_at=started_at,
                    finished_at=finished_at,
                    exit_code=1,
                )
                raise

        finished_at = iso_now()
        status = "succeeded" if result.exit_code == 0 else "failed"
        self.store.write_status(
            context,
            status=status,
            started_at=started_at,
            finished_at=finished_at,
            exit_code=result.exit_code,
        )

        result_path = str(context.result_path.relative_to(context.cwd))
        diff_path = (
            str(context.diff_path.relative_to(context.cwd))
            if context.worktree_path is not None
            else None
        )
        error_summary = (
            first_line(result.stderr)
            if status == "failed" and result.stderr.strip()
            else None
        )
        lines = [
            f"Run: {context.id}",
            f"Status: {status}",
            f"Result: {result_path}",
        ]
        if diff_path is not None:
            lines.append(f"Diff: {diff_path}")
        if error_summary is not None:
            lines.append(f"Error: {error_summary}")
        return RunOutcome(
            exit_code=0 if result.exit_code == 0 else 1,
            run_id=context.id,
            status=status,
            result_path=result_path,
            diff_path=diff_path,
            error_summary=error_summary,
            lines=lines,
        )


def read_task(request: RunRequest) -> TaskInput:
    has_task = request.task is not None
    has_task_file = request.task_file is not None
    if has_task == has_task_file:
        raise ValueError("Provide exactly one of --task or --task-file.")
    if request.task_file is not None:
        if not request.task_file:
            raise ValueError("--task-file requires a non-empty path.")
        return TaskInput(Path(request.task_file).read_text(encoding="utf-8"), False)
    assert request.task is not None
    return TaskInput(request.task, True)


def build_result_document(stdout: str) -> str:
    marker = "--- RIG RESULT ---"
    if marker in stdout:
        return stdout.rsplit(marker, maxsplit=1)[1].strip() + "\n"
    max_chars = 40_000
    if len(stdout) <= max_chars:
        return stdout
    return (
        "Result truncated from stdout.log. Showing the final "
        f"{max_chars} characters.\n\n"
        f"{stdout[-max_chars:]}"
    )


def first_line(value: str) -> str:
    stripped = value.strip()
    return stripped.splitlines()[0] if stripped else ""
