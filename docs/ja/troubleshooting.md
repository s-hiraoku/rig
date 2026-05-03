---
title: トラブルシューティング
description: Rig のセットアップでよくあるつまづき — インストール、PATH、Codex の trusted directory、待機中の実行、env doctor、Pages デプロイなど。
lang: ja
permalink: /ja/troubleshooting.html
---

# トラブルシューティング

このページはセットアップ時のよくある問題集です。トピックで横断的に調べたい場合は
[FAQ](faq.md) も参照してください。

## `rig` コマンドが見つからない

インストールが完了していて、tool ディレクトリが `PATH` に通っているか確認します:

```bash
uv tool list
rig --help
```

必要に応じて再インストール:

```bash
uv tool install --force --refresh "rig @ git+https://github.com/s-hiraoku/rig.git"
```

`uv tool list` には Rig が出るのにシェルから見つからない場合は、
`$(uv tool dir --bin)` が `PATH` に入っているか確認します (多くのシェルでは
最初の `uv tool install` の後に自動的に通ります)。

## Codex が見つからない

デフォルトの `codex` エージェントは `codex exec` を使います。Codex CLI を
インストールし、`codex` が `PATH` に通っているか確認します:

```bash
codex --help
```

別の CLI を使うなら `.rig/config.yaml` で設定してください。
[エージェント](agents.md) を参照。

## Trusted Directory エラー
{: #trusted-directory-error }

Codex が現在のディレクトリを信頼できないと報告した場合:

```txt
Not inside a trusted directory and --skip-git-repo-check was not specified.
```

プロジェクトを Git リポジトリとして初期化してから再実行してください:

```bash
git init
```

これは Rig ではなく Codex の要件です。他の CLI では Git 必須ではない場合があります。

## 実行がない

`rig list` と `rig show latest` は `.rig/runs/` を読みます。先に実行を作って
ください:

```bash
rig run codex --task "現在の差分をレビューして。"
```

実行したのに `rig list` が `No runs found.` を出し続ける場合、同じプロジェクト
ディレクトリにいるか確認してください。`.rig/runs/` はプロジェクトごとです。

## 実行が `waiting` のまま

`manual` ランナーは `waiting` ステータスの実行を作ります。明示的に完了 / 失敗と
マークしてください:

```bash
rig manual complete latest --result "外部で完了。"
rig manual fail latest --error "外部でブロック。"
```

これらのコマンドは `waiting` の実行にしか作用しないので、実 `exec` 実行を上書き
することはありません。

## 終了コード 124 で失敗した

これは Rig のタイムアウトシグナルです。エージェントが `timeout_seconds` より長く
動いたことを意味します。`.rig/config.yaml` でタイムアウトを伸ばすか、タスクを
分割してください。

```yaml
agents:
  codex:
    timeout_seconds: 1200
```

## Worktree のパッチに想定外のファイルが入る

Worktree のパッチには Git に無視されない未追跡ファイルが含まれます。ビルド成果物、
キャッシュ、`node_modules` などがパッチに含まれているなら、再実行 *の前に*
`.gitignore` に追加してください:

```text
node_modules/
dist/
.cache/
```

その上で再実行すると、新しいパッチからは無視対象が外れます。

## 環境チェックで失敗する

次のコマンドを使います:

```bash
rig env doctor
rig env doctor --json   # CI / スクリプト向けの構造化出力
rig env plan
```

これらは Rig 所有のファイル不足、`.rig/env.yaml` で宣言された必須プロジェクト
ファイル、設定済みエージェントコマンド、オプションのアセットマネージャを報告します。
ステータスは `ok` / `missing` / `optional` / `warn` の 4 種です。

`rig env bootstrap` は Rig 所有のファイルしか作りません。外部ツールはインストール
しません。

## MCP クライアントがファイルを読めない

MCP の `cwd` 値はサーバ起動ディレクトリ内、または `RIG_MCP_ROOT` を設定している
場合はそのルート内に解決される必要があります。MCP の `task_file` は選ばれた `cwd`
から解決され、プロジェクト内に留まる必要があります。クライアントが権限エラーのような
ものを受け取った場合、許可スコープ内にパスがあるか確認してください。
[MCP サーバ → 安全デフォルト](mcp.md#安全デフォルト) を参照。

## MCP `rig_apply_patch` が無効と返る

`rig_apply_patch` は `RIG_MCP_ALLOW_APPLY=1` を付けて起動しない限り無効です。
パッチ適用を意図的に許可する場合のみ、その変数付きで再起動してください:

```bash
RIG_MCP_ALLOW_APPLY=1 rig mcp serve
```

## GitHub Pages が更新されない
{: #github-pages-が更新されない }

Pages サイトは `.github/workflows/pages.yml` が `docs/` をビルドして配信しています。
GitHub の Pages 設定が「Deploy from GitHub Actions」になっていることを確認し、
Actions タブから Pages ワークフローを再実行してください。`docs/**` の外の変更は、
`.github/workflows/pages.yml` 自体が変わっていない限り、このワークフローを起動しません。

完全なパイプラインは [GitHub Pages](github-pages.md)。

## Rig 設定をリセットする

生成済み設定を Rig の現行デフォルトに戻したい場合 (既存ファイルはバックアップされます):

```bash
rig init --reset config
rig init --reset env
rig init --reset all   # 両方
```

`.rig/runs/` 以下の実行履歴はこれらのコマンドで触れられません。
