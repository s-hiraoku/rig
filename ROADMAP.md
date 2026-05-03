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

Current shape:

```bash
rig init
rig run <agent> --task "..."
rig list
rig show latest
rig run <agent> --worktree --task "..."
rig worktree show latest
rig worktree apply latest
rig history complete latest --result "..."
rig history fail latest --error "..."
rig env doctor
rig guide agents
```

## Phase 1: CLI and Run Artifacts

Goal: provide the smallest useful local harness.

Implemented:

- `rig init`
- `rig run codex --task "..."`
- `rig run codex --task-file task.md`
- `rig list`
- `rig show latest`
- `rig show <run-id>`
- grouped `rig history ...` forms for the same run-history operations
- file-backed run artifacts under `.rig/runs/<run-id>/`
- Codex execution through `codex exec`
- `.rig/config.yaml` support for `agents.codex.command` and `agents.codex.args`
- friendlier handling of empty, damaged, or incomplete run history
- `rig run codex --dry-run` command preview mode
- clearer failed-run inspection output

## Phase 1.5: Agent Environment Integration

Goal: make Rig easy for AI coding agents to discover and use before MCP exists,
without reimplementing package management for skills, hooks, prompts, or MCP
server configuration.

Implemented:

- `rig guide agents`
- `rig env doctor`
- `rig env plan`
- `rig env bootstrap`
- default `.rig/env.yaml` with configurable required files and optional agent
  asset managers

This prints an `AGENTS.md` snippet instead of editing user files automatically.
User repositories own their own agent instructions.

Possible additions:

- `rig guide agents --target codex`
- `rig guide agents --target claude`
- `rig guide agents --format markdown`
- documented examples for `AGENTS.md`, `CLAUDE.md`, and skill files
- `rig env manager status`

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

Potential `rig env doctor` checks:

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
    snippet_command: rig guide agents
```

`rig env doctor` should be diagnostic. If it suggests installing or updating
agent assets, it should print the external command instead of doing the install
itself.

## Phase 2: Worktree Support

Goal: isolate risky agent changes and make diffs reviewable before application.

Potential commands:

```bash
rig run codex --worktree --task "..."
rig worktree show latest
rig worktree apply latest
```

Concepts:

- create `.rig/worktrees/<run-id>/`
- run the agent inside the worktree
- capture the resulting diff
- let the user inspect before applying

Rig should still avoid automatic patch application by default.

Implemented:

- `rig run <agent> --worktree`
- `.rig/worktrees/<run-id>/`
- `.rig/runs/<run-id>/diff.patch`
- `rig worktree show latest`
- `rig worktree apply latest`

## Phase 3: Generic Execution Runners

Goal: support Codex, GitHub Copilot CLI, Gemini CLI, Claude CLI, and future
agent CLIs without hard-coding each vendor as a first-class adapter.

Rig should model execution style first and vendor presets second.

Runner types:

- `exec`: non-interactive command execution. This is the default and should
  cover tools with programmatic prompt flags such as Codex CLI, GitHub Copilot
  CLI `copilot -p`, and Gemini CLI prompt modes.
- `manual`: create and track a Run for human-driven, GUI-driven, or
  externally executed work. Rig creates artifacts; a human or external agent
  completes them later.
- `pty`: experimental interactive terminal runner for CLIs that require a TTY.
  It should be explicit opt-in, timeout-bound, transcript-backed, and never the
  default architecture.

Implemented:

- `runner: exec`
- `runner: manual`
- `runner: pty` with timeout-backed transcript capture
- `rig history complete` and `rig history fail` for manual run lifecycle management

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
  gemini:
    runner: exec
    command: gemini
    args:
      - --prompt
```

GitHub Copilot CLI and Gemini CLI should not require dedicated adapters unless
their stable non-interactive contracts need special handling. Risky permission
flags such as Copilot's broad tool approval options should remain explicit user
configuration, not Rig defaults.

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
