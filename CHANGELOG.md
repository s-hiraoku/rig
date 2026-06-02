# Changelog

## 0.1.0

- Add Rig initialization and file-backed run artifacts.
- Add exec runner support for configured child coding agents.
- Add isolated patch runs with captured patch review and apply commands.
- Add local setup diagnostics with `rig doctor`.
- Add an initial MCP stdio server with structured Rig run tools.
- Add MCP cwd, task file, and patch-apply safety gates.
- Add MCP policy prompt/resources and configured agent discovery.
- Add `rig init` support for generated Rig instructions and a managed
  `AGENTS.md` reference block.
- Add Antigravity CLI defaults using `agy -p` and doctor guidance for migrating
  legacy Gemini CLI agent configs.
- Add `rig harness` guidance for the companion `codex-harnesses` project
  harness source.
- Add GitHub Pages user guide and CI coverage for tests, lint, type checks, and
  documentation builds.
- Add `rig manager status` to report configured agent asset managers declared in
  `.rig/env.yaml`, including availability checks, required files, and `--json`
  output.
