from __future__ import annotations

from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from rig.adapters.exec import AgentCommandNotFoundError
from rig.config import ConfigError
from rig.orchestrator import RunOrchestrator, RunRequest
from rig.run_store import RigNotInitializedError, RunStore
from rig.worktree import WorktreeError, apply_patch


def create_mcp_server() -> FastMCP:
    server = FastMCP(
        "Rig",
        instructions=(
            "Run configured local coding agents through Rig and inspect "
            "file-backed run artifacts."
        ),
    )

    @server.tool()
    def rig_run(
        task: str | None = None,
        agent: str | None = None,
        task_file: str | None = None,
        worktree: bool = False,
        dry_run: bool = False,
        cwd: str | None = None,
    ) -> dict[str, Any]:
        """Start a Rig run and return structured run metadata."""
        return run_tool(
            task=task,
            agent=agent,
            task_file=task_file,
            worktree=worktree,
            dry_run=dry_run,
            cwd=cwd,
        )

    @server.tool()
    def rig_list_runs(cwd: str | None = None) -> dict[str, Any]:
        """List recent Rig runs."""
        return list_runs_tool(cwd=cwd)

    @server.tool()
    def rig_get_run(run_id: str = "latest", cwd: str | None = None) -> dict[str, Any]:
        """Get one Rig run by ID, or latest."""
        return get_run_tool(run_id=run_id, cwd=cwd)

    @server.tool()
    def rig_get_result(
        run_id: str = "latest", cwd: str | None = None
    ) -> dict[str, Any]:
        """Read result.md for a Rig run."""
        return get_artifact_tool(run_id=run_id, filename="result.md", cwd=cwd)

    @server.tool()
    def rig_get_diff(run_id: str = "latest", cwd: str | None = None) -> dict[str, Any]:
        """Read diff.patch for a worktree Rig run."""
        return get_diff_tool(run_id=run_id, cwd=cwd)

    @server.tool()
    def rig_apply_patch(
        run_id: str = "latest", cwd: str | None = None
    ) -> dict[str, Any]:
        """Apply a captured worktree diff to the repository."""
        return apply_patch_tool(run_id=run_id, cwd=cwd)

    return server


def serve_mcp() -> None:
    create_mcp_server().run()


def run_tool(
    *,
    task: str | None = None,
    agent: str | None = None,
    task_file: str | None = None,
    worktree: bool = False,
    dry_run: bool = False,
    cwd: str | None = None,
) -> dict[str, Any]:
    store = store_for(cwd)
    resolved_task_file = resolve_task_file(store, task_file)
    request = RunRequest(
        agent=agent,
        task=task,
        task_file=resolved_task_file,
        dry_run=dry_run,
        worktree=worktree,
    )
    try:
        outcome = RunOrchestrator(store).run(request)
    except (
        AgentCommandNotFoundError,
        ConfigError,
        RigNotInitializedError,
        ValueError,
        WorktreeError,
    ) as exc:
        return error_response(str(exc))

    data = parse_outcome_lines(outcome.lines)
    data.update(
        {
            "ok": outcome.exit_code == 0,
            "exit_code": outcome.exit_code,
            "messages": outcome.lines,
        }
    )
    return data


def list_runs_tool(*, cwd: str | None = None) -> dict[str, Any]:
    try:
        return {"ok": True, "runs": store_for(cwd).list_runs()}
    except RigNotInitializedError as exc:
        return error_response(str(exc))


def get_run_tool(*, run_id: str = "latest", cwd: str | None = None) -> dict[str, Any]:
    try:
        store = store_for(cwd)
        run = store.resolve_run(run_id)
    except RigNotInitializedError as exc:
        return error_response(str(exc))
    if run is None:
        return error_response(run_not_found_message(run_id))
    return {"ok": True, "run": run}


def get_artifact_tool(
    *, run_id: str = "latest", filename: str, cwd: str | None = None
) -> dict[str, Any]:
    try:
        store = store_for(cwd)
        run = store.resolve_run(run_id)
    except RigNotInitializedError as exc:
        return error_response(str(exc))
    if run is None:
        return error_response(run_not_found_message(run_id))
    return {
        "ok": True,
        "run_id": run.get("id", run_id),
        "filename": filename,
        "content": store.read_artifact(run, filename),
    }


def get_diff_tool(*, run_id: str = "latest", cwd: str | None = None) -> dict[str, Any]:
    try:
        store = store_for(cwd)
        run = store.resolve_run(run_id)
    except RigNotInitializedError as exc:
        return error_response(str(exc))
    if run is None:
        return error_response(run_not_found_message(run_id))

    diff_path_value = run.get("diff_path")
    if not isinstance(diff_path_value, str) or not diff_path_value:
        return error_response(f"Run has no captured diff: {run.get('id', run_id)}")

    diff_path = store.cwd / diff_path_value
    if not diff_path.is_file():
        return error_response(f"Diff file is missing: {diff_path_value}")
    return {
        "ok": True,
        "run_id": run.get("id", run_id),
        "diff_path": diff_path_value,
        "diff": diff_path.read_text(encoding="utf-8", errors="replace"),
    }


def apply_patch_tool(
    *, run_id: str = "latest", cwd: str | None = None
) -> dict[str, Any]:
    try:
        store = store_for(cwd)
        run = store.resolve_run(run_id)
    except RigNotInitializedError as exc:
        return error_response(str(exc))
    if run is None:
        return error_response(run_not_found_message(run_id))

    diff_path_value = run.get("diff_path")
    if not isinstance(diff_path_value, str) or not diff_path_value:
        return error_response(f"Run has no captured diff: {run.get('id', run_id)}")

    diff_path = store.cwd / diff_path_value
    if not diff_path.is_file():
        return error_response(f"Diff file is missing: {diff_path_value}")
    if not diff_path.read_text(encoding="utf-8").strip():
        return {
            "ok": True,
            "applied": False,
            "message": f"No changes to apply: {diff_path_value}",
        }

    try:
        result = apply_patch(store.cwd, diff_path)
    except WorktreeError as exc:
        return error_response(str(exc))
    return {
        "ok": True,
        "applied": True,
        "diff_path": diff_path_value,
        "applied_to_index": result.applied_to_index,
        "index_error": result.index_error,
    }


def store_for(cwd: str | None) -> RunStore:
    return RunStore(Path(cwd).expanduser().resolve() if cwd else Path.cwd())


def resolve_task_file(store: RunStore, task_file: str | None) -> str | None:
    if task_file is None or not task_file:
        return task_file
    path = Path(task_file).expanduser()
    if path.is_absolute():
        return str(path)
    return str(store.cwd / path)


def error_response(message: str) -> dict[str, Any]:
    return {"ok": False, "error": message}


def run_not_found_message(run_id: str) -> str:
    return "No runs found." if run_id == "latest" else f"Run not found: {run_id}"


def parse_outcome_lines(lines: list[str]) -> dict[str, Any]:
    data: dict[str, Any] = {}
    keys = {
        "Run": "run_id",
        "Status": "status",
        "Task": "task_path",
        "Command": "command_path",
        "Result": "result_path",
        "Diff": "diff_path",
        "Error": "error_summary",
    }
    for line in lines:
        label, separator, value = line.partition(": ")
        if separator and label in keys:
            data[keys[label]] = value
    return data
