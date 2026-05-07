---
title: Agent Harness
description: MCP, skills, and hooks recommended for developing Rig itself without turning Rig into an agent asset package manager.
---

# Agent Harness

This page describes the thin AI-agent harness used to build Rig itself. The
goal is consistency for contributors and parent agents, not another package
manager.

## Required

- `AGENTS.md` at the repository root. It tells parent agents how to work on Rig,
  which verification commands to run, and which boundaries not to cross.
- This page (`docs/agent-harness.md`). It is declared in `.rig/env.yaml` so
  repository-specific harness guidance has a durable home.
- Rig's own MCP adapter remains part of the product surface: `rig mcp serve`,
  `rig_delegate`, `rig_patch_create`, `rig_history`, `rig_history_show`,
  `rig_patch_show`, `rig_patch_apply`, and `rig_list_agents`.
- Existing CI remains the final gate for normal changes.

## Recommended

- The project-local `rig-developer` skill in `.agents/skills/rig-developer/`.
  It is intentionally small and covers Rig's design boundaries, artifact
  contract, MCP safety model, and verification commands.
- GitHub app or GitHub MCP access for PR review, CI triage, and review feedback.
  It is useful for repository operations but not required for normal local
  implementation.
- Optional local hooks that run:

```bash
uv run ruff check .
uv run mypy rig tests
uv run pytest -q
```

Hooks should stay optional. Contributors may prefer to run the commands
directly, and CI is the authoritative gate.
- The companion [`codex-harnesses`](codex-harnesses.md) repository when a target
  project needs AGENTS templates, reusable skills, hooks, policies, ledgers, or
  verification scripts beyond Rig's delegated-run model.

## Not Needed By Default

- Filesystem or shell MCP servers. Local development already has direct file and
  shell access.
- Separate Codex, Claude, Gemini, or Copilot skills. Vendor differences belong
  in `.rig/config.yaml` examples and documentation unless a stable CLI contract
  needs code support.
- Automatic installation of skills, hooks, prompts, ledgers, policies, or MCP
  client config. Rig can point to companion harness sources with `rig harness`,
  but external managers or team conventions own installation.

## Test Policy

Normal tests should be deterministic and use fake commands. Real agent E2E
checks are opt-in only because they depend on installed CLIs, credentials,
trusted repositories, and provider behavior outside Rig's control.

There is no repo-supported real-agent E2E command today. Add and document the
explicit script, environment variable, or CI job in the same change that
introduces those checks.
