---
title: Worktree 実行
description: 隔離された Git worktree でエージェントを動かし、パッチを取得・レビューしてから適用する。
lang: ja
permalink: /ja/worktrees.html
---

# Worktree 実行

Worktree 実行は `.rig/worktrees/<run-id>/` 以下の隔離された Git worktree で
エージェントを動かし、結果のパッチを `.rig/runs/<run-id>/diff.patch` に取得します。
メインの作業ツリーは触りません。

次のような場合に最適です:

- 作業ツリーが汚れていて、エージェントに触らせたくない。
- 適用前にレビューを挟みたいくらい大きな変更。
- 同じタスクを複数のエージェントで動かしてパッチを比較したい。

エンドツーエンドの例は
[レシピ → Worktree でリファクタする](recipes.md#worktree-でリファクタする) を
参照。

## Worktree で実行する

```bash
rig worktree run codex --task "依頼された変更を実装して。"
```

Rig は `.rig/worktrees/<run-id>/` を作り、そこでエージェントを動かし、取得した
パッチを `.rig/runs/<run-id>/diff.patch` に書き出します。

## パッチを確認する

```bash
rig worktree show latest
rig worktree show 20260504-141500-codex
```

実行のメタデータと取得済みパッチが表示されるので、レビューに使えます。

## パッチを適用する

```bash
rig worktree apply latest
```

`apply` はメイン作業ツリーに対して `git apply` を走らせます。コンフリクトは
`git apply` のエラーとして報告されるので、通常の Git ツールで解決してください。

<div class="callout callout-warn" markdown="1">
<span class="callout-title">注意</span>
Worktree のパッチは Git に無視されない未追跡ファイルを含みます。再実行する前に、
ビルド成果物 (例: <code>node_modules</code>、<code>dist</code>、キャッシュ類) を
<code>.gitignore</code> に追加してください。さもないとエージェントの一時ディレクトリを
コミットしてしまいます。
</div>

## 反復する

パッチが間違っていたら手で書き換えるのではなく、修正版のタスクで再実行します。
試行ごとに独立した実行と diff が残ります。

```bash
rig worktree run codex --task "再挑戦して。dry-run のパス処理は変えないで。"
rig worktree show latest
```

実行 ID で試行を比較できます:

```bash
rig worktree show 20260504-141500-codex > /tmp/a.patch
rig worktree show 20260504-142000-codex > /tmp/b.patch
diff /tmp/a.patch /tmp/b.patch
```

## 後片付け

```bash
rig worktree prune
```

`prune` は `.rig/worktrees/` 以下の Rig 作成ディレクトリを削除します。
`.rig/runs/` の実行記録は残るので、取得済みパッチは引き続き検査可能です。

## `rig run` との違い

| | `rig run` | `rig worktree run` |
| --- | --- | --- |
| 編集が反映される場所 | 現在の作業ツリー | `.rig/worktrees/<run-id>/` |
| `diff.patch` を取得する | しない | する |
| Git が必須 | CLI 次第 | 必須 (`git worktree` を使う) |
| 適用ステップ | なし | 明示的な `rig worktree apply` |

両方のフローは `.rig/runs/<run-id>/` に同じアーティファクトを書きます。Worktree 実行
だけが追加で `diff.patch` を持ちます。

## Worktree を使わない方がよい場合

- 読み取り中心のタスク (レビュー、説明、提案)。通常の `rig run` の方が早い。
- 呼び出し側のシェル基準でパスを解決する CLI。Worktree 実行は cwd を
  `.rig/worktrees/<run-id>/` に変更します — リポジトリルートを上に辿る CLI なら
  問題ないはずですが、まずは小さなタスクで動作確認しましょう。
