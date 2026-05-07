---
name: develop-with-rig
description: Use when a user wants to use Rig to make software development more efficient through delegated analysis, focused reviews, isolated patch runs, artifact inspection, subagent coordination, parallel task decomposition, or deciding when to delegate work versus editing directly.
---

# Develop With Rig

Use this skill when Rig is available in a project and the user wants to develop
more efficiently with inspectable delegated work. Optimize for throughput while
preserving reviewability: delegate analysis freely, isolate risky edits, inspect
artifacts, and integrate only the changes that survive review.

## Operating Model

- For small, obvious edits, work directly and keep the change scoped.
- For unclear requirements, risky edits, broad codebase questions, or independent
  review, use Rig before committing to an implementation path.
- For uncertain or risky delegated work, choose explicitly between direct work,
  `rig delegate` for read-only analysis, and `rig patch create` for isolated
  edits.
- Use subagents aggressively when the host environment supports them and the
  user has allowed subagent work. Give each subagent a bounded task and a clear
  output contract.
- Prefer Rig for work that should be inspectable later. Rig artifacts make
  delegated reasoning, stdout, stderr, status, and patches auditable.

## Delegation Patterns

Use `rig delegate` for work that should not edit the main tree:

```bash
rig delegate <agent> --task "Inspect the failing tests and identify the likely root cause. Do not edit files."
rig delegate <agent> --task-file task.md
rig delegate <agent> --task "Review this API design for edge cases and missing tests." --json
```

Good delegate tasks:

- Explore unfamiliar code paths and summarize the implementation map.
- Review a proposed plan, patch, or failing test output.
- Compare two approaches and list risks.
- Ask for test ideas before editing shared behavior.
- Reproduce a failure with deterministic local commands.

Read the result before acting:

```bash
rig history show latest
```

## Isolated Patch Runs

Use `rig patch create` when the delegated agent may edit files:

```bash
rig patch create <agent> --task "Implement the parser change and add focused tests."
rig patch show latest
rig patch apply latest
```

Patch-run rules:

- Use patches for non-trivial edits, generated changes, unfamiliar modules, or
  work where the child agent may overreach.
- Keep each patch task scoped to a coherent file set or feature slice.
- Inspect `diff.patch`, `result.md`, `stderr.log`, and `status.json` before
  applying.
- Apply only reviewed patches. If a patch is mostly right but too broad, copy
  the useful idea and implement locally instead of applying it wholesale.
- After applying, run the relevant tests in the main working tree.

## Parallel Execution

When the task is large and separable, split it into independent Rig runs instead
of serially exploring everything yourself.

Parallelize read-only `delegate` runs by question:

```bash
rig delegate <agent> --task "Map the CLI command flow for patch creation. Do not edit files."
rig delegate <agent> --task "Review MCP safety checks and list bypass risks. Do not edit files."
rig delegate <agent> --task "Find tests that cover run artifact contracts. Do not edit files."
```

Parallelize `patch create` runs only when write scopes are disjoint:

```bash
rig patch create <agent> --task "Update documentation examples only."
rig patch create <agent> --task "Add config parsing tests only."
rig patch create <agent> --task "Prototype CLI output changes only."
```

Parallel execution rules:

- Start independent read-only delegates early, then continue local work while
  they run.
- Use multiple patch runs for alternative implementations or disjoint slices,
  then apply at most the best reviewed diffs.
- Do not run competing patch tasks against the same files unless the goal is to
  compare alternatives and discard all but one.
- Label task prompts with ownership: files, modules, or behavior each run owns.
- Inspect each run by ID rather than relying only on `latest` when multiple
  runs are active or recently completed.

## Task Decomposition

Split large work into these lanes:

- Discovery: code map, existing patterns, constraints, hidden risks.
- Design review: proposed approach, edge cases, compatibility, migration.
- Implementation: one bounded behavior or file set per patch run.
- Tests: missing coverage, deterministic failure reproduction, focused test
  additions.
- Final review: diff audit, artifact contract check, docs consistency.

Use direct local work for the critical path when waiting would block progress.
Use delegated work for side questions, independent reviews, and patchable slices
that can run while local work continues.

## Artifact Review

Use artifacts as the integration checkpoint:

- `status.json`: confirm whether the run succeeded, failed, timed out, or was
  aborted.
- `result.md`: read the child agent's final answer or implementation summary.
- `stdout.log`: inspect full output when `result.md` looks incomplete.
- `stderr.log`: inspect failures, warnings, command errors, and timeouts.
- `command.json`: confirm which command, cwd, prompt, and timeout were used.
- `diff.patch`: review file edits from patch runs before applying.

## Command Preference

- In the Rig repository checkout, prefer `uv run rig ...`.
- In ordinary projects with Rig installed, use `rig ...`.
- If Rig is not initialized, say so and run `rig init` only when setup is part
  of the user's request. Otherwise, proceed directly for small work.
- Use `rig harness` when a project needs broader Codex harness assets from
  `codex-harnesses`: AGENTS templates, reusable skills, hooks, policies,
  ledgers, or verification scripts.
- When multiple runs exist, prefer explicit run IDs:

```bash
rig history
rig history show <run-id>
rig patch show <run-id>
```

Before summarizing a Rig result, inspect the matching artifacts. Before applying
a patch, inspect the matching diff.

## Safety

- Do not assume delegated changes are correct just because a child agent
  produced them.
- Treat `.rig/runs/<run-id>/` artifacts as the source of truth for what
  happened.
- Preserve the review step between `rig patch create` and `rig patch apply`.
- Do not use real networked agents, credentials, or destructive operations unless
  the user explicitly asked for that level of execution.
- Never summarize a child run as successful without checking `status.json` or
  the CLI output for status.
- If a delegated run fails, inspect `stderr.log` and decide whether to retry
  with a narrower task, handle the issue locally, or ask the user for direction.
