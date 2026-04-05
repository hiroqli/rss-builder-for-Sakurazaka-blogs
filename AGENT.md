# sakurazaka-rss

## 概要

櫻坂46公式ブログ（https://sakurazaka46.com/s/s46/diary/blog/list?ima=0000）をスクレイピングして RSS フィードを生成し、GitHub Pages（raw.githubusercontent.com）経由で配信するリポジトリ。

## ファイル構成

| ファイル | 役割 |
|---|---|
| `sakurazaka_rss.py` | スクレイピングして `feed.xml` を生成するメインスクリプト |
| `.github/workflows/generate-rss.yml` | 15分おきに `sakurazaka_rss.py` を実行し `feed.xml` をコミットする GitHub Actions ワークフロー |
| `feed.xml` | 生成される RSS フィード（.gitignore 済み・Actions 経由でのみコミット） |

## スクレイピング仕様

- 対象URL: `https://sakurazaka46.com/s/s46/diary/blog/list?ima=0000`
- `BlogParser`（`html.parser.HTMLParser` サブクラス）でHTMLをパース
- `<ul class="com-blog-part">` 内の各 `<li>` からエントリを取得
  - `<a href="/diary/detail/{id}">` → URL・記事ID
  - `<p class="name">` → メンバー名
  - `<p class="date*">` → 投稿日（`YYYY/M/DD` 形式）
  - `<h3 class="title">` → 記事タイトル
  - `<p class="lead">` → リード文
- 生成する RSS は RSS 2.0 形式（`xml.etree.ElementTree` 使用）

## RSS 購読 URL

```
https://raw.githubusercontent.com/hiroqli/rss-builder-for-Sakurazaka-blogs/main/feed.xml
```

## GitHub Actions フロー

1. 15分おき（`*/15 * * * *`）または手動（workflow_dispatch）でトリガー
2. Python 3.12 で `sakurazaka_rss.py` を実行 → `feed.xml` を生成
3. `feed.xml` に差分があればコミット・プッシュ（`github-actions[bot]` として）

## Claude への作業指示

- **外部ライブラリ禁止**: 標準ライブラリのみで実装すること（`requests`・`beautifulsoup4` 等を追加しない）
- **スクレイピング対象の構造変更対応**: サイト改修で取得できなくなった場合は `BlogParser` の `handle_starttag` / `handle_endtag` を修正する。まず実際のHTMLをブラウザのDevToolsで確認してクラス名・タグ構造を特定してから修正すること
- **feed.xml はコミットしない**: `.gitignore` に含まれているため、ローカルで生成してもコミット対象にならない。Actions 経由で自動コミットされる設計
- **テスト方法**: `python sakurazaka_rss.py` をローカルで実行し、`feed.xml` が生成されてエントリ数が表示されれば正常
