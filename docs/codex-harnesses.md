---
title: Codex Harnesses
description: How Rig relates to the companion codex-harnesses repository for AGENTS templates, skills, hooks, policies, ledgers, and verification scripts.
---

# Codex Harnesses

Rig is the local runner: it delegates a task, records artifacts, and captures a
reviewable patch when requested. The companion
[`codex-harnesses`](https://github.com/s-hiraoku/codex-harnesses) repository is
the broader Codex project harness: AGENTS templates, reusable skills, example
hooks, policy files, task ledgers, and verification scripts.

Use them together when a project needs more than run history:

```bash
rig harness
```

That command prints the source repository, docs URL, copyable parts, and starter
copy commands without downloading or modifying anything.

## Boundary

Rig does not install or manage third-party agent assets. Keep those assets in
the project, in an external package manager, or in team-owned setup scripts.
Use `codex-harnesses` as the copyable source for:

- `templates/agents/` for project `AGENTS.md` starting points.
- `skills/` for reusable Codex workflows.
- `hooks/` for deterministic lifecycle guard examples.
- `policies/` for safety and permission examples.
- `ledger/` for long-running task state.
- `scripts/verify.sh` for one command that local development and CI can share.
- `examples/` for minimal, frontend, Next.js, and strict adoption shapes.

## Adoption Pattern

Start with a small copy, then adapt it:

```bash
git clone https://github.com/s-hiraoku/codex-harnesses.git
cp codex-harnesses/templates/agents/strict/AGENTS.md AGENTS.md
cp codex-harnesses/scripts/verify.sh scripts/verify.sh
cp -R codex-harnesses/ledger ledger
```

Then edit the copied files so they match the target project. Replace placeholder
verification commands with real local checks, keep only the skills and hooks
that match repeated work, and make CI call the same adapted `scripts/verify.sh`
when that script becomes the project standard.
