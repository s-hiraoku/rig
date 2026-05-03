---
title: 実行アーティファクト
description: .rig/runs/<run-id>/ に書き出されるファイル一覧 — task、command、ログ、result、status、worktree パッチ。
lang: ja
permalink: /ja/artifacts.html
---

# 実行アーティファクト

Rig は実行履歴をプレーンファイルとして保存するので、完了・失敗した実行は特別な
ツールなしで検査できます。このページはファイル単位のリファレンスです。
高レベルの全体像は [コアコンセプト](concepts.md) を。

## ディレクトリ構成

```txt
.rig/runs/<run-id>/
  task.md
  command.json
  stdout.log
  stderr.log
  result.md
  status.json
  diff.patch       # Worktree 実行のみ
```

`<run-id>` は `YYYYMMDD-HHMMSS-<agent>` 形式で、一覧は時系列順に並びます。

## ファイル

| ファイル | 役割 |
| --- | --- |
| `task.md` | エージェントに渡されたタスクテキスト。 |
| `command.json` | エージェント名・コマンド・引数・実行ディレクトリ・タイミング。 |
| `stdout.log` | エージェントコマンドの標準出力 (生)。 |
| `stderr.log` | エージェントコマンドの標準エラー (生)。 |
| `result.md` | `rig show` が表示する人間向けの結果。 |
| `status.json` | 実行 ID、ステータス、タイムスタンプ、終了コード、実行ディレクトリ、(任意の) diff パス。 |
| `diff.patch` | 隔離 Worktree 実行で取得されたパッチ。 |

### `task.md`

Rig がエージェントに渡したタスク。`--task` の場合は文字列そのまま、
`--task-file` の場合はソースファイルのコピーです。いずれにせよ「何を依頼したか」の
正本となるファイルです。

### `command.json`

```json
{
  "agent": "codex",
  "runner": "exec",
  "command": "codex",
  "args": ["exec", "<rendered prompt>"],
  "cwd": "/path/to/project",
  "started_at": "2026-05-04T14:15:00+00:00"
}
```

`args` の最後の要素が解決済みプロンプトです — `prompt_style` のテンプレートを
デバッグするのに便利。dry-run でも同じファイルが生成されます (コマンドは未起動)。

### `stdout.log` / `stderr.log`

バイト単位の生出力。UTF-8 でデコードされ、不正バイトは置換されます。エージェント
が途中でクラッシュした場合、典型的に `stderr.log` にトレースバック、`stdout.log` に
クラッシュ前に書き出された分が残ります。

### `result.md`

人間向けの結果。デフォルトでは `result.md` は stdout のミラーです。エージェントが
[結果抽出マーカー](#結果抽出) を出力した場合は、マーカー以降のテキストだけが
保存されます。

`failed` の実行では、`rig show` は終了コードと `stderr.log` 由来の `--- Error ---`
セクションも表示するので、`result.md` が空でも実行は検査可能です。

### `status.json`

```json
{
  "id": "20260504-141500-codex",
  "agent": "codex",
  "status": "succeeded",
  "started_at": "2026-05-04T14:15:00+00:00",
  "finished_at": "2026-05-04T14:15:09+00:00",
  "exit_code": 0,
  "run_dir": ".rig/runs/20260504-141500-codex"
}
```

Worktree 実行は `diff_path` フィールド (= `diff.patch` を指す) を追加します。
手動実行は完了 / 失敗とマークされるまで `exit_code` を含みません。

### `diff.patch`

隔離 worktree から取得された unified diff で、`git apply` 可能な形式です。
`rig worktree show <run-id>` がこのファイルをメタデータと併せて表示し、
`rig worktree apply <run-id>` がこの diff を `git apply` します。
[Worktree 実行](worktrees.md) を参照。

## 結果抽出
{: #結果抽出 }

デフォルトでは `result.md` は stdout のコピーです。エージェントが次のマーカーを
出力すると:

```txt
--- RIG RESULT ---
```

Rig はマーカー以降のテキストのみを `result.md` に保存し、完全な stdout は
`stdout.log` に残します。これにより冗長なエージェントでもログを書き出しつつ、
`rig show latest` できれいな最終回答だけを表示できます。

プロンプトテンプレートで明示的に促すこともできます:

```yaml
prompt_template: |
  ...
  最終回答の冒頭に必ず `--- RIG RESULT ---` リテラルマーカーを書いてください。
```

## ステータス値

| ステータス | 意味 |
| --- | --- |
| `created` | dry run のアーティファクトのみ書かれた。コマンドは未実行。 |
| `waiting` | 手動ランナーが作成し、明示的な完了 / 失敗を待っている。 |
| `succeeded` | エージェントコマンド (または手動完了) が成功。 |
| `failed` | エージェントコマンドが失敗 / タイムアウト、または手動で失敗とマーク。 |

## アーティファクトを検査する

通常の検査は CLI で:

```bash
rig list
rig show latest
rig worktree show latest
```

コマンド実行のデバッグや他のローカルツールとの連携にはファイルを直接読みます:

```bash
ls .rig/runs/$(ls -1t .rig/runs | head -n1)
jq . .rig/runs/<run-id>/status.json
jq . .rig/runs/<run-id>/command.json
```

## 実行履歴のバージョン管理

`.rig/runs/` はマシンごとです。多くのチームは `.gitignore` に追加し、
`.rig/config.yaml` と `.rig/env.yaml` だけをコミットします。実行記録はローカルの
監査ログとして使い、マシン間で共有しないのが現実的です。
