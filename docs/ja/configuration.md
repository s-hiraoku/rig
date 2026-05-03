---
title: 設定
description: Rig の 2 つの設定ファイル — エージェント用の .rig/config.yaml と環境チェック用の .rig/env.yaml。
lang: ja
permalink: /ja/configuration.html
---

# 設定

Rig は `.rig/` 以下の 2 つのファイルで設定を保持します。`rig init` が妥当な
デフォルトで生成します。両方ともプレーンな YAML なので手で編集できます。

```txt
.rig/
  config.yaml   # エージェント、ランナー、プロンプトスタイル
  env.yaml      # 必須ファイルとオプションのアセットマネージャ
  runs/         # 実行履歴
```

CLI 別の設定例 (Codex / Claude / Gemini / Copilot / 手動) は
[エージェント](agents.md)、プロンプト文字列のオプションは
[プロンプトスタイル](prompts.md) を参照してください。

## 初期化とリセット
{: #初期化とリセット }

```bash
rig init                # 不足ファイルを作成。既存は上書きしない。
rig init --reset config # config.yaml をバックアップして再生成。
rig init --reset env    # env.yaml をバックアップして再生成。
rig init --reset all    # 両方
rig init --force        # --reset all と同等
```

`rig init` は何度でも安全に実行できます。何も変わらない場合は
`Rig already up to date.` と表示されます。

## エージェント設定

`.rig/config.yaml` は Rig が各エージェントに対して使うコマンドを制御します。
`rig run` でエージェント名を省略すると `default_agent` が使われます。

```yaml
default_agent: codex

agents:
  codex:
    runner: exec
    command: codex
    args:
      - exec
```

### スキーマ

| 項目 | 型 | 備考 |
| --- | --- | --- |
| `default_agent` | string | `rig run` でエージェント名省略時に使われる名前。 |
| `agents.<name>.runner` | `exec` / `manual` / `pty` | [ランナー](#ランナー) 参照。 |
| `agents.<name>.command` | string | Rig が起動する実行ファイル。`exec` と `pty` で必須。 |
| `agents.<name>.args` | list of string | レンダリング済みプロンプトの前に挿入される追加引数。 |
| `agents.<name>.prompt_style` | `rig` (default) / `task` / `template` | [プロンプトスタイル](prompts.md) 参照。 |
| `agents.<name>.prompt_template` | string | `prompt_style: template` のとき必須。 |
| `agents.<name>.timeout_seconds` | integer | `exec` と `pty` に適用。 |

### ランナー

- `exec` — 非対話型のコマンド実行。Rig はレンダリング済みプロンプトを最後の
  引数として追加します。
- `manual` — コマンドを起動せずに `waiting` 状態の実行を作成。
- `pty` — 端末を必要とする CLI 用の実験的な TTY ランナー。

### 例

別の CLI を 2 つ目のエージェントとして:

```yaml
agents:
  gemini:
    runner: exec
    command: gemini
    args:
      - --prompt
    prompt_style: task
    timeout_seconds: 600
```

GUI 作業向けの手動ランナー:

```yaml
agents:
  external:
    runner: manual
```

テンプレート化したプロンプト:

```yaml
agents:
  reviewer:
    runner: exec
    command: codex
    args: [exec]
    prompt_style: template
    prompt_template: |
      あなたは {agent} です。{task_path} を読んで Markdown レポートを返してください。
```

## プロンプトスタイル

`prompt_style` は Rig がエージェントコマンドに付与する文字列を決めます。

- `rig` (デフォルト) — Rig 標準の指示文をタスクファイルパスとともに送る。
- `task` — タスクファイルの内容そのまま。
- `template` — `prompt_template` をレンダリング。

テンプレート変数:

- `{agent}` — 設定上のエージェント名。
- `{task}` — `--task` または `--task-file` から読まれた生のタスクテキスト。
- `{task_md}` — 保存された task.md の内容。
- `{task_path}` — 実行 cwd からの相対パス (task.md を指す)。

実例と CLI 別の推奨は [プロンプトスタイル](prompts.md) を。

## 環境設定
{: #環境設定 }

`.rig/env.yaml` は `rig env doctor` と `rig env plan` のチェック内容を宣言します。
スキーマは小さく、`version` フィールドで前方互換を保ちます。

```yaml
version: 1

required_files:
  - path: AGENTS.md
    label: Agent instructions
    hint: "AGENTS.md を作成し、プロジェクト固有のエージェント指示を記述してください。"
```

必須ファイルは文字列でもマッピングでも書けます:

```yaml
required_files:
  - AGENTS.md
  - path: docs/agent-harness.md
    label: Agent harness docs
    hint: "docs/agent-harness.md にチームのセットアップ手順を書いてください。"
```

オプションのアセットマネージャは `agent_asset_managers` 配下に書きます。生成された
デフォルトには APM、GitHub CLI `gh skills`、Vercel `skills` (npx 経由) が含まれます。
Rig は設定されたコマンドの存在をチェックしますが、インストールはしません。

```yaml
agent_asset_managers:
  - id: apm
    label: APM
    command: apm
  - id: gh-skills
    label: GitHub skills manager
    command: gh
    args:
      - skills
      - --help
  - id: vercel-skills
    label: Vercel skills manager
    command: npx
```

アセットマネージャ自身が必須ファイルを宣言することもできます。ファイルが欠けている
場合、`rig env doctor` はマネージャ名と欠けているファイルの両方を報告します:

```yaml
agent_asset_managers:
  - id: apm
    label: APM
    command: apm
    required_files:
      - path: apm.yml
        label: APM manifest
        hint: "apm.yml を作るか、.rig/env.yaml からこのマネージャを外してください。"
```

Rig は欠けているファイルやツールを報告するだけで、グローバルツールを勝手に
インストールしたり、サードパーティのエージェントアセットを書き換えたりはしません。

## `rig init` がやらないこと

- 既存の `.rig/config.yaml` や `.rig/env.yaml` を編集することはありません。
- Codex、Claude、Gemini、Copilot、アセットマネージャをインストールすることはありません。
- `AGENTS.md`、`CLAUDE.md`、スキルファイルを作成・編集することはありません。
- コミットや push をすることはありません。

生成済み設定を Rig の現行デフォルトに戻したい場合は `rig init --reset config` を
使います (既存ファイルは事前にバックアップされます)。
