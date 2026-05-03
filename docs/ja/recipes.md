---
title: レシピ
description: PR レビュー、隔離リファクタ、テスト追加、複数エージェント比較、手動 GUI フローなどの実例集。
lang: ja
permalink: /ja/recipes.html
---

# レシピ

各レシピは完結したエンドツーエンドのフローです。Rig がインストール済みで、
プロジェクトで `rig init` 済みであることを前提にしています。
セットアップは [はじめに](getting-started.md) を参照してください。

## 現在の差分をレビューする

Rig を再現可能な PR レビューのフロントエンドとして使います。レビューは 1 件の
実行となり、結果が `.rig/runs/<run-id>/result.md` に保存されます。

```bash
rig run codex --task "ステージ済み・未ステージの差分をレビューして。バグや回帰、危険な挙動変更を指摘し、最後に `--- RIG RESULT ---` マーカーに続いて 1 段落の要約を書いて。"
rig show latest
```

過去のレビューを見るには:

```bash
rig list
rig show 20260504-141500-codex
```

チームで一貫させたいなら、`result.md` を非追跡のレビューフォルダに残すか、
PR 本文に貼り付けます。

## Worktree でリファクタする
{: #worktree-でリファクタする }

Worktree 実行は `.rig/worktrees/<run-id>/` 以下でエージェントに編集させ、作業ツリーを
触りません。Rig は生成されたパッチを取得し、適用前にレビューできます。

```bash
rig worktree run codex --task "cli.py の worktree ヘルパを rig/worktree_cli.py に切り出して。挙動は同一に保つ。"
rig worktree show latest
```

パッチが妥当なら:

```bash
rig worktree apply latest
```

問題があれば前の試行を失うことなく繰り返せます。試行ごとに独立した実行と diff が
できます。

```bash
rig worktree run codex --task "再挑戦して。前回は dry-run のパスを保持できていなかった。"
```

完了したら:

```bash
rig worktree prune
```

<div class="callout callout-warn" markdown="1">
<span class="callout-title">注意</span>
Worktree のパッチは、Git に無視されない未追跡ファイルを含みます。パッチを当てる前に
生成物 (例: <code>node_modules</code>、<code>dist</code>、キャッシュ) を
<code>.gitignore</code> に追加してください。さもないとエージェントの一時ディレクトリを
コミットしてしまいます。
</div>

## 実行前に判断する

`rig suggest` はエージェントを起動せずに作業ツリーを観察し、実行方法を推奨します。

```bash
rig suggest "CLI コマンド構造をリファクタする。" --json
```

JSON 形式はスクリプトで便利:

```bash
rig suggest "..." --json | jq -r '.recommendation'
# -> rig run | rig worktree run
```

これを pre-commit やチャットのスラッシュコマンドに組み込めば、汚れた作業ツリーで
コントリビュータが暴走するのを防げます。

## 実装の前にテストカバレッジを足す

2 段階のレシピ。先にテストを生成し、それに対して実装を進めます。各ステップは独立した
実行なので、テスト追加コミットは残しつつ実装試行だけを破棄、といった操作も簡単です。

```bash
rig worktree run codex --task "tests/test_run_store.py の dry-run パスを検証する失敗テストを追加して。rig/run_store.py は変更しないこと。"
rig worktree show latest
rig worktree apply latest
```

その後、実装をテストに合わせます:

```bash
rig worktree run codex --task "新しいテストを通して。差分は最小限に。"
rig worktree show latest
rig worktree apply latest
```

## 同じタスクで 2 つのエージェントを比較する
{: #同じタスクで-2-つのエージェントを比較する }

`.rig/config.yaml` で複数のエージェントを定義し ([エージェント](agents.md))、
同じタスクをそれぞれで実行します。各実行は別ディレクトリなので衝突しません。

```bash
rig worktree run codex --task-file task.md
rig worktree run claude --task-file task.md
rig list
diff <(rig worktree show 20260504-1500-codex)  <(rig worktree show 20260504-1505-claude)
```

`task-file` を使うと実行間でプロンプトが完全に同一になります。

## 手動 / GUI フロー

Rig が直接起動できないツールでの作業を追跡します。`manual` ランナーがタスクを記録し、
あとは待ちます。

```yaml
# .rig/config.yaml
agents:
  design:
    runner: manual
```

```bash
rig run design --task "Figma でツールバーを更新し、SVG を ui/icons/ にエクスポート。"
# ... Figma で作業 ...
rig manual complete latest --result "ツールバー更新と SVG エクスポートを完了。"
rig show latest
```

ブロック / 中止された場合:

```bash
rig manual fail latest --error "デザインレビューでブロック。"
```

`complete` と `fail` は `waiting` 状態の実行にしか作用しないので、実 exec 実行を
誤って上書きすることはありません。

## リスクの前に Dry-Run

`--dry-run` は `task.md`、`command.json`、`status.json` (status: `created`) を書き出し、
エージェントは起動しません。Rig が起動する argv を確認したいときに使えます。

```bash
rig run codex --task "全体で os.system を subprocess に置き換えて。" --dry-run
cat .rig/runs/$(ls -1t .rig/runs | head -n1)/command.json
```

問題なければ本実行:

```bash
rig run codex --task "全体で os.system を subprocess に置き換えて。"
```

## MCP 経由で Rig を使う
{: #mcp-経由で-rig-を使う }

エディタやチャットツールが MCP を話せるなら、Rig をサーバとして公開して、CLI の
テキストをパースせずに実行一覧の取得・新規実行・取得済みパッチの読み取りなどを
させられます。

```bash
rig mcp serve
```

または接続先のエージェントを信頼している場合に限り、パッチ適用を有効化:

```bash
RIG_MCP_ALLOW_APPLY=1 rig mcp serve
```

ツール、リソース URI、`RIG_MCP_ROOT` のスコープフラグについては
[MCP サーバ](mcp.md) を参照。

## AGENTS.md / CLAUDE.md スニペットを生成する

`rig guide agents` はプロジェクト指示ファイルに貼り付ける Markdown スニペットを
出力します。`--write` を付けると長文ポリシーは `.rig/instructions/rig.md` に
保存されるため、`AGENTS.md` 自体は短いまま保てます。

```bash
rig guide agents --target codex --write
rig guide agents --target claude --write --force
```

Rig が `AGENTS.md` や `CLAUDE.md` を直接編集することはありません。スニペットは
1 度だけ貼り付け、長文ポリシーは `.rig/` 以下に置きます。

## ローカル環境を診断する

Issue を立てる前やデバッグログを共有する前に実行してみてください:

```bash
rig env doctor --json | jq
rig env plan
rig env manager status
```

これらは読み取り専用です。Rig 所有のファイル不足、`.rig/env.yaml` で宣言された
必須ファイル、設定済みエージェントコマンド、オプションのアセットマネージャを
報告します。インストールは行いません。
