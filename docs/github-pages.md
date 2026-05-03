---
title: GitHub Pages
description: How this user guide is built and deployed — Jekyll source under docs/, GitHub Actions workflow, and local review notes.
---

# GitHub Pages

This repository publishes the user guide from the `docs/` directory using
GitHub Actions and Jekyll. The Pages site is intentionally separate from the
README: the README is a short repository entry point, while Pages is the
structured manual.

## Files

- `docs/_config.yml` — Jekyll configuration and site defaults.
- `docs/_layouts/default.html` — site frame: header, sidebar, theme toggle,
  prev/next, footer.
- `docs/assets/site.css` — site styling (light + dark, responsive).
- `docs/index.md` — guide landing page.
- `docs/*.md` — individual guide pages.
- `.github/workflows/pages.yml` — build and deploy workflow.

## Workflow

The Pages workflow runs when changes are pushed to `main` under `docs/**` or
when `.github/workflows/pages.yml` itself changes. It can also be started
manually from GitHub Actions with `workflow_dispatch`.

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

Most edits are plain Markdown and can be reviewed directly in a text editor
or any Markdown viewer. For a full Jekyll rendering with the same theme the
site uses:

```bash
cd docs
bundle init
echo 'gem "github-pages", group: :jekyll_plugins' >> Gemfile
bundle install
bundle exec jekyll serve
```

Open `http://127.0.0.1:4000` in a browser. The site uses GitHub's allowed
plugin set, so the locally rendered output matches the deployed site.

## Adding A New Page

1. Create `docs/<page>.md` with front matter:
   ```markdown
   ---
   title: Page Title
   description: One-line description for the SEO and sidebar.
   ---

   # Page Title
   ...
   ```
2. Add the page to the sidebar by editing the `nav_data` block in
   `docs/_layouts/default.html`. Each line is `Group|/path.html|Title`, and
   the surrounding order also drives the prev/next footer.
3. Push to `main` (or open a PR). The Pages workflow rebuilds and deploys.

## Conventions

- Title-case page titles, sentence-case section headings.
- Cross-link freely. Keep each page self-contained but assume the sidebar is
  always visible.
- Code samples use the language hint after the opening fence
  (` ```bash `, ` ```yaml `, ` ```json `) so the syntax highlighter works.
- For callouts, wrap content in
  `<div class="callout callout-tip" markdown="1">…</div>` (or `callout-warn`
  / `callout-danger`).

## Troubleshooting Deploys

If the site does not update after a push, see
[Troubleshooting → GitHub Pages Does Not Update](troubleshooting.md#github-pages-does-not-update).
