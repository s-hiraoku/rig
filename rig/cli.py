from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from pathlib import Path

from rig.adapters.codex import iso_now
from rig.adapters.exec import AgentCommandNotFoundError, ExecAdapter
from rig.adapters.manual import ManualAdapter
from rig.adapters.pty import PtyAdapter
from rig.config import ConfigError
from rig.env_doctor import build_doctor_report, format_doctor_report, format_env_plan
from rig.run_store import InitResult, RigNotInitializedError, RunStore
from rig.worktree import WorktreeError, apply_patch, capture_diff, create_worktree


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rig")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser(
        "init", help="Initialize Rig in the current repository"
    )
    init_parser.add_argument(
        "--force",
        action="store_true",
        help="Reset both .rig/config.yaml and .rig/env.yaml after backing them up",
    )
    init_parser.add_argument(
        "--reset",
        choices=["config", "env", "all"],
        help="Reset selected Rig-owned config after backing up existing files",
    )

    run_parser = subparsers.add_parser("run", help="Run an agent")
    run_parser.add_argument("agent", help="Configured agent name, such as codex")
    run_parser.add_argument("--task", help="Task text to pass to the agent")
    run_parser.add_argument("--task-file", help="Path to a file containing the task")
    run_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Create run artifacts and command metadata without executing the agent",
    )
    run_parser.add_argument(
        "--worktree",
        action="store_true",
        help="Run the agent in an isolated git worktree and capture diff.patch",
    )

    runs_parser = subparsers.add_parser("runs", help="Inspect run history")
    runs_subparsers = runs_parser.add_subparsers(dest="runs_command", required=True)
    runs_subparsers.add_parser("list", help="List recent runs")
    show_parser = runs_subparsers.add_parser("show", help="Show a run")
    show_parser.add_argument("run_id", help="Run ID, or 'latest'")
    complete_parser = runs_subparsers.add_parser(
        "complete", help="Complete a waiting manual run"
    )
    complete_parser.add_argument("run_id", help="Run ID, or 'latest'")
    complete_parser.add_argument("--result", help="Result text to write")
    complete_parser.add_argument("--result-file", help="Path to a result file")
    fail_parser = runs_subparsers.add_parser("fail", help="Fail a waiting manual run")
    fail_parser.add_argument("run_id", help="Run ID, or 'latest'")
    fail_parser.add_argument("--error", help="Error text to write")
    fail_parser.add_argument("--error-file", help="Path to an error file")

    diff_parser = subparsers.add_parser("diff", help="Show a captured run diff")
    diff_parser.add_argument("run_id", help="Run ID, or 'latest'")

    apply_parser = subparsers.add_parser("apply", help="Apply a captured run diff")
    apply_parser.add_argument("run_id", help="Run ID, or 'latest'")

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
    env_subparsers.add_parser(
        "bootstrap",
        help="Create missing Rig-owned environment files and print next steps",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    store = RunStore(Path.cwd())

    try:
        if args.command == "init":
            reset = "all" if args.force else args.reset
            result = store.init(reset=reset)
            print_init_result(result)
            return 0

        if args.command == "run":
            return run_agent(args, store)

        if args.command == "runs":
            if args.runs_command == "list":
                return list_runs(store)
            if args.runs_command == "show":
                return show_run(store, args.run_id)
            if args.runs_command == "complete":
                return complete_run(args, store)
            if args.runs_command == "fail":
                return fail_run(args, store)

        if args.command == "diff":
            return show_diff(store, args.run_id)
        if args.command == "apply":
            return apply_diff(store, args.run_id)

        if args.command == "agents" and args.agents_command == "snippet":
            return print_agents_snippet()

        if args.command == "env" and args.env_command == "doctor":
            return env_doctor(Path.cwd())
        if args.command == "env" and args.env_command == "plan":
            return env_plan(Path.cwd())
        if args.command == "env" and args.env_command == "bootstrap":
            return env_bootstrap(store)

    except RigNotInitializedError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except AgentCommandNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except ConfigError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except WorktreeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    parser.error("unsupported command")
    return 2


def run_agent(args: argparse.Namespace, store: RunStore) -> int:
    if bool(args.task) == bool(args.task_file):
        print("Provide exactly one of --task or --task-file.", file=sys.stderr)
        return 2

    task = args.task
    if args.task_file:
        task = Path(args.task_file).read_text(encoding="utf-8")

    agent_config = store.load_config().agent(args.agent)
    context = store.create_run(args.agent)
    if args.worktree:
        worktree_path = store.worktrees_dir / context.id
        create_worktree(store.cwd, worktree_path)
        context = replace(
            context,
            worktree_path=worktree_path,
            execution_cwd=worktree_path,
        )
    store.write_task(context, task)

    started_at = iso_now()
    if agent_config.runner == "manual":
        manual_adapter = ManualAdapter(args.agent, agent_config)
        store.write_command(
            context, manual_adapter.command_metadata(context, started_at)
        )
        context.stdout_path.write_text("", encoding="utf-8")
        context.stderr_path.write_text("", encoding="utf-8")
        context.result_path.write_text(
            manual_adapter.result_template(context), encoding="utf-8"
        )
        store.write_status(context, status="waiting", started_at=started_at)
        print(f"Run: {context.id}")
        print("Status: waiting")
        print(f"Task: {context.task_path.relative_to(context.cwd)}")
        print(f"Result: {context.result_path.relative_to(context.cwd)}")
        return 0

    command_adapter = (
        PtyAdapter(args.agent, agent_config)
        if agent_config.runner == "pty"
        else ExecAdapter(args.agent, agent_config)
    )
    store.write_command(context, command_adapter.command_metadata(context, started_at))

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
        result = command_adapter.run(context)
    except AgentCommandNotFoundError:
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
    if context.worktree_path is not None:
        context.diff_path.write_text(
            capture_diff(context.worktree_path),
            encoding="utf-8",
        )

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
    if context.worktree_path is not None:
        print(f"Diff: {context.diff_path.relative_to(context.cwd)}")
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
    stderr_path = f"{run_dir}/stderr.log" if run_dir else "stderr.log"
    diff_path = run.get("diff_path")
    result = store.read_result(run)
    stderr = store.read_artifact(run, "stderr.log")
    print(f"ID:        {run.get('id', '')}")
    print(f"Agent:     {run.get('agent', '')}")
    print(f"Status:    {run.get('status', '')}")
    if run.get("exit_code") is not None:
        print(f"Exit code: {run.get('exit_code')}")
    print(f"Run dir:   {run_dir}")
    print(f"Result:    {result_path}")
    print(f"Stderr:    {stderr_path}")
    if isinstance(diff_path, str) and diff_path:
        print(f"Diff:      {diff_path}")
    print()
    print("--- Result ---")
    print()
    if result:
        print(result, end="")
    else:
        print("(result.md is missing or empty)")

    if str(run.get("status", "")) == "failed":
        print()
        print("--- Error ---")
        print()
        if stderr.strip():
            print(stderr, end="" if stderr.endswith("\n") else "\n")
        else:
            print("(stderr.log is missing or empty)")
    return 0


def complete_run(args: argparse.Namespace, store: RunStore) -> int:
    if bool(args.result) == bool(args.result_file):
        print("Provide exactly one of --result or --result-file.", file=sys.stderr)
        return 2

    run = waiting_run(args.run_id, store, action="completed")
    if run is None:
        return 1

    result = args.result
    if args.result_file:
        result = Path(args.result_file).read_text(encoding="utf-8")
    store.write_run_artifact(run, "result.md", result.rstrip() + "\n")
    store.write_run_status(
        run,
        status="succeeded",
        finished_at=iso_now(),
        exit_code=0,
    )

    print(f"Run: {run.get('id', '')}")
    print("Status: succeeded")
    print(f"Result: {run.get('run_dir', '')}/result.md")
    return 0


def fail_run(args: argparse.Namespace, store: RunStore) -> int:
    if bool(args.error) == bool(args.error_file):
        print("Provide exactly one of --error or --error-file.", file=sys.stderr)
        return 2

    run = waiting_run(args.run_id, store, action="failed")
    if run is None:
        return 1

    error = args.error
    if args.error_file:
        error = Path(args.error_file).read_text(encoding="utf-8")
    store.write_run_artifact(run, "stderr.log", error.rstrip() + "\n")
    store.write_run_status(
        run,
        status="failed",
        finished_at=iso_now(),
        exit_code=1,
    )

    print(f"Run: {run.get('id', '')}")
    print("Status: failed")
    print(f"Error: {first_line(error)}")
    print(f"Stderr: {run.get('run_dir', '')}/stderr.log")
    return 1


def waiting_run(
    run_id: str, store: RunStore, *, action: str
) -> dict[str, object] | None:
    run = store.latest_run() if run_id == "latest" else store.find_run(run_id)
    if run is None:
        if run_id == "latest":
            print("No runs found.", file=sys.stderr)
        else:
            print(f"Run not found or unreadable: {run_id}", file=sys.stderr)
        return None
    if run.get("status") != "waiting":
        print(
            f"Run is not waiting and cannot be {action}: {run.get('id', run_id)}",
            file=sys.stderr,
        )
        return None
    return run


def show_diff(store: RunStore, run_id: str) -> int:
    run = store.latest_run() if run_id == "latest" else store.find_run(run_id)
    if run is None:
        if run_id == "latest":
            print("No runs found.", file=sys.stderr)
        else:
            print(f"Run not found or unreadable: {run_id}", file=sys.stderr)
        return 1

    diff_path_value = run.get("diff_path")
    if not isinstance(diff_path_value, str) or not diff_path_value:
        print(f"Run has no captured diff: {run.get('id', run_id)}", file=sys.stderr)
        return 1

    diff_path = store.cwd / diff_path_value
    if not diff_path.is_file():
        print(f"Diff file is missing: {diff_path_value}", file=sys.stderr)
        return 1

    diff = diff_path.read_text(encoding="utf-8", errors="replace")
    if diff:
        print(diff, end="")
    else:
        print("(diff.patch is empty)")
    return 0


def apply_diff(store: RunStore, run_id: str) -> int:
    run = store.latest_run() if run_id == "latest" else store.find_run(run_id)
    if run is None:
        if run_id == "latest":
            print("No runs found.", file=sys.stderr)
        else:
            print(f"Run not found or unreadable: {run_id}", file=sys.stderr)
        return 1

    diff_path_value = run.get("diff_path")
    if not isinstance(diff_path_value, str) or not diff_path_value:
        print(f"Run has no captured diff: {run.get('id', run_id)}", file=sys.stderr)
        return 1

    diff_path = store.cwd / diff_path_value
    apply_patch(store.cwd, diff_path)
    print(f"Applied: {diff_path_value}")
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


def env_bootstrap(store: RunStore) -> int:
    print("Rig environment bootstrap")
    print()
    result = store.init()
    print_init_result(result)
    print()
    print("Next steps")
    report = build_doctor_report(store.cwd)
    suggestions = [
        suggestion
        for suggestion in report.suggestions
        if suggestion != "Run: rig init"
    ]
    if suggestions:
        for suggestion in suggestions:
            print(f"- {suggestion}")
    else:
        print("- No action needed.")
    print()
    print("Rig did not install external tools or third-party agent assets.")
    return 0


def print_init_result(result: InitResult) -> None:
    if result.changed:
        print("Rig init complete.")
        for path in result.created:
            print(f"Created: {path}")
        for path in result.updated:
            print(f"Updated: {path}")
        for path in result.backups:
            print(f"Backup: {path}")
    else:
        print("Rig already up to date.")


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
