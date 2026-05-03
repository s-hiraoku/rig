---
title: GitHub Pages
---

# GitHub Pages

This repository publishes the user guide from the `docs/` directory with
GitHub Actions and Jekyll.

## Files

- `docs/index.md`: guide landing page.
- `docs/_config.yml`: Jekyll Pages metadata and theme.
- `.github/workflows/pages.yml`: build and deploy workflow.

## Publish

The Pages workflow runs when changes are pushed to `main` under `docs/**` or
when `.github/workflows/pages.yml` changes. It can also be started manually
from GitHub Actions with `workflow_dispatch`.

The workflow:

1. Checks out the repository.
2. Configures GitHub Pages.
3. Builds `./docs` into `./_site` with Jekyll.
4. Uploads the Pages artifact.
5. Deploys to the `github-pages` environment.

## Repository Settings

In GitHub, set Pages to deploy from GitHub Actions. The workflow needs these
permissions, which are already declared in `pages.yml`:

- `contents: read`
- `pages: write`
- `id-token: write`

## Local Review

Most guide edits are plain Markdown and can be reviewed directly. For a full
Jekyll rendering, run the Pages workflow in GitHub Actions or use a local Jekyll
setup compatible with `jekyll-theme-minimal`.
