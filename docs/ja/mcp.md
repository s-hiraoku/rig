---
title: MCP サーバ
description: Rig を stdio 上の MCP サーバとして起動し、run / list / suggest / get / apply ツールを cwd とパッチ適用の安全ゲート付きで公開する。
lang: ja
permalink: /ja/mcp.html
---

# MCP サーバ

Rig は stdio 上で MCP サーバを起動できます:

```bash
rig mcp serve
```

MCP 対応のエージェントは、CLI のテキストをパースせずに、実行の開始、実行履歴の
列挙、結果の検査、取得済み worktree diff の読み出しを行えます。

## ツール

| ツール | 用途 |
| --- | --- |
| `rig_run` | 新しい実行を開始。`rig run` のミラー。 |
| `rig_list_runs` | 最近の実行を一覧。`rig list` のミラー。 |
| `rig_list_agents` | `.rig/config.yaml` の設定済みエージェントを一覧。 |
| `rig_suggest` | タスクに対し `rig run` か `rig worktree run` を推奨。 |
| `rig_get_run` | 実行のメタデータを取得。 |
| `rig_get_result` | `result.md` を取得。 |
| `rig_get_diff` | Worktree 実行の `diff.patch` を取得。 |
| `rig_apply_patch` | 取得済みの worktree パッチを適用。**デフォルトでは無効。** |

これらのツールが内部で使うオーケストレータと実行ストアは、CLI が使うものと完全に
同一です。並行する別実装は存在しません。

## リソースとプロンプト

MCP サーバは以下も公開します:

- `rig_policy` — クライアントが Rig の利用ポリシーを取得するために呼べるプロンプト。
- `rig://policy` — 同じポリシーをリソース URI として。
- `rig://agents-md` — プロジェクトの `AGENTS.md` の内容 (存在する場合)。

## 安全デフォルト
{: #安全デフォルト }

MCP 呼び出しはサーバ起動ディレクトリ以下に限定されます。広いルート配下の
リポジトリで作業する場合は:

```bash
RIG_MCP_ROOT=/Users/me/code rig mcp serve
```

MCP クライアントが渡す `cwd` は `RIG_MCP_ROOT` 内に解決される必要があります。
相対パスの `task_file` は選ばれた `cwd` から解決され、これもプロジェクト内に
留まる必要があります。

`rig_apply_patch` は次のように起動した場合にのみ有効です:

```bash
RIG_MCP_ALLOW_APPLY=1 rig mcp serve
```

接続先のエージェントが、ユーザー明示指示の下で取得済みパッチを適用してよいと判断
できる場合のみ有効化してください。デフォルトで無効なのは意図的な設計です。リモート
の MCP クライアントが帯域外のオプトインなしに作業ツリーを変更すべきではないからです。

## 環境変数

| 変数 | 効果 |
| --- | --- |
| `RIG_MCP_ROOT` | MCP の `cwd` と `task_file` がこのルート以下に解決可能になる。デフォルトはサーバ起動ディレクトリ。 |
| `RIG_MCP_ALLOW_APPLY` | `1` で `rig_apply_patch` を有効化。デフォルトは無効。 |

## MCP クライアントから接続する

具体的な配線はクライアントごとに違いますが、パターンは共通です:

1. `rig mcp serve` を stdio で起動するサーバエントリを追加する。
2. (任意) クライアントが複数リポジトリを跨ぐ場合は `RIG_MCP_ROOT` を設定する。
3. (任意・明示オプトイン) パッチ適用を意図する場合のみ `RIG_MCP_ALLOW_APPLY=1`。

短いエンドツーエンド例は
[レシピ → MCP 経由で Rig を使う](recipes.md#mcp-経由で-rig-を使う) を参照。

## MCP 呼び出しを検査する

MCP 経由の実行も CLI 実行と同じ `.rig/runs/<run-id>/` 構造に保存されます (`command.json`
で解決済み argv まで含む)。「MCP 実行」の別レイヤは存在しません。MCP の `rig_run`
呼び出しは通常の実行を生成し、`rig list` と `rig show` で読めます。
