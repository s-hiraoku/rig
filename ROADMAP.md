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
- friendlier handling of empty, damaged, or incomplete run history
- `rig run codex --dry-run` command preview mode

Still in scope for Phase 1 polish:

- clearer failed-run inspection output

## Phase 1.5: Agent Environment Integration

Goal: make Rig easy for AI coding agents to discover and use before MCP exists,
without reimplementing package management for skills, hooks, prompts, or MCP
server configuration.

Implemented:

- `rig agents snippet`
- `rig env doctor`

This prints an `AGENTS.md` snippet instead of editing user files automatically.
User repositories own their own agent instructions.

Possible additions:

- `rig agents snippet --target codex`
- `rig agents snippet --target claude`
- `rig agents snippet --format markdown`
- documented examples for `AGENTS.md`, `CLAUDE.md`, and skill files
- `rig env plan`
- `rig env bootstrap`
- `rig env apm status`

Skills and instruction files are not a replacement for MCP. They tell agents
how to use Rig and what policies to follow. MCP gives agents structured tools.

Rig should not become a package manager for agent assets. Existing package
managers should own fetching, locking, auditing, and deploying skills, hooks,
prompts, and MCP server configuration.

Recommended external managers:

- APM for manifest-driven, reproducible agent environment setup with lockfiles
  and policy support.
- `gh skill` / `gh skills` for GitHub-hosted agent skill search, preview,
  install, update, and publish workflows.
- Vercel `skills` / skills.sh for discovering and installing open Agent Skills
  packages.

Rig's role is integration:

- detect whether relevant managers are installed
- detect whether files such as `apm.yml`, `apm.lock.yaml`, or agent instruction
  files exist
- point users to the right external command
- keep Rig-specific execution policy and run artifacts under `.rig/`
- avoid writing or updating third-party agent asset files unless a future
  command explicitly asks for it

Potential `rig env doctor` checks:

- Rig initialized
- Git repository present
- Codex command available
- APM installed
- `apm.yml` and `apm.lock.yaml` present when APM is used
- `AGENTS.md` or equivalent instruction file present
- Rig snippet appears to be included

## Harness Environment Bootstrap

Many users have a preferred AI development harness: CLIs, package managers,
agent instructions, skill registries, MCP server definitions, and local policy.
Recreating that setup in a fresh repository or machine is tedious. Rig can help
without owning the whole installation surface.

Rig should act as a meta-harness manager:

- define the expected harness profile
- inspect the current environment
- report what is missing
- suggest the external command that should fix it
- create Rig-owned files such as `.rig/config.yaml`
- avoid silently installing global tools or third-party agent assets

Potential commands:

```bash
rig env doctor
rig env plan
rig env bootstrap
```

Suggested responsibilities:

- `rig env doctor`: read-only diagnostics for the current repository and
  machine.
- `rig env plan`: show the desired harness setup and the actions needed to reach
  it.
- `rig env bootstrap`: initialize Rig-owned files and print commands for
  external managers. A future `--apply` mode may run safe, explicit actions.

Potential `.rig/env.yaml` shape:

```yaml
version: 1

profile: personal

tools:
  codex:
    required: true
    check: codex --version
    install_hint: Install Codex CLI from OpenAI docs.
  gh:
    required: true
    check: gh --version
    install_hint: brew install gh
  apm:
    required: false
    check: apm --version
    install_hint: Install APM from the upstream installer.

agent_assets:
  managers:
    - apm
    - gh-skill
    - vercel-skills

instructions:
  agents_md:
    recommended: true
    snippet_command: rig agents snippet
```

`rig env doctor` should be diagnostic. If it suggests installing or updating
agent assets, it should print the external command instead of doing the install
itself.

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
