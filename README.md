# DSProg1-Final

Google が GitHub で公開しているリポジトリ一覧の先頭 2 ページから、リポジトリ名、主なプログラミング言語、スター数を取得します。Playwright の同期 API で公開ページを開き、Next をクリックして 2 ページ目に進みます。ページを開く前と Next をクリックする前に、それぞれ 1 秒待ちます。GitHub API は使用しません。

取得したデータは SQLite の `google_repos.db` に保存し、SQL の `SELECT` でスター数の多い順に表示します。再実行時は同じ名前のデータを更新します。

## 実行方法

Python 3.12 以上と uv を用意し、プロジェクトのディレクトリで次を実行します。

```sh
uv sync
uv run playwright install chromium
uv run python scraping.py
```
