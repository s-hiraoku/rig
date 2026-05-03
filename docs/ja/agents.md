---
title: エージェント
description: Codex、Claude Code、Gemini、Copilot、外部 GUI エージェントを .rig/config.yaml で設定する。
lang: ja
permalink: /ja/agents.html
---

# エージェント

Rig におけるエージェントとは `.rig/config.yaml` 上の名前付きコマンドのことです。
Rig はレンダリング済みプロンプトを最後の引数として付け加え、stdout、stderr、終了コードを
実行アーティファクトに保存します。このページは主要な CLI ごとの動作確認済みの設定例集です。

ランナーの意味とプロンプトプレースホルダのリファレンスは
[設定](configuration.md) と [プロンプトスタイル](prompts.md) を参照。

<div class="callout callout-tip" markdown="1">
<span class="callout-title">ヒント</span>
Rig は CLI ごとの特殊な仕掛けを持ちません。安定した非対話型のプロンプトモードを
公開している CLI なら、`exec` ランナーとして設定できます。
</div>

## Codex (デフォルト)

デフォルトのエージェントです。`codex exec` は付与されたプロンプトを読み、
エージェントの応答を stdout に書きます。

```yaml
default_agent: codex

agents:
  codex:
    runner: exec
    command: codex
    args:
      - exec
```

Codex は実行ディレクトリが信頼された Git リポジトリであることを要求します。
`Not inside a trusted directory` で失敗したら先に `git init` を。
[トラブルシューティング](troubleshooting.md#trusted-directory-error) も参照。

## Claude Code

Claude Code の `claude` CLI は `-p` (`--print`) で 1 つの非対話型プロンプトを受け取ります。

```yaml
agents:
  claude:
    runner: exec
    command: claude
    args:
      - -p
    prompt_style: task
```

Rig 独自のラッパー指示文を含めず、保存された task ファイルの内容を素のまま渡したい
ので `prompt_style: task` を指定します。Rig の stdout を他のツールに渡したい場合は
`--output-format stream-json` や `--output-format json` を追加できます。

Claude 用のプロジェクト指示を生成するには:

```bash
rig guide agents --target claude --write
```

これで `.rig/instructions/rig.md` が作成され、`CLAUDE.md` に貼るスニペットも
表示されます。

## Gemini

```yaml
agents:
  gemini:
    runner: exec
    command: gemini
    args:
      - --prompt
    prompt_style: task
```

`prompt_style: task` でプロンプトを最小化します (Gemini はタスクテキストだけを
見ます)。モデル指定など Gemini 固有のフラグ (例: `--model`) は `args` に追加してください。

## GitHub Copilot CLI

```yaml
agents:
  copilot:
    runner: exec
    command: copilot
    args:
      - -p
    prompt_style: task
```

Copilot CLI はデフォルトで人間向けの出力を行います。プロンプトに
`--- RIG RESULT ---` マーカーを書かせると、Rig はマーカー以降のテキストだけを
`result.md` に残せます。詳しくは
[実行アーティファクト → 結果抽出](artifacts.md#結果抽出)。

## テンプレート化されたプロンプト

エージェントに正確な指示エンベロープを渡したいときは `prompt_style: template` を
使います。テンプレートは `{agent}`、`{task}`、`{task_md}`、`{task_path}` を参照
できます。

```yaml
agents:
  reviewer:
    runner: exec
    command: codex
    args:
      - exec
    prompt_style: template
    prompt_template: |
      あなたは {agent} です。次のタスクをレビューし、`--- RIG RESULT ---` リテラル
      マーカーから始まる 1 つの Markdown セクションだけで返してください。

      タスク ({task_path}):

      {task_md}
```

プレースホルダの完全なリファレンスと例は [プロンプトスタイル](prompts.md) を。

## 手動 / GUI エージェント

GUI、チャット UI、Rig が直接起動すべきでないツールでの作業には `manual` ランナーを
使います。Rig はタスクを書き出し、明示的な `complete` または `fail` を待ちます。

```yaml
agents:
  external:
    runner: manual
```

```bash
rig run external --task "デザインアプリで新しいツールバーを実装する。"
# ... 実際の作業はツール側で進める ...
rig manual complete latest --result-file result.md
```

`rig manual fail latest --error "デザインレビューでブロック。"` は実行と同じ
アーティファクト構造で失敗を記録します。ステータス遷移は `waiting` 中の実行に
限定されているため、完了済みの実行を上書きすることはありません。

## 実験的: PTY ランナー
{: #実験的-pty-ランナー }

CLI によっては実 TTY を必要とするものがあります。`pty` ランナーは PTY を割り当て、
レンダリング済みプロンプトを入力として書き、混合トランスクリプトを `stdout.log` と
`result.md` に取得します。

```yaml
agents:
  interactive:
    runner: pty
    command: interactive-agent
    args:
      - --prompt
    timeout_seconds: 300
    prompt_style: task
```

PTY ランナーは「単一の argv で動かせない CLI」のときだけ使ってください。現代的な
コーディング CLI なら `exec` の方がシンプルで再現性が高いです。

## デフォルトエージェントの切替

`default_agent` は `rig run` でエージェント名を省略したときに使われるエージェントを
決めます。`.rig/config.yaml` で 1 度設定するだけです:

```yaml
default_agent: claude

agents:
  codex:
    runner: exec
    command: codex
    args: [exec]
  claude:
    runner: exec
    command: claude
    args: [-p]
    prompt_style: task
```

```bash
rig run --task "worktree ヘルパをリファクタして。"   # claude を使う
rig run codex --task "worktree ヘルパをリファクタして。"   # 明示的に codex
```

## エージェントごとのタイムアウト

`timeout_seconds` は `exec` と `pty` の両方に適用されます。設定値より長く動作した
場合、Rig はプロセスを終了させ、`failed` ステータスで取得済み出力を保存します。

```yaml
agents:
  codex:
    runner: exec
    command: codex
    args: [exec]
    timeout_seconds: 600
```

## アセットマネージャ vs Rig エージェント

Rig エージェントは「Rig が実行するコマンド」のことです。エージェントの *アセット*
(プロンプト、フック、スキル、MCP サーバ一覧) は外部ツール (APM、GitHub CLI
`gh skill`、Vercel `skills`、自前スクリプト) で管理します。`.rig/env.yaml` で
オプションのアセットマネージャとして宣言しておけば、`rig env doctor` がインストール
状況を報告できます (Rig 自身は何もインストールしません)。詳しくは
[設定 → 環境設定](configuration.md#環境設定)。
