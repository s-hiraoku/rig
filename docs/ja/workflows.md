---
title: ワークフロー
description: rig run、rig worktree run、手動実行、環境セットアップの選び方ガイド。
lang: ja
permalink: /ja/workflows.html
---

# ワークフロー

Rig はエージェント作業を実行・追跡するいくつかの方法を提供します。必要な
隔離やレビューの度合いに応じてワークフローを選びましょう。エンドツーエンドの
完全な例は [レシピ](recipes.md) にあります。

## 判断ガイド

| 状況 | 使うもの | 理由 |
| --- | --- | --- |
| 小さく読み取り中心、低リスクなタスク | `rig run` | ログと履歴付きで最速。 |
| 作業ツリーが汚れている | `rig worktree run` | 生成された変更を現状の編集から分離。 |
| 大規模リファクタやリスクのある編集 | `rig worktree run` | 適用前にパッチをレビューできる。 |
| GUI / Web / 外部エージェントの作業 | `manual` ランナー | コマンドを起動せず、タスクと結果のみ追跡。 |
| どの方法か迷っている | `rig suggest` | リポジトリ状態を見て推奨を出す。 |

<div class="callout callout-tip" markdown="1">
<span class="callout-title">ヒント</span>
迷ったらまず <code>rig suggest "..."</code>。これは読み取りのみで、リポジトリを
調べて推奨を出すだけ。エージェントは決して起動されません。
</div>

## 通常実行

エージェントが現在の作業ツリーで直接動いて問題ない場合に使います。

```bash
rig run codex --task "現在の差分をレビューして。"
rig show latest
```

Rig はタスク、コマンドメタデータ、標準出力、標準エラー、結果、ステータスを
`.rig/runs/<run-id>/` 以下に書き出します。スクリプト用の構造化出力は
`--json` を付けてください:

```bash
rig run codex --task "現在の差分をレビューして。" --json | jq '.status'
```

`--dry-run` はエージェントを起動せずに実行アーティファクトとコマンドプレビューを
書き出します — Rig が起動する argv を確認したいときに便利です。

## 推奨実行

作業を始める前に Rig にリポジトリ状態を見せたいときは `rig suggest` を使います。

```bash
rig suggest "CLI コマンド構造をリファクタする。"
```

推奨はあくまで助言です。エージェントを起動することもパッチを適用することも
ありません。スクリプトには `--json`:

```bash
rig suggest "..." --json | jq -r '.recommendation'
```

出力には推奨コマンド、推奨理由、現在のリポジトリ状態の観察結果が含まれます。

## 隔離された Worktree 実行

メインの作業ツリーに反映する前に、生成された編集をレビューしたい場合に使います。

```bash
rig worktree run codex --task "依頼された変更を実装して。"
rig worktree show latest
rig worktree apply latest
```

パッチが間違っていれば、過去の試行を失わずに繰り返せます。各試行はそれぞれの
diff を持つ独立した実行です。

```bash
rig worktree run codex --task "再挑戦して。前回は worktree のパス処理が抜けていた。"
```

完了したら Rig 所有の worktree を片付けます:

```bash
rig worktree prune
```

<div class="callout callout-warn" markdown="1">
<span class="callout-title">注意</span>
Worktree のパッチには、Git に無視されない未追跡ファイルが含まれます。生成された
ビルド成果物などはパッチを適用する前に <code>.gitignore</code> に追加してください。
</div>

## 手動実行

Rig が直接起動できないツールで作業する場合は `manual` ランナーを使います。

```yaml
agents:
  external:
    runner: manual
```

```bash
rig run external --task "外部ツールでこれを完了して。"
rig manual complete latest --result "外部で完了した。"
```

手動実行は `waiting` 状態で始まります。明示的に完了または失敗とマークする必要が
あります:

```bash
rig manual fail latest --error "外部レビューでブロックされた。"
```

旧形式の `rig history complete` / `rig history fail` も互換のため動きますが、
内部的には `rig manual …` に正規化されます。

## 環境セットアップ
{: #環境セットアップ }

エージェントを動かす前にローカルのハーネスを点検したいときに使います。

```bash
rig env doctor          # 人間向けの診断
rig env doctor --json   # CI 用の構造化出力
rig env plan            # 読み取り専用のセットアップ計画
rig env bootstrap       # Rig 所有のファイルのうち不足分を作成
rig env manager status  # 宣言済みのアセットマネージャをチェック
rig guide agents        # AGENTS.md / CLAUDE.md 用のスニペット生成
```

`env bootstrap` は Rig 所有のファイルしか作りません。Rig がグローバルな
外部ツールやサードパーティ製エージェントアセットを勝手に入れることはありません。
`rig env doctor` のステータスは `ok` / `missing` / `optional` / `warn` の 4 種です。

`.rig/env.yaml` のスキーマは
[設定 → 環境設定](configuration.md#環境設定) を参照してください。
