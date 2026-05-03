---
title: コマンドリファレンス
description: Rig の CLI コマンド・フラグ・JSON 出力を網羅した簡潔なリファレンス。
lang: ja
permalink: /ja/commands.html
---

# コマンドリファレンス

このページは簡潔なリファレンスです。シナリオ別のガイドは
[ワークフロー](workflows.md) または [レシピ](recipes.md) から。

## 共通フロー

```bash
rig init
rig suggest "現在の差分をレビューして。"
rig run codex --task "現在の差分をレビューして。"
rig list
rig show latest
```

## Worktree フロー

```bash
rig worktree run codex --task "依頼された変更を実装して。"
rig worktree show latest
rig worktree apply latest
```

## コマンド一覧

### セットアップ

| コマンド | 用途 |
| --- | --- |
| `rig init` | `.rig/` を初期化。 |
| `rig init --reset config` | `.rig/config.yaml` をバックアップして再生成。 |
| `rig init --reset env` | `.rig/env.yaml` をバックアップして再生成。 |
| `rig init --reset all` / `--force` | 両方リセット。 |

### 実行

| コマンド | 用途 |
| --- | --- |
| `rig run [agent] --task "..."` | 現在の作業ツリーで実行。`[agent]` 省略時は `default_agent`。 |
| `rig run [agent] --task-file task.md` | タスクをファイルから読んで実行。 |
| `rig run [agent] --task "..." --dry-run` | エージェントを起動せず、アーティファクトと argv を書き出す。 |
| `rig run [agent] --task "..." --json` | 実行結果を JSON で出力。 |
| `rig suggest "..." [--json]` | `rig run` か `rig worktree run` を推奨 (実行はしない)。 |

### 検査

| コマンド | 用途 |
| --- | --- |
| `rig list [--json]` | 最近の実行一覧。 |
| `rig show <run-id|latest> [--json]` | 実行のメタデータと結果を表示。 |
| `rig worktree show <run-id|latest>` | メタデータと取得済みパッチを表示。 |

### Worktree

| コマンド | 用途 |
| --- | --- |
| `rig worktree run [agent] --task "..."` | 隔離 worktree で実行。 |
| `rig worktree apply <run-id|latest>` | 取得済みパッチを `git apply`。 |
| `rig worktree prune` | Rig 作成の worktree を削除。 |

### 手動

| コマンド | 用途 |
| --- | --- |
| `rig manual complete <run-id|latest> --result "..."` | `waiting` の手動実行を完了。 |
| `rig manual complete <run-id|latest> --result-file result.md` | ファイルから完了。 |
| `rig manual fail <run-id|latest> --error "..."` | `waiting` の手動実行を失敗とマーク。 |
| `rig manual fail <run-id|latest> --error-file error.txt` | ファイルから失敗マーク。 |
| `rig history complete <...>` / `rig history fail <...>` | 旧名 (互換用)。 |

### 環境

| コマンド | 用途 |
| --- | --- |
| `rig env doctor [--json]` | ローカルハーネス環境を診断。 |
| `rig env plan` | 読み取り専用の環境計画を表示。 |
| `rig env bootstrap` | Rig 所有の環境ファイルのうち不足分を作成。 |
| `rig env manager status [--json]` | 設定済みアセットマネージャの状態を表示。 |

### ガイド

| コマンド | 用途 |
| --- | --- |
| `rig guide agents [--target codex|claude] [--format markdown]` | エージェント指示スニペットを出力。 |
| `rig guide agents --write [--force]` | `.rig/instructions/rig.md` を作りつつ短いスニペットを出力。 |

### MCP

| コマンド | 用途 |
| --- | --- |
| `rig mcp serve` | stdio で MCP サーバを起動。 [MCP サーバ](mcp.md) 参照。 |

## 実行オプション

`--task` と `--task-file` は **どちらか一方** を指定する必要があります。両方指定や
両方省略はエラーです。

`--dry-run` はタスク・コマンドプレビュー・ステータスメタデータを書き出し、エージェント
は起動しません。dry-run のステータスは `created` です。

`--json` は `run`、`list`、`show`、`suggest`、`env doctor` で利用でき、人間向けテキストを
パースしないスクリプトや MCP 連携で便利です。

## 実行 ID

実行 ID は `YYYYMMDD-HHMMSS-<agent>` 形式で、実行ディレクトリの寿命の間ずっと
安定です。実行 ID を受け取るコマンドには `latest` を渡せば最新の実行を意味します。

## メモ

- Worktree のパッチには Git に無視されない未追跡ファイルが含まれます。生成物の
  ディレクトリはパッチを当てる前に `.gitignore` に追加してください。
- エージェントが `--- RIG RESULT ---` を出力すると、Rig はそのマーカー以降のテキスト
  だけを `result.md` に保存し、完全な stdout は `stdout.log` に保持します。
- `prompt_style: template` を使うと `prompt_template` でプレースホルダ `{agent}`、
  `{task_path}`、`{task}`、`{task_md}` が使えます。
  詳しくは [プロンプトスタイル](prompts.md)。
- MCP ツールは CLI と同じ実行ストアとオーケストレータを公開します。初期ツールは
  `rig_run`、`rig_list_runs`、`rig_list_agents`、`rig_suggest`、`rig_get_run`、
  `rig_get_result`、`rig_get_diff`、`rig_apply_patch`。
  [MCP サーバ](mcp.md) 参照。
- MCP は `rig_policy` プロンプト、`rig://policy` / `rig://agents-md` リソースも
  公開します。
- MCP の `cwd` 値はサーバ起動ディレクトリ以下、または `RIG_MCP_ROOT` が設定されて
  いればその下に収まる必要があります。MCP の `task_file` パスは `cwd` から解決され、
  プロジェクト内に留める必要があります。
- MCP の `rig_apply_patch` は `RIG_MCP_ALLOW_APPLY=1` を付けて起動しない限り無効です。
- 旧形式の `rig history list`、`rig history show`、`rig history complete`、
  `rig history fail` は互換のため、現在の `list`、`show`、`manual` に正規化されます。

## 関連項目

- [設定](configuration.md) — `.rig/config.yaml` と `.rig/env.yaml`。
- [エージェント](agents.md) — CLI 別の設定例。
- [プロンプトスタイル](prompts.md) — Rig がエージェントに送る文字列。
- [実行アーティファクト](artifacts.md) — Rig がディスクに書き出すもの。
