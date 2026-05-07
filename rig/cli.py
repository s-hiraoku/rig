from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from pathlib import Path

from rig.adapters.exec import AgentCommandNotFoundError
from rig.config import ConfigError
from rig.env_doctor import build_doctor_report, format_doctor_report
from rig.harnesses import (
    format_harness_guide,
    get_harness_guide,
    harness_guide_payload,
)
from rig.orchestrator import (
    RunOrchestrator,
    RunRequest,
    run_outcome_payload,
)
from rig.policy import agents_snippet
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
        help=(
            "Reset .rig/config.yaml and .rig/instructions/rig.md after backing "
            "them up"
        ),
    )
    init_parser.add_argument(
        "--reset",
        choices=["config", "instructions", "all"],
        help="Reset selected Rig-owned config after backing up existing files",
    )

    delegate_parser = subparsers.add_parser(
        "delegate", help="Delegate a task to a configured coding agent"
    )
    add_run_options(delegate_parser)

    patch_parser = subparsers.add_parser(
        "patch", help="Create, inspect, and apply isolated agent patches"
    )
    patch_subparsers = patch_parser.add_subparsers(
        dest="patch_command", required=True
    )
    patch_create_parser = patch_subparsers.add_parser(
        "create", help="Delegate a task in an isolated worktree and capture a patch"
    )
    add_run_options(patch_create_parser)
    patch_show_parser = patch_subparsers.add_parser(
        "show", help="Show a captured patch"
    )
    patch_show_parser.add_argument("run_id", help="Run ID, or 'latest'")
    patch_apply_parser = patch_subparsers.add_parser(
        "apply", help="Apply a captured patch"
    )
    patch_apply_parser.add_argument("run_id", help="Run ID, or 'latest'")
    patch_subparsers.add_parser("prune", help="Remove Rig-created patch worktrees")

    history_parser = subparsers.add_parser("history", help="List and inspect runs")
    history_parser.add_argument("--json", action="store_true", help="Print JSON output")
    history_subparsers = history_parser.add_subparsers(dest="history_command")
    history_show_parser = history_subparsers.add_parser(
        "show", help="Show one run's metadata and result"
    )
    history_show_parser.add_argument("run_id", help="Run ID, or 'latest'")
    history_show_parser.add_argument(
        "--json", action="store_true", help="Print JSON output"
    )

    doctor_parser = subparsers.add_parser(
        "doctor", help="Diagnose the local Rig setup"
    )
    doctor_parser.add_argument("--json", action="store_true", help="Print JSON output")

    harness_parser = subparsers.add_parser(
        "harness", help="Show companion Codex harness guidance"
    )
    harness_parser.add_argument(
        "--source",
        choices=["codex-harnesses"],
        default="codex-harnesses",
        help="Harness source to describe",
    )
    harness_parser.add_argument("--json", action="store_true", help="Print JSON output")

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
    parser.add_argument(
        "--task",
        help=(
            "Natural-language task text for the agent. Provide exactly one of "
            "--task or --task-file."
        ),
    )
    parser.add_argument(
        "--task-file",
        help=(
            "Path to a file containing the task. Provide exactly one of --task "
            "or --task-file."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Create run artifacts and command metadata without executing the agent",
    )
    parser.add_argument(
        "--timeout-seconds",
        type=positive_int,
        help="Override the configured agent timeout for this run",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON output")


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("must be an integer") from None
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be 1 or greater")
    return parsed


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

        if args.command == "delegate":
            return run_agent(args, store)

        if args.command == "history":
            if args.history_command == "show":
                return show_run(store, args.run_id, json_output=args.json)
            return list_runs(store, json_output=args.json)
        if args.command == "patch":
            if args.patch_command == "create":
                return run_agent(args, store, worktree=True)
            if args.patch_command == "show":
                return show_worktree_run(store, args.run_id)
            if args.patch_command == "apply":
                return apply_worktree_run(store, args.run_id)
            if args.patch_command == "prune":
                return prune_worktree_runs(store)

        if args.command == "doctor":
            return env_doctor(Path.cwd(), json_output=args.json)
        if args.command == "harness":
            return show_harness(args)
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
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        return 130

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
        timeout_seconds=args.timeout_seconds,
    )
    try:
        outcome = RunOrchestrator(store).run(request)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(run_outcome_payload(outcome), indent=2, ensure_ascii=False))
        return outcome.exit_code
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


def show_worktree_run(store: RunStore, run_id: str) -> int:
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

    diff_path = store.resolve_diff_path(run)
    if diff_path is None or not diff_path.is_file():
        print(f"Diff file is missing: {diff_path_value}", file=sys.stderr)
        return 1

    diff = diff_path.read_text(encoding="utf-8", errors="replace")
    print(f"ID:        {run.get('id', '')}")
    print(f"Agent:     {run.get('agent', '')}")
    print(f"Status:    {run.get('status', '')}")
    if run.get("exit_code") is not None:
        print(f"Exit code: {run.get('exit_code')}")
    print(f"Run dir:   {run.get('run_dir', '')}")
    print(f"Diff:      {diff_path_value}")
    print()
    print("--- Diff ---")
    print()
    if diff:
        print(diff, end="")
    else:
        print("(diff.patch is empty)")
    return 0


def apply_worktree_run(store: RunStore, run_id: str) -> int:
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

    diff_path = store.resolve_diff_path(run)
    if diff_path is None or not diff_path.is_file():
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


def env_doctor(cwd: Path, *, json_output: bool = False) -> int:
    report = build_doctor_report(cwd)
    if json_output:
        print(json.dumps(dataclasses.asdict(report), indent=2, ensure_ascii=False))
        return 0
    print(format_doctor_report(report))
    return 0


def show_harness(args: argparse.Namespace) -> int:
    guide = get_harness_guide(args.source)
    if args.json:
        print(json.dumps(harness_guide_payload(guide), indent=2, ensure_ascii=False))
    else:
        print(format_harness_guide(guide), end="")
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
        print("Rig already up to date. Run `rig doctor` to inspect the setup.")
    print()
    print("AGENTS.md and CLAUDE.md now reference .rig/instructions/rig.md.")
    print("Add this snippet to other parent agent instructions if needed:")
    print()
    print(agents_snippet(target="codex"), end="")


def format_started_at(value: str) -> str:
    if not value:
        return ""
    return value[:19].replace("T", " ")


if __name__ == "__main__":
    raise SystemExit(main())
