---
name: pr-guadian
description: Monitor and harden GitHub pull requests until they are ready to merge. Use when Codex is asked to watch a PR, fix failing CI, inspect GitHub Actions failures, respond to CodeRabbit or other review bot comments, address human review feedback, re-run checks, resolve merge blockers, or bring a PR to merge-ready state.
---

# PR Guadian

## Overview

Drive a pull request from uncertain state to merge-ready state by checking CI, review comments, bot feedback, branch freshness, conflicts, and required status checks. Prefer direct evidence from GitHub over assumptions, handle review feedback comment-by-comment, and keep the final response centered on blockers cleared, blockers remaining, and verification performed.

Do not merge the PR unless the user explicitly asks for merge execution. The default goal is "ready to merge."

## Workflow

### 1. Identify the PR

- If the user provides a PR URL or number, use it directly.
- If no PR is provided, infer it from the current branch with `gh pr view --json url,number,headRefName,baseRefName,state,isDraft,mergeable,reviewDecision,statusCheckRollup`.
- Confirm the repository remote and current branch before making changes.
- If multiple matching PRs exist, choose the open PR for the current branch; ask only if ambiguity remains.

### 2. Build the blocker list

Inspect all surfaces before editing:

- `gh pr checks <pr>` or equivalent GitHub app data for failing, pending, skipped, and required checks.
- `gh run view --log-failed` for GitHub Actions failures.
- PR review comments, review threads, and unresolved conversations. Use GitHub GraphQL or the GitHub app when thread resolution state matters.
- Top-level PR comments from bots such as CodeRabbit, Copilot, reviewdog, eslint, typecheck, or coverage tools.
- Draft state, requested changes, merge conflicts, required approvals, branch protection, and stale branch status.

Classify each item as:

- `must-fix`: required CI failure, merge conflict, requested change, real bug, missing required approval blocker.
- `should-fix`: credible review or bot issue that improves correctness, reliability, security, accessibility, or maintainability.
- `needs-human`: product decision, credential, flaky external service, approval requirement, or destructive operation.
- `not-actionable`: stale bot note, duplicate comment, false positive with evidence, or already-fixed issue.

### 3. Fix blockers

- Start with deterministic local failures when available: lint, typecheck, unit tests, focused integration tests.
- For CI failures, reproduce locally where practical before editing. If reproduction is expensive or environment-specific, inspect logs and patch the smallest credible cause.
- For CodeRabbit or review-bot comments, verify the referenced code and decide whether the issue is real before changing code.
- For human review feedback, address requested changes directly and preserve the existing codebase style.
- For review comments, handle one thread or tightly related comment group at a time. Make the fix, run the relevant focused check, then create one small commit for that response before moving to the next thread.
- Keep commits and edits scoped to PR readiness. Do not perform broad refactors unless they are necessary to resolve the blocker.
- Do not squash, amend, or reorder existing PR commits unless the user explicitly asks. Add incremental commits that make each handled comment easy to audit.
- Do not revert unrelated user changes or unrelated PR work.

### 4. Respond and resolve

- After fixing a review comment, reply in the original review thread with a concise note explaining the change and, when helpful, the commit hash that addressed it.
- For false positives, reply with evidence rather than silently ignoring the comment.
- Resolve conversations only when the fix is present in a commit or the false-positive rationale is documented in the thread.
- If a bot supports rechecking via comment command, use it only when repository conventions make that safe.

### 5. Verify merge readiness

Before reporting completion:

- Run the most relevant local checks.
- Push changes when the user asked you to update the PR or when PR readiness requires CI to rerun.
- Re-check GitHub status after push: CI, review decision, mergeability, draft state, and unresolved conversations.
- If checks are still pending, state that the PR is waiting on CI and include the exact checks still running.
- If checks fail again, continue investigating unless blocked by credentials, infrastructure, or user approval.

## Tooling Notes

- Prefer the GitHub app when available for PR metadata, review comments, issue-style comments, and repository context.
- Use `gh` for Actions logs, check reruns, GraphQL review-thread details, and operations not exposed by the app.
- Use existing repository test commands from package scripts, pyproject, Makefile, CI config, or contributor docs.
- For CodeRabbit, inspect both inline review comments and summary comments; actionable comments may appear in either place.
- For flaky CI, look for repeated failure patterns across recent runs before changing code.

## Final Response

Report:

- PR URL or number inspected.
- Blockers found and how each was handled.
- Files changed and checks run.
- Current merge-readiness state: ready, waiting on CI, or blocked.
- Any remaining human action required.
