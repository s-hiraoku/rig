---
title: GitHub Pages
description: このユーザーガイドのビルドとデプロイの仕組み — docs/ 配下の Jekyll ソース、GitHub Actions ワークフロー、ローカルプレビュー手順。
lang: ja
permalink: /ja/github-pages.html
---

# GitHub Pages

このリポジトリは `docs/` ディレクトリのコンテンツを GitHub Actions と Jekyll で
ビルド・公開しています。Pages サイトは README とは意図的に分離されています。
README は短い入口、Pages は構造化されたマニュアルです。

## ファイル

- `docs/_config.yml` — Jekyll 設定とサイトのデフォルト。
- `docs/_layouts/default.html` — サイトの枠 (ヘッダ、サイドバー、テーマトグル、
  prev/next、フッタ)。
- `docs/assets/site.css` — サイトスタイル (ライト + ダーク、レスポンシブ)。
- `docs/index.md` — ガイドのランディングページ。
- `docs/*.md` — 個別ガイドページ。
- `docs/ja/*.md` — 日本語版ページ。
- `.github/workflows/pages.yml` — ビルド・デプロイワークフロー。

## ワークフロー

Pages ワークフローは `main` への `docs/**` への push、または
`.github/workflows/pages.yml` 自体の変更で起動します。GitHub Actions から
`workflow_dispatch` で手動起動も可能です。

ワークフローは:

1. リポジトリをチェックアウト。
2. GitHub Pages を構成。
3. Jekyll で `./docs` を `./_site` にビルド。
4. Pages のアーティファクトをアップロード。
5. `github-pages` 環境にデプロイ。

## リポジトリ設定

GitHub の Pages 設定で「Deploy from GitHub Actions」を選んでください。ワークフロー
は次の権限を必要とします (`pages.yml` で既に宣言済み):

- `contents: read`
- `pages: write`
- `id-token: write`

## ローカルプレビュー

ほとんどの編集はプレーン Markdown なので、テキストエディタや Markdown ビューアで
直接確認できます。サイトと同じテーマで Jekyll の完全レンダリングを見るには:

```bash
cd docs
bundle init
echo 'gem "github-pages", group: :jekyll_plugins' >> Gemfile
bundle install
bundle exec jekyll serve
```

ブラウザで `http://127.0.0.1:4000` を開きます。サイトは GitHub の許可済みプラグイン
セットを使うので、ローカルのレンダリング結果はデプロイ済みサイトと一致します。

## 新しいページを追加する

1. `docs/<page>.md` (英語) と `docs/ja/<page>.md` (日本語) を作成し、フロントマターを
   書きます:
   ```markdown
   ---
   title: ページタイトル
   description: SEO とサイドバー用の 1 行説明。
   lang: ja            # 日本語版のみ
   permalink: /ja/...  # 日本語版のみ
   ---

   # ページタイトル
   ...
   ```
2. `docs/_layouts/default.html` の `nav_data` を編集してサイドバーに追加します。
   各エントリは `Group|/path.html|Title` です。並び順が prev/next フッタの順序にも
   なります。日本語版は `nav_data` の `ja` ブランチに同様に追加します。
3. `main` に push (または PR をオープン)。Pages ワークフローが再ビルド・デプロイ
   します。

## 表記ルール

- ページタイトルは Title Case、セクション見出しは sentence case (英語の場合)。
  日本語版は通常の体言止めで OK。
- ページ間は積極的にクロスリンク。各ページ単体で完結させつつ、サイドバーが
  常に見えていることは前提にして OK です。
- コードサンプルは開きフェンスのあとに言語ヒント (` ```bash `、` ```yaml `、
  ` ```json ` など) を付けるとシンタックスハイライトが効きます。
- コールアウトは
  `<div class="callout callout-tip" markdown="1">…</div>` (または `callout-warn`、
  `callout-danger`) でラップします。

## デプロイのトラブル

push 後にサイトが更新されない場合は
[トラブルシューティング → GitHub Pages が更新されない](troubleshooting.md#github-pages-が更新されない)
を参照してください。
