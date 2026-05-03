---
title: Rig ユーザーガイド
description: Rig はローカルで動く AI コーディングハーネス。タスクをファイルとして残し、実行アーティファクトを検査でき、Worktree で隔離された編集を行い、MCP サーバとしても動作します。
lang: ja
permalink: /ja/
---

<section class="hero" markdown="0">
  <span class="hero-eyebrow">ローカル AI コーディングハーネス</span>
  <h1>エージェントを動かす。証跡を残す。</h1>
  <p>
    Rig は Codex、Claude Code、Gemini、Copilot などのコーディング CLI を、薄い
    ファイルベースのハーネスでラップします。タスク、コマンド、ログ、結果、パッチが
    すべてプロジェクト直下の <code>.rig/</code> 以下にプレーンファイルとして残るため、
    エージェントの作業は検査可能・再実行可能・レビュー可能なまま保たれます。
  </p>
  <div class="hero-actions">
    <a class="btn btn-primary" href="getting-started.html">はじめる →</a>
    <a class="btn btn-secondary" href="https://github.com/s-hiraoku/rig" rel="noopener">GitHub を見る</a>
  </div>
</section>

```bash
uv tool install "rig @ git+https://github.com/s-hiraoku/rig.git"
rig init
rig run codex --task "現在の差分をレビューしてリスクのある変更を指摘して。"
rig show latest
```

<div class="callout" markdown="1">
<span class="callout-title">なぜ Rig か</span>
何を依頼したか、どのコマンドが走ったか、何が変わったか、結果はどこで確認できるか。
これらの監査証跡を、データベースやクラウドサービスに頼らずローカルだけで残したい
ときに Rig を使ってください。
</div>

## 目的別にどうぞ

<div class="card-grid" markdown="0">
  <a href="getting-started.html"><strong>インストールして 1 回動かす</strong><span>Rig をセットアップし、Codex を Rig 経由で実行して、最初の結果を確認します。</span></a>
  <a href="workflows.html"><strong>適切なワークフローを選ぶ</strong><span>通常実行、隔離 Worktree 実行、手動実行、環境セットアップの選び方。</span></a>
  <a href="recipes.html"><strong>実例レシピ</strong><span>PR レビュー、リファクタ、テスト追加、複数エージェント比較などの実例。</span></a>
  <a href="agents.html"><strong>エージェント設定</strong><span>Codex、Claude、Gemini、Copilot、外部 GUI エージェントの設定例。</span></a>
  <a href="mcp.html"><strong>MCP クライアントを接続</strong><span>cwd とパッチ適用の安全ゲートを備えた MCP ツールとして Rig を公開。</span></a>
  <a href="faq.html"><strong>FAQ</strong><span>Rig を使う理由、パッケージマネージャとの違い、安全モデルについて。</span></a>
</div>

## メンタルモデル

Rig には 4 つのレイヤがあります。今知りたいことに最も合う行から読み始めてください。

| レイヤ | 答えること | 出発点 |
| --- | --- | --- |
| 実行 (Run) | エージェントは何をしたか? | [コアコンセプト](concepts.md) ・ [実行アーティファクト](artifacts.md) |
| ワークフロー | このタスクをどう実行すべきか? | [ワークフロー](workflows.md) ・ [レシピ](recipes.md) |
| 設定 | どのコマンドとポリシーを Rig が使うべきか? | [設定](configuration.md) ・ [エージェント](agents.md) ・ [プロンプトスタイル](prompts.md) |
| 連携 | 他のツールから Rig をどう呼ぶか? | [MCP サーバ](mcp.md) |

## よくある作業

- 初回セットアップ: [はじめに](getting-started.md)
- 通常実行と Worktree 実行の使い分け: [ワークフロー](workflows.md)
- 実行が書き出したファイルの中身を見る: [実行アーティファクト](artifacts.md)
- 正確なフラグを調べる: [コマンドリファレンス](commands.md)
- Codex 以外の CLI を設定する: [エージェント](agents.md)
- Rig が送るプロンプトをカスタマイズする: [プロンプトスタイル](prompts.md)
- ローカルセットアップのトラブルを直す: [トラブルシューティング](troubleshooting.md)
- このドキュメントサイト自体を保守する: [GitHub Pages](github-pages.md)

## Rig が「やらないこと」

- **エージェントアセット用のパッケージマネージャではない。** APM、GitHub CLI
  `gh skill`、Vercel `skills` などのツールが、スキル・フック・プロンプト・
  MCP サーバ設定の取得・ロック・デプロイを担います。
- **サンドボックスではない。** Rig は設定されたエージェントコマンドをあなたの
  シェルで実行します。生成された編集をメインの作業ツリーから隔離したいときは
  Worktree 実行を使ってください。
- **クラウドサービスではない。** Rig はローカル CLI です。状態はすべて
  `.rig/` 以下に保存されます。

## リポジトリ

- [GitHub リポジトリ](https://github.com/s-hiraoku/rig)
- [Changelog](https://github.com/s-hiraoku/rig/blob/main/CHANGELOG.md)
- [Roadmap](https://github.com/s-hiraoku/rig/blob/main/ROADMAP.md)
