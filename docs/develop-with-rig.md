---
title: Develop With Rig Skill
description: Install the optional develop-with-rig agent skill for parent agents that should use Rig aggressively for delegated analysis, isolated patch runs, and parallel task decomposition.
---

# Develop With Rig Skill

`develop-with-rig` is an optional user-facing agent skill shipped from this
repository under `skills/develop-with-rig/`. It teaches a parent agent how to
use Rig efficiently: delegate read-only analysis, isolate risky edits with patch
runs, inspect artifacts before summarizing, and split large tasks into parallel
work where the scopes are independent.

This skill is not part of the project-local `.agents/skills/` harness used to
develop Rig itself. Install it into the agent environment where you want parent
agents to use Rig on ordinary projects.

## Install With Codex

Use Codex's `skill-installer` with the GitHub directory URL:

```text
$skill-installer install https://github.com/s-hiraoku/rig/tree/main/skills/develop-with-rig
```

Restart Codex after installing so the new skill is discovered.

When testing from a branch or fork, replace `main` with the branch name or use
the matching GitHub directory URL.

## Install With GitHub CLI

GitHub CLI 2.90.0 and newer includes the preview `gh skill` command. Preview
the skill first, then install it for Codex:

```bash
gh skill preview s-hiraoku/rig skills/develop-with-rig
gh skill install s-hiraoku/rig skills/develop-with-rig --agent codex --scope user
```

Use `--scope project` instead when you want the skill installed into the current
repository's shared project skill directory:

```bash
gh skill install s-hiraoku/rig skills/develop-with-rig --agent codex --scope project
```

The `gh skills add` alias also works:

```bash
gh skills add s-hiraoku/rig skills/develop-with-rig --agent codex --scope user
```

To pin a specific Rig release or commit, add `--pin`:

```bash
gh skill install s-hiraoku/rig skills/develop-with-rig --agent codex --scope user --pin <tag-or-sha>
```

## Install With APM

For a one-off install with Agent Package Manager:

```bash
apm install s-hiraoku/rig/skills/develop-with-rig
```

For reproducible project setup, add the skill to `apm.yml`:

```yaml
name: your-project
version: 1.0.0

dependencies:
  apm:
    - s-hiraoku/rig/skills/develop-with-rig
```

Then install the declared agent assets:

```bash
apm install
```

APM supports version pinning in dependency strings. Once you have a Rig release
tag or commit you want to standardize on, pin the dependency in `apm.yml`:

```yaml
dependencies:
  apm:
    - s-hiraoku/rig/skills/develop-with-rig#<tag-or-sha>
```

## Install With skills.sh

For installers compatible with the `skills` CLI, install the skill from this
repository and target Codex when desired:

```bash
npx skills add s-hiraoku/rig --skill develop-with-rig -a codex
```

Use `--list` first if you want to confirm the repository's available skills:

```bash
npx skills add s-hiraoku/rig --list
```

## Other Skill Installers

For any installer that supports GitHub-backed agent skills, use this repository
as the source and `skills/develop-with-rig/` as the skill path. Keep this
directory as the source of truth rather than copying the skill into
`.agents/skills/`.

## Verify

After installation, ask the parent agent to use the skill explicitly:

```text
Use develop-with-rig to decide whether this task should be handled directly,
with rig delegate, or with rig patch create.
```

The expected behavior is that the parent agent favors `rig delegate` for
read-only analysis and reviews, `rig patch create` for isolated edits, and
artifact inspection before applying or summarizing delegated work.
