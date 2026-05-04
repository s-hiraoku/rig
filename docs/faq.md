---
title: FAQ
description: Frequently asked questions about Rig's scope and command model.
---

# FAQ

## What is Rig in one sentence?

A local harness that parent AI agents use to delegate coding work while keeping
plain-file run history and reviewable patches.

## Who types Rig commands?

Usually the parent AI agent. Humans still type commands for setup, debugging,
audit, and patch review.

## Why not call Codex directly?

Direct CLI calls work, but Rig adds a stable task file, captured stdout/stderr,
exit status, `result.md`, and optional `diff.patch` for isolated edits.

## Is Rig a sandbox?

No. The child agent runs locally with your credentials. Patch runs isolate file
edits in a Git worktree, but they do not sandbox the process.

## What happened to suggest/manual/pty/env manager commands?

They were removed before release. Rig now focuses on delegated agent execution,
history, and reviewable patches.

## How do I inspect a run?

```bash
rig history
rig history show latest
```

## How do I review and apply an AI-generated edit?

```bash
rig patch create codex --task "Make the requested change."
rig patch show latest
rig patch apply latest
```
