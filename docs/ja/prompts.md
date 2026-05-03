---
title: プロンプトスタイル
description: Rig がエージェントコマンドに付与するプロンプトの作り方 — rig / task / template スタイルとプレースホルダ。
lang: ja
permalink: /ja/prompts.html
---

# プロンプトスタイル

`prompt_style` は Rig が実際にエージェントへ送る文字列を決めます。選んだスタイル
が、設定済みコマンドの最後の引数となる文字列を 1 つ生み出します。`command`、
`args`、`timeout_seconds` などはそのままです。

`.rig/runs/<run-id>/command.json` に解決済みの argv が記録されるため、Rig が実際に
使ったプロンプトは後から必ず確認できます。

## 一覧

| スタイル | Rig が送る内容 | 使うとき |
| --- | --- | --- |
| `rig` (デフォルト) | `task.md` を読むよう促す短い指示 | エージェントがファイル直接アクセスでき、汎用ガードレールが役立つ。 |
| `task` | task ファイルの内容そのまま | エージェントがユーザープロンプト (Claude `-p`、Gemini `--prompt`) のみ期待する。 |
| `template` | `prompt_template` をレンダリングしたカスタム文字列 | 厳密な指示エンベロープや構造化マーカーを要求したい。 |

## `rig` スタイル

デフォルトのスタイルは Rig 流の指示文を生成します。Rig はユーザータスクを
`task.md` に保存し、エージェントにそのファイルを開かせます:

```text
You are running as a delegated codex agent through Rig.

Read the task file:

.rig/runs/20260504-141500-codex/task.md

Complete the task and write your final answer to stdout.

Do not assume Rig will automatically apply changes.
If you modify files, explain what you changed.
```

`codex exec` のように、受け取ったファイルパスを開いて作業対象として扱う CLI に
向いています。

## `task` スタイル

`task` はラッパーをスキップします。Rig は `task.md` の生テキストを最後の引数として
そのまま渡します。前置きはありません。

```yaml
agents:
  claude:
    runner: exec
    command: claude
    args: [-p]
    prompt_style: task
```

タスクが `worktree ヘルパをリファクタして。` であれば、実行されるコマンドは実質:

```bash
claude -p "worktree ヘルパをリファクタして。"
```

`-p` / `--prompt` でラップされた指示ではなく単一のユーザーメッセージを期待する CLI
に向いています。

## `template` スタイル

`template` は `prompt_template` を Python の `str.format` テンプレートとして
レンダリングします。プロンプトのエンベロープを完全にコントロールできるのは
このスタイルだけです。

```yaml
agents:
  reviewer:
    runner: exec
    command: codex
    args: [exec]
    prompt_style: template
    prompt_template: |
      あなたは {agent} です。1 つのタスクを最後までレビューしてください。

      タスク ({task_path}):

      {task_md}

      Markdown レポートで返答してください。最終回答は Rig が抽出できるよう、
      `--- RIG RESULT ---` リテラルマーカーから書き始めてください。
```

プレースホルダは設定読み込み時に検証されます。未知のプレースホルダがあれば
`Config value … uses unknown placeholder` のエラーで早期に失敗するので、実行中に
壊れることはありません。

### プレースホルダリファレンス

| プレースホルダ | 値 |
| --- | --- |
| `{agent}` | 設定上のエージェント名 (`agents` 配下のキー)。 |
| `{task}` | `--task` または `--task-file` から渡された生のタスクテキスト。 |
| `{task_md}` | 保存された `task.md` の完全な内容 (Rig が付与するヘッダ含む)。 |
| `{task_path}` | 実行 cwd から見た `task.md` の相対パス。 |

`{task}` と `{task_md}` の差は末尾改行と Rig が付けたヘッダの有無だけです。
ディスク上のバージョンが欲しいなら `{task_md}` を使ってください。

### 実例

厳密な構造化レスポンス:

```yaml
prompt_template: |
  返答は {{"status": string, "summary": string}} 形式の JSON のみで。
  タスク: {task}
```

二重ブレース (`{{` と `}}`) に注意 — `str.format` はシングルブレースをプレースホルダ
として扱います。

保存ファイルを参照する最小限のエンベロープ:

```yaml
prompt_template: "{task_path} を読んでタスクを完了して。"
```

チームが常に欲しい文脈を末尾に付ける:

```yaml
prompt_template: |
  コーディング規約: AGENTS.md と `.rig/instructions/rig.md` を参照。
  タスク ({agent}, {task_path}):

  {task_md}
```

## 結果マーカー

`prompt_style` に関係なく、エージェントは次のセンチネル行を出すと、Rig が最終回答
だけを `result.md` に残せます:

```text
--- RIG RESULT ---
```

stdout の中にこのマーカーがあれば、`result.md` にはマーカー以降のみが入り、
`stdout.log` には完全な出力が保持されます。冗長なエージェントが大量にログを
吐いても、`rig show latest` ではきれいな最終回答だけが見えるようになります。

[実行アーティファクト → 結果抽出](artifacts.md#結果抽出) も参照。

## CLI 別の推奨

| CLI | 推奨 `prompt_style` |
| --- | --- |
| Codex (`codex exec`) | `rig` (デフォルト) |
| Claude Code (`claude -p`) | `task` |
| Gemini (`gemini --prompt`) | `task` |
| GitHub Copilot CLI (`copilot -p`) | `task` |
| カスタムレビュー / レポートジョブ | `template` |

`template` を結果マーカーと組み合わせると、ログの形が大きく違う複数の CLI でも
出力フォーマットを揃えられます。

## 解決済みプロンプトを確認する

過去の実行で Rig が使った argv を確認するには `command.json` を読みます:

```bash
cat .rig/runs/<run-id>/command.json
```

`args` の最後のエントリが Rig が生成したプロンプトです。dry run の場合も同じ
ファイルが生成されます (`rig run … --dry-run`)。
