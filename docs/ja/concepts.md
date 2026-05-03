---
title: コアコンセプト
description: Rig が使う基本用語 — 実行 (run)、エージェント、ランナー、Worktree 実行、アーティファクト、環境チェック。
lang: ja
permalink: /ja/concepts.html
---

# コアコンセプト

Rig の語彙は小さなセットです。このページで各用語を定義し、深く知りたいときの
ページにリンクします。

## 実行 (Run)

「実行 (run)」は Rig の作業の最小単位です。各実行はタスク、コマンドメタデータ、
標準出力、標準エラー、最終結果、ステータスメタデータを記録します。

実行は次の場所に保存されます:

```txt
.rig/runs/<run-id>/
```

代表的なファイル:

- `task.md` — エージェントに渡したユーザータスク。
- `command.json` — Rig が実行(またはプレビュー)したコマンド。
- `stdout.log` — 取得した標準出力。
- `stderr.log` — 取得した標準エラー。
- `result.md` — `rig show` が表示する最終結果。
- `status.json` — 実行ステータスとメタデータ。
- `diff.patch` — Worktree 実行で取得したパッチ。

実行 ID は `YYYYMMDD-HHMMSS-<agent>` 形式で、一覧は時系列順に並びます。

## エージェント

エージェントとは `.rig/config.yaml` で定義されたコマンドです。Rig は Codex
向けの便利なデフォルトを同梱していますが、安定した非対話型のプロンプトモードを
持つ CLI なら他にも設定できます。実例は [エージェント](agents.md) を参照。

## ランナー

ランナーは Rig が作業をどう開始するかを制御します。

- `exec` — 非対話型のコマンド実行。Rig はレンダリングしたプロンプトを
  最後の引数として追加します。
- `manual` — コマンドを起動せず、`waiting` 状態の実行を作成します。
  人手や外部エージェントの作業を追跡します。
- `pty` — 端末を必要とする CLI のための実験的な TTY ランナー。

## プロンプトスタイル

`prompt_style` は Rig がエージェントコマンドに付与する文字列を決めます。
`rig` / `task` / `template` の 3 種類で、デフォルトは `rig` です。
`rig` は `task.md` を読むよう指示する汎用のプロンプトを送ります。
完全なリファレンスは [プロンプトスタイル](prompts.md) を参照してください。

## Worktree 実行

Worktree 実行は `.rig/worktrees/<run-id>/` 以下の隔離された Git worktree で
エージェントを動かし、生成されたパッチを取得します。これによりパッチを確認・
適用するまではメインの作業ツリーは変更されません。
[Worktree 実行](worktrees.md) と
[レシピ → Worktree でリファクタする](recipes.md#worktree-でリファクタする) を参照。

## アーティファクト

アーティファクトとは `.rig/runs/<run-id>/` に書かれるファイルです。アーティファクト
のおかげで、コマンド終了後も実行は検査可能で、連携先には読み込み対象として
安定したファイルが残ります。ファイル単位のリファレンスは
[実行アーティファクト](artifacts.md)。

## ステータス

すべての実行はステータスを持ちます。ライフサイクルは:

```txt
created → succeeded
created → failed
waiting → succeeded   (manual complete)
waiting → failed      (manual fail)
```

`--dry-run` でコマンド未実行のまま終わった実行も、最終ステータスは `created` です。

## 環境チェック

`.rig/env.yaml` はプロジェクト固有のハーネス要件を宣言します。必須の指示ファイルや
オプションのアセットマネージャなどです。`rig env doctor` と `rig env plan` は
不足を報告するのみで、サードパーティツールを勝手にインストールすることはありません。
`rig env bootstrap` は Rig 所有のファイルだけを作成します。

[設定 → 環境設定](configuration.md#環境設定) と
[ワークフロー → 環境セットアップ](workflows.md#環境セットアップ) も参照。

## MCP サーバ

Rig は実行ストアとオーケストレータを stdio 上の MCP サーバとして公開できます。
MCP 対応エージェントは CLI のテキストをパースせずに、実行の一覧表示・開始・
結果の取得・取得済みパッチの読み出しを行えます。詳細は
[MCP サーバ](mcp.md)。
