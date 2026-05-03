from __future__ import annotations

import argparse
import sys
from pathlib import Path

from rig.adapters.codex import CodexAdapter, CodexNotFoundError, iso_now
from rig.config import ConfigError
from rig.env_doctor import build_doctor_report, format_doctor_report, format_env_plan
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
    codex_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Create run artifacts and command metadata without executing Codex",
    )

    runs_parser = subparsers.add_parser("runs", help="Inspect run history")
    runs_subparsers = runs_parser.add_subparsers(dest="runs_command", required=True)
    runs_subparsers.add_parser("list", help="List recent runs")
    show_parser = runs_subparsers.add_parser("show", help="Show a run")
    show_parser.add_argument("run_id", help="Run ID, or 'latest'")

    agents_parser = subparsers.add_parser(
        "agents", help="Print instructions for AI coding agents"
    )
    agents_subparsers = agents_parser.add_subparsers(
        dest="agents_command", required=True
    )
    agents_subparsers.add_parser(
        "snippet", help="Print an AGENTS.md snippet for using Rig"
    )

    env_parser = subparsers.add_parser("env", help="Inspect the agent environment")
    env_subparsers = env_parser.add_subparsers(dest="env_command", required=True)
    env_subparsers.add_parser(
        "doctor", help="Diagnose the local Rig and agent harness environment"
    )
    env_subparsers.add_parser(
        "plan", help="Show a read-only plan for the desired harness environment"
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    store = RunStore(Path.cwd())

    try:
        if args.command == "init":
            result = store.init()
            if result.changed:
                print("Rig init complete.")
                for path in result.created:
                    print(f"Created: {path}")
                for path in result.updated:
                    print(f"Updated: {path}")
            else:
                print("Rig already up to date.")
            return 0

        if args.command == "run" and args.agent == "codex":
            return run_codex(args, store)

        if args.command == "runs":
            if args.runs_command == "list":
                return list_runs(store)
            if args.runs_command == "show":
                return show_run(store, args.run_id)

        if args.command == "agents" and args.agents_command == "snippet":
            return print_agents_snippet()

        if args.command == "env" and args.env_command == "doctor":
            return env_doctor(Path.cwd())
        if args.command == "env" and args.env_command == "plan":
            return env_plan(Path.cwd())

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

    if args.dry_run:
        context.stdout_path.write_text("", encoding="utf-8")
        context.stderr_path.write_text("", encoding="utf-8")
        context.result_path.write_text(
            "Dry run: command was not executed.\n", encoding="utf-8"
        )
        store.write_status(context, status="created", started_at=started_at)
        print(f"Run: {context.id}")
        print("Status: created")
        print(f"Command: {context.command_path.relative_to(context.cwd)}")
        print(f"Result: {context.result_path.relative_to(context.cwd)}")
        return 0

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
    if not runs:
        print("No runs found.")
        return 0
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
        if run_id == "latest":
            print("No runs found.", file=sys.stderr)
        else:
            print(f"Run not found or unreadable: {run_id}", file=sys.stderr)
        return 1

    run_dir = str(run.get("run_dir", ""))
    result_path = f"{run_dir}/result.md" if run_dir else "result.md"
    result = store.read_result(run)
    print(f"ID:        {run.get('id', '')}")
    print(f"Agent:     {run.get('agent', '')}")
    print(f"Status:    {run.get('status', '')}")
    print(f"Run dir:   {run_dir}")
    print(f"Result:    {result_path}")
    print()
    print("--- Result ---")
    print()
    if result:
        print(result, end="")
    else:
        print("(result.md is missing or empty)")
    return 0


def print_agents_snippet() -> int:
    print(AGENTS_SNIPPET)
    return 0


def env_doctor(cwd: Path) -> int:
    print(format_doctor_report(build_doctor_report(cwd)))
    return 0


def env_plan(cwd: Path) -> int:
    print(format_env_plan(build_doctor_report(cwd)))
    return 0


def format_started_at(value: str) -> str:
    if not value:
        return ""
    return value[:19].replace("T", " ")


def first_line(value: str) -> str:
    return value.strip().splitlines()[0]


AGENTS_SNIPPET = """## Rig

Prefer Rig MCP tools when available. If Rig MCP tools are not available, use the Rig CLI.

Use Rig for inspectable AI coding tasks. Rig stores each run under `.rig/runs/<run-id>/`.

Run a task:

```bash
rig run codex --task-file tasks/review.md
```

Inspect the result:

```bash
rig runs list
rig runs show latest
```

Rules:

- Do not assume Rig applies patches automatically.
- Inspect `result.md` after each run.
- Check `stderr.log` when a run fails.
- Prefer `--task-file` for long or structured tasks.
"""


if __name__ == "__main__":
    raise SystemExit(main())
