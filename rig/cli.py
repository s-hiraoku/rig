from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rig.adapters.codex import CodexAdapter, CodexNotFoundError, iso_now
from rig.config import ConfigError
from rig.run_store import RigNotInitializedError, RunStore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rig")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init", help="Initialize Rig in the current repository")

    run_parser = subparsers.add_parser("run", help="Run an agent")
    run_subparsers = run_parser.add_subparsers(dest="agent", required=True)
    codex_parser = run_subparsers.add_parser("codex", help="Run Codex through Rig")
    codex_parser.add_argument("--task", help="Task text to pass to the agent")
    codex_parser.add_argument("--task-file", help="Path to a file containing the task")

    runs_parser = subparsers.add_parser("runs", help="Inspect run history")
    runs_subparsers = runs_parser.add_subparsers(dest="runs_command", required=True)
    runs_subparsers.add_parser("list", help="List recent runs")
    show_parser = runs_subparsers.add_parser("show", help="Show a run")
    show_parser.add_argument("run_id", help="Run ID, or 'latest'")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    store = RunStore(Path.cwd())

    try:
        if args.command == "init":
            initialized = store.init()
            if initialized:
                print("Initialized Rig in .rig/")
            else:
                print("Rig already initialized.")
            return 0

        if args.command == "run" and args.agent == "codex":
            return run_codex(args, store)

        if args.command == "runs":
            if args.runs_command == "list":
                return list_runs(store)
            if args.runs_command == "show":
                return show_run(store, args.run_id)

    except RigNotInitializedError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except CodexNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except ConfigError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    parser.error("unsupported command")
    return 2


def run_codex(args: argparse.Namespace, store: RunStore) -> int:
    if bool(args.task) == bool(args.task_file):
        print("Provide exactly one of --task or --task-file.", file=sys.stderr)
        return 2

    task = args.task
    if args.task_file:
        task = Path(args.task_file).read_text(encoding="utf-8")

    agent_config = store.load_config().agent("codex")
    context = store.create_run("codex")
    store.write_task(context, task)

    adapter = CodexAdapter(command=agent_config.command, args=agent_config.args)
    started_at = iso_now()
    store.write_command(context, adapter.command_metadata(context, started_at))
    store.write_status(context, status="running", started_at=started_at)

    try:
        result = adapter.run(context)
    except CodexNotFoundError:
        finished_at = iso_now()
        store.write_status(
            context,
            status="failed",
            started_at=started_at,
            finished_at=finished_at,
            exit_code=127,
        )
        raise

    context.stdout_path.write_text(result.stdout, encoding="utf-8")
    context.stderr_path.write_text(result.stderr, encoding="utf-8")
    context.result_path.write_text(result.stdout, encoding="utf-8")

    finished_at = iso_now()
    status = "succeeded" if result.exit_code == 0 else "failed"
    store.write_status(
        context,
        status=status,
        started_at=started_at,
        finished_at=finished_at,
        exit_code=result.exit_code,
    )

    print(f"Run: {context.id}")
    print(f"Status: {status}")
    print(f"Result: {context.result_path.relative_to(context.cwd)}")
    if status == "failed" and result.stderr.strip():
        print(f"Error: {first_line(result.stderr)}")
    return 0 if result.exit_code == 0 else 1


def list_runs(store: RunStore) -> int:
    runs = store.list_runs()
    print(f"{'ID':<26} {'AGENT':<7} {'STATUS':<10} STARTED")
    for run in runs:
        started_at = format_started_at(str(run.get("started_at", "")))
        print(
            f"{str(run.get('id', '')):<26} "
            f"{str(run.get('agent', '')):<7} "
            f"{str(run.get('status', '')):<10} "
            f"{started_at}"
        )
    return 0


def show_run(store: RunStore, run_id: str) -> int:
    run = store.latest_run() if run_id == "latest" else store.find_run(run_id)
    if run is None:
        print(f"Run not found: {run_id}", file=sys.stderr)
        return 1

    result_path = f"{run['run_dir']}/result.md"
    print(f"ID:        {run['id']}")
    print(f"Agent:     {run['agent']}")
    print(f"Status:    {run['status']}")
    print(f"Run dir:   {run['run_dir']}")
    print(f"Result:    {result_path}")
    print()
    print("--- Result ---")
    print()
    print(store.read_result(run), end="")
    return 0


def format_started_at(value: str) -> str:
    if not value:
        return ""
    return value[:19].replace("T", " ")


def first_line(value: str) -> str:
    return value.strip().splitlines()[0]


if __name__ == "__main__":
    raise SystemExit(main())
