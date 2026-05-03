from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path

from rig.adapters import create_adapter
from rig.adapters.codex import iso_now
from rig.adapters.exec import AgentCommandNotFoundError
from rig.adapters.manual import ManualAdapter
from rig.run_store import RunStore
from rig.worktree import capture_diff, create_worktree


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


class RunOrchestrator:
    def __init__(self, store: RunStore) -> None:
        self.store = store

    def run(self, request: RunRequest) -> RunOutcome:
        task, wrap_task = read_task(request)
        config = self.store.load_config()
        agent_name = request.agent or config.default_agent
        agent_config = config.agent(agent_name)

        context = self.store.create_run(agent_name)
        if request.worktree:
            worktree_path = self.store.worktrees_dir / context.id
            create_worktree(self.store.cwd, worktree_path)
            context = replace(
                context,
                worktree_path=worktree_path,
                execution_cwd=worktree_path,
            )
        self.store.write_task(context, task, wrap=wrap_task)

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
            return RunOutcome(
                exit_code=0,
                lines=[
                    f"Run: {context.id}",
                    "Status: waiting",
                    f"Task: {context.task_path.relative_to(context.cwd)}",
                    f"Result: {context.result_path.relative_to(context.cwd)}",
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
            return RunOutcome(
                exit_code=0,
                lines=[
                    f"Run: {context.id}",
                    "Status: created",
                    f"Command: {context.command_path.relative_to(context.cwd)}",
                    f"Result: {context.result_path.relative_to(context.cwd)}",
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
            return RunOutcome(
                exit_code=130,
                lines=[
                    f"Run: {context.id}",
                    "Status: aborted",
                    f"Error: {context.stderr_path.relative_to(context.cwd)}",
                ],
            )

        context.stdout_path.write_text(result.stdout, encoding="utf-8")
        context.stderr_path.write_text(result.stderr, encoding="utf-8")
        context.result_path.write_text(build_result_document(result.stdout), encoding="utf-8")
        if context.worktree_path is not None:
            context.diff_path.write_text(
                capture_diff(context.worktree_path),
                encoding="utf-8",
            )

        finished_at = iso_now()
        status = "succeeded" if result.exit_code == 0 else "failed"
        self.store.write_status(
            context,
            status=status,
            started_at=started_at,
            finished_at=finished_at,
            exit_code=result.exit_code,
        )

        lines = [
            f"Run: {context.id}",
            f"Status: {status}",
            f"Result: {context.result_path.relative_to(context.cwd)}",
        ]
        if context.worktree_path is not None:
            lines.append(f"Diff: {context.diff_path.relative_to(context.cwd)}")
        if status == "failed" and result.stderr.strip():
            lines.append(f"Error: {first_line(result.stderr)}")
        return RunOutcome(exit_code=0 if result.exit_code == 0 else 1, lines=lines)


def read_task(request: RunRequest) -> tuple[str, bool]:
    if bool(request.task) == bool(request.task_file):
        raise ValueError("Provide exactly one of --task or --task-file.")
    if request.task_file:
        return Path(request.task_file).read_text(encoding="utf-8"), False
    if request.task is None:
        raise ValueError("Provide exactly one of --task or --task-file.")
    return request.task, True


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
