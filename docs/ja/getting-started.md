---
title: はじめに
description: Rig 未セットアップの状態から、検査可能な実行を 1 回作るまでの最短ルート。チェックアウトからのローカル開発手順も含みます。
lang: ja
permalink: /ja/getting-started.html
---

# はじめに

このページは「Rig が未セットアップの状態」から「検査可能な実行を 1 回作る」までの
最短ルートです。通常実行、Worktree 実行、手動実行の使い分けは
[ワークフロー](workflows.md) を、実例フローは [レシピ](recipes.md) を参照してください。

## インストール

GitHub から直接インストールします:

```bash
uv tool install "rig @ git+https://github.com/s-hiraoku/rig.git"
```

コマンドが使えることを確認します:

```bash
rig --help
```

最新版に再インストールする場合:

```bash
uv tool install --force --refresh "rig @ git+https://github.com/s-hiraoku/rig.git"
```

<div class="callout" markdown="1">
<span class="callout-title">uv が必要です</span>
Rig は <code>uv tool</code> として配布されています。未導入の場合はまず
<a href="https://docs.astral.sh/uv/">uv</a> をインストールしてください。
</div>

## ローカル開発

リポジトリをクローンして開発環境を作ります:

```bash
git clone https://github.com/s-hiraoku/rig.git
cd rig
uv sync --group dev
```

チェックアウトから Rig を実行:

```bash
uv run rig --help
```

zsh 補完は `contrib/completions/rig.zsh` にあります。

## 最初の実行

Rig を使いたいプロジェクトのルートで:

```bash
rig init
rig suggest "現在の差分をレビューしてリスクのある変更を指摘して。"
rig run codex --task "現在の差分をレビューしてリスクのある変更を指摘して。"
rig list
rig show latest
```

Rig リポジトリのチェックアウトから動かす場合は `uv run` を前置します:

```bash
uv run rig init
uv run rig suggest "現在の差分をレビューしてリスクのある変更を指摘して。"
uv run rig run codex --task "現在の差分をレビューしてリスクのある変更を指摘して。"
uv run rig list
uv run rig show latest
```

`rig show` の出力より詳しく中身を見たくなったら、
[実行アーティファクト](artifacts.md) で生成ファイルを確認できます。

## `rig init` が作るもの

```txt
.rig/
  config.yaml   # エージェント、ランナー、プロンプトスタイル
  env.yaml      # 必須ファイルとオプションのアセットマネージャ
  runs/         # 実行履歴 (マシンごと)
```

`rig init` は何度でも安全に実行できます。リセット用フラグは
[設定 → 初期化とリセット](configuration.md#初期化とリセット) を参照してください。

## 環境チェック

初期化後、ローカルのハーネス設定を確認します:

```bash
rig env doctor
rig env doctor --json   # CI 用の構造化出力
rig env plan
```

`rig env bootstrap` は Rig 所有のファイルだけを作成します。Rig が外部ツールや
サードパーティ製のエージェントアセットを勝手に入れることはありません。

## 必要要件

デフォルトの `codex` エージェントは `codex exec` を使うため、Codex CLI が
インストールされ `PATH` に通っている必要があります。別の CLI を使う場合は
[エージェント](agents.md) を参照してください。

Codex は現在のディレクトリが信頼された Git リポジトリであることを要求する場合が
あります。trusted-directory エラーで実行が失敗した場合は、まずプロジェクトを
Git リポジトリとして初期化してください:

```bash
git init
```

## 次のステップ

- ワークフローを選ぶ: [ワークフロー](workflows.md)
- 実例を試す: [レシピ](recipes.md)
- 別のエージェントを設定する: [エージェント](agents.md)
- プロンプトをカスタマイズする: [プロンプトスタイル](prompts.md)
