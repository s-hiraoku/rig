# Roadmap

Rig should grow from a small local CLI into a structured harness that AI coding
agents can use directly.

The main abstraction stays the same across phases:

```txt
Task -> Run -> AgentAdapter -> Artifacts
```

Rig should avoid becoming an agent-to-agent protocol, a PTY automation tool, or
a workflow engine.

## Phase 1: CLI and Run Artifacts

Goal: provide the smallest useful local harness.

Implemented:

- `rig init`
- `rig run codex --task "..."`
- `rig run codex --task-file task.md`
- `rig runs list`
- `rig runs show latest`
- `rig runs show <run-id>`
- file-backed run artifacts under `.rig/runs/<run-id>/`
- Codex execution through `codex exec`
- `.rig/config.yaml` support for `agents.codex.command` and `agents.codex.args`

Still in scope for Phase 1 polish:

- friendlier handling of damaged or incomplete run directories
- clearer failed-run inspection output
- optional dry-run or command preview mode

## Phase 1.5: Agent Adoption Layer

Goal: make Rig easy for AI coding agents to discover and use before MCP exists.

Implemented:

- `rig agents snippet`

This prints an `AGENTS.md` snippet instead of editing user files automatically.
User repositories own their own agent instructions.

Possible additions:

- `rig agents snippet --target codex`
- `rig agents snippet --target claude`
- `rig agents snippet --format markdown`
- documented examples for `AGENTS.md`, `CLAUDE.md`, and skill files

Skills and instruction files are not a replacement for MCP. They tell agents
how to use Rig and what policies to follow. MCP gives agents structured tools.

## Phase 2: Worktree Support

Goal: isolate risky agent changes and make diffs reviewable before application.

Potential commands:

```bash
rig run codex --worktree --task "..."
rig diff latest
rig apply latest
```

Concepts:

- create `.rig/worktrees/<run-id>/`
- run the agent inside the worktree
- capture the resulting diff
- let the user inspect before applying

Rig should still avoid automatic patch application by default.

## Phase 3: More Adapters

Goal: support more execution backends behind the same Run model.

Potential adapters:

- `ClaudeAdapter`
- `GeminiAdapter`
- `CustomCommandAdapter`
- `ManualAdapter`
- `PtyAdapter`

PTY support should remain experimental and should not become the default
architecture.

## Phase 4: MCP Server

Goal: expose Rig as structured tools for MCP-capable agents.

Potential tools:

- `rig_run`
- `rig_list_runs`
- `rig_get_run`
- `rig_get_result`
- `rig_get_diff`
- `rig_apply_patch`

Why MCP:

- Agents can call structured tools instead of shell commands.
- Tool inputs and outputs can use schemas.
- Agents do not need to parse CLI text to discover run IDs or statuses.
- MCP tools can return stable JSON-like data while Rig keeps the CLI for humans
  and fallback automation.

Skills and `AGENTS.md` should remain useful after MCP exists. They should
explain when to use Rig, which policies to follow, and how to inspect artifacts.
The preferred mechanism can shift from CLI to MCP:

```txt
Prefer Rig MCP tools when available.
If MCP tools are not available, use the Rig CLI.
```

## Phase 5: Suggest

Goal: help users decide how to run an agent task.

Potential command:

```bash
rig suggest "..."
```

Possible inputs:

- current git diff size
- changed files
- test presence
- directory spread
- likely best adapter
- whether worktree isolation is recommended

This should remain advisory. Rig should not become a workflow engine.

