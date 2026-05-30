# Roadmap

Rig should grow from a small local CLI into a structured harness that AI coding
agents can use directly.

The main abstraction stays the same across phases:

```txt
Task -> Run -> AgentAdapter -> Artifacts
```

Rig should avoid becoming an agent-to-agent protocol, a PTY automation tool, or
a workflow engine.

## Design Bias: Flexibility First

The AI tooling ecosystem changes quickly. Rig should avoid hard-coding today's
favorite package managers, agent names, file formats, or deployment paths as
permanent assumptions.

Design rules:

- prefer declarative local configuration over baked-in vendor behavior
- detect and report capabilities instead of forcing one provider
- keep defaults useful but easy to replace
- make external tool integration optional and adapter-like
- let users declare project-specific harness requirements in `.rig/env.yaml`
- avoid silently writing files owned by other agent tools
- preserve plain local files so users can inspect and edit everything

Rig may ship defaults, but defaults should be examples, not lock-in.

## Command Design

Rig commands should read well in a Quick Start before they are optimized for
internal implementation categories.

Design rules:

- keep common first-run operations at the top level
- put feature-specific operations under the feature name
- do not expose a command at the top level if it only works for one feature
- prefer command names with a clear object, such as `worktree apply`
- keep grouped commands only when the group explains the scope

MVP command shape:

```bash
rig init
rig delegate <agent> --task "..."
rig history
rig history show latest
rig patch create <agent> --task "..."
rig patch show latest
rig patch apply latest
rig doctor
rig mcp serve
```

## Phase 1: CLI and Run Artifacts

Goal: provide the smallest useful local harness.

Implemented:

- `rig init`
- `rig delegate codex --task "..."`
- `rig delegate codex --task-file task.md`
- `rig history`
- `rig history show latest`
- `rig history show <run-id>`
- `rig history --json`
- `rig history show latest --json`
- `rig delegate codex --json`
- file-backed run artifacts under `.rig/runs/<run-id>/`
- Codex execution through `codex exec`
- `.rig/config.yaml` support for `agents.codex.command` and `agents.codex.args`
- `default_agent` support when `rig delegate` omits the agent name
- friendlier handling of empty, damaged, or incomplete run history
- `rig delegate codex --dry-run` command preview mode
- clearer failed-run inspection output
- task files are preserved without adding Rig's `# Task` wrapper

## Phase 1.5: Agent Environment Integration

Goal: make Rig easy for AI coding agents to discover and use before MCP exists,
without reimplementing package management for skills, hooks, prompts, or MCP
server configuration.

MVP implemented:

- `.rig/instructions/rig.md` as the Rig-owned instruction file referenced by
  generated `AGENTS.md` and `CLAUDE.md` Rig blocks
- `rig doctor`
- configured agent command checks are derived from `.rig/config.yaml`
- documented examples for `AGENTS.md`, `CLAUDE.md`, and skill files

`rig init` creates or updates small managed Rig blocks in `AGENTS.md` and
`CLAUDE.md`. Those blocks reference `.rig/instructions/rig.md`, so user
repositories still own the rest of their agent instructions.

Skills and instruction files are not a replacement for MCP. They tell agents
how to use Rig and what policies to follow. MCP gives agents structured tools.

Rig should not become a package manager for agent assets. Existing package
managers should own fetching, locking, auditing, and deploying skills, hooks,
prompts, and MCP server configuration.

Detected external managers:

- APM for manifest-driven, reproducible agent environment setup with lockfiles.
- `gh skill` / `gh skills` for GitHub-hosted agent skill search, preview,
  install, update, and publish workflows.
- Vercel `skills` / skills.sh for discovering and installing open Agent Skills
  packages.
- Manual or team-specific conventions for repositories that do not want a
  package manager.

Rig's role is integration:

- detect whether relevant managers are installed
- detect whether files declared in `.rig/env.yaml` exist
- point users to the right external command
- keep Rig-specific execution policy and run artifacts under `.rig/`
- avoid writing or updating third-party agent asset files unless a future
  command explicitly asks for it

Potential harness-environment diagnostics:

- Rig initialized
- Git repository present
- Codex command available
- APM installed
- required files declared in `.rig/env.yaml` are present
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
- read project-specific required files from `.rig/env.yaml`
- avoid silently installing global tools or third-party agent assets

Future harness-environment command concepts:

- doctor mode: read-only diagnostics for the current repository and machine
- plan mode: show the desired harness setup and missing actions
- bootstrap mode: initialize Rig-owned files and print external manager commands

Suggested responsibilities:

- Doctor mode should support `--json` for structured CI output.
- Plan mode should show the desired harness setup and the actions needed to
  reach it.
- Bootstrap mode should initialize Rig-owned files and print commands for
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
  agent_asset_manager:
    required: false
    options:
      - apm
      - gh-skill
      - vercel-skills
      - manual

agent_asset_managers:
  - id: apm
    label: APM
    command: apm
    required_files:
      - path: apm.yml
        label: APM manifest
        hint: "Create apm.yml or remove this manager from .rig/env.yaml."
  - id: gh-skills
    label: GitHub skills manager
    command: gh
    args:
      - skills
      - --help
  - id: vercel-skills
    label: Vercel skills manager
    command: npx

required_files:
  - AGENTS.md
  - path: docs/agent-harness.md
    label: Agent harness docs
    hint: "Create docs/agent-harness.md with team setup notes."
  - path: docs/harness.md
    label: Harness docs
    hint: "Create docs/harness.md with team setup notes."

instructions:
  agents_md:
    recommended: true
```

Harness diagnostics should be read-only. If they suggest installing or updating
agent assets, they should print the external command instead of doing the
install itself.

## Phase 2: Patch Runs

Goal: isolate risky agent changes and make diffs reviewable before application.

MVP commands:

```bash
rig patch create codex --task "..."
rig patch show latest
rig patch apply latest
```

Concepts:

- create `.rig/worktrees/<run-id>/`
- run the agent inside the worktree
- capture the resulting diff
- let the user inspect before applying

Rig should still avoid automatic patch application by default.

Implemented:

- `rig patch create <agent>`
- `.rig/worktrees/<run-id>/`
- `.rig/runs/<run-id>/diff.patch`
- `rig patch show latest`
- `rig patch apply latest`
- `rig patch prune`

## Phase 3: Generic Execution Runners

Goal: support Codex, GitHub Copilot CLI, Antigravity CLI, Claude CLI, and future
agent CLIs without hard-coding each vendor as a first-class adapter.

Rig should model execution style first and vendor presets second.

Runner types:

- `exec`: non-interactive command execution. This is the default and should
  cover tools with programmatic prompt flags such as Codex CLI, GitHub Copilot
  CLI `copilot -p`, and Antigravity CLI prompt modes.
- `manual`: create and track a Run for human-driven, GUI-driven, or
  externally executed work. Rig creates artifacts; a human or external agent
  completes them later.
- `pty`: experimental interactive terminal runner for CLIs that require a TTY.
  It should be explicit opt-in, timeout-bound, transcript-backed, and never the
  default architecture.

Future:

- `runner: manual`
- `runner: pty` with timeout-backed transcript capture
- explicit lifecycle actions for completing or failing manual runs
- `rig history complete` and `rig history fail` remain available as compatibility forms
- runner registry and `RunOrchestrator` keep execution setup reusable outside CLI
- `timeout_seconds` applies to exec and pty runners
- `prompt_template` supports project-specific prompt formatting

Vendor tools should usually be presets over runner types:

```yaml
agents:
  codex:
    runner: exec
    command: codex
    args:
      - exec
  copilot:
    runner: exec
    command: copilot
    args:
      - -p
  antigravity:
    runner: exec
    command: agy
    args:
      - -p
      - --add-dir
      - .
```

GitHub Copilot CLI and Antigravity CLI should not require dedicated adapters unless
their stable non-interactive contracts need special handling. Risky permission
flags such as Copilot's broad tool approval options should remain explicit user
configuration, not Rig defaults.

## Phase 4: Optional MCP Adapter

Goal: expose Rig's CLI-first harness as structured tools for MCP-native or
shell-restricted agents.

Implemented:

- `rig_delegate`
- `rig_patch_create`
- `rig_history`
- `rig_history_show`
- `rig_list_agents`
- `rig_patch_show`
- `rig_patch_apply`
- `rig mcp serve` stdio server entrypoint
- `rig_policy` prompt and `rig://policy` / `rig://agents-md` resources
- `RIG_MCP_ROOT` bounds accepted `cwd` values
- `RIG_MCP_ALLOW_APPLY=1` gates MCP patch application

Why MCP:

- Shell-restricted agents can use Rig without direct shell access.
- MCP-native clients can call structured tools instead of shell commands.
- Tool inputs and outputs can use schemas.
- Agents do not need to parse CLI text to discover run IDs or statuses.
- MCP tools can return stable JSON-like data while Rig keeps the CLI as the
  primary interface for shell-capable agents, humans, and scripts.

MCP safety defaults:

- `cwd` is restricted to the server launch directory unless `RIG_MCP_ROOT` is
  set.
- `task_file` paths must stay inside the selected project.
- `rig_patch_apply` is disabled unless `RIG_MCP_ALLOW_APPLY=1` is set.

Skills and `AGENTS.md` remain the primary way to tell shell-capable agents how
to use Rig. They should explain when to use Rig, which policies to follow, and
how to inspect artifacts. MCP is optional:

```txt
Prefer the Rig CLI when shell access is available.
Use Rig MCP tools when the parent agent is MCP-native or shell-restricted.
```

## Phase 5: Suggest

Goal: help users decide how to run an agent task.

Future:

- `rig suggest "..."`
- `rig suggest --task-file task.md`
- `rig suggest "..." --json`

Inputs:

- current git diff size
- changed files
- test presence
- directory spread
- configured default agent
- task length and risk-oriented wording
- whether worktree isolation is recommended

This should remain advisory. Rig should not become a workflow engine.
