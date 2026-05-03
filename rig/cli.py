from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from rig.adapters.codex import iso_now
from rig.adapters.exec import AgentCommandNotFoundError
from rig.config import ConfigError
from rig.env_doctor import build_doctor_report, format_doctor_report, format_env_plan
from rig.orchestrator import RunOrchestrator, RunRequest
from rig.run_store import InitResult, RigNotInitializedError, RunStore
from rig.worktree import WorktreeError, apply_patch, prune_worktrees


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
    add_run_options(run_parser)

    list_parser = subparsers.add_parser("list", help="List recent runs")
    show_parser = subparsers.add_parser("show", help="Show a run")
    show_parser.add_argument("run_id", help="Run ID, or 'latest'")
    list_parser.add_argument("--json", action="store_true", help="Print JSON output")
    show_parser.add_argument("--json", action="store_true", help="Print JSON output")
    worktree_parser = subparsers.add_parser(
        "worktree", help="Manage isolated worktree run changes"
    )
    worktree_subparsers = worktree_parser.add_subparsers(
        dest="worktree_command", required=True
    )
    worktree_run_parser = worktree_subparsers.add_parser(
        "run", help="Run an agent in an isolated git worktree"
    )
    add_run_options(worktree_run_parser)
    worktree_show_parser = worktree_subparsers.add_parser(
        "show", help="Show changes captured from a worktree run"
    )
    worktree_show_parser.add_argument("run_id", help="Run ID, or 'latest'")
    worktree_apply_parser = worktree_subparsers.add_parser(
        "apply", help="Apply changes captured from a worktree run"
    )
    worktree_apply_parser.add_argument("run_id", help="Run ID, or 'latest'")
    worktree_subparsers.add_parser("prune", help="Remove Rig-created worktrees")

    history_parser = subparsers.add_parser("history", help="Inspect run history")
    history_subparsers = history_parser.add_subparsers(
        dest="history_command", required=True
    )
    history_list_parser = history_subparsers.add_parser("list", help="List recent runs")
    show_parser = history_subparsers.add_parser("show", help="Show a run")
    show_parser.add_argument("run_id", help="Run ID, or 'latest'")
    history_list_parser.add_argument(
        "--json", action="store_true", help="Print JSON output"
    )
    show_parser.add_argument("--json", action="store_true", help="Print JSON output")
    complete_parser = history_subparsers.add_parser(
        "complete", help="Complete a waiting manual run"
    )
    complete_parser.add_argument("run_id", help="Run ID, or 'latest'")
    complete_parser.add_argument("--result", help="Result text to write")
    complete_parser.add_argument("--result-file", help="Path to a result file")
    fail_parser = history_subparsers.add_parser(
        "fail", help="Fail a waiting manual run"
    )
    fail_parser.add_argument("run_id", help="Run ID, or 'latest'")
    fail_parser.add_argument("--error", help="Error text to write")
    fail_parser.add_argument("--error-file", help="Path to an error file")

    guide_parser = subparsers.add_parser(
        "guide", help="Generate setup guidance for humans and AI agents"
    )
    guide_subparsers = guide_parser.add_subparsers(dest="guide_command", required=True)
    guide_subparsers.add_parser(
        "agents", help="Generate an AGENTS.md snippet for using Rig"
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

    mcp_parser = subparsers.add_parser("mcp", help="Expose Rig as MCP tools")
    mcp_subparsers = mcp_parser.add_subparsers(dest="mcp_command", required=True)
    mcp_subparsers.add_parser("serve", help="Run the Rig MCP server over stdio")

    return parser


def add_run_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "agent",
        nargs="?",
        help="Configured agent name, such as codex. Defaults to default_agent.",
    )
    parser.add_argument("--task", help="Task text to pass to the agent")
    parser.add_argument("--task-file", help="Path to a file containing the task")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Create run artifacts and command metadata without executing the agent",
    )


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

        if args.command == "list":
            return list_runs(store, json_output=args.json)
        if args.command == "show":
            return show_run(store, args.run_id, json_output=args.json)
        if args.command == "worktree":
            if args.worktree_command == "run":
                return run_agent(args, store, worktree=True)
            if args.worktree_command == "show":
                return show_diff(store, args.run_id)
            if args.worktree_command == "apply":
                return apply_diff(store, args.run_id)
            if args.worktree_command == "prune":
                return prune_worktree_runs(store)

        if args.command == "history":
            if args.history_command == "list":
                return list_runs(store, json_output=args.json)
            if args.history_command == "show":
                return show_run(store, args.run_id, json_output=args.json)
            if args.history_command == "complete":
                return complete_run(args, store)
            if args.history_command == "fail":
                return fail_run(args, store)

        if args.command == "guide" and args.guide_command == "agents":
            return print_agents_snippet()

        if args.command == "env" and args.env_command == "doctor":
            return env_doctor(Path.cwd())
        if args.command == "env" and args.env_command == "plan":
            return env_plan(Path.cwd())
        if args.command == "env" and args.env_command == "bootstrap":
            return env_bootstrap(store)
        if args.command == "mcp" and args.mcp_command == "serve":
            from rig.mcp_server import serve_mcp

            serve_mcp()
            return 0

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


def run_agent(
    args: argparse.Namespace, store: RunStore, *, worktree: bool = False
) -> int:
    request = RunRequest(
        agent=args.agent,
        task=args.task,
        task_file=args.task_file,
        dry_run=args.dry_run,
        worktree=worktree,
    )
    try:
        outcome = RunOrchestrator(store).run(request)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    for line in outcome.lines:
        print(line)
    return outcome.exit_code


def list_runs(store: RunStore, *, json_output: bool = False) -> int:
    runs = store.list_runs()
    if json_output:
        print(json.dumps(runs, indent=2, ensure_ascii=False))
        return 0
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


def show_run(store: RunStore, run_id: str, *, json_output: bool = False) -> int:
    run = store.resolve_run(run_id)
    if run is None:
        if run_id == "latest":
            print("No runs found.", file=sys.stderr)
        else:
            print(f"Run not found or unreadable: {run_id}", file=sys.stderr)
        return 1

    if json_output:
        print(json.dumps(run, indent=2, ensure_ascii=False))
        return 0

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
    run = store.resolve_run(run_id)
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
    run = store.resolve_run(run_id)
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
    run = store.resolve_run(run_id)
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
    if not diff_path.read_text(encoding="utf-8").strip():
        print(f"No changes to apply: {diff_path_value}")
        return 0

    apply_result = apply_patch(store.cwd, diff_path)
    print(f"Applied: {diff_path_value}")
    if not apply_result.applied_to_index:
        if apply_result.index_error:
            print(f"Note: git apply --index failed: {apply_result.index_error}")
        print("Note: patch was applied to the working tree but not staged.")
    return 0


def prune_worktree_runs(store: RunStore) -> int:
    result = prune_worktrees(store.cwd, store.worktrees_dir)
    if not result.removed and not result.failed:
        print("No Rig worktrees found.")
        return 0
    for path in result.removed:
        print(f"Removed: {store.display_path(path)}")
    for path, error in result.failed:
        print(f"Failed: {store.display_path(path)}: {error}", file=sys.stderr)
    return 1 if result.failed else 0


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
    stripped = value.strip()
    return stripped.splitlines()[0] if stripped else ""


AGENTS_SNIPPET = """## Rig

Prefer Rig MCP tools when available. If Rig MCP tools are not available, use the Rig CLI.

Use Rig for inspectable AI coding tasks. Rig stores each run under `.rig/runs/<run-id>/`.

Run a task:

```bash
rig run codex --task-file tasks/review.md
```

Inspect the result:

```bash
rig list
rig show latest
```

Rules:

- Do not assume Rig applies patches automatically.
- Inspect `result.md` after each run.
- Check `stderr.log` when a run fails.
- Prefer `--task-file` for long or structured tasks.
"""


if __name__ == "__main__":
    raise SystemExit(main())
